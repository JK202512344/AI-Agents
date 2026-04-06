from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from qa import QAEngine
from pathlib import Path
import sqlite3
import json
import os

app = FastAPI()
security = HTTPBasic()

# =========================================================
# 🔹 PATHS
# =========================================================

DATA_PATH = Path(__file__).resolve().parent.parent / "data"
CHUNK_PATH = Path(__file__).resolve().parent / "chunks"
EVAL_OUTPUT_DIR = Path(__file__).resolve().parent

# =========================================================
# 🔹 CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qa = QAEngine()

# =========================================================
# 🔹 USERS (RBAC)
# =========================================================

users_db: Dict[str, Dict[str, str]] = {
    "engineeruser": {"password": "engineer1234", "role": "engineering"},
    "marketinguser": {"password": "marketing1234", "role": "marketing"},
    "financeuser": {"password": "finance1234", "role": "finance"},
    "hruser": {"password": "hr1234", "role": "hr"},
    "ceo": {"password": "ceo1234", "role": "c_level"},
    "admin": {"password": "admin1234", "role": "admin"},
}

# =========================================================
# 🔐 AUTH
# =========================================================

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    user = users_db.get(credentials.username)

    if not user or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"username": credentials.username, "role": user["role"]}

# =========================================================
# 🔹 LOGIN
# =========================================================

@app.post("/login")
def login(user=Depends(authenticate)):
    return {
        "message": f"Welcome {user['username']}!",
        "role": user["role"]
    }

# =========================================================
# 🔹 ADMIN - USERS
# =========================================================

@app.get("/admin/users")
def get_users(user=Depends(authenticate)):
    if user["role"] != "admin":
        return {"error": "Access denied"}
    return users_db


@app.post("/admin/create-user")
def create_user(username: str, password: str, role: str, user=Depends(authenticate)):
    if user["role"] != "admin":
        return {"error": "Access denied"}

    if username in users_db:
        return {"error": "User already exists"}

    users_db[username] = {"password": password, "role": role}

    return {"message": f"User {username} created successfully"}


@app.post("/admin/reset-password")
def reset_password(username: str, new_password: str, user=Depends(authenticate)):
    if user["role"] != "admin":
        return {"error": "Access denied"}

    if username not in users_db:
        return {"error": "User not found"}

    users_db[username]["password"] = new_password

    return {"message": f"Password reset for {username}"}


@app.post("/admin/delete-users")
def delete_users(users: str, user=Depends(authenticate)):
    if user["role"] != "admin":
        return {"error": "Access denied"}

    for u in users.split(","):
        users_db.pop(u, None)

    return {"message": "Users deleted"}

# =========================================================
# 🔹 CHAT
# =========================================================

@app.post("/chat")
def chat(message: str, user=Depends(authenticate)):
    try:
        response = qa.run(
            message,
            role=user["role"],
            username=user["username"]
        )

        return {
            "answer": response["answer"],
            "sources": response.get("sources", []),
            "route": response.get("route", "unknown"),
            "role": user["role"],
            "collections": response.get("collections", []),
            "guardrail_triggered": response.get("guardrail", False),
        }

    except PermissionError:
        return {"error": "Access denied"}

    except Exception as e:
        return {"error": str(e)}

# =========================================================
# 🔹 QUERY LOGS
# =========================================================

@app.get("/admin/query-logs")
def get_query_logs(user=Depends(authenticate)):
    if user["role"] != "admin":
        return {"error": "Access denied"}

    conn = sqlite3.connect("queries.db")
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT id, timestamp, username, role, query, route, answer, guardrail
        FROM queries
        ORDER BY id DESC
        LIMIT 100
    """).fetchall()

    return {"logs": [dict(r) for r in rows]}

# =========================================================
# 🔹 DOCUMENTS
# =========================================================

@app.get("/admin/documents")
def get_documents():
    documents = []

    if not DATA_PATH.exists():
        return {"documents": []}

    for folder in DATA_PATH.iterdir():
        if folder.is_dir():
            for file in folder.iterdir():
                if file.is_file():

                    base_name = file.stem
                    chunk_file = CHUNK_PATH / f"{base_name}.json"

                    chunk_count = 0

                    if chunk_file.exists():
                        try:
                            with open(chunk_file, "r", encoding="utf-8") as f:
                                chunk_count = len(json.load(f))
                        except:
                            chunk_count = 0

                    documents.append({
                        "name": file.name,
                        "folder": folder.name,
                        "chunk_count": chunk_count
                    })

    return {"documents": documents}

# =========================================================
# 🔹 UPLOAD
# =========================================================

@app.post("/admin/upload-doc")
def upload_doc(files: List[UploadFile] = File(...), user=Depends(authenticate)):
    if user["role"] != "admin":
        return {"error": "Access denied"}

    DATA_PATH.mkdir(exist_ok=True)

    for file in files:
        file_path = DATA_PATH / file.filename

        with open(file_path, "wb") as f:
            f.write(file.file.read())

    return {"message": "Files uploaded successfully"}

# =========================================================
# 🔹 REINDEX
# =========================================================

@app.post("/admin/reindex")
def reindex(user=Depends(authenticate)):
    if user["role"] != "admin":
        return {"error": "Access denied"}

    from ingest import load_all_files

    load_all_files()

    return {"message": "Reindex completed"}

# =========================================================
# 🔹 EVALUATION ENDPOINTS
# =========================================================

@app.get("/admin/eval-results")
def get_eval_results(mode: str = "full", user=Depends(authenticate)):
    """
    Load previously saved evaluation results.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    json_path = EVAL_OUTPUT_DIR / f"ragas_{mode}.json"

    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"No evaluation results found for mode: {mode}")

    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading eval results: {str(e)}")


@app.post("/admin/run-eval")
def run_eval_endpoint(mode: str = "full", user=Depends(authenticate)):
    """
    Run RAGAS evaluation.
    
    Args:
        mode: Evaluation mode - "full", "no_guardrails", or "no_structured"
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    if mode not in ["full", "no_guardrails", "no_structured"]:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}. Must be 'full', 'no_guardrails', or 'no_structured'")

    try:
        from ragas_evals import run_eval
        result = run_eval(mode=mode, save_results=True)
        return result
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Failed to import ragas_evals: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.post("/admin/run-ablation")
def run_ablation_endpoint(user=Depends(authenticate)):
    """
    Run ablation study comparing all evaluation modes.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        from ragas_evals import run_ablation
        result = run_ablation()
        return result
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Failed to import ragas_evals: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ablation study failed: {str(e)}")


@app.get("/admin/evals")
def get_evals():
    """Legacy endpoint for backward compatibility."""
    file_path = EVAL_OUTPUT_DIR / "ragas_full.json"

    if not file_path.exists():
        return {"error": "No eval data found. Run evaluation first."}

    with open(file_path, "r") as f:
        data = json.load(f)

    return data
