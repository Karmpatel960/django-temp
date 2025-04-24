variable "repository_name" {
  description = "Name of the ECR repository"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "atlas"
}

variable "environment" {
  description = "Environment (e.g., dev, staging, production)"
  type        = string
  default     = "production"
} 