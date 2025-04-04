#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Your specific public IP
PUBLIC_IP="65.1.134.57"

echo -e "${GREEN}Starting Django Docker deployment script...${NC}"
echo -e "${GREEN}Using public IP: $PUBLIC_IP${NC}"

# Check if running on EC2 (basic check)
if [ ! -f /sys/hypervisor/uuid ] || [ "$(head -c 3 /sys/hypervisor/uuid)" != "ec2" ]; then
    echo -e "${YELLOW}Warning: This may not be an EC2 instance. Continuing anyway...${NC}"
fi

# Create project directories
echo -e "${GREEN}Creating project structure...${NC}"
mkdir -p mysite config/nginx

# Create requirements.txt file
echo -e "${GREEN}Creating requirements.txt...${NC}"
cat > mysite/requirements.txt << 'EOF'
Django==4.2.8
gunicorn==21.2.0
whitenoise==6.5.0
boto3==1.28.68
django-storages==1.14.2
requests==2.31.0
python-dotenv==1.0.0
EOF

# Create a basic Django project if none exists
if [ ! -f mysite/manage.py ]; then
    echo -e "${GREEN}Creating a basic Django project...${NC}"
    docker run --rm -v $(pwd)/mysite:/app -w /app python:3.11 bash -c "pip install django && django-admin startproject mysite . && python manage.py startapp main"
fi

# Create the Dockerfile
echo -e "${GREEN}Creating Dockerfile...${NC}"
cat > Dockerfile << 'EOF'
FROM python:3.11

WORKDIR /app

# Install required packages
COPY mysite/requirements.txt .
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Create SQLite database directory
RUN mkdir -p /data/db

# Set permissions
RUN chmod +x /app/entrypoint.sh

# Expose port for gunicorn
EXPOSE 8000

# Use entrypoint script to start the application
ENTRYPOINT ["/app/entrypoint.sh"]
EOF

# Create entrypoint script
echo -e "${GREEN}Creating entrypoint script...${NC}"
cat > entrypoint.sh << 'EOF'
#!/bin/bash

# Wait for a few seconds to ensure everything is ready
sleep 5

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if not exists
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then
    python manage.py createsuperuser --noinput || echo "Superuser already exists."
fi

# Start gunicorn
gunicorn mysite.wsgi:application --bind 0.0.0.0:8000
EOF

# Make entrypoint executable
chmod +x entrypoint.sh

# Create nginx configuration
echo -e "${GREEN}Creating nginx configuration...${NC}"
mkdir -p config/nginx
cat > config/nginx/default.conf << 'EOF'
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name localhost;

    client_max_body_size 100M;

    location /static/ {
        alias /app/static/;
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Create docker-compose.yml
echo -e "${GREEN}Creating docker-compose.yml...${NC}"
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    build: .
    restart: always
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
      - sqlite_data:/data/db
    environment:
      - DEBUG=${DEBUG:-0}
      - SECRET_KEY=${SECRET_KEY:-default_secret_key_change_in_production}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS:-localhost 127.0.0.1}
      - DATABASE_URL=sqlite:////data/db/db.sqlite3
      - DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
      - DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin}
      - DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
    depends_on:
      - nginx

  nginx:
    image: nginx:1.23-alpine
    restart: always
    volumes:
      - ./config/nginx/default.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "80:80"

  s3sync:
    image: amazon/aws-cli:latest
    restart: unless-stopped
    volumes:
      - sqlite_data:/data/db
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-}
      - AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
      - S3_BUCKET_NAME=${S3_BUCKET_NAME:-}
      - BACKUP_INTERVAL=${BACKUP_INTERVAL:-3600}
    command: >
      sh -c "
        if [ -n \"$$AWS_ACCESS_KEY_ID\" ] && [ -n \"$$AWS_SECRET_ACCESS_KEY\" ] && [ -n \"$$S3_BUCKET_NAME\" ]; then
          while true; do
            echo 'Backing up SQLite database to S3...'
            aws s3 sync /data/db s3://$$S3_BUCKET_NAME/db/
            echo 'Backup complete. Sleeping for $$BACKUP_INTERVAL seconds.'
            sleep $$BACKUP_INTERVAL
          done
        else
          echo 'AWS credentials or S3 bucket not provided. S3 backup disabled.'
          sleep infinity
        fi
      "

volumes:
  static_volume:
  media_volume:
  sqlite_data:
EOF

# Create .env file with specific public IP
echo -e "${GREEN}Creating .env file with your public IP...${NC}"
cat > .env << EOF
# Django settings
DEBUG=0
SECRET_KEY=change_this_to_a_secure_random_value
ALLOWED_HOSTS=localhost 127.0.0.1 $PUBLIC_IP

# Admin user (will be created automatically)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=change_this_password
DJANGO_SUPERUSER_EMAIL=admin@example.com

# AWS S3 for database backup (optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=
BACKUP_INTERVAL=3600
EOF

# Update Django settings if a settings file exists
if [ -f mysite/mysite/settings.py ]; then
    echo -e "${GREEN}Updating Django settings...${NC}"
    cat >> mysite/mysite/settings.py << 'EOF'

# Added by deployment script
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Update secret key from environment
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

# Update debug from environment
DEBUG = int(os.environ.get('DEBUG', DEBUG))

# Update allowed hosts from environment
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split() or ALLOWED_HOSTS

# Database path update
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/data/db/db.sqlite3' if os.path.exists('/data/db') else os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
EOF
fi

# Install Docker and Docker Compose
echo -e "${GREEN}Installing Docker and Docker Compose...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}You may need to log out and back in for Docker permissions to take effect${NC}"
else
    echo -e "${GREEN}Docker already installed${NC}"
fi

if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}Docker Compose already installed${NC}"
fi

# Configure AWS CLI if credentials provided
if grep -q "AWS_ACCESS_KEY_ID=" .env && grep -q "AWS_SECRET_ACCESS_KEY=" .env && grep -q "S3_BUCKET_NAME=" .env; then
    source .env
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ] && [ -n "$S3_BUCKET_NAME" ]; then
        echo -e "${GREEN}Configuring AWS CLI...${NC}"
        aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
        aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
        aws configure set default.region "$AWS_DEFAULT_REGION"
        
        # Check if S3 bucket exists, create if not
        if ! aws s3 ls "s3://$S3_BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
            echo -e "${GREEN}S3 bucket $S3_BUCKET_NAME found${NC}"
        else
            echo -e "${GREEN}Creating S3 bucket $S3_BUCKET_NAME...${NC}"
            aws s3 mb "s3://$S3_BUCKET_NAME"
        fi
    fi
fi

# Display security warning
echo -e "${RED}!!SECURITY WARNING!!${NC}"
echo -e "${RED}Before deploying to production:${NC}"
echo -e "1. Update SECRET_KEY in .env file"
echo -e "2. Change admin password in .env file"
echo -e "3. Update ALLOWED_HOSTS in .env file with your domain"
echo -e "4. Configure HTTPS for production use"

# Start Docker containers
echo -e "${GREEN}Starting Docker containers...${NC}"
docker-compose up -d

# Check if containers are running
echo -e "${GREEN}Checking container status...${NC}"
sleep 10
docker-compose ps

# Display success message and next steps
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}----------------------------------------${NC}"
echo -e "Your Django application should now be running at:"
echo -e "${GREEN}http://$PUBLIC_IP${NC}"
echo -e "${GREEN}----------------------------------------${NC}"
echo -e "Admin access:"
echo -e "URL: ${GREEN}http://$PUBLIC_IP/admin/${NC}"
echo -e "Username: ${GREEN}$(grep DJANGO_SUPERUSER_USERNAME .env | cut -d= -f2)${NC}"
echo -e "Password: ${GREEN}$(grep DJANGO_SUPERUSER_PASSWORD .env | cut -d= -f2)${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "To view logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "To stop: ${YELLOW}docker-compose down${NC}"
echo -e "To restart: ${YELLOW}docker-compose restart${NC}"