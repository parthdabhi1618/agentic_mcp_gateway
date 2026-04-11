# Agentic OS

Agentic OS is a modular, contribution-based AI operating system designed to execute complex tasks through a dynamic planner and a robust suite of tools. This repository showcases the final, production-ready version (V6) of the project.

This directory is structured to highlight individual team member contributions, allowing each member to showcase their specific domain of expertise while aggregating into a unified, functional system.

---

## 🌟 Overview

Agentic OS scales a basic AI execution MVP into a full-featured, context-aware platform. The system combines a modern frontend interface with a robust Python backend and a sophisticated AI integration layer. The system iteratively plans, executes jobs, dynamically manages context (RAG), and validates workflows through strict Standard Operating Procedures (SOPs) and release gates.

---

## 🚀 Versions & Evolution

Our development roadmap followed a structured, version-based approach to reach the final product:

### **V4: The Foundation**
- **Focus:** Integrating core components to create an end-to-end functional system.
- **Achievements:** Configured the local AI models for the AI Planner. Established a 7-tool execution workflow with Server-Sent Events (SSE). Connected the backend job system to the frontend to successfully render the real-time execution timeline.

### **V5: Context-Aware Intelligence**
- **Focus:** Implementing memory and robust feedback loops.
- **Achievements:** Created the context tracking module to log job outcomes. Upgraded the planner to support pre-planning RAG (auto-context injection). Created a robust execution loop where past actions directly inform future planning cycles. Merged the secure context vault and task scheduler.

### **V6: Production-Ready OS (Final)**
- **Focus:** Hardening, validation, and demo-readiness.
- **Achievements:** Finalized the unified backend with hardened file management and SOP-compliant planning policies. Restored strict planner failure contracts, tightened scheduler persistence verification, and passed all automated release gate assertions. Completed all final handoff and sign-off documentation.

---

## 👥 Team Roles & Contributions

The project was divided into three distinct ownership domains, ensuring modular and decoupled development:

### **`mem1/` - Frontend Lead**
- Built the responsive **Vite + React** frontend application.
- Developed the spotlight interface and real-time execution timeline (consuming SSE streams).
- Maintained frontend-specific SOPs, issue logs, and component handoff documentation.

### **`mem2/` - Backend Developer**
- Engineered the core **FastAPI** application logic and REST/SSE endpoints.
- Developed the robust task scheduler, tool definitions, and job execution pipeline.
- Authored backend-specific SOPs and architecture handoff logs.

### **`mem3/` - AI & Integration Lead**
- Designed the AI Planner and prompt structuring.
- Built the Context Evaluation Suite, secure vault, and validation scripts.
- Authored the project's **Single Source of Truth (SSoT)**, cross-team integration SOPs, and project sign-off documentation.

---

## 💻 Tech Stack

### Backend
- **Core language:** Python
- **Framework:** FastAPI
- **Architecture:** Task Scheduler & Secure Context Vault

### Frontend
- **Libraries:** React, Vite
- **Languages:** HTML, CSS, JavaScript
- **Styling:** Vanilla CSS with modern dynamic animations

### AI & Integration
- **Models:** Local LLM via Ollama (`gemma4:e4b`)
- **Capabilities:** Pre-Planning RAG (Retrieval-Augmented Generation)

---

## 📂 Project Structure

```text
Online/
│
├── mem1/           # Frontend contributions (Vite+React app, UI/UX docs)
├── mem2/           # Backend contributions (FastAPI, Scheduler, Tools)
└── mem3/           # AI Contributions (Planner, Validations, SSoT)
```

---

## 🧩 How to Assemble

To recreate the full final project source:
1. Merge the contents of all three member directories (`mem1/`, `mem2/`, `mem3/`) into a single root folder. 
2. The folder structure is perfectly preserved so that `frontend/`, `backend/`, and `docs/` align across all pushes seamlessly.

---

## ⚙️ Running Locally

Once assembled into a single root directory:

### 1. Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt

# Ensure Ollama is running locally with the required model
ollama run gemma4:e4b

# Run the application
python main.py
```

### 2. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

Open your browser to the local port specified by Vite (usually `http://localhost:5173`) to interact with the Agentic OS.

---

## ✨ Future Improvements
- Expand the core execution workflow with external API integrations.
- Introduce user authentication for multi-tenant context management.
- Improve UI/UX interface and interactive features.
- Provide comprehensive REST API endpoint documentation.
- Deploy the OS as a centralized cloud service beyond local execution.
