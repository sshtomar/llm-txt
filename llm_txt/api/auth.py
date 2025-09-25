"""Authentication and API key management for LLMxt Cloud."""

import os
import secrets
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# DynamoDB setup for serverless API key storage
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table(os.getenv('USERS_TABLE', 'llmxt-users'))
usage_table = dynamodb.Table(os.getenv('USAGE_TABLE', 'llmxt-usage'))

# Security
security = HTTPBearer()


class User(BaseModel):
    """User model."""
    email: str
    api_key: str
    plan: str = "free"
    stripe_customer_id: Optional[str] = None
    created_at: str
    updated_at: str


class PlanLimits(BaseModel):
    """Plan limits and features."""
    monthly_generations: int
    max_pages_per_crawl: int
    max_concurrent_jobs: int
    batch_processing: bool = False
    github_integration: bool = False
    scheduled_regeneration: bool = False
    priority_processing: bool = False
    support_level: str = "community"


# Plan configurations
PLAN_LIMITS = {
    "free": PlanLimits(
        monthly_generations=10,
        max_pages_per_crawl=50,
        max_concurrent_jobs=1,
        support_level="community"
    ),
    "starter": PlanLimits(
        monthly_generations=100,
        max_pages_per_crawl=200,
        max_concurrent_jobs=3,
        support_level="email"
    ),
    "professional": PlanLimits(
        monthly_generations=1000,
        max_pages_per_crawl=500,
        max_concurrent_jobs=10,
        batch_processing=True,
        github_integration=True,
        priority_processing=True,
        support_level="priority"
    ),
    "enterprise": PlanLimits(
        monthly_generations=999999,  # Unlimited
        max_pages_per_crawl=2000,
        max_concurrent_jobs=100,
        batch_processing=True,
        github_integration=True,
        scheduled_regeneration=True,
        priority_processing=True,
        support_level="dedicated"
    )
}


def generate_api_key() -> str:
    """Generate a secure API key."""
    # Format: llmxt_live_<random_string>
    # Similar to Stripe's key format
    prefix = "llmxt_live_" if os.getenv("ENVIRONMENT") == "production" else "llmxt_test_"
    return prefix + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def create_user(email: str, plan: str = "free") -> Dict[str, str]:
    """Create a new user with API key."""
    api_key = generate_api_key()
    hashed_key = hash_api_key(api_key)

    user = {
        'email': email,
        'api_key_hash': hashed_key,
        'api_key_prefix': api_key[:15],  # Store prefix for identification
        'plan': plan,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'usage_this_month': 0,
        'last_reset_date': datetime.utcnow().strftime('%Y-%m')
    }

    try:
        users_table.put_item(Item=user)

        return {
            'email': email,
            'api_key': api_key,  # Return full key only on creation
            'plan': plan,
            'message': 'Store this API key securely. It will not be shown again.'
        }
    except ClientError as e:
        raise HTTPException(status_code=500, detail="Failed to create user")


async def validate_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """Validate API key from Bearer token."""
    api_key = credentials.credentials

    if not api_key or not api_key.startswith(('llmxt_live_', 'llmxt_test_')):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    # Hash the provided key
    hashed_key = hash_api_key(api_key)

    try:
        # Look up user by API key hash
        response = users_table.scan(
            FilterExpression='api_key_hash = :hash',
            ExpressionAttributeValues={':hash': hashed_key}
        )

        if not response['Items']:
            raise HTTPException(status_code=401, detail="Invalid API key")

        user_data = response['Items'][0]

        # Check if monthly usage needs reset
        current_month = datetime.utcnow().strftime('%Y-%m')
        if user_data.get('last_reset_date') != current_month:
            # Reset monthly usage
            users_table.update_item(
                Key={'email': user_data['email']},
                UpdateExpression='SET usage_this_month = :zero, last_reset_date = :month',
                ExpressionAttributeValues={
                    ':zero': 0,
                    ':month': current_month
                }
            )
            user_data['usage_this_month'] = 0

        return User(
            email=user_data['email'],
            api_key=api_key,  # Return the provided key (not hash)
            plan=user_data.get('plan', 'free'),
            stripe_customer_id=user_data.get('stripe_customer_id'),
            created_at=user_data['created_at'],
            updated_at=user_data['updated_at']
        )

    except ClientError as e:
        raise HTTPException(status_code=500, detail="Authentication failed")


async def check_rate_limit(user: User) -> bool:
    """Check if user has exceeded rate limits."""
    plan_limits = PLAN_LIMITS.get(user.plan, PLAN_LIMITS['free'])

    try:
        # Get current usage
        response = users_table.get_item(Key={'email': user.email})

        if not response.get('Item'):
            return False

        usage = response['Item'].get('usage_this_month', 0)

        if usage >= plan_limits.monthly_generations:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly limit exceeded ({usage}/{plan_limits.monthly_generations}). Upgrade your plan at https://llmxt.com/pricing"
            )

        return True

    except ClientError:
        return True  # Allow on error, track separately


async def track_usage(
    user: User,
    endpoint: str,
    url: str,
    pages_processed: int = 0,
    output_size_kb: float = 0,
    duration_seconds: float = 0
):
    """Track API usage for billing."""
    try:
        # Update user's monthly usage
        users_table.update_item(
            Key={'email': user.email},
            UpdateExpression='SET usage_this_month = usage_this_month + :inc',
            ExpressionAttributeValues={':inc': 1}
        )

        # Log detailed usage
        usage_record = {
            'id': secrets.token_hex(16),
            'email': user.email,
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'url': url,
            'pages_processed': pages_processed,
            'output_size_kb': output_size_kb,
            'duration_seconds': duration_seconds,
            'plan': user.plan
        }

        usage_table.put_item(Item=usage_record)

    except ClientError as e:
        # Log error but don't fail the request
        print(f"Failed to track usage: {e}")


async def get_user_usage(user: User) -> Dict[str, Any]:
    """Get user's current usage statistics."""
    plan_limits = PLAN_LIMITS.get(user.plan, PLAN_LIMITS['free'])

    try:
        # Get user record
        response = users_table.get_item(Key={'email': user.email})

        if not response.get('Item'):
            return {
                'plan': user.plan,
                'monthly_limit': plan_limits.monthly_generations,
                'used_this_month': 0,
                'remaining': plan_limits.monthly_generations
            }

        usage = response['Item'].get('usage_this_month', 0)

        # Get detailed usage for current month
        current_month = datetime.utcnow().strftime('%Y-%m')
        usage_response = usage_table.query(
            IndexName='email-timestamp-index',
            KeyConditionExpression='email = :email AND begins_with(#ts, :month)',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':email': user.email,
                ':month': current_month
            }
        )

        # Calculate totals
        total_pages = sum(item.get('pages_processed', 0) for item in usage_response.get('Items', []))
        total_size_kb = sum(item.get('output_size_kb', 0) for item in usage_response.get('Items', []))

        return {
            'plan': user.plan,
            'plan_limits': plan_limits.dict(),
            'monthly_limit': plan_limits.monthly_generations,
            'used_this_month': usage,
            'remaining': max(0, plan_limits.monthly_generations - usage),
            'total_pages_processed': total_pages,
            'total_output_kb': round(total_size_kb, 2),
            'reset_date': f"{current_month}-01"
        }

    except ClientError as e:
        raise HTTPException(status_code=500, detail="Failed to get usage data")


async def update_user_plan(email: str, new_plan: str, stripe_customer_id: Optional[str] = None):
    """Update user's subscription plan."""
    try:
        update_expr = 'SET #plan = :plan, updated_at = :now'
        expr_values = {
            ':plan': new_plan,
            ':now': datetime.utcnow().isoformat()
        }

        if stripe_customer_id:
            update_expr += ', stripe_customer_id = :stripe_id'
            expr_values[':stripe_id'] = stripe_customer_id

        users_table.update_item(
            Key={'email': email},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={'#plan': 'plan'},
            ExpressionAttributeValues=expr_values
        )

    except ClientError as e:
        raise HTTPException(status_code=500, detail="Failed to update plan")


# JWT functions for dashboard authentication
def create_access_token(email: str) -> str:
    """Create JWT access token for dashboard."""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    payload = {
        'email': email,
        'exp': expire,
        'iat': datetime.utcnow()
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return email."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('email')
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")