# Metadata Store

A Django application for searching and viewing metadata records, with SAML SSO for browser access and an IAM-authenticated API endpoint for machine access.

## What it does

- Serves a web UI to search records and view record details.
- Exposes `GET /api/records/<reference>` for API access.
- Uses SAML 2.0 endpoints for login/logout and metadata exchange.
- Stores records in `Record` and tracks API callers in `APIUser`.

## Tech stack

- Python + Django 4.2
- `python3-saml` (OneLogin toolkit)
- PostgreSQL (or SQLite locally via `DATABASE_URL`)
- AWS deployment support (Lambda/API Gateway/CloudFront/Terraform)

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (example):
   ```env
   SECRET_KEY=change-me
   DEBUG=True
   APP_BASE_URL=http://localhost:8000
   DATABASE_URL=sqlite:///db.sqlite3

   # SAML IdP settings
   SAML_IDP_ENTITY_ID=
   SAML_IDP_SSO_URL=
   SAML_IDP_SLO_URL=
   SAML_IDP_CERT=
   ```
4. Apply migrations:
   ```bash
   python manage.py migrate
   ```
5. Run the app:
   ```bash
   python manage.py runserver
   ```

## Key routes

| Route | Purpose |
|---|---|
| `/` | Search page (login required) |
| `/results?q=<query>` | Search results (login required) |
| `/records/<reference>` | Record detail page (login required) |
| `/api/records/<reference>` | JSON API for a record (expects API Gateway IAM context) |
| `/saml/login` | Start SAML login |
| `/saml/acs` | SAML assertion consumer service |
| `/saml/logout` | Start SAML logout |
| `/saml/sls` | SAML single logout service |
| `/saml/metadata` | Service provider metadata XML |

## Environment variables

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | `True` for local development |
| `APP_BASE_URL` | Yes | Base URL used in SAML settings |
| `DATABASE_URL` | No | Defaults to local SQLite |
| `SAML_IDP_ENTITY_ID` | For SAML | IdP entity ID |
| `SAML_IDP_SSO_URL` | For SAML | IdP SSO endpoint |
| `SAML_IDP_SLO_URL` | For SAML | IdP SLO endpoint |
| `SAML_IDP_CERT` | For SAML | IdP x509 certificate |
| `USE_IAM_AUTH` | No | `true` to use AWS RDS IAM DB auth |
| `AWS_REGION` | With IAM auth | AWS region for token generation |

## Database models

- `Record`: `reference`, `name`, `description`, `data` (JSON)
- `APIUser`: IAM `user_id`, `user_arn`, `first_seen`, `last_seen`

## Tests

Run all tests with:

```bash
python manage.py test
```

## Deployment notes

- `zappa_settings.json` contains a Zappa environment (`dev`) for packaging/deploy.
- `terraform/` provisions Lambda, API Gateway HTTP API, S3, and CloudFront.
- Terraform reads sensitive settings from AWS SSM Parameter Store (`/secret-key`, `/base-url`, `/idp-*`).
