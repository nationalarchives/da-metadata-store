data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host_header" {
  name = "Managed-AllViewerExceptHostHeader"
}

locals {
  lambda_integration_uri = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${aws_lambda_function.metadata_store_api.arn}/invocations"

  lambda_environment = {
    DJANGO_SETTINGS_MODULE = "store.settings"
    SECRET_KEY             = data.aws_ssm_parameter.secret_key
    DEBUG                  = "False"
    APP_BASE_URL           = data.aws_ssm_parameter.app_base_url
    SAML_IDP_ENTITY_ID     = data.aws_ssm_parameter.saml_idp_entity_id
    SAML_IDP_SSO_URL       = data.aws_ssm_parameter.saml_idp_sso_url
    SAML_IDP_SLO_URL       = data.aws_ssm_parameter.saml_idp_slo_url
    SAML_IDP_CERT          = data.aws_ssm_parameter.saml_idp_cert
    AWS_REGION             = data.aws_region.current.name
    USE_IAM_AUTH           = "true"
  }
}

resource "aws_iam_role" "lambda_execution" {
  name = "metadata-store-api-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "metadata_store_api" {
  function_name = "metadata-store-api"
  role          = aws_iam_role.lambda_execution.arn
  filename      = "metadata-store.zip"
  source_code_hash = filebase64sha256("metadata-store.zip")
  runtime       = "python3.12"
  handler       = "handler.lambda_handler"
  memory_size   = 1024
  timeout       = 90

  environment {
    variables = local.lambda_environment
  }
}

resource "aws_apigatewayv2_api" "metadata_store" {
  name          = "metadata-store-api"
  protocol_type = "HTTP"
  body          = templatefile("${path.module}/templates/api.json", {
    integration_uri = local.lambda_integration_uri
  })
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.metadata_store.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowExecutionFromApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.metadata_store_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.metadata_store.execution_arn}/*/*"
}

resource "aws_s3_bucket" "static" {
  bucket = "intg-metadata-store-site"
}

resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_cloudfront_origin_access_control" "static" {
  name                              = "metadata-store-static-oac"
  description                       = "OAC for ${aws_s3_bucket.static.bucket}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "metadata_store" {
  enabled             = true
  default_root_object = ""

  origin {
    domain_name = aws_s3_bucket.static.bucket_regional_domain_name
    origin_id   = "static-s3-origin"

    origin_access_control_id = aws_cloudfront_origin_access_control.static.id
  }

  origin {
    domain_name = replace(aws_apigatewayv2_api.metadata_store.api_endpoint, "https://", "")
    origin_id   = "api-gateway-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/static/*"
    target_origin_id       = "static-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]
    cache_policy_id = data.aws_cloudfront_cache_policy.caching_optimized.id
  }

  default_cache_behavior {
    target_origin_id       = "api-gateway-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods          = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods           = ["GET", "HEAD", "OPTIONS"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

data "aws_iam_policy_document" "static_bucket_policy" {
  statement {
    sid    = "AllowCloudFrontRead"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.static.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.metadata_store.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "static" {
  bucket = aws_s3_bucket.static.id
  policy = data.aws_iam_policy_document.static_bucket_policy.json
}
