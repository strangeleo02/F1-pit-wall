# 🏎️ F1 Pit Wall - Monorepo Deployment Guide (Vercel + Render)

This guide provides step-by-step instructions for deploying the **F1 Pit Wall** single Git repository (monorepo) simultaneously across **Render** (FastAPI Backend) and **Vercel** (Next.js Frontend).

---

## 🏗️ Monorepo Architecture Overview

```
F1-pit-wall/ (GitHub Repository)
├── backend/                  ---> Deployed to Render (Docker / Web Service)
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
└── frontend/                 ---> Deployed to Vercel (Next.js App)
    ├── app/
    ├── package.json
    └── .env.example
```

---

## 🚀 Part 1: Deploy Backend to Render

Deploy the Python FastAPI backend service from the `backend/` directory of your repo.

### Steps:
1. Go to your [Render Dashboard](https://dashboard.render.com/) and click **New +** → **Web Service**.
2. Connect your **`F1-pit-wall`** GitHub repository.
3. Configure the following service settings:
   - **Name**: `f1-pit-wall-backend`
   - **Root Directory**: `backend` *(Crucial: Tells Render where the backend project lives)*
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile`
   - **Instance Type**: Free or Starter
4. Add Environment Variables under the **Environment** tab:
   | Key | Value / Example | Notes |
   | :--- | :--- | :--- |
   | `GROQ_API_KEY` | `gsk_...` | Required for LLM Strategy Generation |
   | `QDRANT_URL` | `https://your-cluster.qdrant.io` | Vector database URL |
   | `QDRANT_API_KEY` | `your_qdrant_key` | Vector database API Key |
   | `HF_TOKEN` | `hf_...` | Optional Hugging Face Token |
   | `CORS_ORIGINS` | `["*"]` | Allows frontend cross-origin requests |

5. Click **Create Web Service**.
6. Wait for deployment to complete. Copy your live backend URL:
   `https://f1-pit-wall-backend.onrender.com`

---

## ⚡ Part 2: Deploy Frontend to Vercel

Deploy the Next.js web application from the `frontend/` directory of your repo.

### Steps:
1. Go to your [Vercel Dashboard](https://vercel.com/new) and click **Import Project**.
2. Select your **`F1-pit-wall`** GitHub repository.
3. Configure the Project Settings:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click **Edit** and set to `frontend` *(Crucial: Tells Vercel to build from the frontend folder)*
   - **Build Command**: `npm run build` *(Auto-detected)*
   - **Output Directory**: `.next` *(Auto-detected)*
4. Environment Variables:
   Expand **Environment Variables** and add:
   | Key | Value |
   | :--- | :--- |
   | `NEXT_PUBLIC_API_BASE_URL` | `https://f1-pit-wall-backend.onrender.com` *(Replace with your Render URL from Part 1)* |

5. Click **Deploy**.
6. Vercel will build and assign a domain (e.g., `https://f1-pit-wall.vercel.app`).

---

## 🔄 How Monorepo Auto-Deployments Work

- **Pushing to `main` branch**:
  - Render detects changes in `backend/` and triggers a backend rebuild.
  - Vercel detects changes in `frontend/` and triggers a frontend rebuild.
- **Preview Deployments**: Vercel will automatically generate preview URLs for Pull Requests without affecting your production Render backend.

---

## 🛠️ Infrastructure as Code (Automated Configuration)

### Render Blueprint (`render.yaml`)
You can add `render.yaml` to the root of your repository to automate Render service creation:

```yaml
services:
  - type: web
    name: f1-pit-wall-backend
    env: docker
    rootDir: backend
    dockerfilePath: Dockerfile
    plan: starter
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: QDRANT_URL
        sync: false
      - key: QDRANT_API_KEY
        sync: false
      - key: CORS_ORIGINS
        value: '["*"]'
```

### Vercel Configuration (`frontend/vercel.json`)
You can create `frontend/vercel.json` for custom settings:

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next"
}
```

---

## ❓ Frequently Asked Questions & Troubleshooting

### 1. CORS Errors (Frontend cannot reach backend)
- **Problem**: Web browser console shows `Access-Control-Allow-Origin` error.
- **Fix**: Ensure `CORS_ORIGINS` on Render is set to `["*"]` or includes your Vercel URL `["https://f1-pit-wall.vercel.app"]`.

### 2. Render Cold Starts (Free Tier)
- **Problem**: First request takes 30-60 seconds after inactivity.
- **Fix**: Render free tier puts web services to sleep after 15 minutes of non-use. Set up a free service like [UptimeRobot](https://uptimerobot.com) to ping `https://f1-pit-wall-backend.onrender.com/health` every 10 minutes to keep the instance active.

### 3. Vercel Build Fails with "Cannot find module"
- **Problem**: Vercel tries to run commands from the root directory instead of `frontend/`.
- **Fix**: Double check Vercel **Project Settings → General → Root Directory** is explicitly set to `frontend`.
