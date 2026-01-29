# 🔑 AI Credentials Setup Guide

To enable full AI agent functionality in the Educational Content Generator, you need to configure credentials for at least one AI service provider.

## Quick Setup (Choose One Provider)

### Option 1: Anthropic Claude (Recommended)
1. Get API key from: https://console.anthropic.com/
2. Add to your `.env` file:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Option 2: OpenAI GPT
1. Get API key from: https://platform.openai.com/api-keys
2. Add to your `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Option 3: Google Gemini
1. Get API key from: https://makersuite.google.com/app/apikey
2. Add to your `.env` file:
```bash
GOOGLE_API_KEY=your_google_api_key_here
```

### Option 4: AWS Bedrock (Recommended for Enterprise)

AWS Bedrock requires standard AWS credentials. The bearer token you have needs to be converted to standard AWS credentials.

#### Method 1: Extract Credentials from Bearer Token
Your bearer token contains temporary AWS credentials. You need to extract:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY  
- AWS_SESSION_TOKEN

#### Method 2: Use AWS CLI (Recommended)
1. Install AWS CLI: https://aws.amazon.com/cli/
2. Configure credentials:
```bash
aws configure
```
3. Or set environment variables:
```bash
AWS_ACCESS_KEY_ID=ASIAW2HECRX4OZ2QL3V5
AWS_SECRET_ACCESS_KEY=your_secret_key_from_token
AWS_SESSION_TOKEN=your_session_token_from_bearer_token
AWS_DEFAULT_REGION=eu-north-1
```

#### Method 3: AWS Profile
Create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = ASIAW2HECRX4OZ2QL3V5
aws_secret_access_key = your_secret_key
aws_session_token = your_session_token
region = eu-north-1
```

**Note**: Bearer tokens are not directly supported by boto3/Strands Agents. You need standard AWS credentials.

## Complete .env File Example

Create `backend/.env` with your chosen provider:

```bash
# Choose ONE AI provider
ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here

# Application settings
DEBUG=true
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads
CHROMA_PERSIST_DIR=chroma_db
```

## Testing Your Setup

After adding credentials, test the system:

```bash
cd backend
uv run python test_agents_setup.py
```

You should see agents connecting successfully instead of "Unable to locate credentials" errors.

## For Hackathon Demo

### If You Have Credentials:
- ✅ Full AI-powered educational content generation
- ✅ Advanced learning objectives with Bloom's taxonomy
- ✅ Sophisticated content structuring and assessments
- ✅ Professional-quality educational scripts

### If You Don't Have Credentials:
- ✅ System still works with robust fallback mechanisms
- ✅ Demonstrates production-ready error handling
- ✅ Shows reliability under adverse conditions
- ✅ Perfect for showing enterprise-grade robustness

## Cost Considerations

### Free Tiers Available:
- **Anthropic**: $5 free credit for new accounts
- **OpenAI**: $5 free credit for new accounts  
- **Google**: Free tier with rate limits
- **AWS Bedrock**: Pay-per-use (typically $0.01-0.10 per request)

### For Demo Purposes:
A few dollars of credit is sufficient for extensive hackathon demonstrations.

## Security Notes

- Never commit `.env` files to version control
- Use environment variables in production
- Rotate API keys regularly
- Monitor usage and set billing alerts

## Troubleshooting

### "Unable to locate credentials" Error:
1. Check `.env` file exists in `backend/` directory
2. Verify API key format is correct
3. Ensure no extra spaces or quotes around keys
4. Restart the server after adding credentials

### API Rate Limits:
- Most providers have generous rate limits for demos
- If you hit limits, the system will gracefully fall back
- Consider upgrading to paid tiers for production use

## Provider Comparison for Educational Content

| Provider | Best For | Strengths |
|----------|----------|-----------|
| **Anthropic Claude** | Educational content | Excellent at structured, pedagogical responses |
| **OpenAI GPT-4** | General purpose | Strong reasoning and creativity |
| **Google Gemini** | Cost-effective | Good balance of quality and cost |
| **AWS Bedrock** | Enterprise | Scalable, integrated with AWS services |

**Recommendation**: Start with Anthropic Claude for the best educational content generation quality.