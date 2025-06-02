#!/bin/bash

# Create top-level files
touch backend.tf
touch main.tf
touch outputs.tf
touch variables.tf
touch terraform.tfvars
touch versions.tf
touch README.md

# Create the 'diagrams' directory and its content
mkdir diagrams
touch diagrams/architecture.mmd

# Create the '.github/workflows' directories and their content
mkdir -p .github/workflows
touch .github/workflows/terraform.yml
touch .github/workflows/security.yml

# Create the 'modules' directory and its subdirectories
mkdir -p modules/iam \
         modules/networking \
         modules/storage \
         modules/compute \
         modules/ai \
         modules/messaging \
         modules/monitoring \
         modules/secrets \
         modules/scheduler \
         modules/external

echo "Directory structure and empty files created successfully!"
