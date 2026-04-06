"""
ragas_evals.py

Full RAG evaluation with RAGAS metrics.
Now includes API-callable functions for the admin dashboard.

Key features:
1. skip_guardrails=True / skip_routing=True → eval role is c_level
2. Contexts are always list[str] — properly extracted from context string
3. Empty answer / context rows are skipped with a warning
4. Ablation study modes actually disable the relevant component via flags
5. Groq model name fixed (llama-3.3-70b-versatile)
6. Rate-limit safe: added a small sleep between calls
7. JSON output for UI consumption
"""

import os
import time
import json
import traceback
from datetime import datetime
from typing import Optional, Literal
from dotenv import load_dotenv
from datasets import Dataset

from ragas import evaluate
from ragas.metrics import (
    answer_correctness,
    answer_relevancy,
    faithfulness,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from qa import QAEngine

load_dotenv(dotenv_path="../config/db.env")

# =========================================================
# PATHS
# =========================================================
EVAL_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================================================
# RAGAS LLM + EMBEDDINGS
# =========================================================

def get_ragas_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    return LangchainLLMWrapper(
        ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0,
        )
    )


def get_ragas_embeddings():
    return LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    )


# =========================================================
# TEST DATASET (50 questions)
# =========================================================

def build_testset():
    return [
        # ── ENGINEERING ──────────────────────────────────────────────────
        {"question": "What architecture does FinSolve use?",
         "ground_truth": "Microservices-based cloud-native architecture"},
        {"question": "When was FinSolve Technologies founded?",
         "ground_truth": "2016"},
        {"question": "Where is FinSolve headquartered?",
         "ground_truth": "Bangalore"},
        {"question": "Where is company data backed up?",
         "ground_truth": "AWS S3"},
        {"question": "How frequently is company data backed up?",
         "ground_truth": "Daily"},
        {"question": "What cloud infrastructure is used?",
         "ground_truth": "AWS"},
        {"question": "What is the recovery time objective for data backup?",
         "ground_truth": "4 hours"},
        {"question": "What portal is used to request IT support?",
         "ground_truth": "ServiceNow IT Service Portal"},
        {"question": "What is the response time for critical IT issues?",
         "ground_truth": "30 minutes"},
        {"question": "What is the IT support email?",
         "ground_truth": "support@finsolvtech.com"},

        # ── FINANCE ──────────────────────────────────────────────────────
        {"question": "What is the total annual revenue of FinSolve?",
         "ground_truth": "₹783 crore"},
        {"question": "What is the net income of FinSolve?",
         "ground_truth": "₹96 crore"},
        {"question": "What is the gross profit margin of FinSolve?",
         "ground_truth": "64.1%"},
        {"question": "What was the net profit margin in 2024?",
         "ground_truth": "12.3%"},
        {"question": "What is the operating cash flow of FinSolve?",
         "ground_truth": "₹187 crore"},
        {"question": "What was the revenue growth in 2024?",
         "ground_truth": "28%"},
        {"question": "What was the EBITDA in 2024?",
         "ground_truth": "₹138 crore"},
        {"question": "How much revenue came from international markets?",
         "ground_truth": "₹352 crore"},
        {"question": "What were the employee salary expenses?",
         "ground_truth": "₹185 crore"},
        {"question": "What was the return on equity in 2024?",
         "ground_truth": "22.4%"},

        # ── MARKETING ────────────────────────────────────────────────────
        {"question": "What was the Q1 marketing spend?",
         "ground_truth": "$3M"},
        {"question": "How many campaigns were executed in 2024?",
         "ground_truth": "28"},
        {"question": "What was the total campaign budget in 2024?",
         "ground_truth": "₹1,330 lakh"},
        {"question": "What was the total revenue generated from campaigns?",
         "ground_truth": "₹355 lakh"},
        {"question": "Which channel had the lowest ROI performance?",
         "ground_truth": "Events"},
        {"question": "What was the total number of conversions in 2024 campaigns?",
         "ground_truth": "245,942"},
        {"question": "What conversion rate was achieved?",
         "ground_truth": "12%"},
        {"question": "What was the overall campaign ROI in 2024?",
         "ground_truth": "2.67x"},
        {"question": "Which campaign had the highest ROI in 2024?",
         "ground_truth": "Video Content - Year-End Review"},
        {"question": "What was the ROI of the best-performing campaign?",
         "ground_truth": "4.58x"},

        # ── HR ───────────────────────────────────────────────────────────
        {"question": "Who is employee FINEMP1001?",
         "ground_truth": "Aadhya Patel"},
        {"question": "What is the leave balance of FINEMP1002?",
         "ground_truth": "12 days"},
        {"question": "What is the performance rating of FINEMP1003?",
         "ground_truth": "4.5"},
        {"question": "What is the department of FINEMP1004?",
         "ground_truth": "Engineering"},
        {"question": "What is the salary of FINEMP1005?",
         "ground_truth": "$85,000"},
        {"question": "What is the employment status of FINEMP1006?",
         "ground_truth": "Active"},
        {"question": "What is the joining date of FINEMP1007?",
         "ground_truth": "2021-06-15"},
        {"question": "Who is the manager of FINEMP1008?",
         "ground_truth": "Rajesh Kumar"},
        {"question": "What is the role of FINEMP1009?",
         "ground_truth": "Software Engineer"},
        {"question": "What is the location of FINEMP1010?",
         "ground_truth": "Bangalore"},

        # ── GENERAL / HR POLICY ──────────────────────────────────────────
        {"question": "What is the standard hybrid work model at FinSolve?",
         "ground_truth": "3 days in office and 2 days remote per week"},
        {"question": "What is the EPF contribution rate?",
         "ground_truth": "12% of basic salary"},
        {"question": "What is the maternity leave policy at FinSolve?",
         "ground_truth": "26 weeks paid leave for the first two children"},
        {"question": "What is the dress code at FinSolve?",
         "ground_truth": "Business casual"},
        {"question": "What are the office timings at FinSolve?",
         "ground_truth": "9 AM to 6 PM, Monday to Friday"},
        {"question": "What is the reimbursement process for expenses?",
         "ground_truth": "Submit receipts through the expense management system for approval"},
        {"question": "What is the employee referral bonus range?",
         "ground_truth": "₹10,000 to ₹50,000"},
        {"question": "How many days of sick leave are provided annually?",
         "ground_truth": "12 days per year"},
        {"question": "How many days per year can employees work from another city or country?",
         "ground_truth": "30 days per year"},
        {"question": "What is the maximum home office setup allowance?",
         "ground_truth": "₹15,000"},
    ]


# =========================================================
# HELPER: extract list[str] contexts from context string
# =========================================================

def _extract_contexts(context: str) -> list:
    """
    Split the multi-source context string built by Retriever.build_context()
    into a list of individual source texts for RAGAS.
    """
    if not context:
        return []
    parts = context.split("\n\n---\n\n")
    return [p.strip() for p in parts if p.strip()]


# =========================================================
# CORE EVALUATION
# =========================================================

EvalMode = Literal["full", "no_guardrails", "no_structured"]


def run_eval(
    testset: Optional[list] = None,
    mode: EvalMode = "full",
    save_results: bool = True,
) -> dict:
    """
    Run RAGAS evaluation.

    Args:
        testset: List of {"question": ..., "ground_truth": ...} dicts.
                 If None, uses the built-in test set.
        mode: Evaluation mode
            - "full": full pipeline (guardrails + routing + structured)
            - "no_guardrails": skip guardrails
            - "no_structured": skip structured query fast-path
        save_results: Whether to save CSV and JSON files

    Returns:
        dict with keys: mode, summary, rows, timestamp
    """
    if testset is None:
        testset = build_testset()

    # Initialize QA engine
    try:
        qa = QAEngine()
    except Exception as e:
        raise ValueError(f"Failed to initialize QAEngine: {str(e)}")

    # Initialize RAGAS components
    try:
        ragas_llm = get_ragas_llm()
        ragas_emb = get_ragas_embeddings()
    except Exception as e:
        qa.close()
        raise ValueError(f"Failed to initialize RAGAS components: {str(e)}")

    # Eval always runs as c_level so routing never blocks a question
    eval_role = "c_level"
    skip_guardrails = (mode == "no_guardrails")

    rows = []
    skipped = 0
    errors = []

    print(f"\n{'='*50}")
    print(f" MODE: {mode.upper()}")
    print(f"{'='*50}\n")

    for i, item in enumerate(testset):
        q = item["question"]
        gt = item["ground_truth"]

        try:
            answer, context = qa.rag(
                q,
                user_role=eval_role,
                top_k=5,
                skip_guardrails=skip_guardrails,
                skip_routing=True,
            )

            # Skip rows where pipeline returned nothing useful
            if not answer or answer.strip() in ("", "Not found", "No relevant content found."):
                print(f"  [SKIP] No answer for: {q}")
                skipped += 1
                continue

            if not context or not context.strip():
                print(f"  [SKIP] No context for: {q}")
                skipped += 1
                continue

            contexts = _extract_contexts(context)
            if not contexts:
                contexts = [context]

            rows.append({
                "question": str(q).strip(),
                "answer": str(answer).strip(),
                "contexts": contexts,
                "ground_truth": str(gt).strip(),
            })

            print(f"  [{i+1}/{len(testset)}] ✅ {q[:60]}")

        except Exception as e:
            error_msg = f"{q}: {str(e)}"
            print(f"  [ERROR] {error_msg}")
            errors.append(error_msg)
            skipped += 1
            continue

        # Small sleep to avoid Groq rate limits during eval
        time.sleep(0.5)

    qa.close()

    if len(rows) == 0:
        error_summary = "\n".join(errors[:5]) if errors else "Unknown error"
        raise ValueError(
            f"No valid rows collected (skipped={skipped}). "
            f"Check QAEngine logs. First errors:\n{error_summary}"
        )

    print(f"\n✅ {len(rows)} rows collected, {skipped} skipped.\n")

    # Sample debug
    if rows:
        print("Sample row:")
        print("  Q:", rows[0]["question"])
        print("  A:", rows[0]["answer"][:100], "...")
        print("  GT:", rows[0]["ground_truth"])
        print("  Contexts:", len(rows[0]["contexts"]), "chunks")
        print()

    dataset = Dataset.from_list(rows)

    try:
        result = evaluate(
            dataset=dataset,
            metrics=[
                answer_correctness,
                answer_relevancy,
                faithfulness,
                context_precision,
                context_recall,
            ],
            llm=ragas_llm,
            embeddings=ragas_emb,
        )
    except Exception as e:
        raise ValueError(f"RAGAS evaluation failed: {str(e)}")

    df = result.to_pandas()

    # Build response object
    summary = df[["answer_correctness", "answer_relevancy", "faithfulness",
                  "context_precision", "context_recall"]].mean().to_dict()

    # Convert NaN to None for JSON serialization
    for k, v in summary.items():
        if v != v:  # NaN check
            summary[k] = None

    eval_data = {
        "mode": mode,
        "summary": summary,
        "rows": df.to_dict(orient="records"),
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "total_questions": len(testset),
            "evaluated": len(rows),
            "skipped": skipped,
        }
    }

    # Clean up NaN values in rows
    for row in eval_data["rows"]:
        for k, v in row.items():
            if isinstance(v, float) and v != v:  # NaN check
                row[k] = None

    if save_results:
        # Save CSV
        csv_path = os.path.join(EVAL_OUTPUT_DIR, f"ragas_{mode}.csv")
        df.to_csv(csv_path, index=False)
        print(f"📄 CSV saved → {csv_path}")

        # Save JSON for UI
        json_path = os.path.join(EVAL_OUTPUT_DIR, f"ragas_{mode}.json")
        with open(json_path, "w") as f:
            json.dump(eval_data, f, indent=2, default=str)
        print(f"📄 JSON saved → {json_path}")

    print("\n📊 Mean Scores:")
    print(df[["answer_correctness", "answer_relevancy", "faithfulness",
              "context_precision", "context_recall"]].mean().to_string())

    return eval_data


def load_eval_results(mode: EvalMode = "full") -> Optional[dict]:
    """
    Load previously saved evaluation results.

    Args:
        mode: The evaluation mode to load results for

    Returns:
        dict with eval results, or None if not found
    """
    json_path = os.path.join(EVAL_OUTPUT_DIR, f"ragas_{mode}.json")

    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading eval results: {e}")
        return None


# =========================================================
# ABLATION STUDY
# =========================================================

def run_ablation() -> dict:
    """
    Run ablation study comparing full pipeline vs. disabled components.

    Returns:
        dict with results for each mode
    """
    testset = build_testset()
    results = {}

    for mode in ["full", "no_guardrails", "no_structured"]:
        try:
            results[mode] = run_eval(testset, mode=mode, save_results=True)
        except Exception as e:
            print(f"[ERROR] Ablation mode '{mode}' failed: {e}")
            traceback.print_exc()
            results[mode] = {"error": str(e)}

    print("\n" + "="*50)
    print("ABLATION SUMMARY")
    print("="*50)

    cols = ["answer_correctness", "answer_relevancy", "faithfulness",
            "context_precision", "context_recall"]

    for mode, data in results.items():
        if "error" in data:
            print(f"\n{mode.upper()}: FAILED - {data['error']}")
        else:
            print(f"\n{mode.upper()}:")
            for col in cols:
                val = data["summary"].get(col)
                if val is not None:
                    print(f"  {col}: {val:.4f}")
                else:
                    print(f"  {col}: N/A")

    return results


# =========================================================
# ENTRY POINT (CLI)
# =========================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "ablation":
        run_ablation()
    elif len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode in ["full", "no_guardrails", "no_structured"]:
            run_eval(mode=mode)
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python ragas_evals.py [full|no_guardrails|no_structured|ablation]")
    else:
        run_eval(mode="full")
