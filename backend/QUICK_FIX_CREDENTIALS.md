# 🚀 Quick Fix: Get Your Demo Working Now

## Problem
Your AWS bearer token isn't compatible with Strands Agents (which uses boto3). The system needs standard AWS credentials.

## Immediate Solutions (Pick One)

### Option A: Use Anthropic Claude (Fastest Fix - 2 minutes)
1. Go to: https://console.anthropic.com/
2. Sign up (free $5 credit)
3. Create API key
4. Edit your `.env` file:
```bash
# Comment out or remove AWS lines
# AWS_BEARER_TOKEN_BEDROCK=...

# Add this instead:
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```
5. Test: `uv run python test_mvp_demo.py`

### Option B: Use OpenAI (Alternative)
1. Go to: https://platform.openai.com/api-keys
2. Sign up (free $5 credit)
3. Create API key
4. Edit your `.env` file:
```bash
# Comment out AWS lines
# AWS_BEARER_TOKEN_BEDROCK=...

# Add this instead:
OPENAI_API_KEY=sk-your-openai-key-here
```

### Option C: Fix AWS Bedrock (More Complex)
Your bearer token contains temporary credentials that need to be extracted:

1. **Extract from your token**: `AWS_BEARER_TOKEN_BEDROCK=ABSKQmVkcm9ja0FQSUtleS1lbXV1LWF0LTQ2ODYyOTc1MzMzNjpx...`

2. **The Access Key ID is**: `ASIAW2HECRX4OZ2QL3V5` (visible in your original token)

3. **You need to find**:
   - Secret Access Key (hidden in the token)
   - Session Token (hidden in the token)

4. **Replace in .env**:
```bash
# Remove this line:
# AWS_BEARER_TOKEN_BEDROCK=...

# Add these instead:
AWS_ACCESS_KEY_ID=ASIAW2HECRX4OZ2QL3V5
AWS_SECRET_ACCESS_KEY=your_secret_key_from_token
AWS_SESSION_TOKEN=your_session_token_from_token
AWS_DEFAULT_REGION=eu-north-1
```

## Why This Happened
- AWS bearer tokens are pre-signed URLs for specific services
- Strands Agents uses boto3 which expects standard AWS credential format
- The bearer token needs to be "unpacked" into individual credential components

## Recommendation for Hackathon Demo
**Use Anthropic Claude** - it's the fastest path to a working demo:
- ✅ 2-minute setup
- ✅ Excellent for educational content
- ✅ Free $5 credit
- ✅ No complex AWS configuration

## Test Your Fix
After updating credentials:
```bash
cd backend
uv run python test_mvp_demo.py
```

You should see "✅ Content generation successful!" instead of credential errors.

## For Production Later
Once your demo is working, you can always switch back to AWS Bedrock with proper credentials from your AWS administrator.