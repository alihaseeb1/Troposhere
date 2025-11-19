<img width="1201" height="838" alt="AWS_Architecture Diagram" src="https://github.com/user-attachments/assets/20597016-840b-4885-8a16-f038a1ac5b51" />
<img width="719" height="820" alt="image" src="https://github.com/user-attachments/assets/ae8dceeb-3e6f-467c-a2ba-b90e239dc9b0" />


# Troposphere API | FastAPI Project Setup & Usage Guide

This document explains how to install, run, and test the FastAPI app locally (with and without Docker), how to configure the database, and how to interact with the API.

---

📘 Notes About the FastAPI API
📝 API Description

The FastAPI application provides a complete backend system designed for authentication, inventory/asset management, and administrative operations. It follows a modular architecture using FastAPI Routers to keep each domain separated and maintainable.

🔑 Core Capabilities

User Authentication & Sessions: Secure login flow with token-based authentication. Tokens can be used to authorize both browser-based and API client requests.

Role-Based Access (if enabled): Certain endpoints may only be accessed by authenticated or privileged users (Club Roles - Admin, Moderator and Member, Global Roles - SuperUser and User).

Inventory / Clubs Management: Endpoints for creating, viewing, updating, and managing clubs, items, and related entities.

Borrow & Return Workflow: Full borrowing system where users can request items, borrow them, and return them. Includes status tracking and validations.

User Management: Admin-level endpoints to create, view, and manage user accounts.

Logging: Centralized logging for server activity.

Cloud-Ready: Built to support AWS RDS (PostgreSQL) and S3 interactions.

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

Fill in the necessary environment values provided to you. Use sample.env as a template, and put it outside /app (only if creating a container)

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

🧩 API Modules

Below is an overview of each router included in the app:

1. Authentication (/login, /auth)

Handles login, session management, and token generation.

Generate authentication token

Validate user credentials

2. Users (/users)

Endpoints for managing platform users.

Create users

Retrieve users

Update/delete users (if implemented)

3. Clubs (/clubs)

Manages club-related information.

Register new clubs

View all clubs

Modify club details

4. Items (/items)

Handles the inventory of items within clubs.

Add new items

View items by club

Update item details

5. Borrow (/borrow)

Handles item borrowing workflows.

Request to borrow an item

View borrow requests

Approve/deny borrow actions (if implemented)

6. Returns (/returns)

Manages the return process.

Submit an item return

Mark an item as returned

📂 Technologies Used

FastAPI for high-performance API development

SQLAlchemy ORM with async support

Alembic for database migrations

PostgreSQL (local or AWS RDS)

Docker for containerized development

AWS S3 (optional) for storage of images

