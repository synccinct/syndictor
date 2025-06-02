project_id         = "newsletter-prod-123"
primary_region     = "us-central1"
secondary_region   = "europe-west1"
environment        = "prod"

# Service configurations
scraper_cpu        = 2
scraper_memory     = "2Gi"
ai_cpu             = 2
ai_memory          = "4Gi"
max_instances      = 50

# External API configs (placeholders)
substack_api_key   = "REPLACE_ME"
twitter_api_key    = "REPLACE_ME"
linkedin_api_key   = "REPLACE_ME"
telegram_bot_token = "REPLACE_ME"

# Monitoring and alerting
alert_email        = "alerts@yourdomain.com"
cost_threshold     = 5000

# Security
enable_vpc         = true
enable_cloud_armor = true

# Feature flags
enable_memorystore = false
