$region = "us-east-1"
$prefix = "/personal_portfolio"
$envFile = ".env"

$keys = @("GROQ_API_KEY", "GOOGLE_KEY", "PINECONE_API_KEY", "MAILGUN_DOMAIN", "MAILGUN_SECRET", "CLOUDFRONT_SECRET")

$envVars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        $envVars[$matches[1].Trim()] = $matches[2].Trim()
    }
}

foreach ($key in $keys) {
    $value = $envVars[$key]
    if ($value) {
        $paramName = "$prefix/$($key.ToLower())"
        aws ssm put-parameter --name $paramName --value $value --type SecureString --overwrite --region $region
        Write-Host "Uploaded: $key"
    } else {
        Write-Host "Skipped (empty): $key"
    }
}
