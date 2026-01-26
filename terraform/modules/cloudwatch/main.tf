# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"

  tags = {
    Name = "${var.project_name}-alerts"
  }
}

# SNS Subscription (Email)
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarm: CPU Utilization
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300  # 5 minutes
  statistic           = "Average"
  threshold           = 80   # 80%
  alarm_description   = "Alert when CPU > 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = var.instance_id
  }
}

# CloudWatch Alarm: Status Check Failed
resource "aws_cloudwatch_metric_alarm" "status_check" {
  alarm_name          = "${var.project_name}-status-check-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Alert when status check fails"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = var.instance_id
  }
}

# CloudWatch Alarm: Disk Space (requires CloudWatch Agent)
resource "aws_cloudwatch_metric_alarm" "disk_space" {
  alarm_name          = "${var.project_name}-low-disk-space"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "disk_free"
  namespace           = "CWAgent"
  period              = 300
  statistic           = "Average"
  threshold           = 2000000000  # 2 GB in bytes
  alarm_description   = "Alert when disk free < 2GB"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = var.instance_id
    path       = "/"
    device     = "nvme0n1p1"
    fstype     = "ext4"
  }
}

# CloudWatch Alarm: Memory (requires CloudWatch Agent)
resource "aws_cloudwatch_metric_alarm" "memory_high" {
  alarm_name          = "${var.project_name}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "mem_used_percent"
  namespace           = "CWAgent"
  period              = 300
  statistic           = "Average"
  threshold           = 85  # 85%
  alarm_description   = "Alert when memory > 85%"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = var.instance_id
  }
}

# CloudWatch Log Group for Application Logs
resource "aws_cloudwatch_log_group" "backend_logs" {
  name              = "/aws/ec2/${var.project_name}-backend"
  retention_in_days = 7  # Free tier: 5 GB ingestion, 7 days retention

  tags = {
    Name = "${var.project_name}-backend-logs"
  }
}
