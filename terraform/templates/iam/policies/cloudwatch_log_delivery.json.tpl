{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:PutLogEvents",
        "logs:CreateLogStream"
      ],
      "Resource": "${log_group_arn}",
      "Principal": {
        "Service": "delivery.logs.amazonaws.com"
      },
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:logs:${region}:${account_id}:*"
        },
        "StringEquals": {
          "aws:SourceAccount": "${account_id}"
        }
      }
    }
  ]
}
