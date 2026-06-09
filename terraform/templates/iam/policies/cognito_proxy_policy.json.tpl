{
  "Version" : "2012-10-17",
  "Statement" : [ {
    "Effect" : "Deny",
    "Principal" : "*",
    "Action" : "execute-api:Invoke",
    "Resource" : "arn:aws:execute-api:${region}:${account_id}:*/*",
    "Condition" : {
      "StringNotEquals" : {
        "aws:SourceVpce" : "${api_gateway_vpc_endpoint}"
      }
    }
  }, {
    "Effect" : "Allow",
    "Principal" : "*",
    "Action" : "execute-api:Invoke",
    "Resource" : "arn:aws:execute-api:${region}:${account_id}:*/*"
  } ]
}