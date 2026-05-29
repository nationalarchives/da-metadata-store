module "metadata_update_queue" {
  source     = "git::https://github.com/nationalarchives/da-terraform-modules//sqs"
  queue_name = "${var.app_name}-metadata-update"
  sqs_policy = null
}