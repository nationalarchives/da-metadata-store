# Metadata Store

A Django application for managing and querying metadata records. Includes comprehensive test coverage, OAuth2
authentication with Cognito, JWT-based API access, and production-ready AWS infrastructure-as-code.

## What it does

- Serves a web UI to search, browse, and manage metadata records
- Exposes `/api/records/<reference>` REST endpoint for API access
- Uses AWS Cognito for authentication (with optional Entra SSO federation)
- JWT bearer token validation for API requests
- Bulk import functionality for metadata records
- Full-text search capability
- User audit logging
- Stores records in PostgreSQL with automatic schema management

## Tech stack

- **Backend**: Python 3.11+ & Django 4.2+
- **Database**: PostgreSQL
- **Authentication**: AWS Cognito with federated identity support
- **Token Validation**: PyJWT for bearer token authentication
- **Infrastructure**: Terraform for complete AWS deployment (Lambda, RDS, API Gateway, CloudFront, S3)
- **Testing**: 107 comprehensive test cases covering models, views, and utilities

## Local setup

### Prerequisites

- Python 3.11+
- PostgreSQL 12+ or SQLite (local dev only)
- pip and virtualenv

### Steps

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** (see example below):
   ```env
   ISSUER=https://test.auth.example.com                                      <aws:dri> <region:eu-west-2>
   export COGNITO_CLIENT_ID=test
   export COGNITO_SECRET=test
   export APP_BASE_URL=http://localhost:8080/test
   export PROXY_URL=https://proxy.example.com
   ```

4. **Apply migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Run the development server**:
   ```bash
   python manage.py runserver
   ```
   Access at `http://localhost:8000`

## Key routes

| Route               | Method   | Purpose                     | Auth        |
|---------------------|----------|-----------------------------|-------------|
| `/`                 | GET      | Search/browse records       | Cognito     |
| `/results`          | GET      | Search results              | Cognito     |
| `/records/<id>`     | GET      | Record detail page          | Cognito     |
| `/api/records/<id>` | GET      | JSON API for record details | JWT Bearer  |

## Environment variables

| Variable              | Required | Notes                                                                                      |
|-----------------------|----------|--------------------------------------------------------------------------------------------|
| `SECRET_KEY`          | Yes      | Django secret key (keep secret in production)                                              |
| `DEBUG`               | No       | `True` for local development (set to `False` in production)                                |
| `APP_BASE_URL`        | Yes      | Base URL for the application (e.g., `http://localhost:8000`)                               |
| `DATABASE_URL`        | No       | Database connection string (defaults to SQLite)                                            |
| `ISSUER`              | For Auth | Cognito token issuer (e.g., `https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_xxxxx`) |
| `COGNITO_CLIENT_ID`   | For Auth | Cognito App Client ID                                                                      |
| `COGNITO_SECRET`      | For Auth | Cognito App Client Secret (if using credential flow)                                       |
| `ALLOWED_HOSTS`       | No       | Comma-separated list of allowed host names                                                 |
| `SECURE_SSL_REDIRECT` | No       | Set to `True` in production to enforce HTTPS                                               |

## Database models

The application includes 16 Django models for comprehensive metadata management:

**Core Models:**

- `CopyrightTitle` - Rights and copyright information
- `AssetTitle` - Asset name/title catalog
- `CatalogRecord` - Main metadata records (supports arrays for relationships)
- `RecordOutput` - Formatted/derived output variants
- `Dimension` - Size/measurement metadata

**Supporting Models:**

- `ImportRecord` - Track bulk import jobs and status
- `RecordStatus` - Record workflow state tracking
- `Relationship` - Links between catalog records
- `RelatedField` - Flexible relationship attributes

**Schema details** in `database/init.sql` includes:

- Automatic `updated_at` timestamps with triggers
- Full-text search indexes using PostgreSQL GIN
- Foreign key relationships with cascading deletes
- User audit logging with IP and user agent tracking

## Tests

### Running tests

```bash
# Set environment variables for OAuth
export ISSUER="https://your-issuer.example.com"
export COGNITO_CLIENT_ID="your-client-id"
export COGNITO_SECRET="your-secret"
export APP_BASE_URL="http://localhost:8000"
export PROXY_URL="https://your-proxy.example.com"
export DATABASE_URL=postgres://postgres@localhost:5432/catalogue

# Run tests
python manage.py test store.tests
python manage.py test store.tests.test_models -v 2
python manage.py test store.tests --keepdb  # Keep test database between runs
```

### Local Deployment

For local testing with Lambda and API Gateway simulation:

```bash
pip install -r requirements.txt
python manage.py runserver
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
