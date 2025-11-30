# Multi-Tenant FastAPI with AWS Cognito

A reference implementation for building secure, multi-tenant SaaS applications using AWS Cognito Custom Attributes and FastAPI.

This project demonstrates:
- **Multi-Tenancy:** Using `custom:tenant_id` to isolate data.
- **RBAC:** Using Cognito Groups (`ADMIN`, `EDITOR`, `VIEWER`) for permission control.
- **FastAPI Integration:** Clean dependency injection for auth and tenant context.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.13+
- Docker (for local Cognito simulation)
- `uv` (for dependency management)

### 2. Install Dependencies
```bash
uv sync
```

### 3. Start Local Infrastructure
Spin up the local Cognito emulator:
```bash
docker-compose up -d
```

Run the setup script to provision the User Pool, Groups, and a Demo User:
```bash
uv run python setup_local_env.py
```
> **Note:** Copy the output from this script (User Pool ID, Client ID, etc.) into a new `.env` file in the project root.

### 4. Run the Application
```bash
uvicorn main:app --host 127.0.0.1 --port 8080 --reload
```

## 🧪 How to Test

The app includes a "Demo User" created by the setup script:
- **Username:** `admin@example.com`
- **Password:** `P@ssword123`
- **Role:** `ADMIN`
- **Tenant:** `tenant-123`

### Step 1: Get a Token
Use the built-in Swagger UI or `curl` to login:
**POST** `http://127.0.0.1:8080/api/v1/auth/token`
```json
{
  "username": "admin@example.com",
  "password": "P@ssword123"
}
```
*Copy the `id_token` from the response.*

### Step 2: Create a Note
**POST** `http://127.0.0.1:8080/api/v1/notes`
*Header:* `Authorization: Bearer <YOUR_ID_TOKEN>`
```json
{
  "content": "My first multi-tenant note!"
}
```

### Step 3: Verify Isolation
Creating a user in a *different* tenant (via the internal API) and logging in as them will show an empty list of notes, proving the isolation works!

## 📂 Project Structure

- `api_methods/`: Endpoints for Notes, Auth, and Tenant management.
- `cognito.py`: Core logic for JWT validation and claim extraction.
- `dtos/`: Pydantic models for request/response validation.