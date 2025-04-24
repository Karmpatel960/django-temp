resource "aws_db_instance" "postgres" {
  identifier                  = "${var.project_name}-${var.environment}-db"
  allocated_storage           = var.db_allocated_storage
  storage_type                = "gp2"
  engine                      = "postgres"
  engine_version              = "13"
  instance_class              = var.db_instance_class
  name                        = var.db_name
  username                    = var.db_username
  password                    = var.db_password
  db_subnet_group_name        = var.db_subnet_group_name
  vpc_security_group_ids      = var.vpc_security_group_ids
  parameter_group_name        = aws_db_parameter_group.postgres.name
  backup_retention_period     = var.db_backup_retention_period
  backup_window               = "03:00-04:00"
  maintenance_window          = "sun:04:30-sun:05:30"
  multi_az                    = var.db_multi_az
  skip_final_snapshot         = var.environment != "production"
  final_snapshot_identifier   = var.environment == "production" ? "${var.project_name}-final-snapshot" : null
  deletion_protection         = var.environment == "production"
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  auto_minor_version_upgrade  = true
  publicly_accessible         = false
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  storage_encrypted           = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_db_parameter_group" "postgres" {
  name        = "${var.project_name}-${var.environment}-pg"
  family      = "postgres13"
  description = "Parameter group for ${var.project_name} ${var.environment} database"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-pg"
    Project     = var.project_name
    Environment = var.environment
  }
} 