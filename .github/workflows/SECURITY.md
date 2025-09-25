# GitHub Actions Security Best Practices

## Current Security Improvements

### ✅ Fixed Issues

1. **Docker Password Masking**
   - Updated `amazon-ecr-login` to v2 with `mask-password: true`
   - Prevents ECR passwords from appearing in logs
   - Applied to all workflows using ECR

2. **Credential Checks**
   - Added pre-flight checks for AWS credentials
   - Clear error messages when secrets are missing
   - No credentials exposed in error messages

## Security Configuration

### Required Secrets (Stored Securely)

These should be configured as repository secrets, not in code:

```yaml
AWS_ACCESS_KEY_ID       # AWS IAM access key
AWS_SECRET_ACCESS_KEY   # AWS IAM secret key
AMPLIFY_APP_ID         # d18z0bfb4y2t29
COHERE_API_KEY         # API key for Cohere (optional)
```

### Recommended: Use OIDC Instead of Keys

For better security, use OpenID Connect (OIDC) instead of long-lived AWS credentials:

1. **Create IAM Role** with trust relationship:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::796973517930:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:sshtomar/llm-txt:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

2. **Add Role ARN as Secret**:
   - Name: `AWS_ROLE_TO_ASSUME`
   - Value: `arn:aws:iam::796973517930:role/GitHubActionsDeployRole`

3. **Remove Access Keys**:
   - Delete `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets

## Security Checklist

### GitHub Actions
- [x] Use `mask-password: true` for ECR login
- [x] Use latest versions of actions
- [x] Validate inputs before use
- [x] Check for secrets before attempting to use them
- [ ] Enable branch protection on main
- [ ] Require PR reviews before merge
- [ ] Use environment protection rules

### AWS Security
- [x] Use minimal IAM permissions
- [x] ECR repositories are private
- [x] S3 bucket has encryption enabled
- [x] App Runner uses secrets manager for sensitive values
- [ ] Enable CloudTrail for audit logging
- [ ] Use AWS GuardDuty for threat detection
- [ ] Rotate access keys every 90 days

### Repository Security
- [ ] Enable Dependabot alerts
- [ ] Enable code scanning (CodeQL)
- [ ] Enable secret scanning
- [ ] Review and limit GitHub App permissions

## IAM Policy for GitHub Actions (Minimal Permissions)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRPush",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": [
        "arn:aws:ecr:us-east-1:796973517930:repository/llm-txt-api"
      ]
    },
    {
      "Sid": "ECRAuth",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "AppRunnerDeploy",
      "Effect": "Allow",
      "Action": [
        "apprunner:StartDeployment",
        "apprunner:DescribeService"
      ],
      "Resource": [
        "arn:aws:apprunner:us-east-1:796973517930:service/llm-txt-api/*"
      ]
    },
    {
      "Sid": "AmplifyDeploy",
      "Effect": "Allow",
      "Action": [
        "amplify:StartJob",
        "amplify:GetApp",
        "amplify:GetBranch"
      ],
      "Resource": [
        "arn:aws:amplify:us-east-1:796973517930:apps/d18z0bfb4y2t29/*"
      ]
    }
  ]
}
```

## Monitoring & Alerts

### Set Up Notifications
1. GitHub Actions failures → Email/Slack
2. AWS CloudWatch alarms → SNS topics
3. ECR image scan findings → Security team

### Regular Audits
- Weekly: Review GitHub Actions logs
- Monthly: Rotate AWS access keys
- Quarterly: Review IAM permissions

## Emergency Response

If credentials are compromised:

1. **Immediately**:
   - Rotate AWS access keys
   - Review CloudTrail logs
   - Check for unauthorized resources

2. **Within 1 hour**:
   - Update all GitHub secrets
   - Review recent deployments
   - Check ECR for unauthorized images

3. **Within 24 hours**:
   - Complete security audit
   - Update IAM policies if needed
   - Document incident

## Additional Resources

- [GitHub Actions Security Guide](https://docs.github.com/en/actions/security-guides)
- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [OWASP CI/CD Security](https://owasp.org/www-project-devsecops-guideline/)