# Terraform Infrastructure for Rayansh AI Portfolio

This directory contains Terraform configuration for deploying the AI assistant backend and frontend infrastructure on AWS.

## Architecture Overview

```
CloudFront (CDN)
    ├── Frontend Origin (S3)
    └── Backend Origin (EC2) with Custom Header Verification

EC2 Instance (Backend API)
├── Docker Container (FastAPI + Redis)
├── EBS Volume (Data)
└── Security Group (Only CloudFront with Custom Header)

S3 Buckets
├── Frontend (Static website files)
├── Assets (Static assets with lifecycle policies)
└── Logs (CloudFront and access logs)

VPC
├── Public Subnet (EC2 instance)
└── Private Subnet (Reserved for future use)
```

## Components

### 1. **VPC & Networking** (`vpc.tf`)
- VPC with public/private subnets
- Internet Gateway for public internet access
- Route tables for traffic management

### 2. **Security** (`security_groups.tf`)
- Backend security group (SSH, HTTP, API port)
- Redis security group (internal only)
- CORS enforced via CloudFront custom headers

### 3. **IAM Roles** (`iam.tf`)
- EC2 instance role for Parameter Store access
- S3 bucket permissions
- ECR access for Docker images
- CloudWatch Logs permissions

### 4. **EC2 Backend** (`ec2.tf`)
- Free tier eligible `t3.micro` instance
- Amazon Linux 2 AMI
- 30GB root volume (EBS gp3)
- 50GB additional EBS volume for data
- Automatic Docker installation and container startup
- Elastic IP for consistent public address

### 5. **S3 & CloudFront** (`s3.tf`)
- Frontend S3 bucket with versioning
- CloudFront distribution with OAI (Origin Access Identity)
- API caching behavior (no cache for `/api/*`)
- Custom domain support
- Logs bucket for access logs

### 6. **User Data** (`user_data.sh`)
- Installs Docker and docker-compose
- Pulls backend Docker image from ECR
- Starts Redis container
- Starts backend API container
- Configures CloudWatch agent for monitoring

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** installed locally (v1.0+)
3. **AWS CLI** configured with credentials
4. **EC2 Key Pair** created in your AWS account
5. **Docker Image** built and pushed to ECR
6. **Environment Variables** file for backend

## Setup Instructions

### 1. Prepare EC2 Key Pair

```bash
# If you don't have a key pair, create one in AWS Console or via CLI
aws ec2 create-key-pair --key-name rayansh-ai-key --query 'KeyMaterial' --output text > rayansh-ai-key.pem
chmod 400 rayansh-ai-key.pem
```

### 2. Create Terraform Variables File

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

Edit `terraform.tfvars` and fill in your values:

```hcl
aws_region              = "us-east-1"         # Free tier region
key_pair_name           = "your-key-pair"    # EC2 key pair name
cloudfront_secret       = "your-random-secret-here"
custom_domain           = ""                  # Optional: your custom domain
```

### 3. Create S3 Backend for Terraform State

```bash
# Create an S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket rayansh-ai-terraform-state-$(date +%s) \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket rayansh-ai-terraform-state-XXXXX \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket rayansh-ai-terraform-state-XXXXX \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 4. Configure Backend

Create `terraform/backend.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "rayansh-ai-terraform-state-XXXXX"
    key            = "infrastructure.tfstate"
    region         = "us-east-1"
    encrypt        = true
  }
}
```

### 5. Build and Push Docker Image

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name rayansh-ai \
  --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t rayansh-ai:latest .

# Tag and push
docker tag rayansh-ai:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/rayansh-ai:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/rayansh-ai:latest
```

### 6. Store Environment Variables in Parameter Store

```bash
# Create parameter with backend environment variables
aws ssm put-parameter \
  --name "/rayansh-ai-portfolio/env" \
  --value "file://backend/.env" \
  --type "String" \
  --region us-east-1 \
  --overwrite
```

### 7. Initialize and Deploy Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan -out=tfplan

# Apply the configuration
terraform apply tfplan
```

### 8. Retrieve Infrastructure Information

```bash
terraform output

# Specific outputs
terraform output backend_public_ip
terraform output cloudfront_domain_name
terraform output backend_api_endpoint
```

## Important Configuration

### CloudFront Origin Verification

The backend is protected from direct access by:

1. **Security Group**: Only allows traffic from specific ports
2. **Custom Header**: CloudFront adds `X-CloudFront-Secret` header to requests
3. **Backend Middleware**: Verifies the secret header before processing requests

The secret is stored in Parameter Store and must match between CloudFront and backend.

### CORS Configuration

CORS is enforced at the backend level:
- Development: Allow localhost
- Production: Only CloudFront origin
- Custom domain: If configured

### Free Tier Optimization

- **EC2**: t3.micro (eligible for free tier)
- **EBS**: 30GB root volume + 50GB additional (30GB/month free)
- **S3**: Standard storage (eligible for free tier)
- **CloudFront**: Eligible for free tier (1TB/month outbound)
- **Data Transfer**: Free tier includes 1GB/month EC2 to internet

## Monitoring

### CloudWatch

- EC2 metrics: CPU, Network, Disk
- Application logs: `/aws/ec2/rayansh-ai-portfolio`
- CloudFront access logs: Stored in logs S3 bucket

### Health Check

```bash
curl http://BACKEND_IP:8080/
curl http://CLOUDFRONT_DOMAIN/api/status
```

## Updating Infrastructure

### Update Docker Image

Edit `terraform.tfvars`:

```hcl
docker_image = "123456789.dkr.ecr.us-east-1.amazonaws.com/rayansh-ai:new-tag"
```

Apply changes:

```bash
terraform apply
```

### Update Backend Environment Variables

```bash
aws ssm put-parameter \
  --name "/rayansh-ai-portfolio/env" \
  --value "file://backend/.env" \
  --type "String" \
  --region us-east-1 \
  --overwrite

# Restart container via EC2 instance
```

## Cleanup

To destroy the infrastructure:

```bash
terraform destroy

# Manual cleanup in AWS Console
# - Delete S3 buckets (if not needed)
# - Delete RDS/ElastiCache (if added)
# - Review CloudWatch logs if needed before deletion
```

## Cost Estimates (Monthly)

- **EC2 t3.micro**: Free (12 months)
- **EBS 30GB**: Free (12 months) + ~$2 for additional 50GB
- **S3**: ~$0.50 (typical usage)
- **CloudFront**: Free (1TB outbound)
- **Data Transfer**: Free (1GB from EC2)

**Total**: ~$2.50/month after free tier expires

## Troubleshooting

### EC2 doesn't have public IP

```bash
# Check if Elastic IP is associated
aws ec2 describe-addresses --allocation-ids ALLOCATION_ID

# Associate if needed
aws ec2 associate-address --instance-id INSTANCE_ID --allocation-id ALLOCATION_ID
```

### Docker containers not starting

```bash
# SSH into instance
ssh -i key.pem ec2-user@PUBLIC_IP

# Check container status
docker-compose -f /opt/backend/docker-compose.yml logs

# Restart containers
docker-compose -f /opt/backend/docker-compose.yml up -d
```

### Backend not accessible through CloudFront

1. Check security group rules
2. Verify custom header is set in CloudFront
3. Check backend middleware logs: `curl http://IP:8080/api/status`

### CloudFront shows 503 error

1. Verify backend is running: `curl http://EC2_IP:8080/`
2. Check backend security group allows port 8080
3. Verify custom header in CloudFront origin configuration

## GitHub Actions Integration

The workflows in `.github/workflows/` automate:

1. **infrastructure.yml**: Terraform plan/apply on push to terraform/ changes
2. **deploy.yml**: Build Docker, deploy frontend to S3, deploy backend to EC2

Set the following secrets in GitHub repository:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
EC2_KEY_PAIR_NAME
EC2_SSH_PRIVATE_KEY
S3_FRONTEND_BUCKET
CLOUDFRONT_DOMAIN
CLOUDFRONT_DISTRIBUTION_ID
CLOUDFRONT_SECRET
CUSTOM_DOMAIN (optional)
DOCKER_IMAGE
TERRAFORM_STATE_BUCKET
```

## Additional Resources

- [AWS Free Tier](https://aws.amazon.com/free/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [CloudFront Origin Access Identity](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
