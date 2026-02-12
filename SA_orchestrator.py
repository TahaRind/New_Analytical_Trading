from SA_classes import StockAnalyser, Strategiser
from SA_manager import save_analysis # Only if orchestrator needs to save intermediate states
import pandas as pd

def create_analysis(stock_name: str, initial_indicators: dict, include_outliers: bool):
    """
    Initializes a new StockAnalyser object.
    Args:
        stock_name (str): The ticker symbol for the stock to analyze.
        initial_indicators (dict): A dictionary of initial indicators to add.
        include_outliers (bool): Whether to detect outliers during initial setup.
    Returns:
        StockAnalyser: An initialized StockAnalyser object.
    """
    # The StockAnalyser constructor will handle downloading data and adding initial indicators
    # based on the initial_indicators dict. Outlier detection is also handled during init.
    analysis_input = {
        'name': stock_name,
        'indicators': initial_indicators,
        'outliers': include_outliers
    }
    stock_analyser_obj = StockAnalyser(analysis_input)
    return stock_analyser_obj

def run_strategies(stock_analyser_obj: StockAnalyser, indicator_params: dict, strategies_to_run: list):
    """
    Updates indicators and runs specified strategies on the StockAnalyser object.
    Args:
        stock_analyser_obj (StockAnalyser): The active StockAnalyser object.
        indicator_params (dict): A dictionary of indicator types and their parameters.
        strategies_to_run (list): A list of strategy names to run.
    Returns:
        StockAnalyser: The updated StockAnalyser object with strategies run.
    """
    if not isinstance(stock_analyser_obj, StockAnalyser):
        raise TypeError("Expected a StockAnalyser object.")

    # Clear existing indicators and strategies to re-apply based on new selections
    stock_analyser_obj.dataframe = stock_analyser_obj.initial_dataframe.copy() # Reset to original data
    stock_analyser_obj.signals_dict = {}
    stock_analyser_obj.strategies_dict = {}

    # Add indicators based on indicator_params
    if indicator_params:
        stock_analyser_obj.add_ind(indicator_params)

    # Run strategies
    for strat_name in strategies_to_run:
        # This is a simplified example. In a real scenario, you'd parse strat_name
        # to create the correct Strategiser object with its specific rules.
        # For now, let's assume a basic Strategiser can be created from the name.
        # You'll need more sophisticated logic here to map strategy names to rules.
        # Example: if strat_name is 'EMA_5-RSI_14', you'd extract 'EMA_5' and 'RSI_14'
        # and create a Strategiser with those indicator strategies.

        # Placeholder for creating a Strategiser based on strat_name
        # This part needs to be fleshed out based on how you define strategies
        # For demonstration, let's assume a simple strategy creation:
        if 'EMA' in strat_name and 'RSI' in strat_name:
            # Example for combined strategy: EMA_5-RSI_14
            parts = strat_name.split('-')
            indicator_strategies = {}
            for part in parts:
                if 'EMA' in part:
                    indicator_strategies['cross'] = [part, 'Close']
                elif 'RSI' in part:
                    indicator_strategies['range'] = [part, 30, 70] # Example range
            strat = Strategiser(strat_name, indicator_strategies)
        elif 'EMA' in strat_name:
            strat = Strategiser(strat_name, {'cross': [strat_name, 'Close']})
        elif 'RSI' in strat_name:
            strat = Strategiser(strat_name, {'range': [strat_name, 30, 70]}) # Example range
        elif 'MACD' in strat_name:
            parts = strat_name.split('_')
            if len(parts) == 4:
                _, fast, slow, signal = parts
                macd_line = f"MACD_{fast}_{slow}_{signal}"
                signal_line = f"MACDs_{fast}_{slow}_{signal}"
                strat = Strategiser(strat_name, {'cross': [macd_line, signal_line]})
            else:
                print(f"Warning: Invalid MACD strategy format for {strat_name}. Skipping.")
                continue
        else:
            print(f"Warning: Could not create strategy for {strat_name}. Skipping.") # Replaced st.warning
            continue
        stock_analyser_obj.run_strat(strat)

    return stock_analyser_obj

def get_analysis_data(stock_analyser_obj: StockAnalyser):
    """
    Extracts relevant data from the StockAnalyser object for plotting and display.
    Args:
        stock_analyser_obj (StockAnalyser): The active StockAnalyser object.
    Returns:
        dict: A dictionary containing the DataFrame and strategy data for visualization.
    """
    if not isinstance(stock_analyser_obj, StockAnalyser):
        return None

    # Ensure the dataframe has a 'Date' column and it's in datetime format for plotting
    if 'Date' in stock_analyser_obj.dataframe.columns:
        stock_analyser_obj.dataframe['Date'] = pd.to_datetime(stock_analyser_obj.dataframe['Date'])
    else:
        # If 'Date' is not a column, assume index is date and reset it
        stock_analyser_obj.dataframe.reset_index(inplace=True)
        stock_analyser_obj.dataframe.rename(columns={'index': 'Date'}, inplace=True)
        stock_analyser_obj.dataframe['Date'] = pd.to_datetime(stock_analyser_obj.dataframe['Date'])

    strategies_data = {}
    for strat_name, strategy_obj in stock_analyser_obj.strategies_dict.items():
        strategies_data[strat_name] = {
            'dataframe': strategy_obj.dataframe, # Assuming each strategy has its own DataFrame with signals/profits
            'stats': strategy_obj.stats_df # Assuming each strategy has its own stats_df
        }

    return {
        'dataframe': stock_analyser_obj.dataframe,
        'strategies_data': strategies_data
    }
