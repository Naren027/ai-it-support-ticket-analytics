# AI-Powered IT Support Ticket Analytics & Auto-Triage System

An end-to-end data analytics project that transforms raw IT support ticket data into structured priority, urgency, and operational-risk insights using **Python, MySQL, SQL, and Power BI**.

The project demonstrates a complete analytics workflow:

**Raw Data → Data Cleaning → Classification → MySQL → SQL Analysis → Power BI Dashboard**

---

## Project Overview

IT support teams receive large volumes of tickets containing information about hardware failures, access problems, HR requests, storage issues, purchasing requests, and other operational problems.

The objective of this project was to build an analytics workflow capable of:

* Cleaning and standardizing raw ticket data
* Classifying tickets by priority
* Measuring ticket urgency
* Identifying operational risk indicators
* Storing enriched data in a relational database
* Creating reusable SQL analytical views
* Building an interactive Power BI dashboard
* Supporting investigation of critical and high-risk tickets

---

## Dataset

**Dataset:** IT Service Ticket Classification Dataset

### Dataset Size

* **47,837 tickets**
* **2 original columns**
* **8 support categories**
* **47,837 unique ticket descriptions**
* No missing values identified in the original dataset
* No duplicate rows identified

### Support Categories

* Hardware
* HR Support
* Access
* Miscellaneous
* Storage
* Purchase
* Internal Project
* Administrative rights

---

## Technology Stack

| Area               | Technology          |
| ------------------ | ------------------- |
| Data Processing    | Python              |
| Data Manipulation  | Pandas              |
| Classification     | Python Rule Engine  |
| AI Experimentation | Ollama / Qwen2.5 3B |
| Database           | MySQL 8.0           |
| Querying           | SQL                 |
| BI                 | Microsoft Power BI  |
| Calculations       | DAX                 |
| Version Control    | Git / GitHub        |

---

## Project Architecture

```text
                 RAW TICKET DATA
                       │
                       ▼
              Python Data Inspection
                       │
                       ▼
                 Data Cleaning
                       │
                       ▼
              Cleaned Ticket Dataset
                       │
                       ▼
          Rule-Based Classification
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
     Priority                 Risk Indicators
          │                         │
          └────────────┬────────────┘
                       ▼
                Enriched Dataset
                       │
                       ▼
                     MySQL
                       │
                       ▼
                 SQL Analytical Views
                       │
                       ▼
                   Power BI
                       │
                       ▼
             Interactive Dashboard
```

---

## Classification Approach

Two approaches were evaluated during development.

### Hybrid Approach

The initial architecture combined:

```text
Python Rules
      ↓
Confident Tickets → Rule Classification
      ↓
Ambiguous Tickets → Local LLM
```

A rule-coverage analysis showed:

* **4,067 tickets (8.5%)** could be confidently classified using the initial rule filters.
* **43,770 tickets (91.5%)** remained ambiguous and would require local LLM processing.

Because processing the complete dataset through a local LLM was not practical for the available development environment, the project was finalized using a deterministic rule-based classification pipeline.

### Final Approach

The final pipeline processes all tickets using Python-based rules and generates:

* Priority
* Urgency score
* Urgency reason
* Work-blocked indicator
* Deadline-present indicator
* Explicit-urgency indicator
* Service-unavailable indicator
* Security-issue indicator
* Multiple-users indicator
* Business-critical indicator
* Limited-functionality indicator

The final enrichment run processed:

**47,837 / 47,837 tickets successfully**

**0 failures**

**Processing time: approximately 1 minute 47 seconds**

The local LLM component remains in the repository as an experimental extension for future improvement of ambiguous-ticket classification.

---

## Priority Distribution

| Priority | Tickets | Percentage |
| -------- | ------: | ---------: |
| Low      |  45,911 |     95.97% |
| Medium   |   1,605 |      3.36% |
| Critical |     321 |      0.67% |

---

## Key Dataset Insights

### Ticket Volume by Category

| Category              | Tickets |  Share |
| --------------------- | ------: | -----: |
| Hardware              |  13,617 | 28.47% |
| HR Support            |  10,915 | 22.82% |
| Access                |   7,125 | 14.89% |
| Miscellaneous         |   7,060 | 14.76% |
| Storage               |   2,777 |  5.81% |
| Purchase              |   2,464 |  5.15% |
| Internal Project      |   2,119 |  4.43% |
| Administrative rights |   1,760 |  3.68% |

### Risk Indicators

* Critical tickets: **321**
* Security-related tickets: **317**
* Average urgency score: **14.02**
* Maximum urgency score: **85**
* Classification failures: **0**

---

## MySQL Database

The enriched dataset is stored in MySQL using a structured ticket table with supporting reference relationships and analytical views.

### Analytical Views

* `vw_ticket_summary`
* `vw_category_kpis`
* `vw_priority_summary`
* `vw_high_impact_tickets`

These views provide reusable datasets for Power BI and SQL-based analysis.

---

## Power BI Dashboard

The dashboard contains three analytical pages.

### 1. IT Support Operations Overview

Focus:

> What does the overall IT support workload look like?

Key metrics include:

* Total Tickets
* Critical Tickets
* Average Urgency
* Critical Rate
* Tickets by Support Category
* Tickets by Priority
* Critical Tickets by Category
* Security Issues by Category

### 2. Priority & Risk Analysis

Focus:

> Why are these tickets risky, and where is operational risk concentrated?

Key metrics include:

* Medium Tickets
* Security Tickets
* Work-Blocked Tickets
* Business-Critical Tickets
* Priority by Category
* Average Urgency by Priority
* Operational Risk Indicators
* Deadline-Driven Tickets
* Work-Blocked Tickets by Category

### 3. IT Action & Investigation

Focus:

> Which tickets should the IT team investigate or act on?

Key metrics include:

* Critical Tickets
* Deadline Tickets
* Security Tickets
* Work-Blocked Tickets
* Average Urgency by Category
* Ticket Risk Profile
* High-Urgency Tickets by Category
* Operational Risk Indicators

---

## Project Documentation

Detailed project documentation is available in the `docs/` directory:

* Business Requirements Document
* Domain Document
* Data Dictionary
* ER Diagram
* KPI Documentation
* Dashboard Requirements
* Data Pipeline Documentation
* Classification Methodology
* SQL Analysis Documentation
* Dashboard User Guide
* Findings & Recommendations

---

## Project Structure

```text
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── data_cleaning.py
│   ├── inspect_dataset.py
│   ├── analyze_cleaned_data.py
│   ├── rule_classifier.py
│   ├── run_rules_only_enrichment.py
│   ├── ai_classifier.py
│   ├── run_ai_enrichment.py
│   └── test_mysql_connection.py
│
├── sql/
│   ├── create_database.sql
│   ├── create_tables.sql
│   ├── create_views.sql
│   └── analysis_queries.sql
│
├── powerbi/
│   └── IT_Support_Analytics.pbix
│
├── docs/
│
├── screenshots/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to Run

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd AI-IT-Support-Ticket-Analytics
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on `.env.example`.

```text
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=it_support_analytics
```

Do not commit `.env` to GitHub.

### 5. Run the data pipeline

```bash
python src/data_cleaning.py
python src/run_rules_only_enrichment.py
```

### 6. Load the enriched data into MySQL

Create the required database objects using the SQL scripts in the `sql/` directory.

### 7. Open the Power BI report

Open the `.pbix` file and connect it to the MySQL analytical views.

---

## Important Note on Data

The original dataset is not reproduced in this repository if redistribution rights do not permit it.

The repository contains the processing logic, SQL scripts, documentation, and dashboard implementation required to reproduce the analysis using the source dataset.

---

## Limitations

The final classification pipeline is deterministic and rule-based. It does not represent production-grade natural-language understanding.

The local LLM architecture was evaluated as an extension, but the final full-dataset pipeline uses deterministic rules because the initial rule-coverage analysis showed that the majority of tickets would require LLM processing.

Future improvements could include:

* Improved NLP-based classification
* Machine-learning ticket classification
* Human validation of classification results
* Model confidence scoring
* Historical trend analysis
* SLA breach prediction
* Automated ticket routing
* Production API integration

---

## Skills Demonstrated

**Data Analysis:** SQL, exploratory analysis, KPI development, data validation

**Data Engineering:** ETL, data cleaning, transformation, relational database design

**Programming:** Python, Pandas

**Database:** MySQL, SQL, views, primary/foreign keys

**Business Intelligence:** Power BI, DAX, dashboard design

**AI/Automation:** Rule-based classification, local LLM experimentation, automated ticket enrichment

---

## Author

**Narender Malik**

Data Analytics | SQL | Python | Power BI | MySQL

GitHub: `<your-github-profile>`

LinkedIn: `<your-linkedin-profile>`
