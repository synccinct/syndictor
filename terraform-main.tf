# Terraform Configuration for Content Syndication Service
# infrastructure/terraform/main.tf

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "pubsub.googleapis.com",
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "iam.googleapis.com"
  ])

  service = each.value
  project = var.project_id

  disable_dependent_services = true
}

# Service Account for Cloud Run services
resource "google_service_account" "syndication_runner" {
  account_id   = "syndication-runner"
  display_name = "Content Syndication Runner"
  description  = "Service account for content syndication Cloud Run services"
}

# IAM bindings for the service account
resource "google_project_iam_member" "syndication_runner_bindings" {
  for_each = toset([
    "roles/run.invoker",
    "roles/datastore.user",
    "roles/secretmanager.secretAccessor",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/aiplatform.user",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.syndication_runner.email}"
}

# Firestore database
resource "google_firestore_database" "content_db" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# Cloud Storage bucket for artifacts and temporary files
resource "google_storage_bucket" "syndication_bucket" {
  name          = "${var.project_id}-syndication-storage"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Pub/Sub topic for async communication
resource "google_pubsub_topic" "content_processing" {
  name = "content-processing"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "content_distribution" {
  name = "content-distribution"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "monitoring_alerts" {
  name = "monitoring-alerts"

  depends_on = [google_project_service.apis]
}

# Pub/Sub subscriptions
resource "google_pubsub_subscription" "content_processing_sub" {
  name  = "content-processing-subscription"
  topic = google_pubsub_topic.content_processing.name

  message_retention_duration = "1200s"
  retain_acked_messages      = false

  ack_deadline_seconds = 300

  expiration_policy {
    ttl = "300000.5s"
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.content_processing.id
    max_delivery_attempts = 10
  }
}

resource "google_pubsub_subscription" "content_distribution_sub" {
  name  = "content-distribution-subscription"
  topic = google_pubsub_topic.content_distribution.name

  message_retention_duration = "1200s"
  retain_acked_messages      = false

  ack_deadline_seconds = 300

  expiration_policy {
    ttl = "300000.5s"
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.content_distribution.id
    max_delivery_attempts = 10
  }
}

# Cloud Scheduler jobs
resource "google_cloud_scheduler_job" "scraping_job" {
  name             = "content-scraping-job"
  description      = "Periodic content scraping job"
  schedule         = "0 */2 * * *"  # Every 2 hours
  time_zone        = "UTC"
  attempt_deadline = "900s"

  retry_config {
    retry_count = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://content-scraper-${google_cloud_run_service.scraper.status[0].url}/scrape"

    oidc_token {
      service_account_email = google_service_account.syndication_runner.email
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "processing_job" {
  name             = "content-processing-job"
  description      = "Periodic content processing job"
  schedule         = "0 */3 * * *"  # Every 3 hours
  time_zone        = "UTC"
  attempt_deadline = "900s"

  retry_config {
    retry_count = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://content-processor-${google_cloud_run_service.processor.status[0].url}/process"

    oidc_token {
      service_account_email = google_service_account.syndication_runner.email
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_cloud_scheduler_job" "distribution_job" {
  name             = "content-distribution-job"
  description      = "Periodic content distribution job"
  schedule         = "0 */4 * * *"  # Every 4 hours
  time_zone        = "UTC"
  attempt_deadline = "900s"

  retry_config {
    retry_count = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://content-distributor-${google_cloud_run_service.distributor.status[0].url}/distribute"

    oidc_token {
      service_account_email = google_service_account.syndication_runner.email
    }
  }

  depends_on = [google_project_service.apis]
}

# Cloud Run Services (placeholders - actual deployment happens separately)
resource "google_cloud_run_service" "scraper" {
  name     = "content-scraper"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/content-scraper:latest"
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
      }

      service_account_name = google_service_account.syndication_runner.email
      timeout_seconds      = 900
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
    ]
  }
}

resource "google_cloud_run_service" "processor" {
  name     = "content-processor"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/content-processor:latest"
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }
      }

      service_account_name = google_service_account.syndication_runner.email
      timeout_seconds      = 900
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "5"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
    ]
  }
}

resource "google_cloud_run_service" "distributor" {
  name     = "content-distributor"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/content-distributor:latest"
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
      }

      service_account_name = google_service_account.syndication_runner.email
      timeout_seconds      = 900
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
    ]
  }
}

resource "google_cloud_run_service" "monitoring" {
  name     = "monitoring-service"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/monitoring-service:latest"
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }

      service_account_name = google_service_account.syndication_runner.email
      timeout_seconds      = 300
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "3"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
    ]
  }
}

# IAM policy to allow unauthenticated access to monitoring service
resource "google_cloud_run_service_iam_member" "monitoring_public" {
  location = google_cloud_run_service.monitoring.location
  project  = google_cloud_run_service.monitoring.project
  service  = google_cloud_run_service.monitoring.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Monitoring and alerting
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notifications"
  type         = "email"
  labels = {
    email_address = "admin@yourdomain.com"  # Replace with your email
  }
}

# Error rate alert policy
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Run service error rate"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.1  # 10% error rate
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "1800s"
  }
}

# Memory utilization alert
resource "google_monitoring_alert_policy" "high_memory_usage" {
  display_name = "High Memory Usage"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Run memory utilization"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.8  # 80% memory usage
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "1800s"
  }
}

# Outputs
output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "service_account_email" {
  description = "Service account email for Cloud Run services"
  value       = google_service_account.syndication_runner.email
}

output "scraper_url" {
  description = "Content scraper service URL"
  value       = google_cloud_run_service.scraper.status[0].url
}

output "processor_url" {
  description = "Content processor service URL"
  value       = google_cloud_run_service.processor.status[0].url
}

output "distributor_url" {
  description = "Content distributor service URL"
  value       = google_cloud_run_service.distributor.status[0].url
}

output "monitoring_url" {
  description = "Monitoring service URL"
  value       = google_cloud_run_service.monitoring.status[0].url
}

output "storage_bucket_name" {
  description = "Cloud Storage bucket name"
  value       = google_storage_bucket.syndication_bucket.name
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.content_db.name
}

# Data sources for existing resources
data "google_project" "project" {
  project_id = var.project_id
}

# Cloud Build trigger for CI/CD (optional)
resource "google_cloudbuild_trigger" "build_trigger" {
  name        = "content-syndication-build"
  description = "Build trigger for content syndication services"

  github {
    owner = "your-github-username"  # Replace with your GitHub username
    name  = "niche-syndication-service"  # Replace with your repository name
    
    push {
      branch = "^main$"
    }
  }

  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t", "gcr.io/${var.project_id}/content-scraper:$COMMIT_SHA",
        "-t", "gcr.io/${var.project_id}/content-scraper:latest",
        "./src/scrapers"
      ]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push", "gcr.io/${var.project_id}/content-scraper:$COMMIT_SHA"
      ]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push", "gcr.io/${var.project_id}/content-scraper:latest"
      ]
    }

    step {
      name = "gcr.io/cloud-builders/gcloud"
      args = [
        "run", "deploy", "content-scraper",
        "--image", "gcr.io/${var.project_id}/content-scraper:$COMMIT_SHA",
        "--region", var.region,
        "--platform", "managed"
      ]
    }
  }

  depends_on = [google_project_service.apis]
}