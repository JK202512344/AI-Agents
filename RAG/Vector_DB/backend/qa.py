"""
qa.py

FINAL FIXED VERSION:
- Guardrails applied to BOTH structured + RAG
- No PII leakage
- Fixed _clean_answer
- Stable pipeline
"""

import os
import re
import time
import unicodedata
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

from router import route_query
from guardrails import Guardrails
from retriever import Retriever
from structured_query import StructuredQueryEngine
from prompts import SYSTEM_PROMPT, RAG_USER_TEMPLATE
from queries_logger import QueryLogger

load_dotenv(dotenv_path="../config/db.env")

GROQ_MODEL = "llama-3.3-70b-versatile"


# ---------------------------
# CLEAN ANSWER (FIXED)
# ---------------------------
import unicodedata
import re

def _clean_answer(text: str) -> str:
    if not text:
        return text

    # Remove warnings
    lines = [l for l in text.split("\n") if not l.strip().startswith("⚠️")]
    text = "\n".join(lines)

    text = unicodedata.normalize("NFKC", text)

    # 🔥 Convert comma-separated fields → new lines
    if "," in text and "employee_id" in text:
        parts = [p.strip() for p in text.split(",")]
        text = "\n".join(parts)

    # 🔥 Beautify keys (optional but clean)
    text = re.sub(r"_", " ", text)

    # Capitalize field names
    lines = []
    for line in text.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip().title()
            val = val.strip()
            lines.append(f"{key}: {val}")
        else:
            lines.append(line)

    return "\n".join(lines).strip()

class QAEngine:
    def __init__(self):
        self.qdrant_client = QdrantClient(path="./qdrant_db")
        self.guardrails = Guardrails()

        print("[QAEngine] Loading embedder...")
        self._embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")

        self.retriever = Retriever(self.qdrant_client, embedder=self._embedder)
        self.structured = StructuredQueryEngine(self.qdrant_client)

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        self.llm_client = Groq(api_key=api_key)
        self.logger = QueryLogger()

        print("✅ QAEngine ready")

    def rag(
        self,
        query: str,
        user_role: str = "c_level",
        top_k: int = 5,
        skip_guardrails: bool = False,
        skip_routing: bool = False,
    ):
        """Core RAG pipeline"""

        query = query.lower().replace("&", "and").strip()
        route = "unknown"

        # ---------------- STEP 1: INPUT GUARDRAILS ----------------
        if not skip_guardrails:
            allowed, message = self.guardrails.check_input(query)
            if not allowed:
                return message, "", route, True

        # ---------------- STEP 2: ROUTING ----------------
        if not skip_routing:
            routing = route_query(query, user_role)

            route = routing.get("route", "unknown")
            print(f"[ROUTER] Route: {route} | Role: {user_role}")

            if not routing.get("allowed", True):
                return routing.get("message", "Access denied"), "", route, True

        # ---------------- STEP 3: STRUCTURED QUERY ----------------
        structured_answer = self.structured.query(query)

        if structured_answer and structured_answer not in (
            "No matching data found.",
            "Field not found for this employee.",
            None,
        ):
            raw_answer = structured_answer

            # ✅ APPLY OUTPUT GUARDRAILS HERE (CRITICAL FIX)
            if not skip_guardrails:
                _, safe_answer = self.guardrails.check_output(
                    raw_answer, "", user_role
                )
                answer = safe_answer
            else:
                answer = raw_answer

            answer = _clean_answer(answer)

            return answer, raw_answer, route, False

        # ---------------- STEP 4: RETRIEVAL ----------------
        chunks = self.retriever.retrieve(query, top_k=top_k)

        if not chunks:
            return "Not found", "", route, False

        context = self.retriever.build_context(chunks)

        # ---------------- STEP 5: LLM ----------------
        user_message = RAG_USER_TEMPLATE.format(context=context, query=query)

        response = self.llm_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
        )

        raw_answer = response.choices[0].message.content

        # ---------------- STEP 6: OUTPUT GUARDRAILS ----------------
        if not skip_guardrails:
            _, safe_answer = self.guardrails.check_output(
                raw_answer, context, user_role
            )
            answer = safe_answer
        else:
            answer = raw_answer

        answer = _clean_answer(answer)

        return answer, context, route, False

    def run(self, query: str, role: str = "c_level", username: str = "unknown"):
        start_time = time.time()

        answer, context, route, guardrail = self.rag(
            query=query,
            user_role=role,
        )

        latency = round(time.time() - start_time, 3)

        sources = []
        if context:
            sources = re.findall(r"\[Source \d+ \| (.+?) \|", context)

        try:
            self.logger.log(
                username=username,
                role=role,
                query=query,
                route=route,
                answer=answer,
                sources=sources,
                guardrail=guardrail,
            )
        except Exception as e:
            print(f"[Logger Error] {e}")

        return {
            "answer": answer,
            "sources": sources,
            "route": route,
            "collections": ["docs"],
            "guardrail": guardrail,
            "latency": latency,
        }

    def close(self):
        try:
            self.retriever.close()
        except Exception:
            pass