terraform {
  backend "gcs" {
    bucket  = "<YOUR_TF_STATE_BUCKET>"
    prefix  = "newsletter-platform/terraform/state"
  }
}
