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

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
sudo apt-get update

# Install Git if not installed
if ! command -v git &> /dev/null; then
    echo -e "${GREEN}Installing Git...${NC}"
    sudo apt-get install -y git
fi

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}Installing Docker...${NC}"
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}Docker installed. You might need a new shell session for group changes to take effect.${NC}"
else
    echo -e "${GREEN}Docker already installed${NC}"
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}Docker Compose already installed${NC}"
fi

# Verify Docker installation
echo -e "${GREEN}Verifying Docker installation...${NC}"
docker --version
docker-compose --version

# Clone the repository
echo -e "${GREEN}Cloning your repository...${NC}"
git clone -b $GIT_BRANCH $GIT_REPO_URL django-project
cd django-project/mysite

# Make entrypoint.sh executable (if it exists)
if [ -f entrypoint.sh ]; then
    echo -e "${GREEN}Making entrypoint.sh executable...${NC}"
    chmod +x entrypoint.sh
fi

# Check for docker-compose file and build containers
if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}Found docker-compose.yml in root directory${NC}"
elif [ -f "mysite/docker-compose.yml" ]; then
    echo -e "${GREEN}Found docker-compose.yml in mysite directory${NC}"
    cd mysite
else
    echo -e "${RED}Error: docker-compose.yml not found in either root or mysite directory${NC}"
    exit 1
fi

# Build and start Docker containers
echo -e "${GREEN}Building and starting Docker containers...${NC}"
docker-compose build
docker-compose up -d

# Check if containers are running
echo -e "${GREEN}Checking container status...${NC}"
sleep 10
docker-compose ps

# Display success message
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}----------------------------------------${NC}"
echo -e "Your Django application should now be running at:"
echo -e "${GREEN}http://$PUBLIC_IP${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "To view logs: ${YELLOW}docker-compose logs -f${NC}"
echo -e "To stop: ${YELLOW}docker-compose down${NC}"
echo -e "To restart: ${YELLOW}docker-compose restart${NC}"
echo -e "To update from Git: ${YELLOW}git pull && docker-compose build && docker-compose up -d${NC}"