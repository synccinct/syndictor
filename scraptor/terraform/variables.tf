variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "primary_region" {
  description = "Primary deployment region"
  type        = string
  default     = "us-central1"
}

variable "secondary_region" {
  description = "Secondary deployment region"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Add variables for all module configurations, e.g., CPU, memory, scaling, API keys, monitoring, cost thresholds, feature flags, etc.
