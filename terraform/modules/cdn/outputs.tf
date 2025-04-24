output "cloudfront_distribution_id" {
  description = "The ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_distribution_domain_name" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_distribution_arn" {
  description = "The ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.arn
}

output "cloudfront_distribution_hosted_zone_id" {
  description = "The CloudFront Route 53 zone ID"
  value       = aws_cloudfront_distribution.main.hosted_zone_id
}

output "static_s3_iam_policy_document" {
  description = "The IAM policy document that allows CloudFront to access the static S3 bucket"
  value       = data.aws_iam_policy_document.static_s3_policy.json
}

output "media_s3_iam_policy_document" {
  description = "The IAM policy document that allows CloudFront to access the media S3 bucket"
  value       = data.aws_iam_policy_document.media_s3_policy.json
}

output "static_origin_access_identity_iam_arn" {
  description = "The IAM ARN of the CloudFront origin access identity for static files"
  value       = aws_cloudfront_origin_access_identity.static_oai.iam_arn
}

output "media_origin_access_identity_iam_arn" {
  description = "The IAM ARN of the CloudFront origin access identity for media files"
  value       = aws_cloudfront_origin_access_identity.media_oai.iam_arn
}

output "static_bucket_policy_json" {
  description = "The IAM policy document for the static S3 bucket in JSON format"
  value       = data.aws_iam_policy_document.static_s3_policy.json
}

output "media_bucket_policy_json" {
  description = "The IAM policy document for the media S3 bucket in JSON format"
  value       = data.aws_iam_policy_document.media_s3_policy.json
}

output "static_s3_access_identity_path" {
  description = "Path for static files CloudFront Origin Access Identity"
  value       = aws_cloudfront_origin_access_identity.static_origin_access_identity.cloudfront_access_identity_path
}

output "media_s3_access_identity_path" {
  description = "Path for media files CloudFront Origin Access Identity"
  value       = aws_cloudfront_origin_access_identity.media_origin_access_identity.cloudfront_access_identity_path
}

output "static_oai_path" {
  description = "CloudFront Origin Access Identity path for static files"
  value       = aws_cloudfront_origin_access_identity.static_oai.cloudfront_access_identity_path
}

output "media_oai_path" {
  description = "CloudFront Origin Access Identity path for media files"
  value       = aws_cloudfront_origin_access_identity.media_oai.cloudfront_access_identity_path
}

output "hostname" {
  description = "Hostname of the CloudFront distribution"
  value       = var.domain_name
}

output "dns_instructions" {
  description = "Instructions for setting up DNS with your provider"
  value       = "Please follow the instructions in dns_setup_instructions.txt to configure your domain with your DNS provider."
} 