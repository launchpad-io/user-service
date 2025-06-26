User Service (FastAPI Microservice)

# 🧩 User Service (FastAPI Microservice)

A modular, production-ready **User Authentication & Management microservice** built with FastAPI, leveraging modern development practices such as:
- JWT-based authentication
- Modular folder structure
- Dockerized deployment
- Environment-based configuration

## 📁 Project Structure
user-service/
│
├── app/
│   ├── api/v1/             # Route definitions (auth, users)
│   ├── core/               # Configuration, DB connection, security
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic (auth, email, etc.)
│   ├── utils/              # Dependency injection, helpers
│   └── main.py             # Entry point for FastAPI app
│
├── .env                    # Environment variables (not tracked)
├── .env.example            # Sample environment file
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── test_import.py          # Import test stub

## 🚀 Getting Started

### 1. 🧪 Clone the Repo
git clone https://github.com/launchpad-io/user-service.git
cd user-service

### 2. 🧱 Create Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

### 3. 📦 Install Dependencies
pip install -r requirements.txt

### 4. ⚙️ Setup Environment Variables
cp .env.example .env

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/users
SECRET_KEY=super-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🧬 Run the API (Dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

📬 Access the docs at: http://localhost:8000/docs

## 🐳 Docker Setup

### Build & Run with Docker Compose:
docker-compose up --build

📍 FastAPI will be available at: http://localhost:8000

## ✅ API Features
- 🔐 JWT Authentication
- 📬 Email service stubbed
- 👥 User Registration & Login
- 🛡️ Role-based access ready
- 📦 Clean modular codebase
- 🐍 Built on FastAPI + SQLAlchemy + Pydantic

## 📄 .env.example
DATABASE_URL=postgresql://user:password@localhost:5432/users
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=super-secret

## 🔧 Future Enhancements
- ✅ CI/CD with GitHub Actions
- ✅ Swagger API security schemes
- 🚨 Rate limiting & logging (via SlowAPI + Loguru)
- 📊 Admin dashboard UI
- ✉️ Integrated email confirmations (via SMTP)

## 📜 License
This project is private and maintained by the NovaNex organization.
All rights reserved © 2025.

## 🙋‍♂️ Maintainers
- **Zohad** – @zohad1 – Backend Engineering Lead

