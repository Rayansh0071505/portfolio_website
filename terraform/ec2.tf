# Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# EC2 Instance for Backend
resource "aws_instance" "backend" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  key_name               = var.key_pair_name
  iam_instance_profile   = aws_iam_instance_profile.backend_instance.name
  vpc_security_group_ids = [aws_security_group.backend.id]

  # Root volume configuration
  root_block_device {
    volume_size           = var.instance_root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true

    tags = {
      Name = "${var.project_name}-root-volume"
    }
  }

  # User data script to install Docker and pull/run the backend
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    AWS_REGION           = var.aws_region
    PROJECT_NAME         = var.project_name
    DOCKER_IMAGE         = var.docker_image
    BACKEND_PORT         = var.backend_port
    CLOUDFRONT_SECRET    = var.cloudfront_secret
    REDIS_CACHE_URL      = var.redis_enabled ? "redis://${aws_elasticache_cluster.semantic_cache[0].cache_nodes[0].address}:${aws_elasticache_cluster.semantic_cache[0].cache_nodes[0].port}" : ""
  }))

  monitoring              = true
  disable_api_termination = false

  tags = {
    Name = "${var.project_name}-backend"
  }

  # Wait for instance to be ready
  depends_on = [
    aws_internet_gateway.main,
    aws_iam_role_policy.backend_parameter_store,
    aws_iam_role_policy.backend_s3,
    aws_iam_role_policy.backend_ecr
  ]
}

# Elastic IP for consistent public IP
resource "aws_eip" "backend" {
  instance = aws_instance.backend.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-backend-eip"
  }

  depends_on = [aws_internet_gateway.main]
}

# Additional EBS Volume for Data
resource "aws_ebs_volume" "backend_data" {
  availability_zone = aws_instance.backend.availability_zone
  size              = 50  # Free tier gives 30GB/month, this is additional
  type              = "gp3"
  encrypted         = true

  tags = {
    Name = "${var.project_name}-data-volume"
  }
}

# Attach EBS volume to EC2 instance
resource "aws_volume_attachment" "backend_data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.backend_data.id
  instance_id = aws_instance.backend.id
}

# CloudWatch Log Group for EC2
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/aws/ec2/${var.project_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-logs"
  }
}
