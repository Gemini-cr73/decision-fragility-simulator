# 🧠 Decision-Fragility Simulator

**Live App:** https://app.fragility-sim.com  
**Status:** ✓ Online & Secure (HTTPS)  
**Tech Stack:** Python · Streamlit · PostgreSQL · Docker · Azure Container Apps

---

## 📌 Overview

The **Decision-Fragility Simulator** models how user decision actions become more or less stable over time.  
It analyzes **behavior patterns** such as:

- Add to cart
- Browse product pages
- Login / logout
- Purchase vs cancel
- Refund requests

The simulator assigns a **Fragility Score**, indicating whether behavior is:

| Score Range | Classification | Meaning |
|------------|----------------|--------|
| < 0.20     | LOW            | Stable decision-making |
| 0.20–0.50  | MEDIUM         | Increasing volatility |
| > 0.50     | HIGH           | Fragile — constant changing of mind |

---

## 🎮 Key Features

✔ Real-time ingestion of synthetic user actions  
✔ PostgreSQL data persistence  
✔ Automated Fragility Score computation  
✔ Visual analytics: bar charts + behavior summaries  
✔ Ability to simulate thousands of user events  
✔ Secure HTTPS + custom domain deployment

## 🔥 Next Deliverables

Here’s what’s next — in order:

| Step | Task |
|------|------|
| 1️⃣ | You paste / commit this README.md into GitHub |
| 2️⃣ | I add an MIT LICENSE to your repo |
| 3️⃣ | Upload screenshots → `/docs/` folder |
| 4️⃣ | Publish GitHub Release v1.0.0 |
| 5️⃣ | Add GitHub badges (live status, deployment, tech stack) |

### ❓ Ready?

Reply:

> 👍 Add LICENSE + Screenshots + Badges next

or

> ✍️ Edit the README first (tell me what to change)

---

Would you like me to **auto-add your name + LinkedIn + GitHub badge** at the top too?


## 🛠️ System Architecture

```ascii
User → Streamlit UI → Fragility Analysis Service → Postgres DB → Dashboard


