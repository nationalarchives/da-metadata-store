data "aws_ssm_parameter" "secret_key" {
  name = "/secret-key"
}

data "aws_ssm_parameter" "app_base_url" {
  name = "/base-url"
}

data "aws_ssm_parameter" "saml_idp_entity_id" {
  name = "/idp-entity-id"
}

data "aws_ssm_parameter" "saml_idp_sso_url" {
  name = "/idp-sso-url"
}

data "aws_ssm_parameter" "saml_idp_slo_url" {
  name = "/idp-slo-url"
}

data "aws_ssm_parameter" "saml_idp_cert" {
  name = "/idp-cert"
}