provider "aws" {
  region = var.aws_region
}

# 1. VPC & Network Setup
resource "aws_vpc" "caloriq_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "caloriq-vpc"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.caloriq_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"
  tags = {
    Name = "caloriq-public-subnet"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.caloriq_vpc.id
  tags = {
    Name = "caloriq-igw"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.caloriq_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = {
    Name = "caloriq-public-rt"
  }
}

resource "aws_route_table_association" "public_rta" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# 2. Security Group (Open SSH & Flask Port 5000)
resource "aws_security_group" "caloriq_sg" {
  name        = "caloriq-security-group"
  description = "Allow inbound traffic to CaloriQ server"
  vpc_id      = aws_vpc.caloriq_vpc.id

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Flask API Port
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "caloriq-sg"
  }
}

# 3. EC2 Instance
resource "aws_instance" "caloriq_instance" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.caloriq_sg.id]
  key_name      = var.key_name

  # Provision sufficient storage for OS + Docker + LLM Weights
  root_block_device {
    volume_size = 40
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              # Update packages
              apt-get update -y
              apt-get install -y docker.io git
              systemctl start docker
              systemctl enable docker
              usermod -aG docker ubuntu

              # Pull and run the container
              # Replace with your Dockerhub registry or build locally on EC2
              # docker run -d -p 5000:5000 -p 11434:11434 your-registry/caloriq:latest
              EOF

  tags = {
    Name = "CaloriQ-Deployment-Host"
  }
}
