module "metadata_store_lambda" {
  source        = "git::https://github.com/nationalarchives/da-terraform-modules//lambda?ref=changes-for-metadata-store"
  function_name = var.app_name
  policies = {
    metadata_store_policy = templatefile("${path.module}/templates/iam/policies/metadata_store.json.tpl", {
      region         = data.aws_region.current.region
      account_number = data.aws_caller_identity.current.account_id
      cluster_id     = aws_rds_cluster.metadata_store.cluster_resource_id
    })
  }
  filename        = "metadata-store.zip"
  handler         = "handler.lambda_handler"
  runtime         = "python3.12"
  timeout_seconds = 30
  memory_size     = 512
  code_sha256     = filebase64sha256("metadata-store.zip")
  vpc_config = {
    subnet_ids         = module.vpc.private_subnets
    security_group_ids = [module.metadata_store_lambda_security_group.security_group_id]
  }
  lambda_invoke_permissions = {
    "apigateway.amazonaws.com" = "arn:aws:execute-api:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:${aws_apigatewayv2_api.metadata_store.id}/*/*/{path+}"
  }
  plaintext_env_vars = {
    APP_BASE_URL     = "https://${aws_cloudfront_distribution.site.domain_name}"
    API_GATEWAY_URL  = "${aws_apigatewayv2_api.metadata_store.id}.execute-api.${data.aws_region.current.region}.amazonaws.com"
    CLIENT_ID        = aws_cognito_user_pool_client.web_app.id
    CLIENT_SECRET    = aws_cognito_user_pool_client.web_app.client_secret
    DATABASE_URL     = "postgres://lambda_user@${aws_rds_cluster.metadata_store.endpoint}:5432/catalogue?sslmode=require"
    ISSUER           = "https://cognito-idp.${data.aws_region.current.region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
    ACCESS_TOKEN_URL = "${aws_api_gateway_stage.cognito_proxy.invoke_url}/oauth2/token"
    SECRET_KEY       = var.app_secret
    USE_IAM_AUTH     = true
    LOGOUT_BASE_URL  = "https://${var.app_name}.auth.eu-west-2.amazoncognito.com/"
  }
  tags = {}
}

data "archive_file" "catalogue_updates_code" {
  type        = "zip"
  source_file = "${path.module}/templates/lambda/catalogue_updates.py"
  output_path = "${path.module}/templates/lambda/catalogue_updates.zip"
}

module "catalogue_updates_lambda" {
  source        = "git::https://github.com/nationalarchives/da-terraform-modules//lambda?ref=changes-for-metadata-store"
  function_name = "${var.environment}-catalogue-updates"
  policies = {
    catalogue_updates_policy = templatefile("${path.module}/templates/iam/policies/catalogue_updates.json.tpl", {
      sqs_arn = module.metadata_update_queue.sqs_arn
    })
  }
  filename        = data.archive_file.catalogue_updates_code.output_path
  code_sha256     = data.archive_file.catalogue_updates_code.output_base64sha256
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.12"
  timeout_seconds = 30
  memory_size     = 512
  vpc_config = {
    subnet_ids         = module.vpc.private_subnets
    security_group_ids = [module.catalogue_updates_lambda_security_group.security_group_id]
  }
  plaintext_env_vars = {
    QUEUE_URL = module.metadata_update_queue.sqs_queue_url
  }
  tags = {}
}

data "archive_file" "catalogue_cache_writer_code" {
  type        = "zip"
  source_file = "${path.module}/templates/lambda/catalogue_cache_writer.py"
  output_path = "${path.module}/templates/lambda/catalogue_cache_writer.zip"
}


module "catalogue_write_cache_lambda" {
  source        = "git::https://github.com/nationalarchives/da-terraform-modules//lambda?ref=changes-for-metadata-store"
  function_name = "${var.environment}-catalogue-write-cache"
  policies = {
    catalogue_write_cache_policy = templatefile("${path.module}/templates/iam/policies/catalogue_write_cache.json.tpl", {
      sqs_arn      = module.metadata_update_queue.sqs_arn
      cache_bucket = "arn:aws:s3:::${module.metadata_store_cache.s3_bucket_name}"
    })
  }
  filename        = data.archive_file.catalogue_cache_writer_code.output_path
  code_sha256     = data.archive_file.catalogue_cache_writer_code.output_base64sha256
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.12"
  timeout_seconds = 900
  memory_size     = 512
  plaintext_env_vars = {
    API_BASE_URL = "https://${aws_cloudfront_distribution.site.domain_name}"
    CACHE_BUCKET = local.cache_bucket_name
  }
  tags = {}
}

module "data_migrations_lambda" {
  source        = "git::https://github.com/nationalarchives/da-terraform-modules//lambda?ref=changes-for-metadata-store"
  function_name = "${var.environment}-data-migration"
  policies = {
    data_migrations_policy = templatefile("${path.module}/templates/iam/policies/metadata_store.json.tpl", {
      region         = data.aws_region.current.region
      account_number = data.aws_caller_identity.current.account_id
      cluster_id     = aws_rds_cluster.metadata_store.cluster_resource_id
    })
  }
  filename        = "migrate.zip"
  handler         = "migrate.lambda_handler"
  runtime         = "python3.12"
  timeout_seconds = 120
  memory_size     = 512
  code_sha256     = filebase64sha256("migrate.zip")
  vpc_config = {
    subnet_ids         = module.vpc.private_subnets
    security_group_ids = [module.metadata_store_lambda_security_group.security_group_id]
  }
  plaintext_env_vars = {
    DATABASE_URL = "postgres://lambda_user@${aws_rds_cluster.metadata_store.endpoint}:5432/catalogue?sslmode=require"
    USE_IAM_AUTH = true
    TEST         = var.environment == "prod"
  }
  tags = {}
}

