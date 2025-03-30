import os
import glob
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,       # How much the answer is grounded in the context
    answer_relevancy,   # How relevant the answer is to the question
    context_recall,     # How well the context captures the necessary info from ground_truth
    context_precision,  # Signal-to-noise ratio of the context
    answer_correctness, # How factually correct the answer is compared to ground_truth

)


# You might need specific LLMs or Embeddings for some metrics
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings # Example

from openai import OpenAI
from dotenv import load_dotenv
from dotenv import find_dotenv


# --- Configuration ---
# Define paths to the directories based on your structure
answers_dir = "../example_outputs"
contexts_dir = "../contexts"
golden_dir = "../golden_outputs"
# RAGAs requires the original question for metrics like answer_relevancy
# Assuming you have a directory 'questions' with 'question1.txt', 'question2.txt', etc.
questions_dir = "../questions"

# --- Check for Required Directories ---
required_dirs = [answers_dir, contexts_dir, golden_dir, questions_dir]
missing_dirs = [d for d in required_dirs if not os.path.isdir(d)]

if missing_dirs:
    print(f"Error: The following required directories are missing:")
    for d in missing_dirs:
        print(f"- {d}")
    if questions_dir in missing_dirs:
        print("\nNote: 'questions' directory is needed for metrics like 'answer_relevancy'.")
    print("\nPlease ensure these directories exist and contain the necessary files.")
    exit()

# --- Data Loading and Preparation ---
data_samples = []
# Find all answer files and sort them to ensure consistent ordering
answer_files = sorted(glob.glob(os.path.join(answers_dir, "answer*.txt")))

print(f"Found {len(answer_files)} answer files in '{answers_dir}'. Processing...")

for answer_file in answer_files:
    base_name = os.path.basename(answer_file)
    # Extract the number N from the filename (e.g., "answer1.txt" -> "1")
    try:
        # Simple extraction assuming "answer<N>.txt" format
        example_num_str = ''.join(filter(str.isdigit, base_name))
        if not example_num_str:
             print(f"Could not extract number from filename: {answer_file}. Skipping.")
             continue
        example_num = int(example_num_str)
    except ValueError:
        print(f"Could not extract number from filename: {answer_file}. Skipping.")
        continue

    # Construct corresponding file paths
    context_file = os.path.join(contexts_dir, f"context{example_num}.txt")
    golden_file = os.path.join(golden_dir, f"golden{example_num}.txt")
    question_file = os.path.join(questions_dir, f"question{example_num}.txt")

    # Check if all corresponding files exist for this example number
    required_files_for_example = [answer_file, context_file, golden_file, question_file]
    missing_files_for_example = [f for f in required_files_for_example if not os.path.exists(f)]

    if missing_files_for_example:
        print(f"\nSkipping example {example_num}: Missing files:")
        for f in missing_files_for_example:
            print(f"  - {f}")
        continue

    # Read file contents
    try:
        with open(question_file, 'r', encoding='utf-8') as f:
            question = f.read().strip()
        with open(answer_file, 'r', encoding='utf-8') as f:
            answer = f.read().strip()
        with open(context_file, 'r', encoding='utf-8') as f:
            # RAGAs expects contexts as list[str].
            # Assuming context file has one main block of text.
            # If your context file represents multiple retrieved chunks,
            # you might need to split it, e.g., by paragraph:
            # contexts = [para.strip() for para in f.read().split('\n\n') if para.strip()]
            contexts = [f.read().strip()]
        with open(golden_file, 'r', encoding='utf-8') as f:
            # RAGAs uses 'ground_truth' for the golden answer/reference
            ground_truth = f.read().strip()

        # Append the data for this example
        data_samples.append(
            {
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
            }
        )
        print(f"Successfully processed example {example_num}.")

    except Exception as e:
        print(f"\nError reading files for example {example_num}: {e}. Skipping.")
        continue

if not data_samples:
    print("\nNo valid data samples were collected. Cannot perform evaluation.")
    exit()

# Convert the list of dictionaries into a Hugging Face Dataset
dataset = Dataset.from_list(data_samples)

print(f"\nSuccessfully prepared dataset with {len(dataset)} samples.")

# --- RAGAs Evaluation ---

# Define the metrics you want to compute
# Note: Some metrics might require specific models (LLMs, Embeddings)
# You may need to configure these globally or pass them to evaluate()
# e.g., os.environ["OPENAI_API_KEY"] = "your_key"
#       llm = ChatOpenAI(model="gpt-3.5-turbo")
#       embeddings = OpenAIEmbeddings()

metrics_to_evaluate = [
    faithfulness,
    answer_relevancy,   # Requires 'question'
    context_precision,
    context_recall,     # Requires 'ground_truth'
    answer_correctness, # Requires 'ground_truth'
]

print(f"\nStarting evaluation with metrics: {[m.name for m in metrics_to_evaluate]}...")

# Perform evaluation
# The evaluation might take some time depending on the dataset size and metrics



# Ensure the environment variable is set, fallback to a default model
dotenv_path = find_dotenv(usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

model_name = os.getenv("OPENAI_MODEL_NAME")

try:
    result = evaluate(
        dataset=dataset,
        metrics=metrics_to_evaluate,
        # If metrics require specific models, provide them here:
        # llm=llm,
        # embeddings=embeddings,
        raise_exceptions=False # Set to True if you want увидеть errors during metric calculation
    )

    print("\n--- RAGAs Evaluation Results ---")
    print(result) # Prints the scores dictionary

    # Optionally, display as a pandas DataFrame for better readability
    try:
        df = result.to_pandas()
        print("\n--- Results DataFrame ---")
        print(df.head()) # Display first few rows
    except ImportError:
        print("\n(Install pandas 'pip install pandas' to view results as a table)")

except Exception as e:
    print(f"\nAn error occurred during RAGAs evaluation: {e}")
    print("Please check your RAGAs setup, API keys (if needed), and data format.")
