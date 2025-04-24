output "media_bucket_name" {
  description = "Name of the media bucket"
  value       = aws_s3_bucket.media.id
}

output "static_bucket_name" {
  description = "Name of the static bucket"
  value       = aws_s3_bucket.static.id
}

output "media_bucket_domain" {
  description = "Domain name for the media bucket"
  value       = "${aws_s3_bucket.media.id}.s3.amazonaws.com"
}

output "static_bucket_domain" {
  description = "Domain name for the static bucket"
  value       = "${aws_s3_bucket.static.id}.s3.amazonaws.com"
}

output "media_bucket_arn" {
  description = "ARN of the media bucket"
  value       = aws_s3_bucket.media.arn
}

output "static_bucket_arn" {
  description = "ARN of the static bucket"
  value       = aws_s3_bucket.static.arn
} 