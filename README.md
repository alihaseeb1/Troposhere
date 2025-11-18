To install the fastapi app:

1. Create a venv on your machine after pulling the code in using "python3 -m venv venv"
2. Then do "pip install requirements.txt"

To setup the database:
1. Run the venv
2. Write "alembic upgrade head" in the vs terminal

To access the documentation:
1. Write "localhost:8000/docs" in the browser
   
To run the server type "fastapi dev app/main.py"
Note: use localhost:8000 instead of the IP address (won't work with the google auth)

To test locally you need a token:
1. type localhost:8000/auth in the browser
2. copy the token
3. Use this in HTTP Authorization header with type bearer (can also use the likes of postman)

To run the the api locally with docker and s3 bucket online
1. fix the .env file (with the values provided)
2. run docker build -t fastapi-app . (to push to ECR from windows use this instead: docker build --platform linux/amd64 --provenance false -t troposphere-api-repo .
3. docker run -d --name fastapi-container --env-file .env -p 8000:80 fastapi-app
4. make sure to allow access in the rds for your pc

# FastAPI Project Setup & Usage Guide

This document explains how to install, run, and test the FastAPI app locally (with and without Docker), how to configure the database, and how to interact with the API.

---

## 📦 Project Installation (Local Development)

### 1. Clone the Repository

```bash
git clone <repo-url>
cd <project-directory>
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

* **Windows**:

```bash
venv\Scripts\activate
```

* **macOS/Linux**:

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup (Alembic)

1. Ensure the virtual environment is activated.
2. Run database migrations:

```bash
alembic upgrade head
```

This will create or update the database schema according to the Alembic migrations.

---

## 🚀 Running the FastAPI Server (Local)

Run the development server using:

```bash
fastapi dev app/main.py
```

### Access the API documentation:

Open your browser and go to:

```
http://localhost:8000/docs
```

> **Note:** Use `localhost:8000` instead of your local IP address. Google OAuth will not work with the IP address.

---

## 🔐 Authentication (Getting a Token Locally)

To test endpoints that require authentication:

1. Go to:

```
http://localhost:8000/auth?redirect={FRONTEND_URL}
```

2. Copy the generated token.
3. Add it to your API client (browser extensions, Postman, Thunder Client, etc.) under:

   * **Authorization Type:** Bearer Token
   * **Token:** *paste your token here*

---

## 🐳 Running Locally Using Docker

### 1. Update your `.env`

Fill in the necessary environment values provided to you.

### 2. Build the Docker Image

**Standard build:**

You can also use docker-compose file, for postgres instance in the container

```bash
docker build -t fastapi-app .
```

**If pushing to ECR from Windows:**

```bash
docker build --platform linux/amd64 --provenance false -t troposphere-api-repo .
```

### 3. Run the Docker Container

```bash
docker run -d --name fastapi-container --env-file .env -p 8000:80 fastapi-app
```

### 4. Allow Access to RDS

Ensure your PC's IP address is allowed inbound access in the RDS security group.

---

## 📘 Additional Notes About the FastAPI API

### ▶ Project Structure (Simplified)

```
app/
 ├── main.py
 ├── auth/
      ├── google.py
      ├── oauth.py
 ├── routers/
 │    ├── login.py
 │    ├── users.py
 │    ├── clubs.py
 │    ├── items.py
 │    ├── borrow.py
 │    ├── returns.py
 ├── database.py
 ├── models.py
 ├── schemas.py
 ├── config.py
 └── logger.py

```

### 🔧 Key Features

* Token-based authentication (Google Oauth2.0)
* SessionMiddleware support
* Modular routing using FastAPI Routers
* CORS support (configurable in `main.py`)
* SQLAlchemy ORM with migrations using Alembic
* Centralized logging configuration

### 🔥 Development Tips

* Any changes to Pydantic settings or `.env` require restarting the server.
* For external clients (Postman, frontend, etc.) ensure CORS origins are configured.
* Logs are handled through `logger.py` — adjust logging level there.

---

## 🧪 Testing

You can test endpoints using:

* Browser (for simple GET requests)
* cURL
* Postman
* Thunder Client
* VS Code REST Client

Example authenticated request using cURL:

```bash
curl -H "Authorization: Bearer <your_token>" http://localhost:8000/items
```

---

## ☁️ Using AWS (For Deployment)

* Ensure your ECR image platform matches your ECS cluster (use `--platform linux/amd64`).
* RDS must allow access from ECS or your local machine when testing.
* S3 buckets need proper IAM permissions for your app.

---
