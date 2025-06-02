# Setup Guide for AI-Powered Micro-Niche Content Syndication Service

This guide will walk you through setting up the complete content syndication system on Google Cloud Platform.

## Prerequisites

1. **Google Cloud Account**: Set up with billing enabled
2. **Domain Name**: For custom URLs and SSL certificates
3. **External API Accounts**: Set up accounts with required platforms
4. **Development Environment**: Python 3.9+, Docker, Terraform

## Required API Keys and Accounts

Before starting the setup, obtain the following API keys:

### Google Cloud Platform
- Create a GCP project
- Enable required APIs (listed below)
- Generate service account keys for Vertex AI, Firestore, etc.

### Content Platforms
- **LinkedIn**: Developer account and app registration
- **Twitter/X**: Developer account and API v2 access
- **Medium**: Integration token (limited functionality)
- **Substack**: No official API (using web automation)
- **Ghost**: API keys if using Ghost CMS

### Monitoring & Support
- **Telegram**: Bot token from @BotFather
- **Impact.com**: Affiliate network API credentials (optional)

### AI Services
- **Gemini Pro**: API key from Google AI Studio

## Step 1: GCP Project Setup

### 1.1 Create GCP Project

```bash
# Set project variables
export PROJECT_ID="niche-syndication-$(date +%s)"
export REGION="us-central1"
export ZONE="us-central1-a"

# Create project
gcloud projects create $PROJECT_ID --name="Niche Content Syndication"

# Set default project
gcloud config set project $PROJECT_ID

# Link billing account (replace BILLING_ACCOUNT_ID)
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### 1.2 Enable Required APIs

```bash
# Enable all required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    cloudscheduler.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    pubsub.googleapis.com \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    iam.googleapis.com
```

### 1.3 Set Up Service Accounts

```bash
# Create service account for Cloud Run services
gcloud iam service-accounts create syndication-runner \
    --description="Service account for content syndication services" \
    --display-name="Syndication Runner"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:syndication-runner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:syndication-runner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:syndication-runner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:syndication-runner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:syndication-runner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

## Step 2: Infrastructure Deployment

### 2.1 Clone Repository

```bash
git clone <your-repo-url>
cd niche-syndication-service
```

### 2.2 Configure Environment Variables

Create a `.env` file with your configuration:

```bash
# .env file
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export GEMINI_API_KEY="your-gemini-api-key"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_ALLOWED_USERS="your-user-id"
export LINKEDIN_CLIENT_ID="your-linkedin-client-id"
export LINKEDIN_CLIENT_SECRET="your-linkedin-client-secret"
export TWITTER_API_KEY="your-twitter-api-key"
export TWITTER_API_SECRET="your-twitter-api-secret"
export TWITTER_ACCESS_TOKEN="your-twitter-access-token"
export TWITTER_ACCESS_SECRET="your-twitter-access-secret"
export MEDIUM_INTEGRATION_TOKEN="your-medium-token"
export IMPACT_API_KEY="your-impact-api-key"
```

### 2.3 Store Secrets in Secret Manager

```bash
# Load environment variables
source .env

# Store API keys securely
gcloud secrets create gemini-api-key --data-file=<(echo -n "$GEMINI_API_KEY")
gcloud secrets create telegram-bot-token --data-file=<(echo -n "$TELEGRAM_BOT_TOKEN")
gcloud secrets create linkedin-client-id --data-file=<(echo -n "$LINKEDIN_CLIENT_ID")
gcloud secrets create linkedin-client-secret --data-file=<(echo -n "$LINKEDIN_CLIENT_SECRET")
gcloud secrets create twitter-api-key --data-file=<(echo -n "$TWITTER_API_KEY")
gcloud secrets create twitter-api-secret --data-file=<(echo -n "$TWITTER_API_SECRET")
gcloud secrets create twitter-access-token --data-file=<(echo -n "$TWITTER_ACCESS_TOKEN")
gcloud secrets create twitter-access-secret --data-file=<(echo -n "$TWITTER_ACCESS_SECRET")
gcloud secrets create medium-integration-token --data-file=<(echo -n "$MEDIUM_INTEGRATION_TOKEN")
gcloud secrets create impact-api-key --data-file=<(echo -n "$IMPACT_API_KEY")
```

### 2.4 Deploy Infrastructure with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION"

# Deploy infrastructure
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION"
```

## Step 3: Deploy Services

### 3.1 Build and Deploy Content Scrapers

```bash
# Navigate to scrapers directory
cd src/scrapers

# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/content-scraper

# Deploy to Cloud Run
gcloud run deploy content-scraper \
    --image gcr.io/$PROJECT_ID/content-scraper \
    --platform managed \
    --region $REGION \
    --service-account syndication-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --no-allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 900 \
    --set-env-vars PROJECT_ID=$PROJECT_ID
```

### 3.2 Build and Deploy Content Processor

```bash
# Navigate to processor directory
cd ../content-processor

# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/content-processor

# Deploy to Cloud Run
gcloud run deploy content-processor \
    --image gcr.io/$PROJECT_ID/content-processor \
    --platform managed \
    --region $REGION \
    --service-account syndication-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --no-allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --timeout 900 \
    --set-env-vars PROJECT_ID=$PROJECT_ID
```

### 3.3 Build and Deploy Distribution Service

```bash
# Navigate to distribution directory
cd ../distribution

# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/content-distributor

# Deploy to Cloud Run
gcloud run deploy content-distributor \
    --image gcr.io/$PROJECT_ID/content-distributor \
    --platform managed \
    --region $REGION \
    --service-account syndication-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --no-allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 900 \
    --set-env-vars PROJECT_ID=$PROJECT_ID
```

### 3.4 Build and Deploy Monitoring Service

```bash
# Navigate to monitoring directory
cd ../monitoring

# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/monitoring-service

# Deploy to Cloud Run
gcloud run deploy monitoring-service \
    --image gcr.io/$PROJECT_ID/monitoring-service \
    --platform managed \
    --region $REGION \
    --service-account syndication-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 3 \
    --timeout 300 \
    --set-env-vars PROJECT_ID=$PROJECT_ID
```

## Step 4: Configure Content Sources

### 4.1 Create Source Configuration

Create a JSON file with your content sources:

```json
{
  "sources": [
    {
      "name": "FDA Medical Devices",
      "type": "rss",
      "config": {
        "feed_urls": [
          "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-devices/rss.xml"
        ],
        "rate_limit": 2.0,
        "max_items": 10
      }
    },
    {
      "name": "Maritime News",
      "type": "html",
      "config": {
        "base_url": "https://www.maritime-executive.com",
        "list_page": "/news",
        "rate_limit": 3.0,
        "max_items": 10
      }
    }
  ]
}
```

### 4.2 Upload Source Configuration to Firestore

```bash
# Use the gcloud firestore command or the Firebase console
# to upload your source configuration
```

## Step 5: Set Up Scheduling

### 5.1 Create Cloud Scheduler Jobs

```bash
# Create scraping job (runs every 2 hours)
gcloud scheduler jobs create http scraping-job \
    --schedule="0 */2 * * *" \
    --uri="https://content-scraper-<hash>-uc.a.run.app/scrape" \
    --http-method=POST \
    --oidc-service-account-email=syndication-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --location=$REGION \
    --time-zone="UTC"

# Create processing job (runs every 3 hours)
gcloud scheduler jobs create http processing-job \
    --schedule="0 */3 * * *" \
    --uri="https://content-processor-<hash>-uc.a.run.app/process" \
    --http-method=POST \
    --oidc-service-account-email=syndication-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --location=$REGION \
    --time-zone="UTC"

# Create distribution job (runs every 4 hours)
gcloud scheduler jobs create http distribution-job \
    --schedule="0 */4 * * *" \
    --uri="https://content-distributor-<hash>-uc.a.run.app/distribute" \
    --http-method=POST \
    --oidc-service-account-email=syndication-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --location=$REGION \
    --time-zone="UTC"
```

## Step 6: Configure Monitoring

### 6.1 Set Up Telegram Bot

1. Create a bot with @BotFather on Telegram
2. Get your user ID by messaging @userinfobot
3. Start your monitoring service
4. Send `/start` to your bot to initialize

### 6.2 Configure Alerting

Set up Cloud Monitoring alerts for:
- Service failures
- High error rates
- Resource exhaustion
- API quota limits

## Step 7: Testing and Validation

### 7.1 Test Individual Services

```bash
# Test scraper
curl -X POST https://content-scraper-<hash>-uc.a.run.app/health

# Test processor
curl -X POST https://content-processor-<hash>-uc.a.run.app/health

# Test distributor
curl -X POST https://content-distributor-<hash>-uc.a.run.app/health

# Test monitoring
curl https://monitoring-service-<hash>-uc.a.run.app/health
```

### 7.2 Run End-to-End Test

```bash
# Trigger a full pipeline run
curl -X POST https://content-scraper-<hash>-uc.a.run.app/scrape
```

### 7.3 Validate Content Flow

1. Check Firestore for scraped content
2. Verify content processing with Gemini
3. Confirm distribution to platforms
4. Monitor system status via Telegram

## Step 8: Production Optimization

### 8.1 Security Hardening

- Review IAM permissions
- Enable audit logging
- Set up VPC firewall rules
- Configure identity-aware proxy

### 8.2 Performance Tuning

- Monitor Cloud Run metrics
- Adjust memory and CPU allocations
- Optimize concurrent request limits
- Configure auto-scaling parameters

### 8.3 Cost Optimization

- Set up billing alerts
- Review resource usage
- Implement cost monitoring
- Optimize scheduling frequency

## Step 9: Legal Compliance Setup

### 9.1 Content Usage Compliance

- Review terms of service for each source
- Implement attribution requirements
- Set up content filtering for sensitive data
- Create privacy policy documentation

### 9.2 GDPR/Data Privacy

- Configure data retention policies
- Implement data anonymization
- Set up consent management
- Create data processing documentation

## Maintenance and Updates

### Regular Tasks

1. **Weekly**: Review system metrics and performance
2. **Monthly**: Update source configurations and test new platforms
3. **Quarterly**: Security review and dependency updates
4. **Annually**: Architecture review and cost optimization

### Backup and Recovery

- Firestore automatic backups enabled
- Secret Manager versioning enabled
- Infrastructure state stored in Cloud Storage
- Disaster recovery procedures documented

## Troubleshooting

### Common Issues

1. **Service timeouts**: Increase timeout values in Cloud Run
2. **Rate limiting**: Adjust scraping intervals and retry logic
3. **API quotas**: Monitor usage and request quota increases
4. **Memory issues**: Increase allocated memory for processing

### Monitoring and Logs

- Use Cloud Logging for centralized log analysis
- Set up log-based metrics for business KPIs
- Configure error reporting for immediate alerts
- Monitor resource utilization trends

## Support and Maintenance

For ongoing support:
1. Monitor the Telegram bot for system alerts
2. Review Cloud Monitoring dashboards daily
3. Check error logs in Cloud Logging
4. Maintain API key rotations and updates

## Cost Estimation

Based on moderate usage (processing 100 articles/day):
- Cloud Run: $20-50/month
- Firestore: $10-30/month
- Vertex AI (Gemini): $50-150/month
- Other services: $20-50/month

**Total estimated cost: $100-280/month**

This can scale up or down based on content volume and processing frequency.