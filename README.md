# Healthcare Backend

A Django REST Framework API for email-based registration and JWT login, patient and doctor records, and patient-doctor assignments. Patients and their mappings are private to their creating user; authenticated users can manage and view all doctors.

## Requirements

- Python 3.10 or newer
- PostgreSQL
- pip

## Install and configure

From the repository root, create and activate a virtual environment, then install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create the PostgreSQL database (for example, in `psql`):

```sql
CREATE DATABASE healthcare_db;
```

Copy `.env.example` to `.env` and set a strong `SECRET_KEY`, PostgreSQL username and password, and the database host/port. The `.env` file is excluded from Git. The settings default to database name `healthcare_db` and local port `5432`.

## Run

```powershell
python manage.py migrate
python manage.py check
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000`. Run automated API tests with:

```powershell
python manage.py test accounts
```

Tests use the configured PostgreSQL database.

## Authentication

Register at `POST /api/auth/register/`:

```json
{
  "name": "Taylor Example",
  "email": "taylor@example.com",
  "password": "A-strong-password-42"
}
```

Log in at `POST /api/auth/login/` using `email` and `password`. The response contains `access` and `refresh` JWTs. Send the access token on protected requests:

```text
Authorization: Bearer <access-token>
```

## API endpoints

All endpoints other than registration and login require a valid access token.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/patients/` | Create a patient |
| GET | `/api/patients/` | List the authenticated user's patients |
| GET, PUT, DELETE | `/api/patients/<id>/` | Retrieve, replace, or delete an owned patient |
| POST | `/api/doctors/` | Create a doctor |
| GET | `/api/doctors/` | List all doctors |
| GET, PUT, DELETE | `/api/doctors/<id>/` | Retrieve, replace, or delete a doctor |
| POST | `/api/mappings/` | Assign a doctor to an owned patient |
| GET | `/api/mappings/` | List mappings for the authenticated user's patients |
| GET | `/api/mappings/<patient_id>/` | List doctors assigned to an owned patient |
| DELETE | `/api/mappings/<id>/` | Delete an assignment owned through its patient |

Patient request body:

```json
{
  "name": "Jordan Patient",
  "age": 35,
  "gender": "unspecified",
  "address": "1 Main Street",
  "phone": "555-0100"
}
```

Doctor request body:

```json
{
  "name": "Dr. Alex",
  "specialization": "General practice",
  "email": "doctor@example.com",
  "phone": "555-0110"
}
```

Mapping request body (use IDs returned by the patient and doctor APIs):

```json
{
  "patient_id": 1,
  "doctor_id": 1
}
```

Invalid input returns `400`, unauthenticated requests return `401`, and nonexistent or unowned records return `404`.
