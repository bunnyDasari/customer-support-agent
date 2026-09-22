import json
import ollama


MODEL_NAME = "qwen2.5:3b"


SYSTEM_PROMPT = """
You are the reasoning component of a customer support agent.

Your job is to evaluate whether the retrieved evidence contains
enough reliable information to answer the customer's goal.

You will receive:

1. Customer goal
2. Order number, if available
3. Customer question
4. Retrieved evidence

IMPORTANT:

- Use ONLY the retrieved evidence to generate the answer.
- Never invent information.
- Do NOT ask the customer for information that is already present
  in the conversation state.
- The customer's order number is already known if it is provided
  in the state.
- Check whether the retrieved evidence actually relates to the
  customer's order number.
- If the evidence refers to a different order number, treat the
  evidence as insufficient.
- Do not confuse a similar order number with the customer's order number.

Possible decisions:

1. SUFFICIENT
   Use this when the evidence directly supports the customer's goal
   and relates to the customer's order number when an order number
   is required.

2. EVIDENCE_INSUFFICIENT
   Use this when the customer information is complete, but the
   retrieved evidence does not contain enough relevant information
   to answer the question.

3. CUSTOMER_INFO_MISSING
   Use this only when information required from the customer is
   actually missing from the conversation state.

Return ONLY valid JSON.


For SUFFICIENT:

{
    "decision": "SUFFICIENT",
    "answer": "..."
}


For EVIDENCE_INSUFFICIENT:

{
    "decision": "EVIDENCE_INSUFFICIENT",
    "answer": "I could not find enough relevant information to answer reliably.",
    "missing_information": "..."
}


For CUSTOMER_INFO_MISSING:

{
    "decision": "CUSTOMER_INFO_MISSING",
    "answer": "Could you please provide ...?",
    "missing_information": "..."
}
"""


def reason( goal,order_number,query,evidence):
    """
    Evaluate whether retrieved evidence is sufficient
    to answer the customer's goal.
    """

    evidence_text = "\n\n".join(evidence)

    prompt = f"""
Customer goal:
{goal}

Customer order number:
{order_number}

Customer question:
{query}

Retrieved evidence:
{evidence_text}

Now evaluate the evidence.

First determine:

1. Is the required customer information available?
2. Does the evidence relate to the customer's goal?
3. If an order number is available, does the evidence relate
   to that exact order number?
4. Does the evidence contain enough information to answer
   the customer's question?

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

    content = response["message"]["content"].strip()

    try:

        result = json.loads(content)

        valid_decisions = {
            "SUFFICIENT",
            "EVIDENCE_INSUFFICIENT",
            "CUSTOMER_INFO_MISSING"
        }

        if result.get("decision") in valid_decisions:
            return result

    except json.JSONDecodeError:
        pass

    return {
        "decision": "EVIDENCE_INSUFFICIENT",
        "answer": "I am unable to determine the answer reliably.",
        "missing_information": "Relevant evidence could not be verified."
    }