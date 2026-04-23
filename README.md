# 🧠 Decision-Fragility Simulator

<p align="center">
  <a href="https://app.fragility-sim.com">
    <img src="https://img.shields.io/badge/Live_App-Online-brightgreen?style=for-the-badge" alt="Live App" />
  </a>
  <img src="https://img.shields.io/badge/Cloud-Railway-0B0D0E?style=for-the-badge&logo=railway" alt="Railway" />
  <img src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Database-Railway_PostgreSQL-336791?style=for-the-badge&logo=postgresql" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker" alt="Docker" />
  <img src="https://img.shields.io/badge/v1.0.0-RELEASE-success?style=for-the-badge" alt="Version" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License" />
</p>

> The Decision-Fragility Simulator is a full-stack **behavioral analytics** app that models how user decision behavior becomes more or less stable over time.  
> It is deployed on **Railway with Docker + HTTPS-secured custom domain**, demonstrating production deployment, event-driven data engineering, and real-time behavioral analytics.

## 🌐 Live App

- **UI:** https://app.fragility-sim.com  
- **Backup UI:** https://crb-decision-fragility.streamlit.app  
- **Status:** Online & Secure (HTTPS)  
- **Stack:** Python · Streamlit · Railway PostgreSQL · Docker  

## 📌 Overview

This simulator models **human decision stability** using synthetic user actions:

- login → browse → add_to_cart → purchase  
- cancel / refund loops  
- hesitation-driven volatility patterns  

A **Fragility Score** is computed:

| Score | Classification | Meaning |
|------:|:--------------:|--------|
| < 0.20 | 🟩 LOW | Confident / stable decisions |
| 0.20-0.50 | 🟨 MEDIUM | Mixed certainty |
| > 0.50 | 🟥 HIGH | Indecisive / fragile behavior |

## 🎯 Purpose of the Project

✔ Demonstrates **end-to-end cloud delivery**  
✔ Showcases **data engineering + behavioral analytics**  
✔ Fully deployed with **containerized workflow**  
✔ Strong portfolio project for **Data / AI / Cloud roles**  

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
| 📝 Stored Reports | Persisted analysis history for comparison |

## 🧩 Architecture Overview

The Decision-Fragility Simulator runs as a modern cloud-native analytics app with a **production deployment on Railway** and a **local development flow** that mirrors it.

### 🌐 Production Architecture (Railway + Cloudflare)

<p align="center">
  <img src="https://img.shields.io/badge/Client-Browser-0A84FF?style=for-the-badge&logo=safari&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/DNS+TLS-Cloudflare-F38020?style=for-the-badge&logo=cloudflare&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/App-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/Data-Railway_PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
</p>

**Flow**

1. **Browser** → user opens `https://app.fragility-sim.com`  
2. **Cloudflare** → handles DNS + HTTPS for the custom domain  
3. **Railway** → runs the Dockerized Streamlit app + analytics engine  
4. **Railway PostgreSQL** → stores `raw.user_actions` and `analytics.reports` tables  

| Component | Role |
|----------|------|
| **Cloudflare** | DNS, TLS, custom domain for `app.fragility-sim.com` |
| **Railway App Service** | Hosts the containerized Streamlit UI and fragility analytics |
| **Railway PostgreSQL** | PostgreSQL backend for events and analysis history |

### 🖥️ Development Architecture (Local Docker + VS Code)

<p align="center">
  <img src="https://img.shields.io/badge/Editor-VS_Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/Runtime-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  ↓
  <img src="https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
</p>

In development, the app runs locally with Docker or Streamlit, using a `.env` file for the database connection.

**Typical local workflow:**

```bash
# Build image
docker build -t decision-fragility-simulator .

# Run locally with env file
docker run -p 8501:8501 --env-file .env decision-fragility-simulator
