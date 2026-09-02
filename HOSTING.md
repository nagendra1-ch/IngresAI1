# 🚀 INGRES AI — Hosting & Deployment Guide

This guide details how to host and deploy the optimized **INGRES AI** application to production across various popular cloud platforms.

---

## 📋 Required Environment Variables

Before deploying, make sure you have the following environment variables ready:

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL or SQLite connection string | `postgresql://user:pass@host:port/dbname` |
| `GEMINI_API_KEY` | Google Gemini API Key for AI Assistant | `AIzaSy...` |
| `JWT_SECRET_KEY` | Secret key used to sign JWT auth tokens | Any secure 32+ character random string |
| `JWT_ALGORITHM` | Token hashing algorithm | `HS256` |
| `CORS_ORIGINS` | Comma-separated allowed origins (or `*`) | `*` or `https://your-domain.vercel.app` |

---

## ⚡ Option 1: Deploy on Vercel (Recommended for Serverless)

The project includes pre-configured `vercel.json` and `.vercelignore` files for seamless full-stack deployment on Vercel.

### Steps:
1. Push your repository to **GitHub** / **GitLab** / **Bitbucket**.
2. Go to [vercel.com](https://vercel.com) and log in.
3. Click **"Add New Project"** and import your repository.
4. Set the **Framework Preset** to `Vite` (or `Other`).
5. Under **Environment Variables**, add:
   - `DATABASE_URL` = Your Supabase / Cloud PostgreSQL connection string
   - `GEMINI_API_KEY` = Your Google AI Studio API key
   - `JWT_SECRET_KEY` = Your secure random secret
   - `CORS_ORIGINS` = `*`
6. Click **Deploy**. Vercel will automatically build the React frontend and deploy the FastAPI backend as serverless functions.

---

## 🌐 Option 2: Deploy on Render (Recommended for Full-Stack Docker)

The repository includes a `render.yaml` Blueprint for 1-click unified hosting.

### Steps:
1. Push your code to **GitHub**.
2. Go to [render.com](https://render.com) and log in.
3. Click **"New +"** &rarr; **"Blueprint"** (or **"Web Service"**).
4. Connect your repository.
5. Select **Docker** as the runtime.
6. Provide your environment variables (`DATABASE_URL`, `GEMINI_API_KEY`, `JWT_SECRET_KEY`).
7. Click **"Create Web Service"**. Render will build the unified multi-stage container and start the service with automatic health monitoring on `/api/health`.

---

## 🚂 Option 3: Deploy on Railway

1. Go to [railway.app](https://railway.app) and click **"New Project"**.
2. Select **"Deploy from GitHub repo"** and choose your repository.
3. Railway will detect the `Dockerfile` automatically.
4. Go to **Variables** tab in your Railway service and add:
   - `DATABASE_URL`
   - `GEMINI_API_KEY`
   - `JWT_SECRET_KEY`
   - `PORT` = `8000`
5. Railway will deploy your unified container and assign a live public HTTPS URL.

---

## 🐳 Option 4: Self-Hosted Docker / VPS (Ubuntu / Debian / AWS EC2 / DigitalOcean)

Run the entire application in a production container on any server:

```bash
# 1. Clone your repository
git clone https://github.com/your-username/ingres-ai.git
cd ingres-ai

# 2. Configure your environment variables in .env
cat <<EOF > .env
DATABASE_URL=postgresql://user:password@db-host:5432/postgres
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_secure_random_jwt_key
CORS_ORIGINS=*
EOF

# 3. Build and launch with Docker Compose
docker compose up -d --build

# 4. Check application logs and status
docker compose logs -f
```

The application will be running at `http://YOUR_SERVER_IP:8000`.

---

## 🗄️ Database Setup (Supabase PostgreSQL)

If you are using Supabase for your database:
1. Create a project at [supabase.com](https://supabase.com).
2. Go to **Project Settings &rarr; Database**.
3. Copy the **Connection String** (URI mode, Session Pooler on port 6543 or Direct on 5432).
4. Set `DATABASE_URL=postgresql://postgres.xxxx:your_password@aws-0-xx.pooler.supabase.com:6543/postgres`.
5. The application will automatically create schemas and performance indexes on initial startup.

---

## 🩺 Verifying Deployment Health

Once deployed, you can verify your service status using:
- **API Status**: `https://your-domain/api`
- **Health Check**: `https://your-domain/api/health`
- **Interactive Swagger Docs**: `https://your-domain/docs`
