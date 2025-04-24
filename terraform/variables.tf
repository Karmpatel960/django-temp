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

variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "aws_access_key_id" {
  description = "AWS access key ID for the application"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS secret access key for the application"
  type        = string
  sensitive   = true
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]
}

# Database Configuration
variable "db_instance_class" {
  description = "Instance class for the RDS database"
  type        = string
  default     = "db.t3.small"
}

variable "db_allocated_storage" {
  description = "Allocated storage for the RDS database (in GB)"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "atlasdb"
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "atlasadmin"
  sensitive   = true
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}

# Load Balancer and DNS Configuration
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "atlas-classroom.example.com"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS"
  type        = string
  default     = ""
}

variable "create_route53_zone" {
  description = "Whether to create a Route53 hosted zone"
  type        = bool
  default     = false
}

# ECS Configuration
variable "app_image_tag" {
  description = "Tag for the application Docker image"
  type        = string
}

variable "container_port" {
  description = "Port on which the container listens"
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "CPU units for the container"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Memory for the container (in MiB)"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired number of container instances"
  type        = number
  default     = 2
}

# Django Configuration
variable "django_secret_key" {
  description = "Secret key for Django"
  type        = string
  sensitive   = true
}

# Alerting Configuration
variable "alarm_email" {
  description = "Email address to send CloudWatch alarms to"
  type        = string
  default     = "admin@example.com"
}

# CDN Configuration
variable "enable_cdn" {
  description = "Whether to enable CloudFront CDN"
  type        = bool
  default     = true
} 