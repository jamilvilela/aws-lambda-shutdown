# S3 bucket that stores config.json (the Lambda can also read a local file).

resource "aws_s3_bucket" "config" {
  bucket = var.config_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "config" {
  bucket = aws_s3_bucket.config.id
  versioning_configuration {
    status = "Enabled"
  }
}