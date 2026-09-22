from app.rag.retrieve import retrieve
from app.agent.reason import reason
from app.agent.router import classify_goal
from app.agent.state import AgentState
from app.utils.order_number import extract_order_number


MAX_ATTEMPTS = 3


def update_state(state: AgentState, message: str):
    """
    Update the conversation state using the latest
    customer message.
    """

    # Store conversation history
    state.conversation.append(message)

    # Extract order number if present
    order_number = extract_order_number(message)

    if order_number:
        state.order_number = order_number


def get_missing_information(state: AgentState):
    """
    Determine what information is still required
    based on the customer's goal.
    """

    missing = []

    if state.goal == "ORDER_STATUS":

        if state.order_number is None:
            missing.append("order_number")

    return missing


def ask_for_missing_information(missing_information):
    """
    Generate a follow-up question based on
    missing information.
    """

    if "order_number" in missing_information:

        return "Could you please provide your order number?"

    return "Could you please provide more information?"


def print_state(state: AgentState):
    """
    Print the current conversation state.
    """

    print("\nCurrent State:")
    print("Goal:", state.goal)
    print("Order Number:", state.order_number)
    print("Conversation:", state.conversation)


def run_agent():

    state = AgentState()

    # ==================================================
    # FIRST CUSTOMER MESSAGE
    # ==================================================

    query = input("\nCustomer: ")

    update_state(state, query)

    # ==================================================
    # ANALYZE CUSTOMER GOAL
    # ==================================================

    goal_result = classify_goal(query)

    state.goal = goal_result.get("goal")

    print("\nCustomer Goal:", state.goal)
    print("Order Number:", state.order_number)

    # ==================================================
    # HANDLE OTHER
    # ==================================================

    if state.goal == "OTHER":

        print(
            "\nAgent: I'm not sure how to help with that. "
            "Could you please provide more details?"
        )

        return

    # ==================================================
    # COLLECT REQUIRED INFORMATION
    # ==================================================

    while True:

        missing_information = get_missing_information(state)

        print("\nMissing Information:", missing_information)

        # --------------------------------------------------
        # INFORMATION IS MISSING
        # --------------------------------------------------

        if missing_information:

            question = ask_for_missing_information(
                missing_information
            )

            print("\nAgent:", question)

            query = input("\nCustomer: ")

            update_state(state, query)

            print_state(state)

            continue

        # --------------------------------------------------
        # ALL REQUIRED INFORMATION AVAILABLE
        # --------------------------------------------------

        break

    # ==================================================
    # RETRIEVAL + REASONING LOOP
    # ==================================================

    for attempt in range(1, MAX_ATTEMPTS + 1):

        print(f"\n========== ATTEMPT {attempt} ==========")

        # ==================================================
        # BUILD RETRIEVAL QUERY
        # ==================================================

        retrieval_query = f"""
            Customer goal: {state.goal}
            Order number: {state.order_number}
        """

        print("\nRetrieval Query:")
        print(retrieval_query)

        # ==================================================
        # RETRIEVE EVIDENCE
        # ==================================================

        results = retrieve(
            retrieval_query,
            top_k=3
        )

        evidence = results["documents"][0]

        print("\nRetrieved Evidence:")

        for i, document in enumerate(evidence):

            print(f"\n--- Evidence {i + 1} ---")
            print(document)

        # ==================================================
        # REASON OVER EVIDENCE
        # ==================================================

        result = reason(
            goal=state.goal,
            order_number=state.order_number,
            query=state.conversation[0],
            evidence=evidence
        )

        decision = result.get("decision")

        print("\nDecision:", decision)

        # ==================================================
        # SUFFICIENT EVIDENCE
        # ==================================================

        if decision == "SUFFICIENT":

            print("\nAgent Answer:")
            print(result.get("answer"))

            return

        # ==================================================
        # CUSTOMER INFORMATION MISSING
        # ==================================================

        if decision == "CUSTOMER_INFO_MISSING":

            print("\nCustomer information is missing:")

            print(
                result.get(
                    "missing_information"
                )
            )

            question = result.get(
                "answer",
                "Could you please provide more information?"
            )

            print("\nAgent:", question)

            query = input("\nCustomer: ")

            update_state(state, query)

            print_state(state)

            continue

        # ==================================================
        # EVIDENCE INSUFFICIENT
        # ==================================================

        if decision == "EVIDENCE_INSUFFICIENT":

            print("\nEvidence is insufficient.")

            print(
                "Reason:",
                result.get(
                    "missing_information"
                )
            )

            # --------------------------------------------------
            # RETRY RETRIEVAL
            # --------------------------------------------------

            if attempt < MAX_ATTEMPTS:

                print(
                    "\nAgent: "
                    "I couldn't find enough relevant information. "
                    "I'll try another search."
                )

                continue

            # --------------------------------------------------
            # MAX ATTEMPTS
            # --------------------------------------------------

            print(
                "\nMaximum attempts reached."
            )

            print(
                "Escalating to human support."
            )

            return

        # ==================================================
        # UNKNOWN DECISION
        # ==================================================

        print(
            "\nUnknown decision from reasoning agent."
        )

        print(
            "Escalating to human support."
        )

        return


if __name__ == "__main__":
    run_agent()