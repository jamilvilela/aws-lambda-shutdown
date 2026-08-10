# Local values shared across the module.

locals {
  name_prefix = "aws-lambda-shutdown"

  common_tags = {
    Project     = "aws-lambda-shutdown"
    ManagedBy   = "Terraform"
    Environment = var.environment
  }
}