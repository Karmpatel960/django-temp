#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Your specific public IP
PUBLIC_IP="65.1.134.57"

# Replace with your Git repository URL
GIT_REPO_URL="https://github.com/Karmpatel960/django-temp.git"
GIT_BRANCH="main"  # Or your desired branch

echo -e "${GREEN}Starting Django Docker deployment script...${NC}"
echo -e "${GREEN}Using public IP: $PUBLIC_IP${NC}"

# Check if Git repository URL is provided
if [ -z "$GIT_REPO_URL" ]; then
    echo -e "${RED}Error: Please edit this script to include your Git repository URL${NC}"
    echo -e "Edit this file and set the GIT_REPO_URL variable"
    exit 1
fi

# Install Git if not installed
if ! command -v git &> /dev/null; then
    echo -e "${GREEN}Installing Git...${NC}"
    sudo apt-get update
    sudo apt-get install -y git
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

# Clone the repository
echo -e "${GREEN}Cloning your repository...${NC}"
git clone -b $GIT_BRANCH $GIT_REPO_URL django-project
cd django-project

# Update ALLOWED_HOSTS in settings (if it exists)
if [ -f mysite/mysite/settings.py ]; then
    echo -e "${GREEN}Updating ALLOWED_HOSTS in settings.py...${NC}"
    # Add your IP to ALLOWED_HOSTS if not already there
    if ! grep -q "$PUBLIC_IP" mysite/mysite/settings.py; then
        sed -i "s/ALLOWED_HOSTS = \[.*\]/ALLOWED_HOSTS = \['localhost', '127.0.0.1', '$PUBLIC_IP'\]/" mysite/mysite/settings.py
    fi
fi

# Create or update .env file
echo -e "${GREEN}Creating/updating .env file...${NC}"
if [ ! -f .env ]; then
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
else
    # Update existing .env file with the new IP
    if ! grep -q "$PUBLIC_IP" .env; then
        sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost 127.0.0.1 $PUBLIC_IP/" .env
    fi
fi

# Make entrypoint.sh executable (if it exists)
if [ -f entrypoint.sh ]; then
    echo -e "${GREEN}Making entrypoint.sh executable...${NC}"
    chmod +x entrypoint.sh
fi

# Display security warning
echo -e "${RED}!!SECURITY WARNING!!${NC}"
echo -e "${RED}Before deploying to production:${NC}"
echo -e "1. Update SECRET_KEY in .env file"
echo -e "2. Change admin password in .env file"
echo -e "3. Configure HTTPS for production use"

# Build and start Docker containers
echo -e "${GREEN}Building and starting Docker containers...${NC}"
docker-compose build
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
echo -e "Admin access (if configured):"
echo -e "URL: ${GREEN}http://$PUBLIC_IP/admin/${NC}"
if [ -f .env ] && grep -q "DJANGO_SUPERUSER_USERNAME" .env; then
    echo -e "Username: ${GREEN}$(grep DJANGO_SUPERUSER_USERNAME .env | cut -d= -f2)${NC}"
    echo -e "Password: ${GREEN}$(grep DJANGO_SUPERUSER_PASSWORD .env | cut -d= -f2)${NC}"
fi
echo -e "${GREEN}=========================================${NC}"
echo -e "To view logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "To stop: ${YELLOW}docker-compose down${NC}"
echo -e "To restart: ${YELLOW}docker-compose restart${NC}"
echo -e "To update from Git: ${YELLOW}git pull && docker-compose build && docker-compose up -d${NC}"