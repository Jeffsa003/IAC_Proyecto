# lambda_generateCertificate.tf

# 1. Empaquetado del código fuente
data "archive_file" "generate_certificate_zip" {
  type        = "zip"
  source_dir  = "logica_recursos/lambdas/generateCertificate/"
  output_path = ".terraform/zips/generateCertificate.zip"
}

# 2. Rol de IAM
resource "aws_iam_role" "generate_certificate_lambda_role" {
  name = "${var.project_name}-generateCertificate-role"

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

# 3. Política de IAM (Logs, DynamoDB Get, SQS Send, Cognito GetUser)
resource "aws_iam_policy" "generate_certificate_lambda_policy" {
  name        = "${var.project_name}-generateCertificate-policy"
  description = "IAM policy for generateCertificate Lambda"

  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-generateCertificate:*"
      },
      {
        Action   = ["dynamodb:GetItem"],
        Effect   = "Allow",
        Resource = aws_dynamodb_table.main_table.arn
      },
      {
        Action   = ["sqs:SendMessage"],
        Effect   = "Allow",
        Resource = aws_sqs_queue.email_notifications.arn
      },
      {
        Action   = ["cognito-idp:AdminGetUser"],
        Effect   = "Allow",
        Resource = aws_cognito_user_pool.main.arn
      }
    ]
  })
}

# 4. Adjuntar la política al rol
resource "aws_iam_role_policy_attachment" "generate_certificate_lambda_attach" {
  role       = aws_iam_role.generate_certificate_lambda_role.name
  policy_arn = aws_iam_policy.generate_certificate_lambda_policy.arn
}

# 5. Recurso de la Función Lambda
resource "aws_lambda_function" "generate_certificate" {
  function_name    = "${var.project_name}-generateCertificate"
  handler          = "main.handler"
  runtime          = "python3.9"
  role             = aws_iam_role.generate_certificate_lambda_role.arn
  filename         = data.archive_file.generate_certificate_zip.output_path
  source_code_hash = data.archive_file.generate_certificate_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME    = aws_dynamodb_table.main_table.name
      SQS_QUEUE_URL          = aws_sqs_queue.email_notifications.url
      COGNITO_USER_POOL_ID   = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-generateCertificate"
  }
}
