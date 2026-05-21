resource "aws_sqs_queue" "metadata_update_queue" {
  name = "${terraform.workspace}-metadata-update-queue"
}