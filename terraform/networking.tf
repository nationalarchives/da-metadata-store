# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/24"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "db-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "db-igw"
  }
}

# Private Subnets
resource "aws_subnet" "private_2a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.0/25"
  availability_zone = "${data.aws_region.current.name}a"

  tags = {
    Name = "private-subnet-2a"
    Type = "Private"
  }
}

resource "aws_subnet" "private_2b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.0.128/25"
  availability_zone = "${data.aws_region.current.name}b"

  tags = {
    Name = "private-subnet-2b"
    Type = "Private"
  }
}

# Route Table for Private Subnets
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "private-rt"
  }
}

resource "aws_vpc_endpoint" "api_gateway" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.execute-api"
  vpc_endpoint_type = "Interface"

  security_group_ids = [
    aws_security_group.api_proxy_endpoint.id,
  ]

  private_dns_enabled = true
}

resource "aws_security_group" "api_proxy_endpoint" {
  name = "${terraform.workspace}-api-proxy-endpoint"
}

resource "aws_security_group_rule" "api_proxy_rules" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.api_proxy_endpoint.id
  source_security_group_id = aws_security_group.metadata_store_lambda.id
  to_port                  = 443
  type                     = "ingress"
}

resource "aws_security_group" "metadata_store_lambda" {
  name = "${terraform.workspace}-metadata-store-lambda"
}

resource "aws_security_group_rule" "metadata_store_lambda_rule_ingress_endpoint" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.metadata_store_lambda.id
  to_port                  = 443
  type                     = "ingress"
  source_security_group_id = aws_security_group.lambda_endpoint.id
}

resource "aws_security_group_rule" "metadata_store_lambda_rule_ingress_db" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.metadata_store_lambda.id
  to_port                  = 443
  type                     = "ingress"
  source_security_group_id = aws_security_group.db.id
}

resource "aws_security_group_rule" "metadata_store_lambda_rule_egress_db" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.metadata_store_lambda.id
  to_port                  = 443
  type                     = "egress"
  source_security_group_id = aws_security_group.db.id
}

resource "aws_security_group_rule" "metadata_store_lambda_rule_egress_api_proxy" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.metadata_store_lambda.id
  to_port                  = 443
  type                     = "egress"
  source_security_group_id = aws_security_group.api_proxy_endpoint.id
}

resource "aws_security_group" "lambda_endpoint" {
  name = "${terraform.workspace}-lambda-endpoint"
}

resource "aws_security_group_rule" "lambda_endpoint_rule_ingress_db" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.lambda_endpoint.id
  to_port                  = 443
  type                     = "ingress"
  source_security_group_id = aws_security_group.db.id
}

resource "aws_security_group_rule" "lambda_endpoint_rule_egress_lambda" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.lambda_endpoint.id
  to_port                  = 443
  type                     = "egress"
  source_security_group_id = aws_security_group.metadata_store_lambda.id
}

resource "aws_security_group" "db" {
  name = "${terraform.workspace}-db"
}

resource "aws_security_group_rule" "db_rule_ingress_lambda" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.db.id
  to_port                  = 443
  type                     = "ingress"
  source_security_group_id = aws_security_group.metadata_store_lambda.id
}

resource "aws_security_group_rule" "db_rule_egress_lambda" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.db.id
  to_port                  = 443
  type                     = "egress"
  source_security_group_id = aws_security_group.metadata_store_lambda.id
}

resource "aws_security_group_rule" "db_rule_egress_lambda_endpoint" {
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.db.id
  to_port                  = 443
  type                     = "egress"
  source_security_group_id = aws_security_group.lambda_endpoint.id
}

resource "aws_route_table_association" "private_2a" {
  subnet_id      = aws_subnet.private_2a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_2b" {
  subnet_id      = aws_subnet.private_2b.id
  route_table_id = aws_route_table.private.id
}

# Secrets Manager for RDS Master Password
resource "aws_secretsmanager_secret" "rds_password" {
  name                    = "metadata-store/rds/master-password"
  description             = "Master password for metadata-store Aurora cluster"
  recovery_window_in_days = 7

  tags = {
    Name = "rds-master-password"
  }
}

resource "aws_secretsmanager_secret_version" "rds_password" {
  secret_id = aws_secretsmanager_secret.rds_password.id
  secret_string = jsonencode({
    username = "postgres"
    password = aws_rds_cluster.metadata_store.master_password
    engine   = "postgres"
    host     = aws_rds_cluster.metadata_store.endpoint
    port     = 5432
    dbname   = "metadata_store"
  })
}

resource "aws_db_subnet_group" "metadata_store" {
  name       = "default-vpc-${aws_vpc.main.id}"
  subnet_ids = [aws_subnet.private_2a.id, aws_subnet.private_2b.id]

  tags = {
    Name = "metadata-store-subnet-group"
  }
}

# Aurora PostgreSQL Cluster
resource "aws_rds_cluster" "metadata_store" {
  cluster_identifier              = "metadata-store"
  engine                          = "aurora-postgresql"
  engine_version                  = "17.7"
  database_name                   = "metadata_store"
  master_username                 = "postgres"
  manage_master_user_password     = true
  port                            = 5432
  db_subnet_group_name            = aws_db_subnet_group.metadata_store.name
  vpc_security_group_ids          = [aws_security_group.db.id]
  backup_retention_period         = 7
  preferred_backup_window         = "22:16-22:46"
  preferred_maintenance_window    = "wed:03:08-wed:03:38"
  skip_final_snapshot             = false
  final_snapshot_identifier       = "metadata-store-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  storage_encrypted               = false
  enabled_cloudwatch_logs_exports = ["postgresql"]
  copy_tags_to_snapshot           = true

  tags = {
    Name = "metadata-store-cluster"
  }
}

# Aurora DB Instance
resource "aws_rds_cluster_instance" "metadata_store" {
  cluster_identifier         = aws_rds_cluster.metadata_store.id
  instance_class             = "db.t4g.medium"
  engine                     = aws_rds_cluster.metadata_store.engine
  engine_version             = aws_rds_cluster.metadata_store.engine_version
  publicly_accessible        = false
  auto_minor_version_upgrade = true

  monitoring_interval = 0

  tags = {
    Name = "metadata-store-instance-1"
  }
}

# IAM Role for RDS Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "rds-monitoring-role"
  }
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Log Group for RDS
resource "aws_cloudwatch_log_group" "rds_postgresql" {
  name              = "/aws/rds/cluster/metadata-store/postgresql"
  retention_in_days = 7

  tags = {
    Name = "rds-postgresql-logs"
  }
}
