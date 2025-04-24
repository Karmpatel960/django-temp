terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket         = "atlas-terraform-state"
    key            = "atlas/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "atlas-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"

  vpc_name               = "${var.project_name}-vpc"
  vpc_cidr               = var.vpc_cidr
  availability_zones     = var.availability_zones
  private_subnet_cidrs   = var.private_subnet_cidrs
  public_subnet_cidrs    = var.public_subnet_cidrs
  database_subnet_cidrs  = var.database_subnet_cidrs
  project_name           = var.project_name
  environment            = var.environment
}

# Security Groups
module "security_groups" {
  source = "./modules/security"

  vpc_id      = module.vpc.vpc_id
  project_name = var.project_name
  environment = var.environment
}

# RDS Database
module "database" {
  source = "./modules/database"

  project_name             = var.project_name
  environment              = var.environment
  db_subnet_group_name     = module.vpc.database_subnet_group_name
  vpc_security_group_ids   = [module.security_groups.database_sg_id]
  db_instance_class        = var.db_instance_class
  db_allocated_storage     = var.db_allocated_storage
  db_name                  = var.db_name
  db_username              = var.db_username
  db_password              = var.db_password
  db_backup_retention_period = 7
  db_multi_az             = var.environment == "production" ? true : false
}

# S3 Buckets for Media and Static files
module "storage" {
  source = "./modules/storage"

  project_name          = var.project_name
  environment           = var.environment
  media_bucket_name     = "${var.project_name}-media-${var.environment}"
  static_bucket_name    = "${var.project_name}-static-${var.environment}"
}

# Application Load Balancer
module "load_balancer" {
  source = "./modules/load_balancer"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_sg_id
  domain_name           = var.domain_name
  certificate_arn       = var.certificate_arn
}

# ECS Cluster and Service
module "ecs" {
  source = "./modules/ecs"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.security_groups.app_sg_id
  alb_target_group_arn  = module.load_balancer.target_group_arn
  ecr_repository_url    = module.ecr.repository_url
  app_image_tag         = var.app_image_tag
  container_port        = var.container_port
  container_cpu         = var.container_cpu
  container_memory      = var.container_memory
  desired_count         = var.desired_count
  
  # Environment variables for the container
  environment_variables = [
    { name = "DEBUG", value = "0" },
    { name = "ALLOWED_HOSTS", value = var.domain_name },
    { name = "SECRET_KEY", value = var.django_secret_key },
    { name = "DATABASE_URL", value = "postgres://${var.db_username}:${var.db_password}@${module.database.db_endpoint}/${var.db_name}" },
    { name = "AWS_STORAGE_BUCKET_NAME", value = module.storage.media_bucket_name },
    { name = "AWS_S3_CUSTOM_DOMAIN", value = module.storage.media_bucket_domain },
    { name = "AWS_ACCESS_KEY_ID", value = var.aws_access_key_id },
    { name = "AWS_SECRET_ACCESS_KEY", value = var.aws_secret_access_key },
    { name = "AWS_DEFAULT_REGION", value = var.aws_region }
  ]
}

# ECR Repository
module "ecr" {
  source = "./modules/ecr"

  repository_name = "${var.project_name}-${var.environment}"
}

# CloudWatch Alarms and Logs
module "monitoring" {
  source = "./modules/monitoring"

  project_name        = var.project_name
  environment         = var.environment
  ecs_cluster_name    = module.ecs.cluster_name
  ecs_service_name    = module.ecs.service_name
  alb_arn_suffix      = module.load_balancer.alb_arn_suffix
  db_instance_id      = module.database.db_instance_id
  alarm_email         = var.alarm_email
}

# Route53 DNS
module "dns" {
  source = "./modules/dns"

  domain_name         = var.domain_name
  alb_dns_name        = module.load_balancer.alb_dns_name
  alb_zone_id         = module.load_balancer.alb_zone_id
  create_route53_zone = var.create_route53_zone
}

# CloudFront Distribution (Optional)
module "cdn" {
  source = "./modules/cdn"
  count  = var.enable_cdn ? 1 : 0

  project_name           = var.project_name
  environment            = var.environment
  domain_name            = var.domain_name
  alb_domain_name        = module.load_balancer.alb_dns_name
  acm_certificate_arn    = var.certificate_arn
  static_bucket_domain   = module.storage.static_bucket_domain
  media_bucket_domain    = module.storage.media_bucket_domain
} 