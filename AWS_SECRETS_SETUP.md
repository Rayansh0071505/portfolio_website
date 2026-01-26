# AWS Parameter Store Setup for personal_portfolio

## Overview

Secrets are **NO LONGER stored in .env files on EBS**. They are securely stored in AWS Systems Manager Parameter Store and accessed via IAM roles.

## ✅ Security Benefits

| Before (.env on EBS) | After (Parameter Store) |
|---------------------|------------------------|
| ❌ Visible to anyone with SSH | ✅ IAM-controlled access |
| ❌ Stored in plaintext | ✅ Encrypted at rest (KMS) |
| ❌ No audit trail | ✅ CloudTrail logs all access |
| ❌ Manual rotation | ✅ Easy rotation |
| ❌ Git leak risk | ✅ Never in git |

## 🔒 Where Blocked IPs are Stored

**Answer: Redis**

```
Redis Key: security:blocked:{ip}

Example:
security:blocked:192.168.1.100
  ├─ reason: "Exceeded daily limit: 65 requests in 24 hours"
  ├─ blocked_at: "2026-01-26T10:30:00"
  └─ ip: "192.168.1.100"

Storage: Persistent (no TTL) - stays until manually unblocked
Location: External Redis Cloud (NOT on EBS)
```

**Check blocked IPs:**
```bash
# Via Redis CLI
redis-cli -h your-host -p your-port -a your-password
KEYS security:blocked:*
HGETALL security:blocked:192.168.1.100

# Via API
curl https://your-api.com/api/security/stats
```

## 📦 What's Stored Where

### AWS Parameter Store (Encrypted):
- ✅ REDIS_SECRET
- ✅ GROQ_API_KEY
- ✅ GOOGLE_KEY
- ✅ PINECONE_API_KEY
- ✅ MAILGUN_DOMAIN
- ✅ MAILGUN_SECRET
- ✅ CLOUDFRONT_SECRET

### EBS Volume (EC2):
- Application code (.py files)
- Docker containers
- Nginx config
- Logs
- .env file with **ONLY** non-sensitive config:
  ```
  ENVIRONMENT=production
  CLOUDFRONT_DOMAIN=d1234.cloudfront.net
  AWS_DEFAULT_REGION=us-east-1
  ```

### Redis (External):
- Chat conversations
- User sessions
- **Blocked IPs** ← HERE
- Rate limiting counters
- Security data

## 🚀 Setup Instructions

### Option 1: Automatic (via Terraform)

Terraform automatically creates all parameters when you run `terraform apply`:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your secrets
nano terraform.tfvars

# Deploy - parameters are created automatically
terraform apply
```

**Terraform creates:**
- `/personal_portfolio/redis_secret`
- `/personal_portfolio/groq_api_key`
- `/personal_portfolio/google_key`
- `/personal_portfolio/pinecone_api_key`
- `/personal_portfolio/mailgun_domain`
- `/personal_portfolio/mailgun_secret`
- `/personal_portfolio/cloudfront_secret` (auto-generated if not provided)

### Option 2: Manual (AWS CLI)

```bash
# 1. Set region
export AWS_DEFAULT_REGION=us-east-1

# 2. Store secrets
aws ssm put-parameter \
  --name /personal_portfolio/redis_secret \
  --value "redis://default:password@host:port" \
  --type SecureString

aws ssm put-parameter \
  --name /personal_portfolio/groq_api_key \
  --value "your-groq-api-key" \
  --type SecureString

aws ssm put-parameter \
  --name /personal_portfolio/google_key \
  --value "your-base64-encoded-google-key" \
  --type SecureString

aws ssm put-parameter \
  --name /personal_portfolio/pinecone_api_key \
  --value "your-pinecone-api-key" \
  --type SecureString

aws ssm put-parameter \
  --name /personal_portfolio/mailgun_domain \
  --value "yourdomain.mailgun.org" \
  --type SecureString

aws ssm put-parameter \
  --name /personal_portfolio/mailgun_secret \
  --value "your-mailgun-api-key" \
  --type SecureString

aws ssm put-parameter \
  --name /personal_portfolio/cloudfront_secret \
  --value "$(openssl rand -base64 32)" \
  --type SecureString
```

### Option 3: AWS Console

1. Go to AWS Console → Systems Manager → Parameter Store
2. Click **Create parameter**
3. For each secret:
   - Name: `/personal_portfolio/redis_secret`
   - Type: **SecureString**
   - Value: Your secret value
   - Click **Create parameter**

## 🔍 Verify Parameters

```bash
# List all parameters
aws ssm describe-parameters --region us-east-1 \
  --parameter-filters "Key=Name,Option=BeginsWith,Values=/personal_portfolio/"

# Get a parameter value (decrypted)
aws ssm get-parameter \
  --name /personal_portfolio/redis_secret \
  --with-decryption \
  --region us-east-1
```

## 🔄 How the Application Uses Secrets

### Development (Local):
```python
# Uses .env file (backward compatible)
from config import get_redis_secret

redis_url = get_redis_secret()  # Reads from .env
```

### Production (EC2):
```python
# Uses AWS Parameter Store automatically
from config import get_redis_secret

redis_url = get_redis_secret()  # Fetches from Parameter Store via IAM
```

**Environment Detection:**
- `ENVIRONMENT=development` → Use .env file
- `ENVIRONMENT=production` → Use Parameter Store

## 🔐 IAM Permissions

The EC2 instance has this IAM policy (created by Terraform):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/personal_portfolio/*"
    },
    {
      "Effect": "Allow",
      "Action": ["kms:Decrypt"],
      "Resource": "*"
    }
  ]
}
```

**Security:**
- ✅ EC2 can **read** secrets
- ✅ EC2 **cannot** write/modify secrets
- ✅ Only from `/personal_portfolio/*` path
- ✅ All access logged in CloudTrail

## 🔄 Rotating Secrets

```bash
# Update a secret (creates new version)
aws ssm put-parameter \
  --name /personal_portfolio/redis_secret \
  --value "new-redis-url" \
  --type SecureString \
  --overwrite

# Restart backend to pick up new value
ssh -i key.pem ubuntu@<EC2_IP>
docker-compose restart backend
```

## 🛡️ CloudFront Origin Protection

The backend **ONLY accepts requests from CloudFront**, not direct access.

### How it Works:

```
User → CloudFront → Backend (✅ Allowed)
User → EC2 IP directly (❌ Blocked)
```

**CloudFront adds custom header:**
```http
X-CloudFront-Secret: <random-32-char-string>
```

**Backend verifies header:**
```python
if cf_secret != CLOUDFRONT_SECRET:
    return 403 Forbidden
```

**Setup:**
1. CloudFront secret stored in Parameter Store
2. CloudFront adds header to all requests
3. Backend verifies header matches
4. Direct EC2 access blocked (no header = blocked)

## 📊 Monitoring

### View Parameter Access Logs (CloudTrail):

```bash
# AWS Console → CloudTrail → Event history
# Filter by: Event name = GetParameter
```

### Check Application Logs:

```bash
# SSH into EC2
ssh -i key.pem ubuntu@<EC2_IP>

# View logs
docker-compose logs backend | grep "parameter"

# Should see:
# ✅ Retrieved parameter: /personal_portfolio/redis_secret
# ✅ Retrieved parameter: /personal_portfolio/groq_api_key
```

## 💰 Cost

**AWS Parameter Store Pricing:**
- Standard parameters: **FREE** (up to 10,000 parameters)
- API calls: **FREE** (up to 1 million/month)
- SecureString encryption: **FREE** (uses AWS KMS default key)

**Total Cost: $0/month** ✅

## 🧪 Testing

### Test Local (Development):

```bash
cd backend
cp .env.example .env
# Edit .env with your secrets

ENVIRONMENT=development python -c "from config import get_redis_secret; print(get_redis_secret())"
# Should print value from .env
```

### Test Production (Parameter Store):

```bash
# On EC2 with IAM role
ENVIRONMENT=production python -c "from config import get_redis_secret; print(get_redis_secret())"
# Should fetch from Parameter Store
```

## 🔍 Troubleshooting

### Error: "Parameter not found"

```bash
# Check parameter exists
aws ssm get-parameter --name /personal_portfolio/redis_secret

# Check EC2 IAM role has permissions
aws iam get-role-policy --role-name personal-portfolio-ec2-role --policy-name personal-portfolio-parameter-store-policy
```

### Error: "Access Denied"

```bash
# Check IAM instance profile
aws ec2 describe-instances --instance-ids i-xxxxx | grep IamInstanceProfile

# Verify role attached
# Should show: personal-portfolio-ec2-role
```

### Application not fetching secrets

```bash
# Check environment variable
ssh -i key.pem ubuntu@<EC2_IP>
docker-compose exec backend env | grep ENVIRONMENT

# Should show: ENVIRONMENT=production
```

## 📚 Files Modified

- ✅ `backend/config.py` - New config module
- ✅ `backend/main.py` - CloudFront verification middleware
- ✅ `backend/personal_ai.py` - Use config module
- ✅ `backend/conversation_tracker.py` - Use config module
- ✅ `backend/security_middleware.py` - Use config module
- ✅ `terraform/main.tf` - Create parameters, add IAM permissions
- ✅ `terraform/modules/iam/main.tf` - Parameter Store policy
- ✅ `terraform/modules/s3-cloudfront/main.tf` - Custom header for backend
- ✅ `terraform/user_data.sh` - No secrets in .env

## 🎯 Summary

| Question | Answer |
|----------|--------|
| **Where are blocked IPs stored?** | Redis (`security:blocked:{ip}`) |
| **Are secrets safe on EBS?** | No - now using Parameter Store instead |
| **Can backend block direct access?** | Yes - CloudFront custom header verification |
| **How to restrict to CloudFront only?** | Middleware checks `X-CloudFront-Secret` header |
| **Cost of Parameter Store?** | $0 (free tier covers everything) |

---

**Status**: ✅ Production Ready - Secrets secured in AWS Parameter Store
**Project**: personal_portfolio
**Last Updated**: 2026-01-26
