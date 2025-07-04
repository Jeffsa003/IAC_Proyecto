# lambda_updateVideoStatus.tf

# --- Lambda updateVideoStatus ---

# 1. Empaquetado del código fuente
data "archive_file" "update_video_status_zip" {
  type        = "zip"
  source_dir  = "logica_recursos/lambdas/updateVideoStatus/"
  output_path = ".terraform/zips/updateVideoStatus.zip"
}

# 2. Rol de IAM para la Lambda
resource "aws_iam_role" "update_video_status_lambda_role" {
  name = "${var.project_name}-updateVideoStatus-role"

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

# 3. Política de IAM para la Lambda (Logs y escritura en DynamoDB)
resource "aws_iam_policy" "update_video_status_lambda_policy" {
  name        = "${var.project_name}-updateVideoStatus-policy"
  description = "IAM policy for updateVideoStatus Lambda"

  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-updateVideoStatus:*"
      },
      {
        Action   = ["dynamodb:UpdateItem"],
        Effect   = "Allow",
        Resource = aws_dynamodb_table.main_table.arn
      }
    ]
  })
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# 4. Adjuntar la política al rol de la Lambda
resource "aws_iam_role_policy_attachment" "update_video_status_lambda_attach" {
  role       = aws_iam_role.update_video_status_lambda_role.name
  policy_arn = aws_iam_policy.update_video_status_lambda_policy.arn
}

# 5. Recurso de la Función Lambda
resource "aws_lambda_function" "update_video_status" {
  function_name    = "${var.project_name}-updateVideoStatus"
  handler          = "main.handler"
  runtime          = "python3.9"
  role             = aws_iam_role.update_video_status_lambda_role.arn
  filename         = data.archive_file.update_video_status_zip.output_path
  source_code_hash = data.archive_file.update_video_status_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.main_table.name
    }
  }
}
