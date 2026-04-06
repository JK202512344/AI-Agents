"""
router.py

Semantic routing + RBAC.

Performance fix: uses the shared Qwen encoder instead of loading a
second copy. Cuts cold-start time by 4–10 s.
"""

from semantic_router import Route, SemanticRouter
from shared_encoder import get_encoder   # ← shared singleton


finance_route = Route(
    name="finance_route",
    utterances=[
        "What was FinSolve's revenue growth in 2024",
        "What was the total cost of vendor services",
        "What is the company's gross margin",
        "What was the cash flow from operations",
        "What is the Days Sales Outstanding",
        "What was the total annual revenue",
        "Quarterly financial report",
        "key Performance Indicators",
        "Q1/Q2/Q3/Q4 Strategic Highlights"
        "Budget allocation",
        "Profit and loss statement",
        "Invoice to pay process",
        "Balance sheet",
        "TECHNOLOGY DEPARTMENT",
        "OPERATIONS & SUPPLY CHAIN DEPARTMENT",
        "EBITDA",
        "Key Performance Indicators for quarter/year/Annual/semi annual",
        "Financial projections",
        "Investment returns",
        "Operating expenses",
        "Capital expenditure",
        "Financial metrics",
        "Revenue breakdown",
        "Negotiation Strategy",
        "Vendor",
        "Risk Analysis",
    ],
)

engineering_route = Route(
    name="engineering_route",
    utterances=[
        "What architecture does FinSolve use",
        "Company Overview",
        "about company",
        "business overview",
        "Which database is used for transactional data",
        "What protocol is used for authentication",
        "What is the target API response time",
        "What is the disaster recovery RTO",
        "What technology stack is used",
        "How is the system deployed",
        "What are the security protocols",
        "Show me the API documentation",
        "What is the incident response procedure",
        "System architecture",
        "Technical specifications",
        "Database schema",
        "Infrastructure details",
        "DevOps pipeline",
        "CI/CD process",
        "Deployment",
        "Server configuration",
        "Cloud infrastructure",
        "Microservices architecture",
    ],
)

marketing_route = Route(
    name="marketing_route",
    utterances=[
        "What was the Q1 marketing spend",
        "What was the customer acquisition target",
        "What ROI was achieved in the campaign",
        "How many InstantPay sign-ups were achieved",
        "What conversion rate was achieved",
        "What was the Q4 marketing budget",
        "Marketing campaign results",
        "Brand awareness metrics",
        "Customer acquisition cost",
        "Lead generation numbers",
        "Social media engagement",
        "Marketing analytics",
        "Campaign performance",
        "Market share",
        "Advertising spend",
        "Digital marketing metrics",
    ],
)

hr_route = Route(
    name="hr_route",
    utterances=[
        "What is the full name of employee",
        "Who is employee FINEMP1001",
        "Find employee by ID",
        "Get employee details",
        "Show me employee information",
        "Employee with ID",
        "Look up employee",
        "Search for employee",
        "Find staff member",
        "What is the name of FINEMP",
        "full name of FINEMP",
        "employee FINEMP",
        "details of FINEMP",
        "information about FINEMP",
        "Who is Aadhya Patel",
        "Find Aadhya",
        "Details of Aadhya Patel",
        "Information about employee named",
        "Find employee by name",
        "Leave Balance by name",
        "Performance by name",
        "Who works in sales",
        "Employees in engineering department",
        "List marketing team members",
        "Staff in finance department",
        "Which department does employee work in",
        "What department is employee in",
    ],
)

general_route = Route(
    name="general_route",
    utterances=[
        "How many sick leave days are allowed per year",
        "When is salary credited each month",
        "Termination Process",
        "What is the standard work duration per day",
        "How long is maternity leave",
        "What is the vacation policy",
        "What is the leave policy",
        "Employee Onboarding & Benefits",
        "Company holiday calendar",
        "Work from home policy",
        "What is EPF",
        "Dress code",
        "Office timings",
        "Reimbursement process",
        "Travel policy",
        "Code of conduct",
        "Ethics policy",
        "Employee benefits",
        "Health insurance policy",
    ],
)

# Build router once at import time using the shared encoder
router = SemanticRouter(
    encoder=get_encoder(),
    routes=[
        finance_route,
        engineering_route,
        marketing_route,
        hr_route,
        general_route,
    ],
    auto_sync="local",
)

ROLE_ACCESS = {
    "finance":     ["finance_route", "general_route"],
    "engineering": ["engineering_route", "general_route"],
    "marketing":   ["marketing_route", "general_route"],
    "hr":          ["hr_route", "general_route"],
    "c_level": [
        "finance_route", "engineering_route", "marketing_route",
        "general_route", "hr_route",
    ],
}


def route_query(query: str, user_role: str):
    route = router(query).name
    print(f"  Route detected: {route}")
    allowed_routes = ROLE_ACCESS.get(user_role, [])
    if route not in allowed_routes:
        return {
            "route": route,
            "allowed": False,
            "message": f"Access denied: {user_role} cannot access {route}",
        }
    return {"route": route, "allowed": True, "message": f"Routed to {route}"}
