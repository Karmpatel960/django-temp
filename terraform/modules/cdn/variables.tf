variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "A map of tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "cloudfront_price_class" {
  description = "The price class for CloudFront distribution"
  type        = string
  default     = "PriceClass_100" # Use PriceClass_100, PriceClass_200, or PriceClass_All
}

variable "domain_name" {
  description = "Custom domain name for CloudFront distribution"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for custom domain"
  type        = string
  default     = ""
}

variable "static_path_pattern" {
  description = "The path pattern for static files"
  type        = string
  default     = "/static/*"
}

variable "media_path_pattern" {
  description = "The path pattern for media files"
  type        = string
  default     = "/media/*"
}

variable "static_ttl" {
  description = "TTL for static files in CloudFront cache (seconds)"
  type        = number
  default     = 604800 # 1 week
}

variable "media_ttl" {
  description = "TTL for media files in CloudFront cache (seconds)"
  type        = number
  default     = 2592000 # 30 days
}

variable "default_ttl" {
  description = "Default TTL for CloudFront cache (seconds)"
  type        = number
  default     = 86400 # 1 day
}

variable "max_ttl" {
  description = "Maximum TTL for CloudFront cache (seconds)"
  type        = number
  default     = 31536000 # 1 year
}

variable "alb_dns_name" {
  description = "The DNS name of the ALB"
  type        = string
}

variable "static_bucket_name" {
  description = "Name of the S3 bucket for static files"
  type        = string
}

variable "static_bucket_arn" {
  description = "The ARN of the S3 bucket for static files"
  type        = string
}

variable "static_bucket_regional_domain_name" {
  description = "The regional domain name of the S3 bucket for static files"
  type        = string
}

variable "media_bucket_name" {
  description = "Name of the S3 bucket for media files"
  type        = string
}

variable "media_bucket_arn" {
  description = "The ARN of the S3 bucket for media files"
  type        = string
}

variable "media_bucket_regional_domain_name" {
  description = "The regional domain name of the S3 bucket for media files"
  type        = string
}

variable "alb_domain_name" {
  description = "The domain name of the ALB"
  type        = string
}

variable "static_bucket_domain" {
  description = "The domain name of the S3 bucket for static files"
  type        = string
}

variable "media_bucket_domain" {
  description = "The domain name of the S3 bucket for media files"
  type        = string
} 