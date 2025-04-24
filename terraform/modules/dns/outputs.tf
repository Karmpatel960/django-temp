output "zone_id" {
  description = "ID of the Route53 zone"
  value       = local.zone_id
}

output "domain_name" {
  description = "Domain name"
  value       = var.domain_name
}

output "fqdn" {
  description = "Fully qualified domain name"
  value       = aws_route53_record.main.fqdn
} 