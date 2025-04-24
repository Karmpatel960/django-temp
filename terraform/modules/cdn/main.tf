terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 3.0.0"
    }
  }
}

# Origin Access Identities for S3 buckets
resource "aws_cloudfront_origin_access_identity" "static_oai" {
  comment = "OAI for ${var.project_name} static files"
}

resource "aws_cloudfront_origin_access_identity" "media_oai" {
  comment = "OAI for ${var.project_name} media files"
}

# Main CloudFront distribution
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name} CloudFront Distribution"
  price_class         = var.cloudfront_price_class
  wait_for_deployment = false
  
  # If a custom domain is provided
  aliases = var.domain_name != "" ? [var.domain_name] : []
  
  # ALB Origin for default content
  origin {
    domain_name = var.alb_dns_name
    origin_id   = "alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # S3 Origin for static files
  origin {
    domain_name = var.static_bucket_regional_domain_name
    origin_id   = "s3-static"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.static_oai.cloudfront_access_identity_path
    }
  }

  # S3 Origin for media files
  origin {
    domain_name = var.media_bucket_regional_domain_name
    origin_id   = "s3-media"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.media_oai.cloudfront_access_identity_path
    }
  }

  # Default behavior (ALB)
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "alb"

    forwarded_values {
      query_string = true
      cookies {
        forward = "all"
      }
      headers = ["Host", "Origin"]
    }

    min_ttl                = 0
    default_ttl            = var.default_ttl
    max_ttl                = var.max_ttl
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }
  
  # Static files behavior
  ordered_cache_behavior {
    path_pattern     = var.static_path_pattern
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "s3-static"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 0
    default_ttl            = var.static_ttl
    max_ttl                = var.max_ttl
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }

  # Media files behavior
  ordered_cache_behavior {
    path_pattern     = var.media_path_pattern
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "s3-media"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 0
    default_ttl            = var.media_ttl
    max_ttl                = var.max_ttl
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }
  
  # Custom error responses
  custom_error_response {
    error_code         = 404
    response_code      = 404
    response_page_path = "/404.html"
  }
  
  custom_error_response {
    error_code         = 403
    response_code      = 403
    response_page_path = "/403.html"
  }
  
  # Viewer certificate configuration
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  
  # Geo restriction
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  # Tags
  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-cloudfront"
      Environment = var.environment
    }
  )
}

# Policy document for static S3 bucket
data "aws_iam_policy_document" "static_s3_policy" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${var.static_bucket_arn}/*"]
    
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.static_oai.iam_arn]
    }
  }
}

# Policy document for media S3 bucket
data "aws_iam_policy_document" "media_s3_policy" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${var.media_bucket_arn}/*"]
    
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.media_oai.iam_arn]
    }
  }
}

# Attach policy to static S3 bucket
resource "aws_s3_bucket_policy" "static_bucket_policy" {
  bucket = var.static_bucket_name
  policy = data.aws_iam_policy_document.static_s3_policy.json
}

# Attach policy to media S3 bucket
resource "aws_s3_bucket_policy" "media_bucket_policy" {
  bucket = var.media_bucket_name
  policy = data.aws_iam_policy_document.media_s3_policy.json
}

# Generate a config file with deployment information for DNS setup
resource "local_file" "dns_config" {
  content = <<-EOT
    # DNS Configuration for External DNS Provider
    # Please update your DNS settings at your provider with these values

    Domain: ${var.domain_name}
    
    # CloudFront Distribution Information
    CloudFront Domain: ${aws_cloudfront_distribution.main.domain_name}
    
    # Create the following records at your DNS provider:
    
    # For apex domain (${var.domain_name}):
    # Type: CNAME
    # Name: @
    # Value: ${aws_cloudfront_distribution.main.domain_name}
    # TTL: 300
    
    # For www subdomain:
    # Type: CNAME
    # Name: www
    # Value: ${aws_cloudfront_distribution.main.domain_name}
    # TTL: 300
    
    # Note: Some DNS providers don't allow CNAME records for apex domains.
    # In that case, check if your provider offers ALIAS/ANAME records or similar functionality.
  EOT
  
  filename = "${path.module}/dns_setup_instructions.txt"
} 
} 