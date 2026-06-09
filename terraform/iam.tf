module "run_e2e_tests_role" {
  count  = var.create_e2e_test_role ? 1 : 0
  source = "git::https://github.com/nationalarchives/da-terraform-modules//iam_role?ref=main"
  assume_role_policy = templatefile("${path.module}/templates/iam/roles/github_assume_role.json.tpl", {
    account_id = data.aws_caller_identity.current.account_id
  })
  name = "${var.environment}-run-e2e-tests-role"
  policy_attachments = {
    run_e2e_tests_policy = module.run_e2e_tests_policy[count.index].policy_arn
  }
  tags = {}
}

module "run_e2e_tests_policy" {
  count  = var.create_e2e_test_role ? 1 : 0
  source = "git::https://github.com/nationalarchives/da-terraform-modules//iam_policy?ref=main"
  name   = "${var.environment}-run-e2e-tests"
  policy_string = templatefile("${path.module}/templates/iam/policies/run_e2e_tests.json.tpl", {
    password_parameter_arn      = aws_ssm_parameter.cognito_test_password[count.index].arn,
    client_secret_parameter_arn = aws_ssm_parameter.api_client_secret.arn,
    client_id_parameter_arn     = aws_ssm_parameter.api_client_id.arn
  })
}

