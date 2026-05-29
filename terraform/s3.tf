locals {
  cache_bucket_name        = "${var.app_name}-cache-${data.aws_caller_identity.current.account_id}-eu-west-2-an"
  static_files_bucket_name = "${var.app_name}-static-files-${data.aws_caller_identity.current.account_id}-eu-west-2-an"
}
module "metadata_store_static_files" {
  source            = "../../../da/da-terraform-modules/s3"
  bucket_name       = local.static_files_bucket_name
  bucket_namespace  = "account-regional"
  create_log_bucket = false
  bucket_policy = templatefile("${path.module}/templates/s3/static_files.json.tpl", {
    bucket_name    = local.static_files_bucket_name
    cloudfront_arn = aws_cloudfront_distribution.site.arn
  })
}

module "metadata_store_cache" {
  source            = "../../../da/da-terraform-modules/s3"
  bucket_name       = local.cache_bucket_name
  bucket_namespace  = "account-regional"
  create_log_bucket = false
}