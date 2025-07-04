# lambda_trackProgress.tf

# 1. Source code packaging
data "archive_file" "track_progress_zip" {
  type        = "zip"
  source_dir  = "logica_recursos/lambdas/trackProgress/"
  output_path = ".terraform/zips/trackProgress.zip"
}

# 2. IAM Role
resource "aws_iam_role" "track_progress_lambda_role" {
  name = "${var.project_name}-trackProgress-role"

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

# 3. IAM Policy (Logs and DynamoDB Update)
resource "aws_iam_policy" "track_progress_lambda_policy" {
  name        = "${var.project_name}-trackProgress-policy"
  description = "IAM policy for trackProgress Lambda"

  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-trackProgress:*"
      },
      {
        Action   = ["dynamodb:UpdateItem"],
        Effect   = "Allow",
        Resource = aws_dynamodb_table.main_table.arn
      }
    ]
  })
}

# 4. Attach policy to role
resource "aws_iam_role_policy_attachment" "track_progress_lambda_attach" {
  role       = aws_iam_role.track_progress_lambda_role.name
  policy_arn = aws_iam_policy.track_progress_lambda_policy.arn
}

# 5. Lambda Function resource
resource "aws_lambda_function" "track_progress" {
  function_name    = "${var.project_name}-trackProgress"
  handler          = "main.handler"
  runtime          = "python3.9"
  role             = aws_iam_role.track_progress_lambda_role.arn
  filename         = data.archive_file.track_progress_zip.output_path
  source_code_hash = data.archive_file.track_progress_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.main_table.name
    }
  }

  tags = {
    Name = "${var.project_name}-trackProgress"
  }
}
