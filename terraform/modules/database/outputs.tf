output "db_instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.postgres.id
}

output "db_endpoint" {
  description = "Connection endpoint for the database"
  value       = aws_db_instance.postgres.endpoint
}

output "db_name" {
  description = "Name of the database"
  value       = aws_db_instance.postgres.name
}

output "db_username" {
  description = "Master username for the database"
  value       = aws_db_instance.postgres.username
  sensitive   = true
} 