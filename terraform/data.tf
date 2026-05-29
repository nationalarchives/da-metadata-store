data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_organizations_organization" "org" {}

data "aws_ssm_parameter" "admin_role" {
  name = "/dev/admin-role"
}