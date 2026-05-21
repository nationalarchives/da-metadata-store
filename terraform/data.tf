data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_ssm_parameter" "saml_tenant" {
  name = "/saml/tenant"
}

data "aws_ssm_parameter" "secret_key" {
  name = "/django/secret"
}
