import json
import ollama


MODEL_NAME = "llama3.2:1b"


SYSTEM_PROMPT = """
You are an intent classifier for a customer support agent.

Your ONLY task is to classify the user's message.

Return ONLY valid JSON:

{
    "intent": "..."
}

You MUST choose exactly one of:

NEED_ORDER_NUMBER
ORDER_NUMBER_PROVIDED
KNOWLEDGE_QUERY
OTHER


========================
INTENT 1: NEED_ORDER_NUMBER
========================

Choose NEED_ORDER_NUMBER when the customer is asking about
an order, package, delivery, tracking, or order status,
but has NOT provided an order number.

Examples:

User: Where is my order?
Intent: NEED_ORDER_NUMBER

User: Where is my package?
Intent: NEED_ORDER_NUMBER

User: Can you track my order?
Intent: NEED_ORDER_NUMBER

User: My order has not arrived.
Intent: NEED_ORDER_NUMBER

User: My order is out for delivery but I haven't received it.
Intent: NEED_ORDER_NUMBER

User: Can I provide my order number?
Intent: NEED_ORDER_NUMBER

User: What is my order number?
Intent: NEED_ORDER_NUMBER


=============================
INTENT 2: ORDER_NUMBER_PROVIDED
=============================

Choose ORDER_NUMBER_PROVIDED ONLY when the customer actually
provides an order number.

Examples:

User: My order number is BB123456.
Intent: ORDER_NUMBER_PROVIDED

User: Here is my order number: BB987654.
Intent: ORDER_NUMBER_PROVIDED

User: BB123456
Intent: ORDER_NUMBER_PROVIDED

User: My order number is 123456.
Intent: ORDER_NUMBER_PROVIDED


========================
INTENT 3: KNOWLEDGE_QUERY
========================

Choose KNOWLEDGE_QUERY when the customer asks a general
customer-support question that does not require a specific
order.

Examples:

User: What is your return policy?
Intent: KNOWLEDGE_QUERY

User: Can I return a product?
Intent: KNOWLEDGE_QUERY

User: How long do refunds take?
Intent: KNOWLEDGE_QUERY

User: Do you offer international shipping?
Intent: KNOWLEDGE_QUERY


================
INTENT 4: OTHER
================

Choose OTHER only when the message does not match any of
the three intents above.

Examples:

User: Hello
Intent: OTHER

User: Thank you
Intent: OTHER

User: Good morning
Intent: OTHER


========================
IMPORTANT RULES
========================

1. Mentioning the words "order number" is NOT the same as
   providing an order number.

2. "What is my order number?"
   → NEED_ORDER_NUMBER

3. "Can I provide my order number?"
   → NEED_ORDER_NUMBER

4. "My order number is BB123456."
   → ORDER_NUMBER_PROVIDED

5. If the customer asks where an order is and gives NO
   order number:
   → NEED_ORDER_NUMBER

6. Do not answer the customer.

7. Do not retrieve information.

8. Do not explain your decision.

9. Return ONLY JSON.
"""

def classify_intent(message):

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": message
            }
        ]
    )

    content = response["message"]["content"]

    try:
        result = json.loads(content)

        valid_intents = {
            "NEED_ORDER_NUMBER",
            "ORDER_NUMBER_PROVIDED",
            "KNOWLEDGE_QUERY",
            "OTHER"
        }

        if result.get("intent") in valid_intents:
            return result

    except json.JSONDecodeError:
        pass

    return {
        "intent": "OTHER"
    }