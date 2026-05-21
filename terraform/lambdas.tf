locals {
  bucket = "zappa-sui1a2tac"
}
resource "aws_lambda_function" "metadata_store" {
  s3_bucket = local.bucket
  s3_key    = "metadata-store.zip"

  function_name = "metadata-store"
  role          = aws_iam_role.metadata_store_lambda_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 512

  vpc_config {
    subnet_ids         = [aws_subnet.private_2a.id, aws_subnet.private_2b.id]
    security_group_ids = [aws_security_group.metadata_store_lambda.id]
  }

  environment {
    variables = {
      APP_BASE_URL          = "https://dbkf8zrho5zj1.cloudfront.net/"
      COGNItrueTO_CLIENT_ID = aws_cognito_user_pool_client.web_app.id
      COGNITO_SECRET        = aws_cognito_user_pool_client.web_app.client_secret
      DATABASE_URL          = "postgres://lambda_user@${aws_rds_cluster.metadata_store.endpoint}:5432/catalogue?sslmode=require"
      ISSUER                = "https://cognito-idp.eu-west-2.amazonaws.com/${aws_cognito_user_pool.main.id}"
      PROXY_URL             = aws_api_gateway_stage.metadata_store.invoke_url
      SECRET_KEY            = data.aws_ssm_parameter.secret_key.value
      USE_IAM_AUTH          = true
    }
  }

  tags = {
    Name = "metadata-store-lambda"
  }
}

data "archive_file" "catalogue_updates_code" {
  type        = "zip"
  source_file = "${path.module}/lambda/catalogue_updates.py"
  output_path = "${path.module}/lambda/catalogue_updates.zip"
}

# Catalogue Updates Lambda
resource "aws_lambda_function" "catalogue_updates" {
  filename         = data.archive_file.catalogue_updates_code.output_path
  source_code_hash = data.archive_file.catalogue_updates_code.output_base64sha256
  function_name    = "catalogue-updates"
  role             = aws_iam_role.catalogue_updates_lambda_role.arn
  handler          = "catalogue_updates.lambda_handler"
  runtime          = "python3.13"
  timeout          = 3
  memory_size      = 128

  vpc_config {
    subnet_ids         = [aws_subnet.private_2a.id, aws_subnet.private_2b.id]
    security_group_ids = [aws_security_group.metadata_store_lambda.id]
  }

  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.metadata_update_queue.url
    }
  }

  tags = {
    Name = "catalogue-updates-lambda"
  }
}

data "archive_file" "catalogue_cache_writer_code" {
  type        = "zip"
  source_file = "${path.module}/lambda/catalogue_cache_writer.py"
  output_path = "${path.module}/lambda/catalogue_cache_writer.zip"
}

resource "aws_lambda_function" "catalogue_write_cache" {
  filename      = data.archive_file.catalogue_cache_writer_code.output_path
  function_name = "catalogue-writer-cache"
  role          = aws_iam_role.catalogue_write_cache_lambda_role.arn
  handler       = "catalogue_cache_writer.lambda_handler"
  runtime       = "python3.13"
  timeout       = 63
  memory_size   = 128

  vpc_config {
    subnet_ids         = [aws_subnet.private_2a.id, aws_subnet.private_2b.id]
    security_group_ids = [aws_security_group.metadata_store_lambda.id]
  }

  environment {
    variables = {
      API_BASE_URL = "https://${aws_cloudfront_distribution.main.domain_name}"
      CACHE_BUCKET = "metadata-cache-${data.aws_caller_identity.current.account_id}-eu-west-2-an"
    }
  }

  tags = {
    Name = "catalogue-write-cache-lambda"
  }
}

# CloudWatch Log Groups for Lambdas
resource "aws_cloudwatch_log_group" "metadata_store" {
  name              = "/aws/lambda/metadata-store"
  retention_in_days = 7

  tags = {
    Name = "metadata-store-logs"
  }
}

resource "aws_cloudwatch_log_group" "catalogue_updates" {
  name              = "/aws/lambda/catalogue-updates"
  retention_in_days = 7

  tags = {
    Name = "catalogue-updates-logs"
  }
}

resource "aws_cloudwatch_log_group" "catalogue_write_cache" {
  name              = "/aws/lambda/catalogue-write-cache"
  retention_in_days = 7

  tags = {
    Name = "catalogue-write-cache-logs"
  }
}
