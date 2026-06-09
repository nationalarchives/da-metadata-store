variable "app_name" {}

variable "use_entra_for_sso" {
  type    = bool
  default = false
}

variable "environment" {}

variable "saml_tenant" {}

variable "app_secret" {
  sensitive = true
}

variable "entra_app_id" {}

variable "create_e2e_test_role" {}