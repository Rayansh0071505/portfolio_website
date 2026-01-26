output "role_arn" {
  description = "IAM role ARN"
  value       = aws_iam_role.ec2_role.arn
}

output "instance_profile_name" {
  description = "IAM instance profile name"
  value       = aws_iam_instance_profile.ec2_profile.name
}
