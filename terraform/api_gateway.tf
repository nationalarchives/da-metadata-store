resource "aws_api_gateway_rest_api" "metadata_store" {
  name = "metadata-store"
  body = templatefile("${path.module}/apigateway/metadata_store.json.tpl", {
    region     = data.aws_region.current.name,
    account_id = data.aws_caller_identity.current.account_id
    cognito_id = aws_cognito_user_pool.main.id
  })
}

resource "aws_api_gateway_deployment" "metadata_store" {
  rest_api_id = aws_api_gateway_rest_api.metadata_store.id
}

resource "aws_api_gateway_stage" "metadata_store" {
  deployment_id = aws_api_gateway_deployment.metadata_store.id
  rest_api_id   = aws_api_gateway_rest_api.metadata_store.id
  stage_name    = terraform.workspace
}

resource "aws_api_gateway_rest_api" "cognito_proxy" {
  name = "cognito-proxy"
  endpoint_configuration {
    types            = ["PRIVATE"]
    vpc_endpoint_ids = [aws_vpc_endpoint.api_gateway.id]
  }
  body = templatefile("${path.module}/apigateway/cognito_proxy.json.tpl", {
    environment              = terraform.workspace
    region                   = data.aws_region.current.name,
    account_id               = data.aws_caller_identity.current.account_id
    api_gateway_vpc_endpoint = aws_vpc_endpoint.api_gateway.id
  })
}

resource "aws_api_gateway_deployment" "cognito_proxy" {
  rest_api_id = aws_api_gateway_rest_api.cognito_proxy.id
}

resource "aws_api_gateway_stage" "cognito_proxy" {
  deployment_id = aws_api_gateway_deployment.cognito_proxy.id
  rest_api_id   = aws_api_gateway_rest_api.cognito_proxy.id
  stage_name    = terraform.workspace
}