{
  "Statement": [
    {
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Effect": "Allow",
      "Resource": [
        "${function_arn}"
      ]
    }
  ],
  "Version": "2012-10-17"
}
