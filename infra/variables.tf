variable "region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "notification_email" {
  description = "Email address for SNS notifications"
  type        = string
}

variable "config_bucket_name" {
  description = "S3 bucket name for config.json (must be globally unique)"
  type        = string
}

variable "lambda_runtime" {
  description = "Python runtime used by the Lambda function"
  type        = string
  default     = "python3.13"
}

variable "lambda_source_path" {
  description = "Path to the repository root (parent of the 'src' package), used by the archive provider"
  type        = string
  default     = ".."
}

variable "lambda_output_path" {
  description = "Path where the Lambda deployment package will be created"
  type        = string
  default     = "../dist/lambda.zip"
}

variable "layer_source_path" {
  description = "Path to the directory prepared by scripts/build-layer.sh (contains python/lib/python3.x/site-packages)"
  type        = string
  default     = "../build/layer"
}

variable "layer_output_path" {
  description = "Path where the Lambda layer package will be created"
  type        = string
  default     = "../dist/layer.zip"
}

variable "config_file_path" {
  description = "Path to the config.json file"
  type        = string
  default     = "../config.json"
}