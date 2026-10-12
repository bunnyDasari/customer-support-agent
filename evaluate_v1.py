import json
import os
from datetime import datetime

from app.agent.router import classify_goal
from app.agent.reason import reason
from app.agent.state import AgentState
from app.rag.retrieve import retrieve
from app.utils.order_number import extract_order_number


# ============================================================
# CONFIG
# ============================================================

EVAL_FILE = "eval/v1_eval_50.json"

RESULTS_DIR = "results"

RESULTS_FILE = os.path.join(
    RESULTS_DIR,
    "v1-results.md"
)

MAX_ATTEMPTS = 3


# ============================================================
# STATE
# ============================================================

def update_state(state, message):
    """
    Update the existing V1 state with a customer message.
    """

    state.conversation.append(message)

    order_number = extract_order_number(message)

    if order_number:
        state.order_number = order_number


def get_missing_information(state):
    """
    Determine whether V1 needs additional customer information.
    """

    missing = []

    if state.goal == "ORDER_STATUS":

        if state.order_number is None:
            missing.append("order_number")

    return missing


# ============================================================
# RUN ONE CASE
# ============================================================

def run_single_case(case):

    messages = case["messages"]

    state = AgentState()

    # --------------------------------------------------------
    # Initial customer message
    # --------------------------------------------------------

    first_message = messages[0]

    update_state(
        state,
        first_message
    )

    # --------------------------------------------------------
    # Goal classification
    # --------------------------------------------------------

    goal_result = classify_goal(
        first_message
    )

    predicted_goal = goal_result.get(
        "goal",
        "OTHER"
    )

    state.goal = predicted_goal

    expected_goal = case["expected_goal"]

    goal_correct = (
        predicted_goal == expected_goal
    )

    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    if predicted_goal == "OTHER":

        return {
            "case": case,
            "predicted_goal": predicted_goal,
            "goal_correct": goal_correct,

            "final_decision": "OTHER",
            "actual_action": "OTHER",

            "agent_response": (
                "I'm not sure how to help with that. "
                "Could you please provide more details?"
            ),

            "attempts": [],

            "order_number": state.order_number,

            "conversation": list(
                state.conversation
            ),
        }

    # --------------------------------------------------------
    # Handle missing information
    # --------------------------------------------------------

    message_index = 1

    while True:

        missing_information = (
            get_missing_information(state)
        )

        # We have everything required
        if not missing_information:
            break

        # ----------------------------------------------------
        # If another customer message exists,
        # feed it into the state.
        # ----------------------------------------------------

        if message_index < len(messages):

            customer_message = (
                messages[message_index]
            )

            update_state(
                state,
                customer_message
            )

            message_index += 1

            continue

        # ----------------------------------------------------
        # No more messages.
        # V1 would ask the customer for information.
        # ----------------------------------------------------

        question = (
            "Could you please provide your order number?"
        )

        return {
            "case": case,
            "predicted_goal": predicted_goal,
            "goal_correct": goal_correct,

            "final_decision":
                "CUSTOMER_INFO_MISSING",

            "actual_action":
                "ASK_FOR_ORDER_NUMBER",

            "agent_response": question,

            "attempts": [],

            "order_number":
                state.order_number,

            "conversation":
                list(state.conversation),
        }

    # ========================================================
    # RETRIEVAL + REASONING
    # ========================================================

    attempts = []

    final_decision = None
    final_answer = None

    for attempt_number in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        print(
            f"    Attempt {attempt_number}"
        )

        # ----------------------------------------------------
        # Retrieval query
        # ----------------------------------------------------

        retrieval_query = f"""
Customer goal: {state.goal}
Order number: {state.order_number}
""".strip()

        # ----------------------------------------------------
        # Retrieve
        # ----------------------------------------------------

        results = retrieve(
            retrieval_query,
            top_k=3
        )

        # Make sure evidence always exists
        documents = results.get(
            "documents",
            []
        )

        if documents:
            evidence = documents[0]
        else:
            evidence = []

        if evidence is None:
            evidence = []

        # ----------------------------------------------------
        # Reason
        # ----------------------------------------------------

        reasoning_result = reason(
            goal=state.goal,
            order_number=state.order_number,
            query=state.conversation[0],
            evidence=evidence,
        )

        decision = reasoning_result.get(
            "decision"
        )

        # ----------------------------------------------------
        # Save complete attempt
        # ----------------------------------------------------

        attempts.append(
            {
                "attempt": attempt_number,

                "retrieval_query":
                    retrieval_query,

                "retrieved_evidence":
                    list(evidence),

                "decision":
                    decision,

                "reasoning_result":
                    reasoning_result,
            }
        )

        # ----------------------------------------------------
        # SUFFICIENT
        # ----------------------------------------------------

        if decision == "SUFFICIENT":

            final_decision = (
                "SUFFICIENT"
            )

            final_answer = (
                reasoning_result.get(
                    "answer",
                    ""
                )
            )

            break

        # ----------------------------------------------------
        # CUSTOMER INFO MISSING
        # ----------------------------------------------------

        if decision == "CUSTOMER_INFO_MISSING":

            final_decision = (
                "CUSTOMER_INFO_MISSING"
            )

            final_answer = (
                reasoning_result.get(
                    "answer",
                    "Could you please provide more information?"
                )
            )

            break

        # ----------------------------------------------------
        # EVIDENCE INSUFFICIENT
        # ----------------------------------------------------

        if decision == "EVIDENCE_INSUFFICIENT":

            if attempt_number < MAX_ATTEMPTS:
                continue

            final_decision = "ESCALATED"

            final_answer = (
                "I couldn't find enough relevant "
                "information to answer reliably. "
                "Escalating to human support."
            )

            break

        # ----------------------------------------------------
        # Unknown decision
        # ----------------------------------------------------

        final_decision = "UNKNOWN"

        final_answer = (
            "I was unable to determine "
            "the answer reliably."
        )

        break

    # ========================================================
    # ACTUAL ACTION
    # ========================================================

    if final_decision == "SUFFICIENT":

        actual_action = "ANSWER"

    elif final_decision == "CUSTOMER_INFO_MISSING":

        actual_action = "ASK_FOR_INFORMATION"

    elif final_decision == "ESCALATED":

        actual_action = "ESCALATE"

    else:

        actual_action = final_decision

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "case": case,

        "predicted_goal":
            predicted_goal,

        "goal_correct":
            goal_correct,

        "final_decision":
            final_decision,

        "actual_action":
            actual_action,

        "agent_response":
            final_answer,

        "attempts":
            attempts,

        "order_number":
            state.order_number,

        "conversation":
            list(state.conversation),
    }


# ============================================================
# LOAD DATASET
# ============================================================

def load_cases():

    with open(
        EVAL_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# RUN ALL CASES
# ============================================================

def evaluate_cases(cases):

    results = []

    print()
    print("=" * 60)
    print("V1 EVALUATION")
    print("=" * 60)

    for index, case in enumerate(
        cases,
        start=1
    ):

        print(
            f"\nRunning case {index}/{len(cases)}..."
        )

        try:

            result = run_single_case(
                case
            )

            results.append(
                result
            )

        except Exception as error:

            print(
                f"ERROR in case {case['id']}: {error}"
            )

            results.append(
                {
                    "case": case,

                    "predicted_goal":
                        "ERROR",

                    "goal_correct":
                        False,

                    "final_decision":
                        "ERROR",

                    "actual_action":
                        "ERROR",

                    "agent_response":
                        str(error),

                    "attempts":
                        [],

                    "order_number":
                        None,

                    "conversation":
                        case["messages"],
                }
            )

    return results


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(results):

    total = len(results)

    goal_correct = sum(
        1
        for result in results
        if result.get("goal_correct") is True
    )

    goal_accuracy = (
        goal_correct / total * 100
        if total > 0
        else 0
    )

    answers = sum(
        1
        for result in results
        if result.get("actual_action")
        == "ANSWER"
    )

    asks = sum(
        1
        for result in results
        if result.get("actual_action")
        in {
            "ASK_FOR_INFORMATION",
            "ASK_FOR_ORDER_NUMBER",
        }
    )

    escalations = sum(
        1
        for result in results
        if result.get("actual_action")
        == "ESCALATE"
    )

    errors = sum(
        1
        for result in results
        if result.get("actual_action")
        == "ERROR"
    )

    return {
        "total":
            total,

        "goal_correct":
            goal_correct,

        "goal_accuracy":
            goal_accuracy,

        "answers":
            answers,

        "asks":
            asks,

        "escalations":
            escalations,

        "errors":
            errors,
    }


# ============================================================
# DETERMINE CASE RESULT
# ============================================================

def determine_case_result(result):

    case = result["case"]

    expected_action = (
        case["expected_action"]
    )

    actual_action = (
        result.get("actual_action")
    )

    # --------------------------------------------------------
    # Order status with known order number
    # --------------------------------------------------------

    if expected_action == "ANSWER_OR_ESCALATE":

        return actual_action in {
            "ANSWER",
            "ESCALATE",
        }

    # --------------------------------------------------------
    # Order status without order number
    # --------------------------------------------------------

    if expected_action == "ASK_FOR_ORDER_NUMBER":

        return actual_action in {
            "ASK_FOR_ORDER_NUMBER",
            "ASK_FOR_INFORMATION",
        }

    # --------------------------------------------------------
    # Normal cases
    # --------------------------------------------------------

    return (
        actual_action
        == expected_action
    )


# ============================================================
# TABLE HELPERS
# ============================================================

def clean_text(value, max_length=120):

    if value is None:
        return "-"

    value = str(value)

    value = value.replace(
        "\n",
        " "
    )

    value = value.replace(
        "|",
        "\\|"
    )

    value = value.strip()

    if len(value) > max_length:

        value = (
            value[:max_length - 3]
            + "..."
        )

    return value


def get_customer_input(case):

    messages = case.get(
        "messages",
        []
    )

    if not messages:
        return "-"

    return " / ".join(
        clean_text(
            message,
            max_length=100
        )
        for message in messages
    )


def get_attempt_count(result):

    attempts = result.get(
        "attempts",
        []
    )

    if not isinstance(
        attempts,
        list
    ):
        return 0

    return len(attempts)


def get_last_decision(result):

    attempts = result.get(
        "attempts",
        []
    )

    if not isinstance(
        attempts,
        list
    ):
        return "-"

    if not attempts:
        return result.get(
            "final_decision",
            "-"
        )

    return attempts[-1].get(
        "decision",
        "-"
    )


def get_evidence_count(result):

    attempts = result.get(
        "attempts",
        []
    )

    if not isinstance(
        attempts,
        list
    ):
        return 0

    count = 0

    for attempt in attempts:

        evidence = attempt.get(
            "retrieved_evidence",
            []
        )

        if isinstance(
            evidence,
            list
        ):

            count += len(evidence)

    return count


# ============================================================
# GENERATE TABLE-BASED MARKDOWN
# ============================================================

def generate_markdown(
    results,
    metrics
):

    lines = []

    # ========================================================
    # HEADER
    # ========================================================

    lines.append(
        "# V1 Customer Support Agent Evaluation"
    )

    lines.append("")

    lines.append(
        f"Generated: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    lines.append("")

    lines.append(
        "> V1 evaluation results generated "
        "from the configured evaluation dataset."
    )

    lines.append("")

    # ========================================================
    # 1. SUMMARY TABLE
    # ========================================================

    lines.append(
        "## 1. Evaluation Summary"
    )

    lines.append("")

    lines.append(
        "| Metric | Result |"
    )

    lines.append(
        "|---|---:|"
    )

    lines.append(
        f"| Total Cases | {metrics['total']} |"
    )

    lines.append(
        f"| Goal Correct | "
        f"{metrics['goal_correct']} / {metrics['total']} |"
    )

    lines.append(
        f"| Goal Accuracy | "
        f"{metrics['goal_accuracy']:.2f}% |"
    )

    lines.append(
        f"| Answers | {metrics['answers']} |"
    )

    lines.append(
        f"| Information Requests | "
        f"{metrics['asks']} |"
    )

    lines.append(
        f"| Escalations | "
        f"{metrics['escalations']} |"
    )

    lines.append(
        f"| Errors | "
        f"{metrics['errors']} |"
    )

    lines.append("")

    # ========================================================
    # 2. MAIN EVALUATION MATRIX
    # ========================================================

    lines.append(
        "## 2. Evaluation Matrix"
    )

    lines.append("")

    lines.append(
        "| Case | Customer Input | Expected Goal | "
        "Predicted Goal | Goal | Expected Action | "
        "Actual Action | Decision | Attempts | Result |"
    )

    lines.append(
        "|---:|---|---|---|:---:|---|---|---|---:|:---:|"
    )

    for result in results:

        case = result["case"]

        case_pass = determine_case_result(
            result
        )

        goal_status = (
            "PASS"
            if result.get("goal_correct")
            else "FAIL"
        )

        result_status = (
            "PASS"
            if case_pass
            else "FAIL"
        )

        customer_input = (
            get_customer_input(case)
        )

        expected_goal = (
            case.get(
                "expected_goal",
                "-"
            )
        )

        predicted_goal = (
            result.get(
                "predicted_goal",
                "-"
            )
        )

        expected_action = (
            case.get(
                "expected_action",
                "-"
            )
        )

        actual_action = (
            result.get(
                "actual_action",
                "-"
            )
        )

        decision = (
            result.get(
                "final_decision",
                "-"
            )
        )

        attempts = get_attempt_count(
            result
        )

        lines.append(
            f"| {case.get('id', '-')} "
            f"| {customer_input} "
            f"| `{expected_goal}` "
            f"| `{predicted_goal}` "
            f"| {goal_status} "
            f"| `{expected_action}` "
            f"| `{actual_action}` "
            f"| `{decision}` "
            f"| {attempts} "
            f"| **{result_status}** |"
        )

    lines.append("")

    # ========================================================
    # 3. GOAL CLASSIFICATION MATRIX
    # ========================================================

    lines.append(
        "## 3. Goal Classification Matrix"
    )

    lines.append("")

    lines.append(
        "| Case | Customer Input | Expected Goal | "
        "Predicted Goal | Result |"
    )

    lines.append(
        "|---:|---|---|---|:---:|"
    )

    for result in results:

        case = result["case"]

        status = (
            "PASS"
            if result.get("goal_correct")
            else "FAIL"
        )

        lines.append(
            f"| {case.get('id', '-')} "
            f"| {get_customer_input(case)} "
            f"| `{case.get('expected_goal', '-')}` "
            f"| `{result.get('predicted_goal', '-')}` "
            f"| **{status}** |"
        )

    lines.append("")

    # ========================================================
    # 4. ACTION MATRIX
    # ========================================================

    lines.append(
        "## 4. Action / Decision Matrix"
    )

    lines.append("")

    lines.append(
        "| Case | Expected Action | Actual Action | "
        "Final Decision | Attempts | Evidence Items | Result |"
    )

    lines.append(
        "|---:|---|---|---|---:|---:|:---:|"
    )

    for result in results:

        case = result["case"]

        case_pass = determine_case_result(
            result
        )

        status = (
            "PASS"
            if case_pass
            else "FAIL"
        )

        lines.append(
            f"| {case.get('id', '-')} "
            f"| `{case.get('expected_action', '-')}` "
            f"| `{result.get('actual_action', '-')}` "
            f"| `{result.get('final_decision', '-')}` "
            f"| {get_attempt_count(result)} "
            f"| {get_evidence_count(result)} "
            f"| **{status}** |"
        )

    lines.append("")

    # ========================================================
    # 5. FAILURES ONLY
    # ========================================================

    lines.append(
        "## 5. Failure Matrix"
    )

    lines.append("")

    failures = [
        result
        for result in results
        if not determine_case_result(
            result
        )
    ]

    if not failures:

        lines.append(
            "No failed cases."
        )

    else:

        lines.append(
            "| Case | Customer Input | Expected Goal | "
            "Predicted Goal | Expected Action | "
            "Actual Action | Decision |"
        )

        lines.append(
            "|---:|---|---|---|---|---|---|"
        )

        for result in failures:

            case = result["case"]

            lines.append(
                f"| {case.get('id', '-')} "
                f"| {get_customer_input(case)} "
                f"| `{case.get('expected_goal', '-')}` "
                f"| `{result.get('predicted_goal', '-')}` "
                f"| `{case.get('expected_action', '-')}` "
                f"| `{result.get('actual_action', '-')}` "
                f"| `{result.get('final_decision', '-')}` |"
            )

    lines.append("")

    # ========================================================
    # 6. DETAILED RESULTS
    # ========================================================

    lines.append(
        "## 6. Detailed Case Results"
    )

    lines.append("")

    for result in results:

        case = result["case"]

        case_pass = determine_case_result(
            result
        )

        status = (
            "PASS"
            if case_pass
            else "FAIL"
        )

        lines.append(
            f"### Case {case.get('id', '-')}"
        )

        lines.append("")

        lines.append(
            f"**Result:** {status}"
        )

        lines.append("")

        lines.append(
            f"**Customer Input:** "
            f"{get_customer_input(case)}"
        )

        lines.append("")

        lines.append(
            f"**Expected Goal:** "
            f"`{case.get('expected_goal', '-')}`"
        )

        lines.append("")

        lines.append(
            f"**Predicted Goal:** "
            f"`{result.get('predicted_goal', '-')}`"
        )

        lines.append("")

        lines.append(
            f"**Goal Correct:** "
            f"`{result.get('goal_correct', False)}`"
        )

        lines.append("")

        lines.append(
            f"**Expected Action:** "
            f"`{case.get('expected_action', '-')}`"
        )

        lines.append("")

        lines.append(
            f"**Actual Action:** "
            f"`{result.get('actual_action', '-')}`"
        )

        lines.append("")

        lines.append(
            f"**Final Decision:** "
            f"`{result.get('final_decision', '-')}`"
        )

        lines.append("")

        lines.append(
            f"**Order Number:** "
            f"`{result.get('order_number', '-')}`"
        )

        lines.append("")

        lines.append(
            f"**Agent Response:** "
            f"{clean_text(result.get('agent_response', ''), 500)}"
        )

        lines.append("")

        # ----------------------------------------------------
        # Attempts
        # ----------------------------------------------------

        attempts = result.get(
            "attempts",
            []
        )

        if not isinstance(
            attempts,
            list
        ):

            attempts = []

        if attempts:

            lines.append(
                "**Attempts:**"
            )

            lines.append("")

            lines.append(
                "| Attempt | Retrieval Query | "
                "Decision | Evidence Count |"
            )

            lines.append(
                "|---:|---|---|---:|"
            )

            for attempt in attempts:

                evidence = attempt.get(
                    "retrieved_evidence",
                    []
                )

                evidence_count = (
                    len(evidence)
                    if isinstance(
                        evidence,
                        list
                    )
                    else 0
                )

                lines.append(
                    f"| {attempt.get('attempt', '-')} "
                    f"| {clean_text(attempt.get('retrieval_query', ''), 200)} "
                    f"| `{attempt.get('decision', '-')}` "
                    f"| {evidence_count} |"
                )

            lines.append("")

        lines.append("---")

        lines.append("")

    # ========================================================
    # 7. V1 OBSERVATIONS
    # ========================================================

    lines.append(
        "## 7. V1 Observations"
    )

    lines.append("")

    lines.append(
        "- Goal classification and action decisions are evaluated separately."
    )

    lines.append(
        "- Order-status requests require an order number before retrieval."
    )

    lines.append(
        "- Retrieval and reasoning are attempted up to "
        f"{MAX_ATTEMPTS} times."
    )

    lines.append(
        "- Cases that remain evidence-insufficient are escalated."
    )

    lines.append(
        "- Failed cases are listed separately above for V2 analysis."
    )

    lines.append("")

    # ========================================================
    # 8. V1 → V2 BASELINE
    # ========================================================

    lines.append(
        "## 8. V1 Baseline"
    )

    lines.append("")

    lines.append(
        "| Metric | V1 Baseline |"
    )

    lines.append(
        "|---|---:|"
    )

    lines.append(
        f"| Cases | {metrics['total']} |"
    )

    lines.append(
        f"| Goal Accuracy | "
        f"{metrics['goal_accuracy']:.2f}% |"
    )

    lines.append(
        f"| Answers | {metrics['answers']} |"
    )

    lines.append(
        f"| Information Requests | {metrics['asks']} |"
    )

    lines.append(
        f"| Escalations | {metrics['escalations']} |"
    )

    lines.append(
        f"| Errors | {metrics['errors']} |"
    )

    lines.append("")

    lines.append(
        "This table is the V1 baseline for comparison with V2."
    )

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Create results directory
    # --------------------------------------------------------

    os.makedirs(
        RESULTS_DIR,
        exist_ok=True
    )

    print()
    print("=" * 60)
    print("LOADING EVALUATION DATASET")
    print("=" * 60)

    cases = load_cases()

    print(
        f"Loaded {len(cases)} evaluation cases."
    )

    # --------------------------------------------------------
    # Run all cases
    # --------------------------------------------------------

    results = evaluate_cases(
        cases
    )

    # --------------------------------------------------------
    # Calculate metrics
    # --------------------------------------------------------

    metrics = calculate_metrics(
        results
    )

    # --------------------------------------------------------
    # Generate markdown
    # --------------------------------------------------------

    markdown = generate_markdown(
        results,
        metrics
    )

    # --------------------------------------------------------
    # Write results
    # --------------------------------------------------------

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            markdown
        )

    # --------------------------------------------------------
    # Console summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("V1 EVALUATION COMPLETE")
    print("=" * 60)

    print(
        f"Total cases      : "
        f"{metrics['total']}"
    )

    print(
        f"Goal correct     : "
        f"{metrics['goal_correct']}"
    )

    print(
        f"Goal accuracy    : "
        f"{metrics['goal_accuracy']:.2f}%"
    )

    print(
        f"Answers          : "
        f"{metrics['answers']}"
    )

    print(
        f"Info requests    : "
        f"{metrics['asks']}"
    )

    print(
        f"Escalations      : "
        f"{metrics['escalations']}"
    )

    print(
        f"Errors           : "
        f"{metrics['errors']}"
    )

    print()
    print(
        "Results saved to:"
    )

    print(
        RESULTS_FILE
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()