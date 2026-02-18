import pickle


def load_analysis_from_file(filename: str):
    """Load and return a serialized StockAnalyser object from disk."""
    print(f"Loading analysis from {filename}...")
    with open(filename, "rb") as file_handle:
        analysis_object = pickle.load(file_handle)
    return analysis_object


def save_analysis_to_file(analysis_object, filename: str):
    """Serialize a StockAnalyser object to disk."""
    print(f"Saving analysis to {filename}...")
    with open(filename, "wb") as file_handle:
        pickle.dump(analysis_object, file_handle)


# Backward-compatible aliases
load_analysis = load_analysis_from_file
save_analysis = save_analysis_to_file
