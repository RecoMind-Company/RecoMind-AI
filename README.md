# 🚀 RecoMind-AI: Enterprise Reporting System & AI Copilot

[![Python](https://img.shields.io/badge/Python-81.2%25-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)
[![AI Powered](https://img.shields.io/badge/AI-LangChain%20%7C%20CrewAI-orange.svg)]()

**RecoMind-AI** is a next-generation, AI-driven reporting engine and conversational data copilot. Built for modern data analysis companies, it automates complex data pipelines, generates comprehensive reports asynchronously, and provides an intelligent AI assistant that allows stakeholders to interact with their data using natural language.

---

## 📈 Business Impact for Data Analysis Companies

In the fast-paced data industry, time-to-insight is critical. RecoMind-AI is designed to transform how data consultancy and analytics firms operate:

*   **Scale Client Reporting:** Reduce the turnaround time for client reports from days to minutes. Automate repetitive ETL (Extract, Transform, Load) tasks and monthly reporting cycles.
*   **Democratize Data Access:** Empower non-technical stakeholders (executives, marketing teams, clients) to query complex databases using plain English via the AI Copilot, reducing the bottleneck on data engineering teams.
*   **Actionable AI Insights:** Move beyond static dashboards. The multi-agent AI system detects anomalies, summarizes trends, and suggests actionable metrics automatically.
*   **Cost Efficiency:** By utilizing asynchronous processing (Celery/Redis) and intelligent query routing (LiteLLM/LangChain), infrastructure and API costs are kept heavily optimized.

---

## ✨ Key Features

### 🤖 Intelligent Data Copilot (`src/copilot`)
*   **Natural Language to SQL/Insights:** Ask complex questions and get accurate data summaries.
*   **Multi-Agent Architecture:** Powered by **CrewAI** and **LangGraph**, specific AI agents handle distinct tasks (e.g., Data Analyst Agent, QA Agent, Summarization Agent).
*   **Context-Aware Memory:** Utilizes **Sentence-Transformers** for semantic search, ensuring the AI understands the context of your specific business domains.

### 📊 Automated Reporting System (`src/reporting_system`)
*   **Asynchronous Generation:** Handles massive datasets without timing out, utilizing **Celery** and **Redis** for background task management.
*   **Multi-Source Integration:** Connects seamlessly to PostgreSQL, SQL Server, and flat files using `SQLAlchemy`, `psycopg2`, and `pyodbc`.
*   **Dynamic Data Pipelines:** Robust `pandas` and `numpy` integrations for heavy data aggregation, cleaning, and formatting.

---

## 🛠️ Technology Stack

RecoMind-AI is built on a modern, scalable, and high-performance Python ecosystem:

*   **Core Backend:** Python 3.x, FastAPI, Uvicorn, Pydantic
*   **AI & LLM Frameworks:** CrewAI, LangChain, LangGraph, LiteLLM
*   **Data Processing:** Pandas, NumPy, Sentence-Transformers
*   **Database & ORM:** SQLAlchemy, PostgreSQL (psycopg2), ODBC (pyodbc)
*   **Task Queue:** Celery, Redis, Gevent
*   **Infrastructure:** Docker, Docker Compose

---

## 🏗️ System Architecture

```text
RecoMind-AI/
├── src/
│   ├── copilot/             # AI Assistant APIs, CrewAI Agents, and LLM integrations
│   ├── reporting_system/    # Async report generation, data pipelines, Celery workers
│   └── data_embedding/      # Vectorization processes and semantic search utilities
├── notebooks/               # Jupyter Notebooks for EDA and prompt engineering
└── docker-compose.yml       # Orchestration for microservices
