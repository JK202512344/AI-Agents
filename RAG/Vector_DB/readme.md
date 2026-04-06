# FinSolve Enterprise RAG System

A production-style **Role-Based RAG (Retrieval-Augmented Generation) system** built for a financial company (FinSolve).

This project simulates how real enterprise AI assistants work — with **security, access control, and guardrails**.

---

# What This System Does

* Answers employee questions using company documents
* Enforces **role-based access (RBAC)**
* Prevents **prompt injection & misuse**
* Supports **structured queries (like employee lookup)**
* Ensures answers come only from company knowledge

---

# System Architecture (Simple View)

'''
User → Guardrails → Router → (Structured OR RAG) → LLM → Answer
'''

---

# File-by-File Explanation (ELI5 Style)

---

## query.py → CLI Interface (User Interaction)

This is the **entry point**

What it does:

* Takes user input
* Lets user set role (HR, Finance, etc.)
* Sends question to QAEngine
* Prints answer + sources

Think of it as:

> “Chat window for the user”

---

## 'qa.py' → Brain of the System

This is the **main pipeline**

What it does:

1. Runs **guardrails** (safety checks)
2. Routes the query (HR / Finance / etc.)
3. Checks **structured data first**
4. If not found → runs **RAG (vector search)**
5. Sends context to LLM (Groq)
6. Applies output checks

Think of it as:

> “Decision maker + orchestrator”

---

## 'guardrails.py' → Security Layer

This protects the system

### Input Guardrails:

* Blocks off-topic questions (jokes, weather, etc.)
* Blocks prompt injection (“ignore instructions”)
* Blocks harmful queries (fraud, hacking)
* Detects PII (email, Aadhaar, phone)
* Allows employee ID queries (FINEMP1009)

### Output Guardrails:

* Detects hallucinated numbers
* Prevents cross-role data leakage
* Ensures sources exist

Think of it as:

> “Security guard at the gate”

---

## 'router.py' → Smart Traffic Controller

Decides **which department** the query belongs to

Examples:

* "salary" → Finance
* "leave policy" → HR
* "system design" → Engineering

Also enforces:

* Role-Based Access Control (RBAC)
* Blocks unauthorized access

Think of it as:

> “Which department should answer this?”

---

## 'retriever.py' → Document Search Engine

Finds relevant content from documents

What it does:

* Converts query → embeddings
* Searches in Qdrant (vector DB)
* Returns top relevant chunks
* Builds context for LLM

Think of it as:

> “Google search for internal documents”

---

## 'structured_query.py' → Database-like Queries

Handles **exact data lookups**

Examples:

* "email of FINEMP1009"
* "salary of FINEMP1012"

What it does:

* Extracts employee ID
* Extracts requested field (email, salary, etc.)
* Searches stored data
* Returns exact value

Think of it as:

> "SQL for employees (but simple)"

---

## 'vectordb.py' → Vector Database Setup

Handles Qdrant DB

What it does:

* Stores embeddings
* Manages collections
* Supports search queries

Think of it as:

> "Memory storage for documents"

---

## 'chunker.py' → Document Splitter

Breaks large documents into small chunks

Why?

* LLMs work better with small pieces
* Improves retrieval accuracy

Think of it as:

> "Cutting a book into readable pages"

---

## 'ingest.py' → Data Loader

Loads documents into vector DB

What it does:

* Reads PDFs / CSV / DOCX
* Splits into chunks
* Converts to embeddings
* Stores in Qdrant

Think of it as:

> "Feeding knowledge into the system"

---

##  'prompts.py' → LLM Rules
Controls how the LLM behaves

Rules:

* Answer only from context
* Be concise
* No hallucination
* No external knowledge

Think of it as:

> "Instructions given to the AI"

---

# Key Features

### Role-Based Access Control (RBAC)

* HR cannot access Finance data
* Engineering cannot access HR records

---

### Guardrails (Safety)

* Blocks prompt injection
* Blocks off-topic queries
* Prevents misuse

---

### Structured + RAG Hybrid

* Structured → exact answers
* RAG → contextual answers

---

### Source Grounding

* Every answer backed by documents
* No hallucinated responses

---

# Example Behavior

| Query                           | Result            |
| ------------------------------- | ----------------- |
| What is EPF                     | Answer            |
| Email of FINEMP1009             | Structured answer |
| Tell me a joke                  | Blocked           |
| What is LLM                     | Blocked           |
| Salary of employee (wrong role) | Access denied     |

---

# Key Learnings

* Guardrails should be **strict but not over-blocking**
* Routing is critical for **correct data access**
* Retrieval quality affects **answer quality**
* Structured queries improve **accuracy**

---

# How to Run

'''bash
python query.py
'''

---

# Final Thought

This project simulates a **real enterprise AI assistant**:

* Secure
* Role-based access
* Context-grounded
* Reliable
