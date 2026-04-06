"""
structured_query.py

Handles intelligent CSV queries (robust + safe version)
"""

import re
from typing import Optional


class StructuredQueryEngine:
    def __init__(self, client, collection_name: str = "docs"):
        self.client = client
        self.collection_name = collection_name

        # ✅ Centralized field mapping
        self.field_map = {
            "name": "full_name",
            "age": "date_of_birth",
            "email": "email",
            "attendance": "attendance_pct",
            "performance": "performance_rating",
            "review": "last_review_date",
            "location": "location",
            "join": "date_of_joining",
            "joining": "date_of_joining",
            "status": "employment_status",
            "mobile": "phone",
            "phone": "phone",
            "type": "employee_type",
            "exit": "exit_date",
            "manager": "manager_id",
            "role": "role",
            "designation": "designation_level",
            "department": "department",
            "salary": "salary",
            "leave balance": "leave_balance",
            "leaves taken": "leaves_taken",
        }

    # --------------------------------------------------
    # 🔍 Extract Employee ID (e.g., FINEMP1009)
    # --------------------------------------------------
    def extract_id(self, query: str) -> Optional[str]:
        match = re.search(r"\b[A-Z]+\d{3,}\b", query.upper())
        return match.group(0) if match else None

    # --------------------------------------------------
    # 🔍 Extract requested field safely
    # --------------------------------------------------
    def extract_field(self, query: str) -> Optional[str]:
        query = query.lower()

        for key, value in self.field_map.items():
            # ✅ Exact word / phrase match (no substring bugs)
            if re.search(rf"\b{re.escape(key)}\b", query):
                return value

        return None

    # --------------------------------------------------
    # 🔍 Convert CSV row string → dict
    # --------------------------------------------------
    def parse_row(self, row_text: str) -> dict:
        data = {}

        for item in row_text.split(","):
            if ":" in item:
                key, value = item.split(":", 1)
                data[key.strip().lower()] = value.strip()

        return data

    # --------------------------------------------------
    # 🚀 Main query function
    # --------------------------------------------------
    def query(self, query: str):
        emp_id = self.extract_id(query)
        field = self.extract_field(query)

        if not emp_id:
            return None  # Let RAG handle it

        # 🔍 Fetch all rows (could optimize later)
        results, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=2000,
            with_payload=True,
        )

        for point in results:
            payload = point.payload
            text = payload.get("chunk_text", "").lower()

            # ✅ Match employee ID
            if f"employee_id: {emp_id.lower()}" in text:

                row_data = payload.get("content", "")
                parsed = self.parse_row(row_data)

                # ✅ If no specific field → return full row
                if not field:
                    return row_data

                # ✅ Return clean value
                value = parsed.get(field.lower())

                if value:
                    return f"{field}: {value}"

                return "Field not found for this employee."

        return "No matching data found."