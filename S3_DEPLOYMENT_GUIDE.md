# S3 Deployment Guide for AWS App Runner

## Overview
This guide explains how to set up S3 persistence for the LLM-TXT API when deployed on AWS App Runner. S3 persistence solves the job state issue when running multiple instances or when instances restart.

## Why S3 Persistence?
- **Multi-instance support**: App Runner can run multiple instances; S3 provides shared state
- **Persistence across restarts**: Jobs survive instance restarts
- **Cost-effective**: S3 is extremely cheap (< $0.10/month for typical usage)
- **Scalable**: Handles unlimited jobs without memory constraints

## Setup Instructions

### 1. Create S3 Bucket

```bash
# Create bucket
aws s3api create-bucket \
  --bucket llm-txt-jobs \
  --region us-east-1

# Enable versioning (optional, for data protection)
aws s3api put-bucket-versioning \
  --bucket llm-txt-jobs \
  --versioning-configuration Status=Enabled

# Set lifecycle policy to auto-delete old jobs (optional)
cat > lifecycle.json << 'EOF'
{
  "Rules": [{
    "Id": "DeleteOldJobs",
    "Status": "Enabled",
    "Prefix": "jobs/",
    "Expiration": {
      "Days": 7
    }
  }]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket llm-txt-jobs \
  --lifecycle-configuration file://lifecycle.json
```

### 2. Create IAM Policy for S3 Access

Create a policy file `s3-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::llm-txt-jobs/*",
        "arn:aws:s3:::llm-txt-jobs"
      ]
    }
  ]
}
```

Create the policy:
```bash
aws iam create-policy \
  --policy-name llm-txt-s3-access \
  --policy-document file://s3-policy.json
```

### 3. Configure App Runner Service

#### Option A: Using IAM Role (Recommended)

1. Create/update App Runner service role:
```bash
# Attach the S3 policy to your App Runner instance role
aws iam attach-role-policy \
  --role-name AppRunnerServiceRole \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/llm-txt-s3-access
```

2. Set environment variables in App Runner:
```yaml
# apprunner.yaml
Runtime:
  EnvironmentVariables:
    - Name: USE_S3_STORAGE
      Value: "true"
    - Name: S3_BUCKET_NAME
      Value: "llm-txt-jobs"
    - Name: AWS_REGION
      Value: "us-east-1"
    - Name: COHERE_API_KEY
      Value: "your-api-key"
```

#### Option B: Using Access Keys (Less Secure)

1. Create IAM user with programmatic access
2. Attach the `llm-txt-s3-access` policy
3. Add credentials as environment variables:

```yaml
# apprunner.yaml
Runtime:
  EnvironmentVariables:
    - Name: USE_S3_STORAGE
      Value: "true"
    - Name: S3_BUCKET_NAME
      Value: "llm-txt-jobs"
    - Name: AWS_REGION
      Value: "us-east-1"
    - Name: AWS_ACCESS_KEY_ID
      Value: "AKIAXXXXXXXXXXXXXXXX"
    - Name: AWS_SECRET_ACCESS_KEY
      Value: "your-secret-key"
    - Name: COHERE_API_KEY
      Value: "your-api-key"
```

### 4. Deploy to App Runner

```bash
# Build and push Docker image
docker build -t llm-txt-api .
docker tag llm-txt-api:latest YOUR_ECR_REPO/llm-txt-api:latest
docker push YOUR_ECR_REPO/llm-txt-api:latest

# Update App Runner service
aws apprunner update-service \
  --service-arn YOUR_SERVICE_ARN \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "YOUR_ECR_REPO/llm-txt-api:latest",
      "ImageConfiguration": {
        "RuntimeEnvironmentVariables": {
          "USE_S3_STORAGE": "true",
          "S3_BUCKET_NAME": "llm-txt-jobs",
          "AWS_REGION": "us-east-1"
        }
      }
    }
  }'
```

## Testing S3 Integration

### 1. Local Testing

```bash
# Set environment variables
export USE_S3_STORAGE=true
export S3_BUCKET_NAME=llm-txt-jobs
export AWS_REGION=us-east-1
export AWS_PROFILE=your-profile  # Or use AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY

# Run the API
make dev

# Test job creation
curl -X POST http://localhost:8000/v1/generations \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org"}'

# Check S3 bucket
aws s3 ls s3://llm-txt-jobs/jobs/ --recursive
```

### 2. Production Testing

```bash
# Create a job
curl -X POST https://hdinqg7vmm.us-east-1.awsapprunner.com/v1/generations \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org"}'

# Save the job_id from response
JOB_ID="returned-job-id"

# Check job status
curl https://hdinqg7vmm.us-east-1.awsapprunner.com/v1/generations/$JOB_ID

# Verify in S3
aws s3 ls s3://llm-txt-jobs/jobs/$JOB_ID/
```

## Monitoring & Maintenance

### View S3 Usage
```bash
# Check bucket size
aws s3 ls s3://llm-txt-jobs/ --recursive --human-readable --summarize

# Count jobs
aws s3 ls s3://llm-txt-jobs/jobs/ | wc -l
```

### Clean Up Old Jobs
```bash
# Manual cleanup (jobs older than 7 days)
aws s3 rm s3://llm-txt-jobs/jobs/ \
  --recursive \
  --exclude "*" \
  --include "*/status.json" \
  --include "*/llm.txt" \
  --include "*/llms-full.txt" \
  --older-than 7d
```

### Monitor Costs
```bash
# Check S3 costs (via Cost Explorer)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --filter '{
    "Dimensions": {
      "Key": "SERVICE",
      "Values": ["Amazon Simple Storage Service"]
    }
  }'
```

## Troubleshooting

### Common Issues

1. **404 Errors on Job Status**
   - Check S3 bucket exists: `aws s3 ls s3://llm-txt-jobs/`
   - Verify IAM permissions: Check CloudTrail for access denied errors
   - Check environment variables: Ensure `USE_S3_STORAGE=true`

2. **S3 Access Denied**
   - Verify IAM role/policy attached
   - Check bucket policy doesn't block access
   - Ensure correct region specified

3. **Jobs Not Persisting**
   - Check `USE_S3_STORAGE` is set to `true`
   - Look for errors in App Runner logs
   - Verify S3 bucket name matches configuration

### Debug Commands
```bash
# Check App Runner logs
aws logs tail /aws/apprunner/YOUR_SERVICE_NAME --follow

# Test S3 access from local
aws s3 ls s3://llm-txt-jobs/ --profile your-profile

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn YOUR_ROLE_ARN \
  --action-names s3:GetObject s3:PutObject \
  --resource-arns arn:aws:s3:::llm-txt-jobs/*
```

## Cost Optimization

### Estimated Monthly Costs
- **Storage**: ~$0.023 per GB (negligible for JSON job data)
- **Requests**: ~$0.0004 per 1,000 PUT requests
- **Total**: Typically < $0.10/month for moderate usage

### Cost Reduction Tips
1. Enable lifecycle policies to auto-delete old jobs
2. Use S3 Intelligent-Tiering for automatic cost optimization
3. Consider S3 Glacier for long-term job archival

## Security Best Practices

1. **Use IAM Roles** instead of access keys when possible
2. **Enable S3 Versioning** for data protection
3. **Enable S3 Server-Side Encryption**:
```bash
aws s3api put-bucket-encryption \
  --bucket llm-txt-jobs \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

4. **Enable Access Logging**:
```bash
aws s3api put-bucket-logging \
  --bucket llm-txt-jobs \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "your-logs-bucket",
      "TargetPrefix": "s3-access-logs/"
    }
  }'
```

5. **Regular Audits**: Review S3 access patterns and remove unused permissions

## Rollback Plan

To disable S3 and revert to in-memory storage:

1. Set environment variable: `USE_S3_STORAGE=false`
2. Restart App Runner service
3. Note: This will only work reliably with a single instance

## Next Steps

1. **Set up monitoring**: CloudWatch alarms for S3 errors
2. **Implement backup**: Cross-region replication for critical data
3. **Performance tuning**: Consider S3 Transfer Acceleration for global users
4. **Cost monitoring**: Set up AWS Budgets alerts