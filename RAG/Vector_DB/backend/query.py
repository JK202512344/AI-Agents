"""
query.py

User-facing CLI for interacting with QAEngine
"""

from qa import QAEngine


VALID_ROLES = {"finance", "engineering", "hr", "marketing", "c_level"}


def get_valid_role(prompt: str = "Enter your role") -> str:
    """Prompt user until a valid role is entered.
    Accepts both plain role names ('hr') and prefixed form ('role hr').
    """
    while True:
        raw = input(f"{prompt} ({'/'.join(sorted(VALID_ROLES))}): ").strip().lower()

        # Strip accidental 'role ' prefix — users often type it here too
        role = raw[5:].strip() if raw.startswith("role ") else raw

        if role in VALID_ROLES:
            return role

        print(f"Invalid role '{role}'. Choose from: {', '.join(sorted(VALID_ROLES))}")


def handle_role_switch(command: str, current_role: str) -> str:
    """Handle role switching command."""
    parts = command.split()

    if len(parts) != 2:
        print(f"Usage: role <{'|'.join(VALID_ROLES)}>")
        return current_role

    new_role = parts[1].lower()

    if new_role not in VALID_ROLES:
        print("Invalid role")
        return current_role

    print(f"Role updated to: {new_role}")
    return new_role


def main():
    print("Starting CLI...")
    try:
        qa = QAEngine()
        print("QAEngine initialized")
    except Exception as e:
        print("Failed to initialize QAEngine:", e)
        return

    try:
        # Ask role first
        user_role = get_valid_role()

        while True:
            question = input(
                "\nAsk a question (or 'exit' / 'role <new_role>'): "
            ).strip()

            if not question:
                continue

            if question.lower() == "exit":
                print("Exiting...")
                break

            # Handle role switching
            if question.lower().startswith("role "):
                user_role = handle_role_switch(question, user_role)
                continue

            # Normal QA flow
            try:
                if len(question.strip()) < 5:
                    print("Please provide a more specific query.")
                    continue
                #answer, context = qa.rag(question, user_role=user_role)
                answer, context, route, guardrail = qa.rag(question, user_role=user_role)

                print("\n🤖 ANSWER:\n", answer)
                print(f"Route: {route} | Guardrail triggered: {guardrail}")

                # 🔥 Hide sources for guardrail / no-info responses
                if (context
                        and "i can only answer finsolve-related queries" not in answer.lower()
                        and "i don't have information" not in answer.lower()):
                    print("\n📚 SOURCES:\n", context)

            except Exception as e:
                print(f"Error while processing question: {e}")

    finally:
        qa.close()


if __name__ == "__main__":
    main()