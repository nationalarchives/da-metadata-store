# S3 Buckets

# intg-pronom-website
resource "aws_s3_bucket" "intg_pronom_website" {
  bucket = "${terraform.workspace}-metadata-store-website"
}

resource "aws_s3_bucket_versioning" "intg_pronom_website" {
  bucket = aws_s3_bucket.intg_pronom_website.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "intg_pronom_website" {
  bucket = aws_s3_bucket.intg_pronom_website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "intg_pronom_website" {
  bucket = aws_s3_bucket.intg_pronom_website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# metadata-store bucket
resource "aws_s3_bucket" "metadata_store" {
  bucket = "metadata-store-${data.aws_caller_identity.current.account_id}-eu-west-2-an"
  tags = {
    Name = "metadata-store-bucket"
  }
}

resource "aws_s3_bucket_versioning" "metadata_store" {
  bucket = aws_s3_bucket.metadata_store.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "metadata_store" {
  bucket = aws_s3_bucket.metadata_store.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "metadata_store" {
  bucket = aws_s3_bucket.metadata_store.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# metadata-cache bucket
resource "aws_s3_bucket" "metadata_cache" {
  bucket = "metadata-cache-${data.aws_caller_identity.current.account_id}-eu-west-2-an"

  tags = {
    Name = "metadata-cache-bucket"
  }
}

resource "aws_s3_bucket_versioning" "metadata_cache" {
  bucket = aws_s3_bucket.metadata_cache.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "metadata_cache" {
  bucket = aws_s3_bucket.metadata_cache.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "metadata_cache" {
  bucket = aws_s3_bucket.metadata_cache.id

  rule {
    id     = "delete-old-cache"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 30
    }
  }
}

resource "aws_s3_bucket_public_access_block" "metadata_cache" {
  bucket = aws_s3_bucket.metadata_cache.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}