# lambda_purchaseCourse.tf

# 1. Empaquetado del código fuente
data "archive_file" "purchase_course_zip" {
  type        = "zip"
  source_dir  = "logica_recursos/lambdas/purchaseCourse/"
  output_path = ".terraform/zips/purchaseCourse.zip"
}

# 2. Rol de IAM
resource "aws_iam_role" "purchase_course_lambda_role" {
  name = "${var.project_name}-purchaseCourse-role"

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

# 3. Política de IAM (Logs, DynamoDB y permisos de red para VPC)
resource "aws_iam_policy" "purchase_course_lambda_policy" {
  name        = "${var.project_name}-purchaseCourse-policy"
  description = "IAM policy for purchaseCourse Lambda"

  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-purchaseCourse:*"
      },
      {
        Action   = ["dynamodb:PutItem"],
        Effect   = "Allow",
        Resource = aws_dynamodb_table.main_table.arn
      },
      # Permisos necesarios para que la Lambda opere dentro de una VPC
      {
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:ec2:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:network-interface/*"
      }
    ]
  })
}

# 4. Adjuntar la política al rol
resource "aws_iam_role_policy_attachment" "purchase_course_lambda_attach" {
  role       = aws_iam_role.purchase_course_lambda_role.name
  policy_arn = aws_iam_policy.purchase_course_lambda_policy.arn
}

# 5. Security Group para la Lambda
resource "aws_security_group" "lambda" {
  name        = "${var.project_name}-lambda-sg"
  description = "Security group for Lambda functions in VPC"
  vpc_id      = aws_vpc.main.id

  # Permitir todo el tráfico de salida (egress)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic."
  }

  tags = {
    Name = "${var.project_name}-lambda-sg"
  }
}

# 6. Recurso de la Función Lambda
resource "aws_lambda_function" "purchase_course" {
  function_name    = "${var.project_name}-purchaseCourse"
  handler          = "main.handler"
  runtime          = "python3.9"
  role             = aws_iam_role.purchase_course_lambda_role.arn
  filename         = data.archive_file.purchase_course_zip.output_path
  source_code_hash = data.archive_file.purchase_course_zip.output_base64sha256
  timeout          = 15

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.main_table.name
    }
  }

  # Configuración de VPC
  vpc_config {
    subnet_ids         = [for subnet in aws_subnet.private : subnet.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = {
    Name = "${var.project_name}-purchaseCourse"
  }
}
