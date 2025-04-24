variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (e.g., dev, staging, production)"
  type        = string
}

variable "media_bucket_name" {
  description = "Name of the S3 bucket for media files"
  type        = string
}

variable "static_bucket_name" {
  description = "Name of the S3 bucket for static files"
  type        = string
} 