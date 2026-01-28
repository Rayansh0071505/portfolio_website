#!/bin/bash
set -e

# Set variables (passed from Terraform templatefile)
AWS_REGION="${AWS_REGION}"
PROJECT_NAME="${PROJECT_NAME}"
DOCKER_IMAGE="${DOCKER_IMAGE}"
BACKEND_PORT="${BACKEND_PORT}"
CLOUDFRONT_SECRET="${CLOUDFRONT_SECRET}"

# Logging
echo "Starting EC2 instance setup at $(date)" | tee -a /var/log/backend-setup.log

# Update system
echo "Updating system packages..." | tee -a /var/log/backend-setup.log
yum update -y

# Install Docker
echo "Installing Docker..." | tee -a /var/log/backend-setup.log
yum install -y docker git

# Start Docker daemon
echo "Starting Docker daemon..." | tee -a /var/log/backend-setup.log
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install AWS CLI and additional tools
echo "Installing AWS CLI..." | tee -a /var/log/backend-setup.log
yum install -y aws-cli

# Format and mount additional EBS volume (if available)
if [ -b /dev/nvme1n1 ]; then
    echo "Formatting and mounting EBS volume..." | tee -a /var/log/backend-setup.log
    mkfs.ext4 /dev/nvme1n1
    mkdir -p /data
    mount /dev/nvme1n1 /data
    chmod 777 /data

    # Persist mount in fstab
    echo "/dev/nvme1n1 /data ext4 defaults,nofail 0 2" >> /etc/fstab
fi

# Create docker-compose directory
mkdir -p /opt/backend
cd /opt/backend

# Get environment variables from AWS Parameter Store
echo "Fetching environment variables from Parameter Store..." | tee -a /var/log/backend-setup.log
aws ssm get-parameter --name "/${PROJECT_NAME}/env" --region "$AWS_REGION" --query 'Parameter.Value' --output text > .env 2>/dev/null || {
    echo "Error: Could not fetch .env from Parameter Store." | tee -a /var/log/backend-setup.log
    echo "Make sure to upload backend/.env to Parameter Store:" | tee -a /var/log/backend-setup.log
    echo "aws ssm put-parameter --name \"/${PROJECT_NAME}/env\" --value \"file://backend/.env\" --type \"String\" --region $AWS_REGION --overwrite" | tee -a /var/log/backend-setup.log
    exit 1
}

# Login to ECR if using private registry
if [[ ! -z "${AWS_REGION}" ]]; then
    echo "Logging in to ECR..." | tee -a /var/log/backend-setup.log
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.${AWS_REGION}.amazonaws.com"
fi

# Pull Docker image
echo "Pulling Docker image: ${DOCKER_IMAGE}..." | tee -a /var/log/backend-setup.log
docker pull ${DOCKER_IMAGE} || {
    echo "Could not pull image. Building from local Dockerfile..." | tee -a /var/log/backend-setup.log
    git clone https://github.com/your-repo/portfolio_website.git /tmp/backend-repo
    cd /tmp/backend-repo
    docker build -t ${DOCKER_IMAGE} .
    docker tag ${DOCKER_IMAGE} ${DOCKER_IMAGE}:latest
}

# Create docker-compose file
echo "Creating docker-compose.yml..." | tee -a /var/log/backend-setup.log
cat > /opt/backend/docker-compose.yml << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: backend_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - backend_network
    restart: always

  backend:
    image: ${DOCKER_IMAGE}
    container_name: backend_api
    ports:
      - "${BACKEND_PORT}:8080"
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379
      - CLOUDFRONT_SECRET=${CLOUDFRONT_SECRET}
      - AWS_REGION=${AWS_REGION}
    depends_on:
      - redis
    volumes:
      - /data:/app/data
    networks:
      - backend_network
    restart: always
    logging:
      driver: awslogs
      options:
        awslogs-group: /aws/ec2/${PROJECT_NAME}
        awslogs-region: ${AWS_REGION}
        awslogs-stream-prefix: backend

volumes:
  redis_data:

networks:
  backend_network:
    driver: bridge
EOF

# Start containers
echo "Starting Docker containers..." | tee -a /var/log/backend-setup.log
docker-compose -f /opt/backend/docker-compose.yml up -d

# Install CloudWatch agent for monitoring
echo "Installing CloudWatch agent..." | tee -a /var/log/backend-setup.log
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Create CloudWatch agent config
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json << EOF
{
  "metrics": {
    "namespace": "${PROJECT_NAME}",
    "metrics_collected": {
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MemoryUtilization"
          }
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DiskUtilization"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": ["/", "/data"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/docker",
            "log_group_name": "/aws/ec2/${PROJECT_NAME}",
            "log_stream_name": "docker-logs"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

echo "EC2 instance setup completed at $(date)" | tee -a /var/log/backend-setup.log
