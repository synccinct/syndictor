output "cloud_run_urls" {
  value = module.compute.cloud_run_urls
}

output "firestore_database_id" {
  value = module.storage.firestore_database_id
}

output "pubsub_topics" {
  value = module.messaging.topics
}

output "monitoring_dashboard_url" {
  value = module.monitoring.dashboard_url
}
