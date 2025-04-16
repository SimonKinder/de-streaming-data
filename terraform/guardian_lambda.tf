data "archive_file" "guardian_lambda" {
  type        = "zip"
  output_path = "${path.module}/../packages/guardian_lambda.zip"
  source_dir = "${path.module}/../src"
}

resource "aws_lambda_function" "guardian_lambda_api" {
  function_name = "guardian_lambda"
  filename = data.archive_file.guardian_lambda.output_path
  source_code_hash = data.archive_file.guardian_lambda.output_base64sha256
  role = aws_iam_role.lambda_role.arn
  handler = "lambda_main.guardian_lambda"
  runtime = "python3.12"
  timeout = 5
  layers = [aws_lambda_layer_version.dependencies.arn]
  environment {
    variables = {GUARDIAN_API_KEY=var.api_key}
  }
}