# Metadata Store

A Django application for managing and querying metadata records. Includes comprehensive test coverage, OAuth2
authentication with Cognito, JWT-based API access, and production-ready AWS infrastructure-as-code.

## What it does

- Serves a web UI to search, browse, and manage metadata records
- Exposes `/api/records/<reference>` REST endpoint for API access
- Uses AWS Cognito for authentication (with optional Entra SSO federation)
- JWT bearer token validation for API requests
- User audit logging
- Stores records in PostgreSQL with automatic schema management

## Tech stack

- **Backend**: Python 3.12+ & Django 6+
- **Database**: PostgreSQL
- **Authentication**: AWS Cognito with federated identity support
- **Token Validation**: PyJWT for bearer token authentication
- **Infrastructure**: Terraform for complete AWS deployment (Lambda, RDS, API Gateway, CloudFront, S3)
- **Testing**: 43 test cases covering models, views, and utilities
- **UI Testing**: Cypress tests testing the webapp routes and API endpoints.

## Local setup

### Prerequisites

- Python 3.12+
- PostgreSQL 12+
- poetry

### Steps

1. **Create and activate a virtual environment and install depdendencies**:
   ```bash
   poetry install
   ```
   
2. **Export environment variables**:
   ```env
   ISSUER=https://test.auth.example.com
   export CLIENT_ID=test
   export CLIENT_SECRET=test
   export APP_BASE_URL=http://localhost:8080/test
   export PROXY_URL=https://proxy.example.com
   ```
   
3. **Update hosts file**:
   ```bash
   echo "127.0.0.1 oidc" | sudo tee -a /etc/hosts
   ```

4. **Apply migrations**:
   ```bash
   poetry run python manage.py migrate
   poetry run python manage.py loaddata change_reason 
   ```

5. **Run the development server**:
   ```bash
   poetry run python manage.py runserver
   ```
   Access at `http://localhost:8000`

## Key routes

| Route               | Method | Purpose                     | Auth       |
|---------------------|--------|-----------------------------|------------|
| `/`                 | GET    | Search/browse records       | Cognito    |
| `/results`          | GET    | Search results              | Cognito    |
| `/records/<id>`     | GET    | Record detail page          | Cognito    |
| `/api/records/<id>` | GET    | JSON API for record details | JWT Bearer |

## Environment variables

| Variable              | Required | Notes                                                                                      |
|-----------------------|----------|--------------------------------------------------------------------------------------------|
| `SECRET_KEY`          | Yes      | Django secret key (keep secret in production)                                              |
| `DEBUG`               | No       | `True` for local development (set to `False` in production)                                |
| `APP_BASE_URL`        | Yes      | Base URL for the application (e.g., `http://localhost:8000`)                               |
| `DATABASE_URL`        | No       | Database connection string (defaults to SQLite)                                            |
| `ISSUER`              | For Auth | Cognito token issuer (e.g., `https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_xxxxx`) |
| `CLIENT_ID`           | For Auth | Cognito App Client ID                                                                      |
| `CLIENT_SECRET`       | For Auth | Cognito App Client Secret (if using credential flow)                                       |
| `ALLOWED_HOSTS`       | No       | Comma-separated list of allowed host names                                                 |
| `SECURE_SSL_REDIRECT` | No       | Set to `True` in production to enforce HTTPS                                               |

## Database setup

### Initial database creation

For new PostgreSQL deployments in AWS, you need to set up the lambda_user

```bash
# Connect as root user to PostgreSQL
CREATE DATABASE catalogue;

# Connect as root user to catalogue
CREATE USER lambda_user; 
GRANT rds_iam TO lambda_user;
GRANT USAGE, CREATE ON SCHEMA public TO lambda_user;
```

This script:

- Creates the `catalogue` database
- Creates a `lambda_user` with appropriate permissions and IAM authentication.

### Schema management

The Django ORM handles schema creation and migrations:

```bash
# Create initial migrations
poetry run python manage.py makemigrations

# Apply all pending migrations
poetry run python manage.py migrate

# Apply fixtures
poetry run python manage.py loaddata change_reason
```

## Database models

The application includes 4 Django models for comprehensive metadata management:

**Core Models:**

- `Metadata` - Main metadata records with JSON-based flexible schema, including catalogue reference, type, mastery status, and timestamps
- `RelationshipTypes` - Defines types of relationships between metadata records (e.g., parent-child, related-to)
- `Relationships` - Links between metadata records with relationship type and attributes
- `ChangeReason` - Predefined reasons for metadata changes (closures, corrections, FOI reviews, etc.)

## Infrastructure (AWS/Terraform)

The application is deployed on AWS using Terraform for infrastructure-as-code. The complete infrastructure is defined in
the `terraform/` directory.

### Infrastructure components

- **Lambda**: Serverless compute for the Django application
- **RDS (PostgreSQL)**: Managed relational database
- **API Gateway**: REST API endpoint routing
- **CloudFront**: CDN for static assets and content distribution
- **S3**: Static asset storage and Lambda code packages
- **Cognito**: User authentication and identity management
- **SQS**: Asynchronous task queue (optional)
- **VPC/Networking**: Secure networking setup

### Configuration

Terraform uses environment-specific variable files:

- `intg.auto.tfvars` - Integration environment
- `prod.auto.tfvars` - Production environment

Key variables in `variables.tf`:

- `app_name` - Application name (used for resource naming)
- `environment` - Deployment environment (intg/prod)
- `use_entra_for_sso` - Enable Microsoft Entra ID federation (bool)
- `saml_tenant` - SAML tenant for SSO federation
- `app_secret` - Django SECRET_KEY

### Backend state management

Terraform state is stored in an S3 bucket with encryption and locking:

```
s3://metadata-store-terraform-state/terraform.state
```

### Deploying infrastructure

```bash
cd terraform/

# Initialise Terraform
terraform init

# Select correct workspace
terraform workspace select intg

# Plan changes for a specific environment
terraform plan -var-file=intg.auto.tfvars

# Apply infrastructure changes
terraform apply -var-file=intg.auto.tfvars

# Destroy infrastructure (use with caution)
terraform destroy -var-file=intg.auto.tfvars
```

### Lambda deployment

The application code is packaged and deployed to Lambda with migrations automatically run on deployment:

- `metadata-store.zip` - Application code package
- `migrate.zip` - Database migration job

## Tests

### Running tests

```bash
# Run tests
python manage.py test store.tests
python manage.py test store.tests.test_models -v 2
python manage.py test store.tests --keepdb  # Keep test database between runs
```

### Running cypress tests
```bash
export USER=user1 
export PASSWORD=password 
export TOKEN_ENDPOINT=http://oidc/token
export CLIENT_ID=demo-client
export CLIENT_SECRET=demo-secret
export CYPRESS_BASE_URL=http://localhost:8000/
cd tests/e2e 
npm t
```

## Development

### Adding new models

1. Create model in `store/models.py`
2. Create migration: `python manage.py makemigrations`
3. Apply migration: `python manage.py migrate`
4. Add test coverage in `store/tests/test_models.py`
5. Update `database/init.sql` with schema changes

### Adding API endpoints

1. Create view in `store/views.py`
2. Add URL route in `store/urls.py`
3. Add test case in `store/tests/test_views.py`
4. Document in API section above
