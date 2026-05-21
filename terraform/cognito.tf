# Cognito User Pool
locals {
  domain_name = "metadata-store"
}
resource "aws_cognito_user_pool" "main" {
  name = "${local.domain_name}-user-pool"

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  auto_verified_attributes = ["email"]

  username_attributes = ["email"]

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  schema {
    attribute_data_type      = "String"
    name                     = "email"
    required                 = true
    mutable                  = true
    developer_only_attribute = false
  }

  schema {
    attribute_data_type      = "String"
    name                     = "name"
    required                 = false
    mutable                  = true
    developer_only_attribute = false
  }

  tags = {
    Name = "${local.domain_name}-user-pool"
  }
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = local.domain_name
  user_pool_id = aws_cognito_user_pool.main.id
}

# Cognito App Client - Web (Django with federated login support)
resource "aws_cognito_user_pool_client" "web_app" {
  name         = "${local.domain_name}-web-app"
  user_pool_id = aws_cognito_user_pool.main.id
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  supported_identity_providers         = [aws_cognito_identity_provider.entra_saml.provider_name, "COGNITO"]

  callback_urls = [
    "http://localhost:8000/auth",
    "https://${local.domain_name}.example.com/auth"
  ]

  logout_urls = [
    "http://localhost:8000/logout",
    "https://${local.domain_name}.example.com/logout"
  ]

  default_redirect_uri = "http://localhost:8000/auth"

  enable_token_revocation = true
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 30

  read_attributes  = ["email", "email_verified", "name"]
  write_attributes = ["email", "name"]

  prevent_user_existence_errors = "ENABLED"
}

# Cognito App Client - API
resource "aws_cognito_user_pool_client" "api_client" {
  name         = "${local.domain_name}-api-client"
  user_pool_id = aws_cognito_user_pool.main.id
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_CUSTOM_AUTH"
  ]

  generate_secret = true

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials"]
  allowed_oauth_scopes                 = ["${local.domain_name}/read", "${local.domain_name}/write"]

  token_validity_units {
    access_token  = "minutes"
    refresh_token = "days"
  }

  access_token_validity  = 60
  refresh_token_validity = 30

  prevent_user_existence_errors = "ENABLED"
}

# Cognito Identity Provider - Entra (Microsoft Azure AD) SAML
resource "aws_cognito_identity_provider" "entra_saml" {
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Entra"
  provider_type = "SAML"

  attribute_mapping = {
    email       = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    name        = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
    family_name = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
  }

  provider_details = {
    MetadataURL = "https://login.microsoftonline.com/${data.aws_ssm_parameter.saml_tenant.value}/federationmetadata/2007-06/federationmetadata.xml"
  }
}

