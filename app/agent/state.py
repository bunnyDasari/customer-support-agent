from dataclasses import dataclass, field


@dataclass
class AgentState:
    goal: str | None = None
    order_number: str | None = None
    conversation: list[str] = field(default_factory=list)


if __name__ == "__main__":

    state = AgentState()

    state.goal = "ORDER_STATUS"
    state.order_number = "BB123456"

    state.conversation.append("Where is my order?")
    state.conversation.append(
        "My order number is BB123456."
    )

    print(state)