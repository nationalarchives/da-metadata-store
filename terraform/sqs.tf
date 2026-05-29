locals {
  metadata_update_queue_name = "${var.app_name}-metadata-update"
}
module "metadata_update_queue" {
  source             = "git::https://github.com/nationalarchives/da-terraform-modules//sqs?ref=main"
  queue_name         = local.metadata_update_queue_name
  sqs_policy         = null
  visibility_timeout = 900
}