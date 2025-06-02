module "iam" {
  source = "./modules/iam"
  project_id = var.project_id
  environment = var.environment
}

module "networking" {
  source = "./modules/networking"
  project_id = var.project_id
  primary_region = var.primary_region
  enable_vpc = var.enable_vpc
}

module "storage" {
  source = "./modules/storage"
  project_id = var.project_id
  primary_region = var.primary_region
  secondary_region = var.secondary_region
}

module "compute" {
  source = "./modules/compute"
  project_id = var.project_id
  primary_region = var.primary_region
  # Pass all service configs
}

module "ai" {
  source = "./modules/ai"
  project_id = var.project_id
  primary_region = var.primary_region
}

module "messaging" {
  source = "./modules/messaging"
  project_id = var.project_id
}

module "monitoring" {
  source = "./modules/monitoring"
  project_id = var.project_id
  alert_email = var.alert_email
  cost_threshold = var.cost_threshold
}

module "secrets" {
  source = "./modules/secrets"
  project_id = var.project_id
  # Pass all API keys and secrets
}

module "scheduler" {
  source = "./modules/scheduler"
  project_id = var.project_id
}

module "external" {
  source = "./modules/external"
  project_id = var.project_id
  # Pass all external API configs
}
