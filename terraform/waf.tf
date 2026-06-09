locals {
  web_acls = {
    cognito = {
      region = data.aws_region.current.region
      name   = "${var.environment}-wafwebacl-cognito"
      scope  = "REGIONAL"
    }
    cloudfront = {
      region = local.us_east_1
      name   = "${var.environment}-wafwebacl-metadata-store-website"
      scope  = "CLOUDFRONT"
    }
  }
}

resource "aws_wafv2_web_acl" "web_acl" {
  for_each = local.web_acls

  region = each.value.region
  name   = each.value.name
  scope  = each.value.scope

  default_action {
    allow {}
  }

  data_protection_config {
    data_protection {
      action = "HASH"
      field {
        field_type = "BODY"
      }
    }
  }

  rule {
    name     = "SizeLessThan8k"
    priority = 4
    action {
      block {}
    }
    statement {
      size_constraint_statement {
        comparison_operator = "GT"
        size                = 8192
        field_to_match {
          body {}
        }
        text_transformation {
          priority = 0
          type     = "NONE"
        }
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SizeLessThan8k"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AntiDDOS"
    priority = 2

    override_action {
      count {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAntiDDoSRuleSet"
        vendor_name = "AWS"

        managed_rule_group_configs {
          aws_managed_rules_anti_ddos_rule_set {
            client_side_action_config {
              challenge {
                usage_of_action = "DISABLED"
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AntiDDOS"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "KnownBadInputs"
    priority = 3
    override_action {
      count {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AntiDDOS"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 10000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "WAFRules"
    sampled_requests_enabled   = true
  }
}

resource "aws_cloudwatch_log_group" "waf_logs" {
  for_each = local.web_acls
  region   = each.value.region
  name     = "aws-waf-logs-${var.environment}-${each.key}"
}

resource "aws_wafv2_web_acl_logging_configuration" "waf_logging_aws_managed_rules" {
  for_each                = local.web_acls
  region                  = each.value.region
  log_destination_configs = [aws_cloudwatch_log_group.waf_logs[each.key].arn]
  resource_arn            = aws_wafv2_web_acl.web_acl[each.key].arn
}

resource "aws_cloudwatch_log_resource_policy" "cloudwatch_log_policy" {
  for_each = local.web_acls
  region   = each.value.region
  policy_document = templatefile("${path.module}/templates/iam/policies/cloudwatch_log_delivery.json.tpl", {
    account_id    = data.aws_caller_identity.current.account_id
    region        = each.value.region
    log_group_arn = aws_cloudwatch_log_group.waf_logs[each.key].arn
  })
  policy_name = "${var.environment}-cloudwatch-log-policy"
}
