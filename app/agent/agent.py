from app.rag.retrieve import retrieve
from app.agent.reason import reason
from app.agent.router import classify_intent

MAX_ATTEMPTS = 3




def run_agent():

    query = input("\nCustomer: ")

    while True:
        intent_result = classify_intent(query)
        intent = intent_result.get("intent")

        print("Classified Intent:", intent)

        if intent == "NEED_ORDER_NUMBER":

            print("\nAgent: Could you please provide your order number?")
            query = input("\nCustomer: ")
            continue

        elif intent in ["KNOWLEDGE_QUERY", "ORDER_NUMBER_PROVIDED"]:

            break

        else:

            print("\nAgent: I'm not sure how to help with that. Could you please provide more details?")
            query = input("\nCustomer: ")
            continue
        

    for attempt in range(1, MAX_ATTEMPTS + 1):

        print(f"\n========== ATTEMPT {attempt} ==========")


        # 1. Retrieve evidence
        results = retrieve(query, top_k=3)

        evidence = results["documents"][0]

        print("\nRetrieved Evidence:")

        for i, document in enumerate(evidence):
            print(f"\n--- Evidence {i + 1} ---")
            print(document)

        # 2. LLM evaluates evidence
        result = reason(
            query=query,
            evidence=evidence
        )

        decision = result.get("decision")

        print("\nDecision:", decision)

        # 3. Evidence is sufficient
        if decision == "SUFFICIENT":

            print("\nAgent Answer:")
            print(result.get("answer"))

            return

        # 4. Evidence is insufficient
        print("\nUNCERTAINTY")
        print("Missing information:")
        print(result.get("missing_information"))

        # 5. Maximum attempts reached
        if attempt == MAX_ATTEMPTS:

            print("\nMaximum attempts reached.")
            print("Escalating to human support.")

            return

        # 6. Ask customer for missing information
        question = result.get(
            "answer",
            "Could you please provide more information?"
        )

        print("\nAgent:")
        print(question)

        query = input("\nCustomer: ")


if __name__ == "__main__":
    run_agent()