#!/bin/bash
set -e

# ============================================================================
# EC2 User Data Script for Rayansh's Portfolio Backend
# Runs on first boot to setup the environment
# ============================================================================

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
apt-get install -y docker-compose

# Install Nginx
apt-get install -y nginx

# Install CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i amazon-cloudwatch-agent.deb

# Install Git
apt-get install -y git

# Install Certbot for SSL
apt-get install -y certbot python3-certbot-nginx

# Create application directory
mkdir -p /home/ubuntu/app
cd /home/ubuntu/app

# Clone repository (replace with your repo URL)
git clone https://github.com/Rayansh0071505/portfolio_website.git .

# Create .env file with environment variables (NO SECRETS!)
# Secrets are fetched from AWS Parameter Store by the application
cat > /home/ubuntu/app/backend/.env <<EOF
# Environment
ENVIRONMENT=${environment}

# CloudFront/CORS configuration
CLOUDFRONT_DOMAIN=${cloudfront_domain}
CUSTOM_DOMAIN=${custom_domain}

# AWS Region for Parameter Store
AWS_DEFAULT_REGION=us-east-1

# NOTE: Application secrets are stored in AWS Parameter Store
# Path: /personal_portfolio/*
# The application will fetch them automatically using IAM role
EOF

# Set permissions
chown -R ubuntu:ubuntu /home/ubuntu/app

# Create Docker Compose file
cat > /home/ubuntu/app/docker-compose.yml <<'DOCKER_EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    env_file:
      - ./backend/.env
    restart: unless-stopped
    volumes:
      - ./backend:/app
    logging:
      driver: "awslogs"
      options:
        awslogs-region: "us-east-1"
        awslogs-group: "/aws/ec2/rayansh-portfolio-backend"
        awslogs-create-group: "true"
DOCKER_EOF

# Create Dockerfile for backend
cat > /home/ubuntu/app/backend/Dockerfile <<'DOCKERFILE_EOF'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
DOCKERFILE_EOF

# Configure Nginx as reverse proxy
cat > /etc/nginx/sites-available/backend <<'NGINX_EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/backend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Configure CloudWatch Agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<'CW_EOF'
{
  "metrics": {
    "namespace": "CWAgent",
    "metrics_collected": {
      "disk": {
        "measurement": [
          {
            "name": "disk_free",
            "rename": "disk_free",
            "unit": "Bytes"
          },
          {
            "name": "disk_used_percent",
            "rename": "disk_used_percent",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 300,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "mem_used_percent",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 300
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/aws/ec2/rayansh-portfolio-backend",
            "log_stream_name": "{instance_id}/nginx-access"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "/aws/ec2/rayansh-portfolio-backend",
            "log_stream_name": "{instance_id}/nginx-error"
          }
        ]
      }
    }
  }
}
CW_EOF

# Start CloudWatch Agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

# Build and start Docker containers
cd /home/ubuntu/app
docker-compose up -d --build

# Create startup script to run on boot
cat > /etc/systemd/system/portfolio-backend.service <<'SERVICE_EOF'
[Unit]
Description=Portfolio Backend Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/app
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Enable service
systemctl daemon-reload
systemctl enable portfolio-backend.service

echo "✅ EC2 instance setup complete!"
echo "Backend running on port 8080"
echo "Nginx reverse proxy on port 80/443"
