# lambda_sendEmail.tf

# --- Lambda sendEmail ---

# 1. Empaquetado del código fuente
data "archive_file" "send_email_zip" {
  type        = "zip"
  source_dir  = "logica_recursos/lambdas/sendEmail/"
  output_path = ".terraform/zips/sendEmail.zip"
}

# 2. Rol de IAM para la Lambda
resource "aws_iam_role" "send_email_lambda_role" {
  name = "${var.project_name}-sendEmail-role"

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

# 3. Política de IAM para la Lambda (Logs, SQS, SES)
resource "aws_iam_policy" "send_email_lambda_policy" {
  name        = "${var.project_name}-sendEmail-policy"
  description = "IAM policy for sendEmail Lambda"

  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-sendEmail:*"
      },
      {
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ],
        Effect   = "Allow",
        Resource = aws_sqs_queue.email_notifications.arn
      },
      {
        Action   = ["ses:SendEmail", "ses:SendRawEmail"],
        Effect   = "Allow",
        Resource = aws_ses_email_identity.main.arn
      }
    ]
  })
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# 4. Adjuntar la política al rol
resource "aws_iam_role_policy_attachment" "send_email_lambda_attach" {
  role       = aws_iam_role.send_email_lambda_role.name
  policy_arn = aws_iam_policy.send_email_lambda_policy.arn
}

# 5. Recurso de la Función Lambda
resource "aws_lambda_function" "send_email" {
  function_name    = "${var.project_name}-sendEmail"
  handler          = "main.handler"
  runtime          = "python3.9"
  role             = aws_iam_role.send_email_lambda_role.arn
  filename         = data.archive_file.send_email_zip.output_path
  source_code_hash = data.archive_file.send_email_zip.output_base64sha256

  environment {
    variables = {
      SENDER_EMAIL = var.sender_email
    }
  }
}

# 6. Mapeo del origen de eventos (SQS -> Lambda)
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.email_notifications.arn
  function_name    = aws_lambda_function.send_email.arn
  batch_size       = 5 # Procesar hasta 5 mensajes a la vez
}
