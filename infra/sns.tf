# SNS topic for failure/error notifications.

resource "aws_sns_topic" "shutdown" {
  name = "${local.name_prefix}-sns"
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.shutdown.arn
  protocol  = "email"
  endpoint  = var.notification_email
}