resource "aws_cognito_user_pool" "sso_user_pool" {
  count = var.use_entra_for_sso ? 0 : 1
  name  = "${var.app_name}-sso-user-pool"
  admin_create_user_config {
    allow_admin_create_user_only = true
  }
  user_pool_add_ons {
    advanced_security_mode = "AUDIT"
  }

}

resource "aws_cognito_user_pool_client" "sso_client" {
  count                        = var.use_entra_for_sso ? 0 : 1
  name                         = "${var.app_name}-sso-user-pool-client"
  user_pool_id                 = aws_cognito_user_pool.sso_user_pool[count.index].id
  generate_secret              = true
  callback_urls                = ["https://${var.app_name}.auth.${data.aws_region.current.region}.amazoncognito.com/oauth2/idpresponse"]
  supported_identity_providers = ["COGNITO"]
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

  user_pool_add_ons {
    advanced_security_mode = "AUDIT"
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
    allow_admin_create_user_only = true
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

resource "aws_wafv2_web_acl_association" "main" {
  resource_arn = aws_cognito_user_pool.main.arn
  web_acl_arn  = aws_wafv2_web_acl.cognito_web_acl.arn
}

resource "aws_wafv2_web_acl_association" "sso_user_pool" {
  count        = var.use_entra_for_sso ? 0 : 1
  resource_arn = aws_cognito_user_pool.sso_user_pool[count.index].arn
  web_acl_arn  = aws_wafv2_web_acl.cognito_web_acl.arn
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = var.app_name
  user_pool_id = aws_cognito_user_pool.main.id
}

resource "aws_cognito_user_pool_domain" "sso" {
  count        = var.use_entra_for_sso ? 0 : 1
  domain       = "${var.app_name}-sso"
  user_pool_id = aws_cognito_user_pool.sso_user_pool[count.index].id
}

resource "random_password" "test_password" {
  count       = var.use_entra_for_sso ? 0 : 1
  length      = 10
  min_special = 1
}

resource "aws_ssm_parameter" "cognito_test_password" {
  count = var.use_entra_for_sso ? 0 : 1
  name  = "/cognito/test/password"
  type  = "SecureString"
  value = random_password.test_password[count.index].result
}

resource "aws_cognito_user" "user" {
  count        = var.use_entra_for_sso ? 0 : 1
  user_pool_id = aws_cognito_user_pool.sso_user_pool[count.index].id
  username     = "test@test.com"
  password     = random_password.test_password[count.index].result
  attributes = {
    email = "test@test.com"
  }
}

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
  supported_identity_providers         = [var.use_entra_for_sso ? one(aws_cognito_identity_provider.entra_saml).provider_name : one(aws_cognito_identity_provider.cognito_oidc).provider_name]

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
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_details = {
    authorize_scopes              = "email openid"
    client_id                     = aws_cognito_user_pool_client.sso_client[count.index].id
    client_secret                 = aws_cognito_user_pool_client.sso_client[count.index].client_secret
    oidc_issuer                   = "https://cognito-idp.eu-west-2.amazonaws.com/${aws_cognito_user_pool.sso_user_pool[count.index].id}"
    attributes_request_method     = "GET"
    attributes_url_add_attributes = false
  }
  attribute_mapping = {
    email    = "email"
    username = "sub"
  }
}
resource "aws_cognito_identity_provider" "entra_saml" {
  count           = var.use_entra_for_sso ? 1 : 0
  user_pool_id    = aws_cognito_user_pool.main.id
  provider_name   = "Entra"
  provider_type   = "SAML"
  idp_identifiers = []
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
resource "aws_wafv2_web_acl" "cognito_web_acl" {
  region = data.aws_region.current.region
  name   = "${var.environment}-wafwebacl-cognito"
  scope  = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AntiDDOS"
    priority = 2

    override_action {
      count {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAntiDDoSRuleSet"
        vendor_name = "AWS"

        managed_rule_group_configs {
          aws_managed_rules_anti_ddos_rule_set {
            client_side_action_config {
              challenge {
                usage_of_action = "DISABLED"
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AntiDDOS"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 10000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "WAFRules"
    sampled_requests_enabled   = true
  }
}

