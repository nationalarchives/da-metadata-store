resource "aws_apigatewayv2_api" "metadata_store" {
  name = var.app_name
  body = templatefile("${path.module}/templates/apigateway/metadata_store.json.tpl", {
    region      = data.aws_region.current.region,
    account_id  = data.aws_caller_identity.current.account_id
    cognito_id  = aws_cognito_user_pool.main.id
    title       = var.app_name
    lambda_name = var.app_name
  })
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_deployment" "metadata_store" {
  api_id = aws_apigatewayv2_api.metadata_store.id
}

resource "aws_apigatewayv2_stage" "metadata_store" {
  api_id      = aws_apigatewayv2_api.metadata_store.id
  name        = var.environment
  auto_deploy = true
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.metadata_store_api.arn
    format = jsonencode(
      {
        "httpMethod"     = "$context.httpMethod"
        "ip"             = "$context.identity.sourceIp"
        "protocol"       = "$context.protocol"
        "requestId"      = "$context.requestId"
        "requestTime"    = "$context.requestTime"
        "responseLength" = "$context.responseLength"
        "routeKey"       = "$context.routeKey"
        "status"         = "$context.status"
        "path"           = "$context.path"
      }
    )
  }
}

resource "aws_cloudwatch_log_group" "metadata_store_api" {
  name              = "API-Gateway-Execution-Logs_${aws_apigatewayv2_api.metadata_store.id}/${var.environment}"
  retention_in_days = 365
}

resource "aws_cloudwatch_log_group" "cognito_proxy_api" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.cognito_proxy.id}/${var.environment}"
  retention_in_days = 365
}

resource "aws_iam_role" "cloudwatch" {
  name = "api_gateway_cloudwatch_global"
  assume_role_policy = templatefile("${path.module}/templates/iam/roles/service_source_account_only.json.tpl", {
    account_id = data.aws_caller_identity.current.account_id
    service    = "apigateway"
  })
}

resource "aws_iam_role_policy" "cloudwatch" {
  policy = templatefile("${path.module}/templates/iam/policies/api_gateway_cloudwatch.json.tpl", {})
  role   = aws_iam_role.cloudwatch.id
}

resource "aws_api_gateway_account" "metadata_store" {
  cloudwatch_role_arn = aws_iam_role.cloudwatch.arn
}

resource "aws_api_gateway_rest_api" "cognito_proxy" {
  name              = "${var.environment}-cognito-proxy"
  put_rest_api_mode = "merge"
  endpoint_configuration {
    types            = ["PRIVATE"]
    vpc_endpoint_ids = [module.vpc.interface_endpoints["execute_api"].id]
  }
  body = templatefile("${path.module}/templates/apigateway/cognito_proxy.json.tpl", {
    title          = "${var.environment}-cognito-proxy"
    environment    = var.environment
    region         = data.aws_region.current.region,
    account_id     = data.aws_caller_identity.current.account_id
    cognito_domain = var.app_name
  })
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_rest_api_policy" "cognito_proxy" {
  policy = templatefile("${path.module}/templates/iam/policies/cognito_proxy_policy.json.tpl", {
    region                   = data.aws_region.current.region,
    account_id               = data.aws_caller_identity.current.account_id
    api_gateway_vpc_endpoint = module.vpc.interface_endpoints["execute_api"].id
  })
  rest_api_id = aws_api_gateway_rest_api.cognito_proxy.id
}

resource "aws_api_gateway_deployment" "cognito_proxy" {
  rest_api_id = aws_api_gateway_rest_api.cognito_proxy.id
  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.cognito_proxy.body))
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "cognito_proxy" {
  deployment_id = aws_api_gateway_deployment.cognito_proxy.id
  rest_api_id   = aws_api_gateway_rest_api.cognito_proxy.id
  stage_name    = var.environment
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.cognito_proxy_api.arn
    format = jsonencode(
      {
        "httpMethod"     = "$context.httpMethod"
        "ip"             = "$context.identity.sourceIp"
        "protocol"       = "$context.protocol"
        "requestId"      = "$context.requestId"
        "requestTime"    = "$context.requestTime"
        "responseLength" = "$context.responseLength"
        "routeKey"       = "$context.routeKey"
        "status"         = "$context.status"
        "path"           = "$context.path"
      }
    )
  }
}

resource "aws_wafv2_web_acl_association" "proxy_waf_association" {
  resource_arn = aws_api_gateway_stage.cognito_proxy.arn
  web_acl_arn  = aws_wafv2_web_acl.web_acl["cognito"].arn
}