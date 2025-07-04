# main.tf
# Este archivo puede usarse para definir variables locales (locals) 
# o para gestionar dependencias explícitas si el proyecto crece en complejidad.
# Por ahora, Terraform cargará automáticamente todos los archivos .tf del directorio.

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
