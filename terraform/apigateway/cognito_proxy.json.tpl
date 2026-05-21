{
  "swagger" : "2.0",
  "info" : {
    "description" : "Proxies to the cognito endpoints",
    "version" : "2026-05-20T10:30:36Z",
    "title" : "cognito-proxy"
  },
  "basePath" : "/${environment}",
  "schemes" : [ "https" ],
  "paths" : {
    "/oauth2/{path+}" : {
      "x-amazon-apigateway-any-method" : {
        "produces" : [ "application/json" ],
        "parameters" : [ {
          "name" : "path",
          "in" : "path",
          "required" : true,
          "type" : "string"
        } ],
        "responses" : {
          "200" : {
            "description" : "200 response",
            "schema" : {
              "$ref" : "#/definitions/Empty"
            }
          }
        },
        "x-amazon-apigateway-integration" : {
          "uri" : "https://metadata-store.auth.${region}.amazoncognito.com/oauth2/{path}",
          "httpMethod" : "ANY",
          "responses" : {
            "default" : {
              "statusCode" : "200"
            }
          },
          "requestParameters" : {
            "integration.request.path.path" : "method.request.path.path"
          },
          "passthroughBehavior" : "when_no_match",
          "cacheNamespace" : "efpvax",
          "responseTransferMode" : "BUFFERED",
          "cacheKeyParameters" : [ "method.request.path.path" ],
          "type" : "http_proxy"
        }
      }
    }
  },
  "definitions" : {
    "Empty" : {
      "type" : "object",
      "title" : "Empty Schema"
    }
  },
  "x-amazon-apigateway-security-policy" : "SecurityPolicy_TLS13_1_3_2025_09",
  "x-amazon-apigateway-policy" : {
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
  },
  "x-amazon-apigateway-endpoint-access-mode" : "BASIC"
}