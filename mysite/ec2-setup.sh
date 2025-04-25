#!/bin/bash
set -e

# EC2 Setup Script for Django Application
# This script sets up a new EC2 instance to run the Django application

# Detect OS type
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION_ID=$VERSION_ID
fi

echo "Detected OS: $OS $VERSION_ID"

# Update system packages
echo "Updating system packages..."
if [[ "$OS" == *"Amazon"* ]]; then
    # Amazon Linux specific
    sudo yum update -y
    
    # Handle Amazon Linux 2023 vs Amazon Linux 2
    if [[ "$VERSION_ID" == *"2023"* ]]; then
        # Amazon Linux 2023
        echo "Installing dependencies for Amazon Linux 2023..."
        sudo yum install -y --allowerasing unzip tar wget git
        # Only install packages that aren't already installed
        if ! command -v curl &> /dev/null; then
            sudo yum install -y --allowerasing curl
        fi
        
        # Install Docker for AL2023
        echo "Installing Docker..."
        sudo yum install -y docker
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        # Amazon Linux 2
        echo "Installing dependencies for Amazon Linux 2..."
        sudo yum install -y curl unzip tar wget git
        
        # Install Docker for AL2
        echo "Installing Docker..."
        sudo amazon-linux-extras install -y docker
        sudo systemctl start docker
        sudo systemctl enable docker
    fi
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    # Other RHEL-based
    sudo yum update -y
    sudo yum upgrade -y
    
    # Install dependencies
    echo "Installing dependencies..."
    sudo yum install -y curl unzip tar wget git
    
    # Install Docker
    echo "Installing Docker..."
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y docker-ce docker-ce-cli containerd.io
    sudo systemctl start docker
    sudo systemctl enable docker
else
    # Ubuntu/Debian-based
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Docker
    echo "Installing Docker..."
    
    # Check Ubuntu version
    if [[ "$OS" == *"Ubuntu"* ]] && [[ "$VERSION_ID" == "24.04" ]]; then
        # Ubuntu 24.04 uses the Ubuntu repository for Docker
        echo "Detected Ubuntu 24.04, using Ubuntu repository for Docker..."
        sudo apt-get install -y ca-certificates curl gnupg
        sudo apt-get install -y docker.io containerd
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        # Ubuntu 20.04, 22.04 or other Debian distros
        sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        
        # Add Docker's official GPG key
        if [[ "$OS" == *"Ubuntu"* ]] && [[ "$VERSION_ID" == "22.04" ]]; then
            # Ubuntu 22.04 
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        else
            # Ubuntu 20.04 or other Debian
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
            sudo add-apt-repository "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        fi
        
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    fi
    
    # Install Docker Compose
    echo "Installing Docker Compose..."
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Docker Compose (common for all Linux variants)
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed, skipping..."
fi

# Add the current user to the docker group
echo "Adding user to docker group..."
sudo usermod -aG docker $USER
echo "NOTE: You may need to log out and back in for the docker group changes to take effect."

# Create directories
echo "Creating necessary directories..."
sudo mkdir -p /data/postgres
sudo mkdir -p /data/backups
sudo mkdir -p /etc/letsencrypt
sudo mkdir -p /var/www/certbot
sudo chown -R $USER:$USER /data

# Set up environment variables
echo "Setting up environment variables..."
cat << 'EOF' > .env
# Django settings
DEBUG=0
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=localhost,127.0.0.1,$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4),$(curl -s http://169.254.169.254/latest/meta-data/public-hostname)

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
AWS_DEFAULT_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone | sed 's/[a-z]$//')

# Logging
LOG_TO_CLOUDWATCH=1
CLOUDWATCH_LOG_GROUP=/django/app
EOF

# Setup Cloudwatch Agent
echo "Setting up CloudWatch agent..."
if [[ "$OS" == *"Amazon"* ]]; then
    # Amazon Linux
    if [[ "$VERSION_ID" == *"2023"* ]]; then
        # Amazon Linux 2023
        sudo yum install -y amazon-cloudwatch-agent
    else
        # Amazon Linux 2
        sudo yum install -y amazon-cloudwatch-agent
    fi
else
    # Ubuntu/Debian or other Linux
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        wget https://s3.amazonaws.com/amazoncloudwatch-agent/debian/amd64/latest/amazon-cloudwatch-agent.deb
        sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
        rm ./amazon-cloudwatch-agent.deb
    else
        # RHEL/CentOS
        sudo yum install -y https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
    fi
fi

# Configure CloudWatch
cat << EOF > cloudwatch-config.json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/ec2/nginx/access",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "/ec2/nginx/error",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  },
  "metrics": {
    "metrics_collected": {
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "resources": [
          "/"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ]
      }
    }
  }
}
EOF
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:cloudwatch-config.json -s

# SSL setup with certbot (optional, uncomment to use)
# Domain name setup (replace with your actual domain)
# echo "Setting up SSL certificates..."
# DOMAIN="example.com"
# EMAIL="admin@example.com"
# sudo docker run -it --rm \
#     -v /etc/letsencrypt:/etc/letsencrypt \
#     -v /var/www/certbot:/var/www/certbot \
#     certbot/certbot certonly --standalone \
#     -d $DOMAIN -d www.$DOMAIN \
#     --email $EMAIL --agree-tos --no-eff-email

# Start the application
echo "Starting the application..."
sudo docker-compose -f docker-compose.ec2.yml up -d

# Set up automatic updates and backups
echo "Setting up automatic backups..."
cat << 'EOF' > /tmp/backup.sh
#!/bin/bash

# Create a database backup
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR=/data/backups
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker exec -t $(docker ps -q -f name=db) pg_dumpall -c -U postgres > $BACKUP_DIR/db-$TIMESTAMP.sql

# Rotate backups (keep last 7 days)
find $BACKUP_DIR -name "db-*.sql" -type f -mtime +7 -delete

# Sync backups to S3 if configured
if [[ -n "$AWS_STORAGE_BUCKET_NAME" ]]; then
  aws s3 sync $BACKUP_DIR s3://$AWS_STORAGE_BUCKET_NAME/backups/
fi
EOF

chmod +x /tmp/backup.sh
sudo mv /tmp/backup.sh /usr/local/bin/backup.sh

# Add to crontab
(crontab -l 2>/dev/null || echo "") | grep -v "backup.sh" | { cat; echo "0 2 * * * /usr/local/bin/backup.sh > /tmp/backup.log 2>&1"; } | crontab -

echo "EC2 setup complete! The application should now be running."
echo "You can access it at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "" 
echo "Next steps:"
echo "1. Configure your DNS to point to this server"
echo "2. Uncomment and update the SSL certificate section in this script then run again"
echo "3. Update the .env file with your specific settings" 