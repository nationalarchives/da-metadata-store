locals {
  nacl_inbound_from_subnet_https = [for idx, cidr in module.vpc.private_cidr_blocks : {
    rule_no    = 100 * (idx + 2)
    cidr_block = cidr
    action     = "allow"
    from_port  = 443
    to_port    = 443
    egress     = false
  }]
  nacl_outbound_to_subnet_ephemeral = [for idx, cidr in module.vpc.private_cidr_blocks : {
    rule_no    = 100 * (idx + 2)
    cidr_block = cidr
    action     = "allow"
    from_port  = 1024
    to_port    = 65535
    egress     = true
  }]
}

module "vpc" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//vpc?ref=changes-for-metadata-store"
  environment = var.environment
  interface_endpoints = {
    execute_api = {
      name = "com.amazonaws.${data.aws_region.current.region}.execute-api"
      policy = templatefile("${path.module}/templates/vpc/default_endpoint_policy.json.tpl", {
        service_name = "execute-api"
        org_id       = data.aws_organizations_organization.org.id
      })
      security_group_ids = [module.execute_api_endpoint_security_group.security_group_id]
      enable_private_dns = true
    }
    lambda = {
      name = "com.amazonaws.${data.aws_region.current.region}.lambda"
      policy = templatefile("${path.module}/templates/vpc/default_endpoint_policy.json.tpl", {
        service_name = "lambda"
        org_id       = data.aws_organizations_organization.org.id
      })
      security_group_ids = [module.lambda_endpoint_security_group.security_group_id]
      enable_private_dns = true
    }
    cognito_idp = {
      name = "com.amazonaws.${data.aws_region.current.region}.cognito-idp"
      policy = templatefile("${path.module}/templates/vpc/default_endpoint_policy.json.tpl", {
        service_name = "cognito-idp"
        org_id       = data.aws_organizations_organization.org.id
      })
      security_group_ids = [module.cognito_idp_endpoint_security_group.security_group_id]
      enable_private_dns = true
    }
    sqs = {
      name = "com.amazonaws.${data.aws_region.current.region}.sqs"
      policy = templatefile("${path.module}/templates/vpc/default_endpoint_policy.json.tpl", {
        service_name = "sqs"
        org_id       = data.aws_organizations_organization.org.id
      })
      security_group_ids = [module.sqs_endpoint_security_group.security_group_id]
      enable_private_dns = true
    }
    ssm = {
      name = "com.amazonaws.${data.aws_region.current.region}.ssm"
      policy = templatefile("${path.module}/templates/vpc/default_endpoint_policy.json.tpl", {
        service_name = "ssm"
        org_id       = data.aws_organizations_organization.org.id
      })
      security_group_ids = [module.ssm_endpoint_security_group.security_group_id]
      enable_private_dns = true
    }
  }
  private_nacl_rules = concat([
    { rule_no = 100, cidr_block = "0.0.0.0/0", action = "allow", from_port = 443, to_port = 443, egress = true },
    { rule_no = 100, cidr_block = "0.0.0.0/0", action = "allow", from_port = 1024, to_port = 65535, egress = false },
  ], local.nacl_inbound_from_subnet_https, local.nacl_outbound_to_subnet_ephemeral)
  use_nat_gateway                = false
  use_nat_instance               = false
  create_public_subnet           = false
  create_elastic_ips             = false
  vpc_name                       = "${var.environment}-main"
  create_dynamo_gateway_endpoint = false
  create_s3_gateway_endpoint     = true
  az_count                       = 2
}


module "lambda_endpoint_security_group" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//security_group?ref=main"
  common_tags = {}
  description = "A security group for lambda vpc endpoints"
  name        = "${var.environment}-lambda-endpoint"
  vpc_id      = module.vpc.vpc_id
  rules = {
    ingress = [
      {
        port              = 443,
        description       = "Allow the DB trigger to access the catalogue-updates function through the endpoint",
        security_group_id = module.db_security_group.security_group_id
      }
    ],
    egress = [
      {
        port              = 443
        description       = "Allow traffic to the catalogue updates lambda"
        security_group_id = module.catalogue_updates_lambda_security_group.security_group_id
      }
    ]
  }
}

module "metadata_store_lambda_security_group" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//security_group?ref=main"
  common_tags = {}
  description = "A security group for the django lambda"
  name        = "${var.environment}-metadata-store-lambda"
  vpc_id      = module.vpc.vpc_id
  rules = {
    ingress = [
      {
        port              = 443,
        description       = "Allow inbound from the VPC endpoint",
        security_group_id = module.lambda_endpoint_security_group.security_group_id
      }
    ]
    egress = [
      {
        port              = 5432,
        description       = "Allow outbound to the database",
        security_group_id = module.db_security_group.security_group_id
      },
      {
        port              = 443,
        description       = "Allow outbound to the cognito idp endpoint",
        security_group_id = module.cognito_idp_endpoint_security_group.security_group_id
      },
      {
        port              = 443,
        description       = "Allow outbound to the cognito proxy API",
        security_group_id = module.execute_api_endpoint_security_group.security_group_id
      },
      {
        port              = 443
        description       = "Allow outbound to the ssm endpoint to get secrets",
        security_group_id = module.ssm_endpoint_security_group.security_group_id
      }
    ]
  }
}

module "catalogue_updates_lambda_security_group" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//security_group?ref=main"
  common_tags = {}
  description = "A security group for the django lambda"
  name        = "${var.environment}-catalogue-updates-lambda"
  vpc_id      = module.vpc.vpc_id
  rules = {
    ingress = [
      {
        port              = 443,
        description       = "Allow DB trigger to call the lambda",
        security_group_id = module.db_security_group.security_group_id
      }
    ],
    egress = [
      {
        port              = 443
        description       = "Allow the lambda to send to sqs"
        security_group_id = module.sqs_endpoint_security_group.security_group_id
      }
    ]
  }
}

module "execute_api_endpoint_security_group" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//security_group?ref=main"
  common_tags = {}
  description = "A security group for execute-api vpc endpoints"
  name        = "${var.environment}-execute-api-endpoint"
  vpc_id      = module.vpc.vpc_id
  rules = {
    ingress = [
      {
        port              = 443,
        description       = "Allow access to the cognito authentication urls from lambda",
        security_group_id = module.metadata_store_lambda_security_group.security_group_id
      }
    ]
  }
}

module "cognito_idp_endpoint_security_group" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//security_group?ref=main"
  common_tags = {}
  description = "A security group for Cognito IDP vpc endpoints"
  name        = "${var.environment}-cognito-idp-endpoint"
  vpc_id      = module.vpc.vpc_id
  rules = {
    ingress = [
      {
        port              = 443,
        description       = "Allow access to cognito idp urls from lambda",
        security_group_id = module.metadata_store_lambda_security_group.security_group_id
      }
    ]
  }
}

module "sqs_endpoint_security_group" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//security_group?ref=main"
  common_tags = {}
  description = "A security group for SQS vpc endpoints"
  name        = "${var.environment}-sqs-endpoint"
  vpc_id      = module.vpc.vpc_id
  rules = {
    ingress = [
      {
        port              = 443,
        description       = "Allow catalogue-updates to call sqs",
        security_group_id = module.catalogue_updates_lambda_security_group.security_group_id
      }
    ]
  }
}

module "ssm_endpoint_security_group" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//security_group?ref=main"
  common_tags = {}
  description = "A security group for SSM vpc endpoints"
  name        = "${var.environment}-ssm-endpoint"
  vpc_id      = module.vpc.vpc_id
  rules = {
    ingress = [
      {
        port              = 443,
        description       = "Allow metadata-store to call ssm to get secrets",
        security_group_id = module.metadata_store_lambda_security_group.security_group_id
      }
    ]
  }
}

module "db_security_group" {
  source      = "git::https://github.com/nationalarchives/da-terraform-modules//security_group?ref=main"
  common_tags = {}
  description = "A security group for SQS vpc endpoints"
  name        = "${var.environment}-db"
  vpc_id      = module.vpc.vpc_id
  rules = {
    ingress = [
      {
        port              = 5432,
        description       = "Allow inbound access from the webapp lambda",
        security_group_id = module.metadata_store_lambda_security_group.security_group_id
      }
    ]
    egress = [
      {
        port              = 443
        description       = "Allow DB trigger to call catalogue-updates lambda"
        security_group_id = module.catalogue_updates_lambda_security_group.security_group_id
      },
      {
        port              = 443
        description       = "Allow DB trigger to use the lambda vpc endpoint"
        security_group_id = module.lambda_endpoint_security_group.security_group_id
      }
    ]
  }
}
