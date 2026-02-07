import pickle


def load_analysis(stock_filename):
    print(f"File {stock_filename} exists. Loading object...")
    with open(stock_filename, "rb") as f:
        stock = pickle.load(f)
        print(" Loaded object...")
    return stock


def save_analysis(stock, stock_filename):
    print(f"Saving Object as {stock_filename}")
    with open(stock_filename, "wb") as f:
        pickle.dump(stock, f)
