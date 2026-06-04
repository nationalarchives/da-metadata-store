resource "aws_db_subnet_group" "metadata_store" {
  name       = "${var.app_name}-subnet-group"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${var.app_name}-subnet-group"
  }
}

resource "random_string" "snapshot_suffix" {
  length = 5
  special = false
}

resource "aws_rds_cluster" "metadata_store" {
  cluster_identifier                  = var.app_name
  engine                              = "aurora-postgresql"
  engine_version                      = "17.7"
  database_name                       = "metadata_store"
  manage_master_user_password         = true
  deletion_protection                 = true
  port                                = 5432
  db_subnet_group_name                = aws_db_subnet_group.metadata_store.name
  vpc_security_group_ids              = [module.db_security_group.security_group_id]
  backup_retention_period             = 7
  preferred_backup_window             = "22:16-22:46"
  preferred_maintenance_window        = "wed:03:08-wed:03:38"
  skip_final_snapshot                 = false
  final_snapshot_identifier           = "${var.app_name}-final-snapshot-${random_string.snapshot_suffix.result}"
  storage_encrypted                   = false
  enabled_cloudwatch_logs_exports     = ["postgresql"]
  copy_tags_to_snapshot               = true
  iam_database_authentication_enabled = true
  apply_immediately                   = true
  serverlessv2_scaling_configuration {
    max_capacity             = 1.0
    min_capacity             = 0.0
    seconds_until_auto_pause = 300
  }
  tags = {
    Name = "${var.app_name}-cluster"
  }
}

resource "aws_rds_cluster_role_association" "lambda_trigger_role" {
  db_cluster_identifier = aws_rds_cluster.metadata_store.id
  feature_name          = "Lambda"
  role_arn              = module.rds_lambda_role.role_arn
}

resource "aws_rds_cluster_instance" "metadata_store" {
  cluster_identifier         = aws_rds_cluster.metadata_store.id
  instance_class             = "db.serverless"
  engine                     = aws_rds_cluster.metadata_store.engine
  engine_version             = aws_rds_cluster.metadata_store.engine_version
  publicly_accessible        = false
  auto_minor_version_upgrade = true
  monitoring_interval        = 0
  db_subnet_group_name       = aws_db_subnet_group.metadata_store.name
  tags = {
    Name = "${var.app_name}-instance-1"
  }
}


module "rds_lambda_monitoring_role" {
  source = "git::https://github.com/nationalarchives/da-terraform-modules//iam_role"
  assume_role_policy = templatefile("${path.module}/templates/iam/roles/service_source_account_only.json.tpl", {
    account_id = data.aws_caller_identity.current.account_id,
    service    = "monitoring.rds"
  })
  name = "${var.environment}-rds-monitoring"
  policy_attachments = {
    rds_monitoring_policy = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  }
  tags = {}
}

resource "aws_cloudwatch_log_group" "rds_postgresql" {
  name              = "/aws/rds/cluster/${var.app_name}/postgresql"
  retention_in_days = 7

  tags = {
    Name = "rds-postgresql-logs"
  }
}

module "rds_lambda_role" {
  source = "git::https://github.com/nationalarchives/da-terraform-modules//iam_role"
  assume_role_policy = templatefile("${path.module}/templates/iam/roles/service_source_account_only.json.tpl", {
    account_id = data.aws_caller_identity.current.account_id,
    service    = "rds"
  })
  name = "${var.environment}-rds"
  policy_attachments = {
    rds_policy = module.rds_lambda_policy.policy_arn
  }
  tags = {}
}

module "rds_lambda_policy" {
  source        = "git::https://github.com/nationalarchives/da-terraform-modules//iam_policy"
  name          = "${var.environment}-rds"
  policy_string = templatefile("${path.module}/templates/iam/policies/rds.json.tpl", { function_arn = module.catalogue_updates_lambda.lambda_arn })
}
