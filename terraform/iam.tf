resource "aws_iam_role" "lambda_role" {
    name_prefix = "guradian-lambda-role"
    assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  tags = {
    tag-key = "de-data-streaming-guardian"
  }
}


resource "aws_iam_policy" "lambda_access" {
  name = "lambda-logging-sqs"
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "sqs:SetQueueAttributes",
                "sqs:GetQueueAttributes",
                "sqs:SendMessage"
            ],
            "Resource": "*"
        } 
    ]
})
}

resource "aws_iam_role_policy_attachment" "attach_lambda_access" { 
  role = aws_iam_role.lambda_role.name 
  policy_arn = aws_iam_policy.lambda_access.arn 
  }
