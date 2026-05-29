locals {
  s3_origin_name     = "s3-origin"
  webapp_origin_name = "webapp-origin"
  us_east_1          = "us-east-1"
}
resource "aws_cloudfront_response_headers_policy" "security" {
  name    = "ResponseHeadersPolicy"
  comment = "Adds strict Content-Security-Policy for CloudFront responses"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    content_type_options {
      override = false
    }

    frame_options {
      frame_option = "DENY"
      override     = false
    }

    referrer_policy {
      referrer_policy = "strict-origin"
      override        = false
    }
  }
}

resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "${var.environment}-metadata-store-s3-oac"
  description                       = "OAC for S3 origin"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_cloudfront_cache_policy" "caching_optimised" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

resource "aws_cloudfront_distribution" "site" {

  enabled         = true
  is_ipv6_enabled = true
  comment         = var.app_name
  price_class     = "PriceClass_All"

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  origin {
    domain_name              = module.metadata_store_static_files.s3_bucket_regional_domain_name
    origin_id                = local.s3_origin_name
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  origin {
    domain_name = "${aws_apigatewayv2_api.metadata_store.id}.execute-api.eu-west-2.amazonaws.com"
    origin_id   = local.webapp_origin_name
    origin_path = "/${var.environment}"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = local.webapp_origin_name
    viewer_protocol_policy = "https-only"

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id
    # response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
  }

  ordered_cache_behavior {
    path_pattern           = "/static/*"
    target_origin_id       = local.s3_origin_name
    viewer_protocol_policy = "https-only"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD", "OPTIONS"]

    cache_policy_id = data.aws_cloudfront_cache_policy.caching_optimised.id

    # response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
  }
}

resource "aws_cloudwatch_log_delivery_source" "access_logs_source" {
  name         = "${var.environment}-site-access-logs"
  log_type     = "ACCESS_LOGS"
  region       = local.us_east_1
  resource_arn = aws_cloudfront_distribution.site.arn
}

resource "aws_cloudwatch_log_group" "site_access_logs" {
  name              = "${var.environment}-site-access-logs"
  region            = local.us_east_1
  retention_in_days = 90
}

resource "aws_cloudwatch_log_delivery_destination" "cloudfront_logs_destination" {
  name          = "${var.environment}-site-logs-destination"
  region        = local.us_east_1
  output_format = "json"
  delivery_destination_configuration {
    destination_resource_arn = aws_cloudwatch_log_group.site_access_logs.arn
  }
}

resource "aws_cloudwatch_log_delivery" "access_logs_delivery" {
  region                   = local.us_east_1
  delivery_source_name     = aws_cloudwatch_log_delivery_source.access_logs_source.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.cloudfront_logs_destination.arn
}
