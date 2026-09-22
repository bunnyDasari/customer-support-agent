import re


def extract_order_number(message: str) -> str | None:
    """
    Extract an order number from a customer message.

    Supports examples such as:
        BB67890
        my order number is BB67890
        this is my order number BB67890
        order number: BB67890
        my order is BB67890
        123456
    """

    message = message.strip()

    # -----------------------------------------
    # Pattern 1: BB-prefixed order number
    # -----------------------------------------

    match = re.search(
        r"\bBB\d+\b",
        message,
        re.IGNORECASE
    )

    if match:
        return match.group(0).upper()

    # -----------------------------------------
    # Pattern 2: Numeric order number
    # -----------------------------------------

    match = re.search(
        r"\b\d{5,}\b",
        message
    )

    if match:
        return match.group(0)

    return None


if __name__ == "__main__":

    test_messages = [
        "BB67890",
        "my order number is BB67890",
        "this is my order number BB67890",
        "order number: BB67890",
        "My order is BB67890",
        "123456",
        "My order number is 123456",
        "hello"
    ]

    for message in test_messages:

        result = extract_order_number(message)

        print(
            f"{message} -> {result}"
        )