output "lambda_function_name" {
  value       = aws_lambda_function.metadata_store_api.function_name
  description = "Name of the metadata-store API Lambda function."
}

output "api_gateway_endpoint" {
  value       = aws_apigatewayv2_api.metadata_store.api_endpoint
  description = "Invoke endpoint for the HTTP API Gateway."
}

output "static_bucket_name" {
  value       = aws_s3_bucket.static.bucket
  description = "S3 bucket used for static file hosting."
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.metadata_store.domain_name
  description = "CloudFront distribution domain name."
}
