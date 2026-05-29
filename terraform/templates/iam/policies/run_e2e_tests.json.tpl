{
  "Statement": [
    {
      "Action": [
        "ssm:GetParameter"
      ],
      "Effect": "Allow",
      "Resource": ["${password_parameter_arn}", "${client_secret_parameter_arn}", "${client_id_parameter_arn}"]
    }
  ],
  "Version": "2012-10-17"
}
