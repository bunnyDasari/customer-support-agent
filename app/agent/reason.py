import json
import ollama


MODEL_NAME = "llama3.2:1b"


SYSTEM_PROMPT = """
            You are a customer support reasoning agent.

            Your job is to determine whether the retrieved evidence is sufficient
            to answer the customer's question.

            Rules:
            1. Use ONLY the retrieved evidence.
            2. Never invent information.
            3. If the evidence directly supports the customer's question,
            decision must be SUFFICIENT.
            4. If the evidence does not contain enough information,
            decision must be UNCERTAIN.
            5. If uncertain, identify what information is missing.
            6. Return ONLY valid JSON.

            Required format:

            {
            "decision": "SUFFICIENT",
            "answer": "..."
            }

            OR

            {
            "decision": "UNCERTAIN",
            "answer": "...",
            "missing_information": "..."
            }
    """


def reason(query, evidence):

    evidence_text = "\n\n".join(evidence)

    prompt = f"""
        Customer question:
        {query}

        Retrieved evidence:
        {evidence_text}

        Determine whether the evidence is sufficient to answer the customer's
        question.

        Return ONLY JSON.
    """

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response["message"]["content"]

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        return {
            "decision": "UNCERTAIN",
            "answer": "I am unable to determine the answer reliably.",
            "missing_information": "Additional information is required."
        }