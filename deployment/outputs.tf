output "public_ip" {
  value       = aws_instance.caloriq_instance.public_ip
  description = "Public IP Address of the CaloriQ Host"
}

output "api_endpoint" {
  value       = "http://${aws_instance.caloriq_instance.public_ip}:5000/api"
  description = "Backend URL endpoint to put in settings / Flutter configuration"
}
