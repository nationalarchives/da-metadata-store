# RDS Lambda Role
resource "aws_iam_role" "rds_lambda_role" {
  name = "rds-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "rds-lambda-role"
  }
}

# RDS Lambda Policy - VPC Execution
resource "aws_iam_role_policy" "rds_lambda_vpc_policy" {
  name = "rds-lambda-vpc-policy"
  role = aws_iam_role.rds_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.catalogue_updates.arn
      }
    ]
  })
}

# Metadata Store Lambda Role
resource "aws_iam_role" "metadata_store_lambda_role" {
  name = "metadata-store-lambda-role"

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

  tags = {
    Name = "metadata-store-lambda-role"
  }
}

# Metadata Store Lambda Policy
resource "aws_iam_role_policy" "metadata_store_lambda_policy" {
  name = "metadata-store-lambda-policy"
  role = aws_iam_role.metadata_store_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds-db:connect"
        ]
        Resource = [
          "arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_rds_cluster.metadata_store.id}/lambda_user"
        ]
      }
    ]
  })
}

# Catalogue Updates Lambda Role
resource "aws_iam_role" "catalogue_updates_lambda_role" {
  name = "catalogue-updates-lambda-role"

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

  tags = {
    Name = "catalogue-updates-lambda-role"
  }
}

# Catalogue Updates Lambda Policy
resource "aws_iam_role_policy" "catalogue_updates_lambda_policy" {
  name = "catalogue-updates-lambda-policy"
  role = aws_iam_role.catalogue_updates_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = [
          aws_sqs_queue.metadata_update_queue.arn
        ]
      }
    ]
  })
}

# Catalogue Write Cache Lambda Role
resource "aws_iam_role" "catalogue_write_cache_lambda_role" {
  name = "catalogue-write-cache-lambda-role"

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

  tags = {
    Name = "catalogue-write-cache-lambda-role"
  }
}

# Catalogue Write Cache Lambda Policy
resource "aws_iam_role_policy" "catalogue_write_cache_lambda_policy" {
  name = "catalogue-write-cache-lambda-policy"
  role = aws_iam_role.catalogue_write_cache_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::metadata-cache-${data.aws_caller_identity.current.account_id}-eu-west-2-an/*",
          aws_sqs_queue.metadata_update_queue.arn
        ]
      }
    ]
  })
}

