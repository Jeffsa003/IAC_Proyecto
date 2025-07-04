# lambda_getCourses.tf

# 1. Empaquetado del código fuente de la Lambda getCourses
data "archive_file" "get_courses_zip" {
  type        = "zip"
  source_dir  = "logica_recursos/lambdas/getCourses/"
  output_path = ".terraform/zips/getCourses.zip"
}

# 2. Rol de IAM para la Lambda
resource "aws_iam_role" "get_courses_lambda_role" {
  name = "${var.project_name}-getCourses-role"

  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# 3. Política de IAM (permisos para logs y para leer de DynamoDB)
resource "aws_iam_policy" "get_courses_lambda_policy" {
  name        = "${var.project_name}-getCourses-policy"
  description = "IAM policy for getCourses Lambda"

  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-getCourses:*"
      },
      {
        Action   = ["dynamodb:Scan"],
        Effect   = "Allow",
        Resource = aws_dynamodb_table.main_table.arn
      }
    ]
  })
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# 4. Adjuntar la política al rol
resource "aws_iam_role_policy_attachment" "get_courses_lambda_attach" {
  role       = aws_iam_role.get_courses_lambda_role.name
  policy_arn = aws_iam_policy.get_courses_lambda_policy.arn
}

# 5. Recurso de la Función Lambda
resource "aws_lambda_function" "get_courses" {
  function_name    = "${var.project_name}-getCourses"
  handler          = "main.handler"
  runtime          = "python3.9"
  role             = aws_iam_role.get_courses_lambda_role.arn
  filename         = data.archive_file.get_courses_zip.output_path
  source_code_hash = data.archive_file.get_courses_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.main_table.name
    }
  }

  tags = {
    Name = "${var.project_name}-getCourses"
  }
}
