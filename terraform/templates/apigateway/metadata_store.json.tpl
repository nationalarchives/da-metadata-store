{
  "openapi" : "3.0.1",
  "info" : {
    "title" : "${title}",
    "version" : "2026-05-29 08:40:34UTC"
  },
  "paths" : {
    "/{path+}" : {
      "get" : {
        "responses" : {
          "default" : {
            "description" : "Default response for GET /{path+}"
          }
        },
        "x-amazon-apigateway-integration" : {
          "payloadFormatVersion" : "2.0",
          "type" : "aws_proxy",
          "httpMethod" : "POST",
          "uri" : "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${region}:${account_id}:function:${lambda_name}/invocations",
          "connectionType" : "INTERNET"
        }
      },
      "post" : {
        "responses" : {
          "default" : {
            "description" : "Default response for POST /{path+}"
          }
        },
        "x-amazon-apigateway-integration" : {
          "payloadFormatVersion" : "2.0",
          "type" : "aws_proxy",
          "httpMethod" : "POST",
          "uri" : "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/arn:aws:lambda:${region}:${account_id}:function:${lambda_name}/invocations",
          "connectionType" : "INTERNET"
        }
      },
      "parameters" : [ {
        "name" : "path+",
        "in" : "path",
        "description" : "Generated path parameter for path+",
        "required" : true,
        "schema" : {
          "type" : "string"
        }
      } ]
    }
  },
  "components" : {
    "securitySchemes" : {
      "cognito-jwt" : {
        "type" : "oauth2",
        "flows" : { },
        "x-amazon-apigateway-authorizer" : {
          "identitySource" : "$request.header.Authorization",
          "jwtConfiguration" : {
            "audience" : [ "default-m2m-resource-server-5apqnq/read" ],
            "issuer" : "https://cognito-idp.${region}.amazonaws.com/${cognito_id}"
          },
          "type" : "jwt"
        }
      }
    }
  },
  "x-amazon-apigateway-importexport-version" : "1.0"
}