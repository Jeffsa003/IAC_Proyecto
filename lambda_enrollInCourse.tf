# lambda_enrollInCourse.tf

# 1. Empaquetado del código fuente
data "archive_file" "enroll_in_course_zip" {
  type        = "zip"
  source_dir  = "logica_recursos/lambdas/enrollInCourse/"
  output_path = ".terraform/zips/enrollInCourse.zip"
}

# 2. Rol de IAM
resource "aws_iam_role" "enroll_in_course_lambda_role" {
  name = "${var.project_name}-enrollInCourse-role"

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

# 3. Política de IAM (Logs y escritura en DynamoDB)
resource "aws_iam_policy" "enroll_in_course_lambda_policy" {
  name        = "${var.project_name}-enrollInCourse-policy"
  description = "IAM policy for enrollInCourse Lambda"

  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-enrollInCourse:*"
      },
      {
        Action   = ["dynamodb:PutItem"],
        Effect   = "Allow",
        Resource = aws_dynamodb_table.main_table.arn
      }
    ]
  })
}

# 4. Adjuntar la política al rol
resource "aws_iam_role_policy_attachment" "enroll_in_course_lambda_attach" {
  role       = aws_iam_role.enroll_in_course_lambda_role.name
  policy_arn = aws_iam_policy.enroll_in_course_lambda_policy.arn
}

# 5. Recurso de la Función Lambda
resource "aws_lambda_function" "enroll_in_course" {
  function_name    = "${var.project_name}-enrollInCourse"
  handler          = "main.handler"
  runtime          = "python3.9"
  role             = aws_iam_role.enroll_in_course_lambda_role.arn
  filename         = data.archive_file.enroll_in_course_zip.output_path
  source_code_hash = data.archive_file.enroll_in_course_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.main_table.name
    }
  }

  tags = {
    Name = "${var.project_name}-enrollInCourse"
  }
}
