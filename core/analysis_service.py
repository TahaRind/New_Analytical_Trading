import pandas as pd

from core.analysis_models import StockAnalyser, Strategiser


def create_stock_analysis(ticker_symbol: str, indicators: dict, include_outliers: bool):
    analysis_config = {
        'name': ticker_symbol,
        'indicators': indicators,
        'outliers': include_outliers,
    }
    return StockAnalyser(analysis_config)


def _build_strategy(strategy_name: str):
    if 'EMA' in strategy_name and 'RSI' in strategy_name:
        indicator_rules = {}
        for part in strategy_name.split('-'):
            if 'EMA' in part:
                indicator_rules['cross'] = [part, 'Close']
            elif 'RSI' in part:
                indicator_rules['range'] = [part, 30, 70]
        return Strategiser(strategy_name, indicator_rules)

    if 'EMA' in strategy_name:
        return Strategiser(strategy_name, {'cross': [strategy_name, 'Close']})

    if 'RSI' in strategy_name:
        return Strategiser(strategy_name, {'range': [strategy_name, 30, 70]})

    if 'MACD' in strategy_name:
        parts = strategy_name.split('_')
        if len(parts) != 4:
            return None
        _, fast, slow, signal = parts
        macd_line = f"MACD_{fast}_{slow}_{signal}"
        signal_line = f"MACDs_{fast}_{slow}_{signal}"
        return Strategiser(strategy_name, {'cross': [macd_line, signal_line]})

    return None


def run_selected_strategies(analysis: StockAnalyser, indicator_params: dict, strategy_names: list):
    if not isinstance(analysis, StockAnalyser):
        raise TypeError("Expected a StockAnalyser object.")

    analysis.dataframe = analysis.initial_dataframe.copy()
    analysis.signals_dict = {}
    analysis.strategies_dict = {}

    if indicator_params:
        analysis.add_ind(indicator_params)

    for strategy_name in strategy_names:
        strategy = _build_strategy(strategy_name)
        if strategy is None:
            print(f"Warning: Could not create strategy for {strategy_name}. Skipping.")
            continue
        analysis.run_strat(strategy)

    return analysis


def prepare_analysis_view_data(analysis: StockAnalyser):
    if not isinstance(analysis, StockAnalyser):
        return None

    if 'Date' in analysis.dataframe.columns:
        analysis.dataframe['Date'] = pd.to_datetime(analysis.dataframe['Date'])
    else:
        analysis.dataframe.reset_index(inplace=True)
        analysis.dataframe.rename(columns={'index': 'Date'}, inplace=True)
        analysis.dataframe['Date'] = pd.to_datetime(analysis.dataframe['Date'])

    strategy_payload_by_name = {}
    for strategy_name, strategy_obj in analysis.strategies_dict.items():
        strategy_payload_by_name[strategy_name] = {
            'dataframe': strategy_obj.dataframe,
            'stats': strategy_obj.stats_df,
        }

    return {
        'dataframe': analysis.dataframe,
        'strategies_data': strategy_payload_by_name,
    }


# Backward-compatible aliases
create_analysis = create_stock_analysis
run_strategies = run_selected_strategies
get_analysis_data = prepare_analysis_view_data
