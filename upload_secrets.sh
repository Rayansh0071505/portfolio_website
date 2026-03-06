#!/bin/bash
set -a
source .env
set +a

REGION="us-east-1"
PREFIX="/personal_portfolio"

keys=("GROQ_API_KEY" "GOOGLE_KEY" "PINECONE_API_KEY" "MAILGUN_DOMAIN" "MAILGUN_SECRET" "CLOUDFRONT_SECRET")

for key in "${keys[@]}"; do
    value="${!key}"
    if [ -n "$value" ]; then
        aws ssm put-parameter \
            --name "$PREFIX/${key,,}" \
            --value "$value" \
            --type SecureString \
            --overwrite \
            --region $REGION
        echo "Uploaded: $key"
    else
        echo "Skipped (empty): $key"
    fi
done
