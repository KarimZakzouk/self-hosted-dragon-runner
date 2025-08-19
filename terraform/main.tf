provider "aws" {
  region = "us-east-1"
}

# ----------------------------
# Variables
# ----------------------------
variable "github_token" {
  description = "GitHub Personal Access Token with repo and admin:repo_hook permissions"
  type        = string
  sensitive   = true
}

# ----------------------------
# IAM Role for Lambda
# ----------------------------
resource "aws_iam_role" "lambda_exec" {
  name = "lambda-github-runner-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic logging + EC2 control policies
resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_ec2" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

# ----------------------------
# Lambda Function
# ----------------------------
resource "aws_lambda_function" "runner_manager" {
  function_name = "github-runner-manager"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "runner_manager.lambda_handler"
  runtime       = "python3.9"

  filename         = "./lambda/runner_manager.zip"
  source_code_hash = filebase64sha256("./lambda/runner_manager.zip")

  environment {
    variables = {
      GITHUB_TOKEN = var.github_token
    }
  }
}

# ----------------------------
# API Gateway
# ----------------------------
resource "aws_apigatewayv2_api" "http_api" {
  name          = "runner-manager-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.runner_manager.arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# Route for create
resource "aws_apigatewayv2_route" "create_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /lambda/create"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Route for destroy
resource "aws_apigatewayv2_route" "destroy_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /lambda/destroy"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Lambda permission to be invoked by API Gateway
resource "aws_lambda_permission" "apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.runner_manager.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# Stage deployment
resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}
