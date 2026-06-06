variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Target AWS Region"
}

variable "instance_type" {
  type        = string
  default     = "t3.xlarge" # Or GPU instance (e.g. g5.xlarge) if hardware acceleration for OCR/inference is preferred
  description = "EC2 Instance Size"
}

variable "ami_id" {
  type        = string
  default     = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS AMD64 in us-east-1 (Change depending on region)
  description = "Ubuntu AMI ID"
}

variable "key_name" {
  type        = string
  description = "Name of the AWS EC2 Key Pair for SSH"
}
