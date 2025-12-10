## Setup

Here is a comprehensive, professional **README.md** file for your project. You can copy-paste this directly into your GitHub repository.

I have structured it to cover the entire stack: **Chrome Extension (FE)**, **FastAPI (BE)**, **Docker Infrastructure**, and **MLflow Observability**.

-----

# 🌐 LinguaFlow: AI-Powered Real-Time Translation

> **Select text anywhere on the web and get instant, context-aware translations powered by Llama-3.**

**LinguaFlow** is a production-grade Chrome Extension that provides real-time translation using Large Language Models (LLMs). Unlike standard translators, it uses **Groq** for ultra-low latency inference, **Redis** for intelligent caching, and **MLflow** for complete observability of translation performance.

## 🚀 Key Features

  * **⚡ Real-Time Translation:** Instant translation of selected text on any webpage.
  * **🧠 AI-Powered:** Uses **Llama-3-8b** (via Groq) for high-quality, contextual translations.
  * **💾 Smart Caching:** Redis caching layer prevents re-translating common phrases, saving costs and latency.
  * **📊 Observability:** Full MLflow integration to track latency, prompts, and translation quality.
  * **🐳 Containerized:** Fully Dockerized architecture (API, DB, Cache, Dashboard) for easy deployment.
  * **🔒 Secure:** Production-ready Nginx reverse proxy with automatic SSL (via Let's Encrypt).

-----

## 🛠️ Tech Stack

### Frontend (Chrome Extension)

  * **React 18** + **TypeScript**
  * **Vite** (with CRXJS plugin)
  * **Shadow DOM** (Style isolation)

### Backend (API)

  * **FastAPI** (Python 3.11)
  * **LangChain** (LLM Orchestration)
  * **Groq API** (Llama-3 Inference)
  * **UV** (Fast Python package manager)

### Infrastructure & DevOps

  * **Docker & Docker Compose**
  * **Redis** (Caching)
  * **PostgreSQL** (MLflow Backend Store)
  * **MLflow** (LLM Tracing & Experiment Tracking)
  * **Nginx Proxy Manager** (SSL & Reverse Proxy)

-----

## 🏗️ Architecture

```mermaid
graph TD
    User[User Selects Text] -->|Chrome Ext| FE[Frontend (React)]
    FE -->|HTTPS| Nginx[Nginx Proxy Manager]
    Nginx -->|Reverse Proxy| API[FastAPI Backend]
    
    API -->|Check Cache| Redis[(Redis)]
    Redis -- Hit --> API
    
    API -- Miss --> LLM[Groq API / Llama-3]
    LLM --> API
    
    API -->|Log Trace| MLflow[MLflow Server]
    MLflow -->|Store Data| DB[(PostgreSQL)]
```

-----

## ⚙️ Environment Variables

Create a `.env` file in the `linguaflow-backend` directory:

```ini
# AI Provider
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama3-8b-8192
TARGET_LANG=French

# Database & Cache (Docker Service Names)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=mlflow_db

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000
```

-----

## 🚀 Getting Started

### 1\. Clone the Repository

```bash
git clone https://github.com/yourusername/linguaflow.git
cd linguaflow
```

### 2\. Start the Backend (Docker)

We use Docker Compose to spin up the API, Redis, Postgres, and MLflow.

```bash
cd linguaflow-backend
docker-compose up -d --build
```

  * **API:** `http://localhost:8000`
  * **MLflow UI:** `http://localhost:5000`
  * **Nginx Admin:** `http://localhost:81`

### 3\. Build the Frontend (Extension)

The frontend must be built locally to generate the Chrome Extension files.

```bash
cd ../linguaflow-frontend
npm install
npm run build
```

This creates a `dist` folder.

### 4\. Load into Chrome

1.  Open Chrome and go to `chrome://extensions`.
2.  Enable **Developer Mode** (top right).
3.  Click **Load unpacked**.
4.  Select the `linguaflow-frontend/dist` folder.

-----

## ☁️ Deployment (AWS / VPS)

This project is ready for cloud deployment (AWS EC2, DigitalOcean, Hetzner).

1.  **Provision Server:** Ubuntu 22.04+ (2GB RAM recommended).
2.  **Firewall:** Allow ports `80`, `443`, `81`.
3.  **Deploy:**
    ```bash
    git clone ...
    cd linguaflow-backend
    docker compose up -d --build
    ```
4.  **SSL Setup:**
      * Access Nginx Admin at `http://<YOUR_IP>:81`.
      * Create a Proxy Host pointing to `backend:8000`.
      * Use **sslip.io** for easy domain resolution (e.g., `54.123.45.67.sslip.io`).
      * Request a Let's Encrypt SSL Certificate.

-----

## 📊 Observability (MLflow)

LinguaFlow includes a robust tracing system.

1.  Access the dashboard at `http://localhost:5000` (or your server IP).
2.  Navigate to the **LinguaFlow-Live-Translations** experiment.
3.  Click on any run to see:
      * **Input:** The text selected by the user.
      * **Output:** The translated text.
      * **Latency:** Time taken (ms).
      * **Source:** Whether it came from `Cache` (Redis) or `API` (Groq).

-----

## 🤝 Contributing

Contributions are welcome\!

1.  Fork the Project.
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the Branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.