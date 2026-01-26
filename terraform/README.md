# Terraform AWS Deployment - Free Tier

Complete Infrastructure as Code (IaC) for deploying Rayansh's AI Portfolio on AWS Free Tier.

## 🏗️ Infrastructure Overview

```
┌─────────────────────────────────────────────────┐
│  Frontend (S3 + CloudFront) - FREE             │
│  ├─ Static files (HTML, CSS, JS)               │
│  ├─ CloudFront CDN (1 TB transfer/month)       │
│  └─ SSL Certificate (free)                     │
└───────────────┬─────────────────────────────────┘
                │
                ▼ HTTPS API Calls
┌─────────────────────────────────────────────────┐
│  Backend (EC2 t3.micro) - FREE (12 months)     │
│  ├─ Ubuntu 22.04 LTS                           │
│  ├─ Docker + Docker Compose                    │
│  ├─ Nginx (reverse proxy + SSL)                │
│  ├─ FastAPI Backend                            │
│  └─ CloudWatch Agent (monitoring)              │
└───────────────┬─────────────────────────────────┘
                │
    ┌───────────┴───────────┐
    ▼                       ▼
┌──────────────┐      ┌──────────────┐
│ Redis Cloud  │      │  Pinecone    │
│ (Free 30MB)  │      │  (Free tier) │
└──────────────┘      └──────────────┘
```

## 📦 What's Included

### Free Tier Resources:
- ✅ **EC2 t3.micro** (750 hours/month for 12 months)
- ✅ **30 GB EBS** storage (gp3)
- ✅ **S3** for frontend (5 GB storage, 20,000 GET requests)
- ✅ **CloudFront** CDN (1 TB transfer/month for 12 months)
- ✅ **Elastic IP** (free when attached)
- ✅ **CloudWatch** monitoring (10 metrics, 10 alarms)
- ✅ **SNS** email alerts (1000 emails/month)

### Paid Resources (After Free Tier):
- EC2 t3.micro: ~$7.50/month
- EBS 20 GB: ~$2/month
- Data transfer: ~$1-3/month
- **Total**: ~$10-12/month

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with Free Tier
2. **Terraform** installed (`>= 1.0`)
3. **AWS CLI** configured
4. **SSH Key Pair** created in AWS EC2

### Step 1: Install Terraform

```bash
# macOS
brew install terraform

# Windows (Chocolatey)
choco install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### Step 2: Configure AWS CLI

```bash
aws configure

# Enter:
# AWS Access Key ID: [your-key]
# AWS Secret Access Key: [your-secret]
# Default region: us-east-1
# Default output format: json
```

### Step 3: Create SSH Key Pair

```bash
# In AWS Console:
# EC2 → Key Pairs → Create key pair
# Name: rayansh-portfolio-key
# Download .pem file
chmod 400 rayansh-portfolio-key.pem
```

### Step 4: Configure Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
nano terraform.tfvars
```

**Required Changes:**
```hcl
# SSH key name (from Step 3)
key_name = "rayansh-portfolio-key"

# Your email for alerts
alert_email = "your-email@example.com"

# Your IP for SSH access
ssh_allowed_ips = ["YOUR_IP/32"]  # Get from: curl ifconfig.me

# Application secrets
redis_secret     = "redis://default:password@host:port"
groq_api_key     = "your-groq-key"
google_key       = "your-google-key-base64"
pinecone_api_key = "your-pinecone-key"
mailgun_domain   = "your-mailgun-domain.com"
mailgun_secret   = "your-mailgun-key"
```

### Step 5: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy (will ask for confirmation)
terraform apply

# Or auto-approve
terraform apply -auto-approve
```

**Deployment time:** ~5-10 minutes

### Step 6: Get Outputs

```bash
terraform output

# You'll see:
# ec2_public_ip = "54.123.45.67"
# ssh_connection = "ssh -i rayansh-portfolio-key.pem ubuntu@54.123.45.67"
# cloudfront_domain = "d1234abcd.cloudfront.net"
# s3_bucket_name = "rayansh-portfolio-frontend-abc123"
```

### Step 7: Verify Backend

```bash
# SSH into EC2
ssh -i rayansh-portfolio-key.pem ubuntu@<EC2_PUBLIC_IP>

# Check Docker containers
docker ps

# Check logs
docker-compose logs -f

# Check Nginx
curl http://localhost:80
```

## 📤 Deploy Frontend to S3

```bash
# Build your frontend
cd ../project
npm run build

# Upload to S3
aws s3 sync dist/ s3://$(terraform -chdir=../terraform output -raw s3_bucket_name) --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform -chdir=../terraform output -raw cloudfront_id) \
  --paths "/*"
```

## 🔒 SSL Setup (HTTPS)

### Option 1: CloudFront Domain (Automatic)
```bash
# Access frontend via:
https://d1234abcd.cloudfront.net  # SSL included!
```

### Option 2: Custom Domain

1. **Get ACM Certificate** (us-east-1 region):
```bash
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

2. **Update terraform.tfvars**:
```hcl
domain_name = "yourdomain.com"
acm_certificate_arn = "arn:aws:acm:..."
```

3. **Re-deploy**:
```bash
terraform apply
```

4. **Update DNS**:
```
yourdomain.com → CNAME → d1234abcd.cloudfront.net
```

### Option 3: Backend SSL (Let's Encrypt)

```bash
# SSH into EC2
ssh -i key.pem ubuntu@<EC2_IP>

# Run Certbot
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal is setup automatically
```

## 📊 Monitoring

### CloudWatch Alarms (Automatic)

You'll receive email alerts for:
- ✅ CPU > 80%
- ✅ Memory > 85%
- ✅ Disk < 2 GB
- ✅ Status check failures

### View Metrics

```bash
# AWS Console → CloudWatch → Dashboards

# Or via CLI
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 300 \
  --statistics Average
```

### View Logs

```bash
# SSH into EC2
ssh -i key.pem ubuntu@<EC2_IP>

# Application logs
docker-compose logs -f backend

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log
```

## 🔧 Common Operations

### Update Backend Code

```bash
# SSH into EC2
cd /home/ubuntu/app

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

### Scale to Multiple Instances

```bash
# Edit terraform/main.tf
# Uncomment ALB module
# Set instance count = 2

terraform apply
```

### Backup

```bash
# Snapshot EBS volume
aws ec2 create-snapshot \
  --volume-id vol-1234567890 \
  --description "Portfolio backup $(date +%Y-%m-%d)"

# Backup S3 (versioning enabled automatically)
```

## 🧹 Cleanup (Destroy Infrastructure)

```bash
# Preview what will be deleted
terraform plan -destroy

# Destroy all resources
terraform destroy

# Or force
terraform destroy -auto-approve
```

**WARNING:** This deletes everything! Make backups first.

## 💰 Cost Optimization

### Free Tier Limits (First 12 Months):
- ✅ EC2: 750 hours/month (1 instance 24/7)
- ✅ EBS: 30 GB storage
- ✅ S3: 5 GB storage, 20,000 GET, 2,000 PUT
- ✅ CloudFront: 1 TB data transfer
- ✅ Data Transfer: 100 GB/month out

### Tips to Stay Free:
1. **Run only 1 EC2 instance** (t3.micro)
2. **Use < 30 GB EBS** storage
3. **Compress frontend assets** (reduces S3/CloudFront usage)
4. **Use Redis Cloud** (free tier) instead of ElastiCache
5. **Monitor usage** via AWS Cost Explorer

### After Free Tier:
- Switch to **Lightsail** ($3.50/month for 512MB RAM)
- Or keep t3.micro: ~$10/month

## 🐛 Troubleshooting

### EC2 Not Accessible

```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-123456

# Check instance status
aws ec2 describe-instance-status --instance-ids i-123456

# Check system logs
aws ec2 get-console-output --instance-id i-123456
```

### Backend Not Running

```bash
# SSH and check
docker ps  # Should show backend container

docker-compose logs backend  # Check for errors

# Restart
docker-compose restart backend
```

### CloudFront Not Serving Files

```bash
# Check S3 bucket
aws s3 ls s3://your-bucket-name

# Check CloudFront distribution
aws cloudfront get-distribution --id E123456

# Create invalidation
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"
```

## 📚 Additional Resources

- [AWS Free Tier](https://aws.amazon.com/free/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EC2 Instance Types](https://aws.amazon.com/ec2/instance-types/)
- [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)

## 📝 Module Structure

```
terraform/
├── main.tf                 # Root configuration
├── variables.tf            # Input variables
├── terraform.tfvars        # Variable values (not in git!)
├── user_data.sh            # EC2 startup script
├── modules/
│   ├── ec2/                # EC2 instance module
│   ├── s3-cloudfront/      # Frontend hosting module
│   ├── cloudwatch/         # Monitoring module
│   └── iam/                # IAM roles module
```

## 🔐 Security Best Practices

1. ✅ **Never commit `terraform.tfvars`** (contains secrets)
2. ✅ **Restrict SSH** to your IP only
3. ✅ **Use IAM roles** instead of hardcoded credentials
4. ✅ **Enable MFA** on AWS account
5. ✅ **Encrypt EBS volumes** (enabled by default)
6. ✅ **Use HTTPS** everywhere (CloudFront + Let's Encrypt)
7. ✅ **Regular security updates** (`apt update && apt upgrade`)

---

**Questions?** Check the [main README](../README.md) or create an issue.

**Status**: ✅ Production Ready for AWS Free Tier
