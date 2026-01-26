# EC2 Instance for Backend API
resource "aws_instance" "backend" {
  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name

  subnet_id              = var.subnet_id
  vpc_security_group_ids = var.security_group_ids
  iam_instance_profile   = var.iam_instance_profile

  # EBS root volume (Free tier: 30 GB)
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20  # GB (under free tier limit of 30 GB)
    delete_on_termination = true
    encrypted             = true

    tags = {
      Name = "${var.project_name}-root-volume"
    }
  }

  # User data script for initial setup
  user_data = var.user_data

  # Enable detailed monitoring (free tier includes basic monitoring)
  monitoring = false  # Detailed monitoring costs extra

  # Instance metadata options
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # IMDSv2
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "${var.project_name}-backend"
  }

  lifecycle {
    ignore_changes = [ami]  # Prevent recreation on AMI updates
  }
}

# Elastic IP (Free if attached to running instance)
resource "aws_eip" "backend" {
  instance = aws_instance.backend.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-backend-eip"
  }
}
