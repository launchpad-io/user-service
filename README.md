### 🚀 LaunchPAID - TikTok Influencer Marketing Platform
A comprehensive SaaS platform connecting TikTok creators with brands and agencies for influencer marketing campaigns. Built with modern technologies and enterprise-grade security.

## 🎯 Overview
•	- Multi-role authentication (Creators, Agencies, Brands)
•	- TikTok Shop integration for real-time GMV tracking
•	- Automated campaign management and creator payments
•	- Discord integration for community management
•	- SMS/Email notifications for engagement
•	- Performance analytics and reporting dashboards

## 🛠️ Tech Stack
•	Backend:
- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT
- Bcrypt
- Slowapi
•	Frontend:
- Next.js 14
- TypeScript
- Tailwind CSS
- Shadcn/ui
- Axios
•	Infrastructure:
- Docker
- CORS
- SMTP
  
## 🚀 Getting Started
•	Prerequisites:
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Git
  
## 🔧 Backend Setup
•	1. Clone the repository:
   git clone https://github.com/yourusername/launchpaid.git
   cd launchpaid/user-service
•	2. Create virtual environment:
   python -m venv venv
   source venv/bin/activate (Linux/macOS)
   venv\Scripts\activate (Windows)
•	3. Install dependencies:
   pip install -r requirements.txt
•	4. Configure environment:
   cp .env.example .env (Edit it)
•	5. Setup database:
   createdb launchpaid_db
   alembic upgrade head
•	6. Run the backend:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## 🌐 Frontend Setup
•	cd ../frontend
•	npm install
•	cp .env.example .env.local (Update API URL)
•	npm run dev

## 📋 Features
•	Authentication & Security:
- JWT auth
- Email verification
- Password reset
- Rate limiting
- Bcrypt
- Account lockout (In Progress)
- Two-factor auth (Planned)
- Refresh tokens (Planned)
•	User Management:
- Multi-role
- Role-based profiles
- Email templates
- Discord/TikTok OAuth (Planned)
•	Campaign Features:
- Campaign lifecycle
- Creator applications
- Analytics
- Payouts
- Content approval

## 🔑 Environment Variables
•	Backend (.env):
APP_NAME=LaunchPAID API
... (etc)
•	Frontend (.env.local):
NEXT_PUBLIC_API_URL=http://localhost:8000

## 🧪 Testing
•	Backend:
cd user-service
pytest
•	Frontend:
cd frontend
npm test

## 🐳 Docker Deployment
•	docker-compose up --build
•	Starts: Backend(8000), Frontend(3000), PostgreSQL

## 🔄 Development Workflow
•	Backend: app/api/v1/, app/services/, app/models/
•	Frontend: src/app/, src/components/, src/lib/api.ts

## 📈 Roadmap
•	Phase 1: Auth, Email, Lockout, 2FA, OAuth
•	Phase 2: Campaigns, Profiles, Analytics, Payments
•	Phase 3: Advanced Analytics, SMS, Referrals

## 🤝 Contributing
•	1. Fork the repo
2. Create branch
3. Commit
4. Push
5. PR

## 📄 License
•	This project is proprietary and confidential. All rights reserved © 2025 Novanex Ventures.

## 👥 Team
- Armaghan
- Abdul Samad
- Zohad
  
## 📞 Support
•	Email: novanexventures@gmail.com
