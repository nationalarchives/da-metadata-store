{
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Action": [
        "ssm:GetParameter"
      ],
      "Effect": "Allow",
      "Resource": ["${client_secret_parameter_arn}", "${client_id_parameter_arn}"]
    },
    {
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "s3:PutObject"
      ],
      "Effect": "Allow",
      "Resource": [
        "${sqs_arn}",
        "${cache_bucket}/*"
      ]
    }
  ],
  "Version": "2012-10-17"
}
