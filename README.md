# 🧠 Decision-Fragility Simulator

<p align="center">
  <a href="https://app.fragility-sim.com">
    <img src="https://img.shields.io/badge/Live_App-Online-brightgreen?style=for-the-badge&logo=azuredevops" alt="Live App" />
  </a>
  <img src="https://img.shields.io/badge/Cloud-Azure_Container_Apps-0078D4?style=for-the-badge&logo=microsoftazure" alt="Azure Container Apps" />
  <img src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Database-Neon_PostgreSQL-15A3FF?style=for-the-badge&logo=postgresql" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker" alt="Docker" />
  <img src="https://img.shields.io/badge/v1.0.0-RELEASE-success?style=for-the-badge" alt="Version" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License" />
</p>

> The Decision-Fragility Simulator is a full-stack **behavioral analytics** app that models how user decision behavior becomes more or less stable over time.  
> It is deployed to Azure with **Docker + HTTPS-secured custom domain**, demonstrating production DevOps, event-driven data engineering, and real-time cloud analytics.

🔗 **Live App:** https://app.fragility-sim.com  
📡 **Status:** ✓ Online & Secure (TLS)  
🧱 **Stack:** Python · Streamlit · Neon PostgreSQL · Docker · Azure Container Apps

## 📌 Overview

This simulator models **human decision stability** using synthetic user actions:

- login → browse → add_to_cart → purchase  
- cancel / refund loops  
- hesitation-driven volatility patterns  

A **Fragility Score** is computed:

| Score | Classification | Meaning |
|------:|:--------------:|--------|
| < 0.20 | 🟩 LOW | Confident/stable decisions |
| 0.20-0.50 | 🟨 MEDIUM | Mixed certainty |
| > 0.50 | 🟥 HIGH | Indecisive / fragile |

## 🎯 Purpose of the Project

✔ Demonstrates **end-to-end cloud delivery**  
✔ Showcases **data engineering + behavioral analytics**  
✔ Fully deployed with **CI-style container workflow**  
✔ Excellent hiring-portfolio showcase project 🎓💼  

## 🎮 Application Features

| Feature | Description |
|--------|-------------|
| 🔁 Refresh Metrics | Live sync from PostgreSQL |
| ➕ Insert Event | Add a single action for any user |
| 📦 Bulk Ingest | Generate many users & events |
| ▶ Run Analysis | Compute score + persist results |
| 📈 Trend View | Score + event volume over time |
| 🔥 Transition Graphs | Most common behavior flows |
| 🧭 Sequence Explorer | Real user-journey windows |

## 🧩 Architecture Overview

The Decision-Fragility Simulator runs as a modern cloud-native analytics app with **two environments**: a production deployment on Azure and a local development flow that mirrors it.

### 🌐 Production Architecture (Azure + Cloudflare + Neon)

<p align="center">
  <img src="https://img.shields.io/badge/Client-Browser-0A84FF?style=for-the-badge&logo=safari&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/DNS+TLS-Cloudflare-F38020?style=for-the-badge&logo=cloudflare&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/App-Azure_Container_Apps-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/Data-Neon_PostgreSQL-008272?style=for-the-badge&logo=postgresql&logoColor=white" />
</p>

**Flow**

1. **Browser** → user opens `https://app.fragility-sim.com`  
2. **Cloudflare** → handles DNS + HTTPS for the custom domain  
3. **Azure Container Apps** → runs the Dockerized Streamlit app + analytics engine  
4. **Neon PostgreSQL** → stores `raw.user_actions` and `analytics.reports` tables  

| Component | Role |
|----------|------|
| **Cloudflare** | DNS, TLS termination, custom domain for `app.fragility-sim.com` |
| **Azure Container Apps** | Hosts the containerized Streamlit UI and fragility analytics |
| **Neon PostgreSQL** | Serverless Postgres backend for events and analysis history |

The **same Docker image** is used locally and in Azure → strong environment consistency.

### 🖥️ Development Architecture (Local Docker + VS Code)

<p align="center">
  <img src="https://img.shields.io/badge/Editor-VS_Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/Runtime-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/Database-Neon_PostgreSQL-4B8BBE?style=for-the-badge&logo=postgresql&logoColor=white" />
</p>

In development, the app runs as a local Docker container, connecting securely to the same Neon PostgreSQL instance (or a dev branch of it), using the same environment variables as production.

**Typical local workflow:**

```bash
# Build image
docker build -t decision-fragility-simulator .

# Run locally with env file
docker run -p 8501:8501 --env-file .env decision-fragility-simulator
