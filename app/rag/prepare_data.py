import pandas as pd
import json


INPUT_FILE = "data/raw/customer_support.csv"
OUTPUT_FILE = "data/processed/knowledge.json"


def prepare_data():
    # Load the original CSV
    df = pd.read_csv(INPUT_FILE)

    documents = []
    skipped_rows = 0

    for row_number, row in df.iterrows():

        try:
            # Convert the QA string into a Python dictionary
            qa_data = json.loads(row["qa"])

        except (json.JSONDecodeError, TypeError):
            print(f"Skipping row {row_number}: invalid JSON")
            skipped_rows += 1
            continue

        # Some rows contain actual knowledge,
        # while some contain only a schema definition.
        if "knowledge" not in qa_data:
            print(f"Skipping row {row_number}: no knowledge found")
            skipped_rows += 1
            continue

        # Extract each question/solution pair
        for item in qa_data["knowledge"]:

            question = item.get("customer_summary_question")
            solution = item.get("agent_summary_solution")

            # Make sure both fields actually exist
            if not question or not solution:
                print(f"Skipping incomplete knowledge in row {row_number}")
                continue

            document = {
                "category": row["issue_category"],
                "sub_category": row["issue_sub_category"],
                "product": row["product_category"],
                "question": question,
                "solution": solution
            }

            documents.append(document)

    # Save the cleaned knowledge
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            documents,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\n-----------------------------")
    print("Data preparation completed")
    print("-----------------------------")
    print(f"Original rows : {len(df)}")
    print(f"Documents     : {len(documents)}")
    print(f"Skipped rows  : {skipped_rows}")
    print(f"Output file   : {OUTPUT_FILE}")


if __name__ == "__main__":
    prepare_data()