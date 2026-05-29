resource "aws_cognito_user_pool" "sso_user_pool" {
  count = var.use_entra_for_sso ? 0 : 1
  name  = "${var.app_name}-sso-user-pool"
}

resource "aws_cognito_user_pool_client" "sso_client" {
  count        = var.use_entra_for_sso ? 0 : 1
  name         = "${var.app_name}-sso-user-pool-client"
  user_pool_id = aws_cognito_user_pool.sso_user_pool[count.index].id
}

resource "aws_cognito_user_pool" "main" {
  name = "${var.app_name}-user-pool"

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

  tags = {
    Name = "${var.app_name}-user-pool"
  }
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = var.app_name
  user_pool_id = aws_cognito_user_pool.main.id
}

resource "random_password" "test_password" {
  count  = var.environment == "prod" ? 0 : 1
  length = 10
}

resource "aws_ssm_parameter" "cognito_test_password" {
  count = var.environment == "prod" ? 0 : 1
  name  = "/cognito/test/password"
  type  = "SecureString"
  value = random_password.test_password[count.index].result
}

resource "aws_cognito_user" "user" {
  count        = var.environment == "prod" ? 0 : 1
  user_pool_id = aws_cognito_user_pool.main.id
  username     = "test@test.com"
  password     = random_password.test_password[count.index].result
}

# Cognito App Client - Web (Django with federated login support)
resource "aws_cognito_user_pool_client" "web_app" {
  name         = "${var.app_name}-web-app"
  user_pool_id = aws_cognito_user_pool.main.id
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_CUSTOM_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]
  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  supported_identity_providers         = [var.environment == "prod" ? one(aws_cognito_identity_provider.entra_saml).provider_name : one(aws_cognito_identity_provider.cognito_oidc).provider_name]

  callback_urls = [
    "http://localhost:8000/auth",
    "https://${aws_cloudfront_distribution.site.domain_name}/auth",
    "https://${aws_cloudfront_distribution.site.domain_name}/",
  ]

  logout_urls = [
    "http://localhost:8000/logout",
    "https://${aws_cloudfront_distribution.site.domain_name}/logout"
  ]

  default_redirect_uri = "https://${aws_cloudfront_distribution.site.domain_name}/"

  enable_token_revocation = true
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 30

  read_attributes  = ["email", "email_verified", "name", "given_name", "family_name"]
  write_attributes = ["email", "name", "given_name", "family_name"]

  prevent_user_existence_errors = "ENABLED"
}

# Cognito App Client - API
resource "aws_cognito_user_pool_client" "api_client" {
  name         = "${var.app_name}-api-client"
  user_pool_id = aws_cognito_user_pool.main.id
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_CUSTOM_AUTH"
  ]

  generate_secret = true

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["client_credentials"]
  allowed_oauth_scopes                 = ["${var.app_name}/read", "${var.app_name}/write"]

  token_validity_units {
    access_token  = "minutes"
    refresh_token = "days"
  }

  access_token_validity  = 60
  refresh_token_validity = 30

  prevent_user_existence_errors = "ENABLED"
}


resource "aws_cognito_identity_provider" "cognito_oidc" {
  count         = var.use_entra_for_sso ? 0 : 1
  provider_name = "${var.app_name}-sso-provider"
  provider_type = "OIDC"
  user_pool_id  = aws_cognito_user_pool.sso_user_pool[count.index].id
  provider_details = {
    authorize_scopes = "email"
    client_id        = aws_cognito_user_pool_client.sso_client[count.index].id
    client_secret    = aws_cognito_user_pool_client.sso_client[count.index].client_secret
  }
}
resource "aws_cognito_identity_provider" "entra_saml" {
  count         = var.use_entra_for_sso ? 1 : 0
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Entra"
  provider_type = "SAML"

  attribute_mapping = {
    email       = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    family_name = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
    given_name  = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
    name        = "http://schemas.microsoft.com/identity/claims/displayname"
    username    = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
  }

  provider_details = {
    MetadataURL = "https://login.microsoftonline.com/${var.saml_tenant}/federationmetadata/2007-06/federationmetadata.xml?appid=${var.entra_app_id}"
  }
  lifecycle {
    ignore_changes = [provider_details["ActiveEncryptionCertificate"], provider_details["SLORedirectBindingURI"], provider_details["SSORedirectBindingURI"]]
  }
}

resource "aws_cognito_resource_server" "resource" {
  identifier = var.app_name
  name       = "Metadata store"

  scope {
    scope_name        = "read"
    scope_description = "Is allowed to read all metadata"
  }

  scope {
    scope_name        = "write"
    scope_description = "Is allowed to write all metadata"
  }

  user_pool_id = aws_cognito_user_pool.main.id
}

