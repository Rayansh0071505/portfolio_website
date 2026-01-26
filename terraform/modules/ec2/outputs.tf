output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.backend.id
}

output "public_ip" {
  description = "Public IP address (Elastic IP)"
  value       = aws_eip.backend.public_ip
}

output "public_dns" {
  description = "Public DNS name"
  value       = aws_instance.backend.public_dns
}

output "private_ip" {
  description = "Private IP address"
  value       = aws_instance.backend.private_ip
}
