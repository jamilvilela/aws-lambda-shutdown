output "lambda_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.shutdown.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.shutdown.function_name
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic"
  value       = aws_sns_topic.shutdown.arn
}

output "sns_topic_name" {
  description = "Name of the SNS topic"
  value       = aws_sns_topic.shutdown.name
}

output "scheduler_role_arn" {
  description = "ARN of the IAM role for EventBridge Scheduler"
  value       = aws_iam_role.scheduler_role.arn
}

output "config_bucket_name" {
  description = "Name of the S3 bucket for config.json"
  value       = aws_s3_bucket.config.id
}

output "config_bucket_arn" {
  description = "ARN of the S3 bucket for config.json"
  value       = aws_s3_bucket.config.arn
}