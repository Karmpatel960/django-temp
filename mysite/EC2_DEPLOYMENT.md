# Deploying Django Application on EC2

This guide provides step-by-step instructions for deploying the Django application on an AWS EC2 instance.

## Prerequisites

1. An AWS account
2. An EC2 instance with:
   - Ubuntu 20.04 or Amazon Linux 2
   - At least 2GB RAM and 1 vCPU
   - Security group with ports 22, 80, and 443 open
   - IAM role with permissions for:
     - S3 access (if using S3 for static/media files)
     - CloudWatch access (for logging)

## EC2 Instance Setup

### Launch an EC2 Instance

1. Launch an EC2 instance with Ubuntu 20.04 or Amazon Linux 2
2. Attach an IAM role with appropriate permissions
3. Ensure instance has at least 20GB of storage
4. Connect to your instance via SSH:

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Quick Setup

For a quick setup, you can use the provided setup script:

```bash
# Clone the repository
git clone https://your-repository-url.git
cd your-repository/test/django-temp/mysite

# Make the setup script executable
chmod +x ec2-setup.sh

# Run the setup script
./ec2-setup.sh
```

The script will:
1. Install Docker and Docker Compose
2. Create necessary directories
3. Set up environment variables
4. Configure CloudWatch monitoring
5. Start the application
6. Set up automatic backups

### Manual Setup

If you prefer to set up manually or need to customize the setup:

1. Install Docker:

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker $USER
```

2. Install Docker Compose:

```bash
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

3. Create necessary directories:

```bash
sudo mkdir -p /data/postgres
sudo mkdir -p /data/backups
sudo mkdir -p /etc/letsencrypt
sudo mkdir -p /var/www/certbot
sudo chown -R $USER:$USER /data
```

4. Create environment file:

```bash
# Generate a secure secret key
SECRET_KEY=$(openssl rand -hex 32)
# Get instance metadata
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
PUBLIC_DNS=$(curl -s http://169.254.169.254/latest/meta-data/public-hostname)
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone | sed 's/[a-z]$//')

cat << EOF > .env
# Django settings
DEBUG=0
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=localhost,127.0.0.1,$PUBLIC_IP,$PUBLIC_DNS

# Database settings
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_USER=postgres
POSTGRES_DB=django_db
DATABASE_URL=postgres://postgres:${POSTGRES_PASSWORD}@db:5432/django_db

# AWS settings
USE_S3=1
# If using EC2 IAM role, these can be left empty
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_DEFAULT_REGION=$REGION

# Logging
LOG_TO_CLOUDWATCH=1
CLOUDWATCH_LOG_GROUP=/django/app
EOF
```

5. Start the application:

```bash
sudo docker-compose -f docker-compose.ec2.yml up -d
```

## SSL Certificate Setup

To set up SSL with Let's Encrypt:

1. Update your DNS to point to your EC2 instance's IP address
2. Uncomment and edit the SSL certificate section in the `ec2-setup.sh` script:

```bash
# Domain name setup
DOMAIN="example.com"
EMAIL="admin@example.com"
sudo docker run -it --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/www/certbot:/var/www/certbot \
    certbot/certbot certonly --standalone \
    -d $DOMAIN -d www.$DOMAIN \
    --email $EMAIL --agree-tos --no-eff-email
```

3. Run the certificate section of the script

## Using S3 for Static and Media Files

To use S3 for static and media files:

1. Create an S3 bucket with appropriate permissions
2. Update the `.env` file with your S3 bucket information:

```
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_DEFAULT_REGION=your-region
```

3. If not using IAM roles, also provide:

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

4. Uncomment the S3 proxy settings in the `nginx.conf` file:

```
# Static files
location /static/ {
    proxy_pass https://your-bucket-name.s3.amazonaws.com/static/;
    proxy_set_header Host your-bucket-name.s3.amazonaws.com;
    proxy_set_header Authorization "";
    proxy_hide_header x-amz-id-2;
    proxy_hide_header x-amz-request-id;
    expires 30d;
}
```

## Monitoring and Maintenance

### CloudWatch Monitoring

The application is configured to send logs to CloudWatch. You can view these logs in the AWS Console under CloudWatch > Log Groups.

### Database Backups

Automatic database backups are configured to run daily at 2 AM. Backups are stored in `/data/backups` and also synced to S3 if configured.

### Container Management

Common Docker commands:

```bash
# View running containers
sudo docker ps

# View container logs
sudo docker logs mysite_web_1

# Restart the application
sudo docker-compose -f docker-compose.ec2.yml restart

# Stop the application
sudo docker-compose -f docker-compose.ec2.yml down

# Update the application (after pulling new code)
sudo docker-compose -f docker-compose.ec2.yml up -d --build
```

## Scaling and High Availability

For production workloads requiring high availability, consider:

1. Using AWS RDS instead of the containerized PostgreSQL
2. Setting up an Auto Scaling Group with multiple EC2 instances
3. Using an Application Load Balancer in front of your EC2 instances
4. Using ElastiCache for session storage
5. Migrating to ECS or EKS for container orchestration

## Troubleshooting

### Common Issues

1. **Container fails to start**: Check logs with `sudo docker logs mysite_web_1`
2. **Database connection errors**: Verify PostgreSQL container is running and credentials are correct
3. **SSL certificate issues**: Check that the certificate files are correctly mounted in the Nginx container
4. **S3 access problems**: Verify IAM permissions and bucket policies

For more detailed troubleshooting, check the application logs in CloudWatch.

## Security Best Practices

1. Keep the EC2 instance updated with security patches
2. Use strong passwords for all services
3. Restrict access to the instance using security groups
4. Use IAM roles with the principle of least privilege
5. Enable encryption for data at rest and in transit
6. Regularly backup your database and configuration 