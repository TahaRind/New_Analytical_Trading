from SA_classes import StockAnalyser, Strategiser
from graph_manager import display_analysis_graph


if __name__ == "__main__":
    indicators = {
        'ema': ['5', '10', '20'],
        'rsi': ['14']
    }

    stock_input = {
        'name': 'UAL',
        'indicators': indicators,
        'outliers': False,
    }

    analysis = StockAnalyser(stock_input)

    strategies = [
        Strategiser('EMA_5', {'cross': ['EMA_5', 'Close']}),
        Strategiser('RSI_14', {'range': ['RSI_14', 30, 70]}),
        Strategiser('EMA5-RSI14', {'cross': ['EMA_5', 'Close'], 'range': ['RSI_14', 30, 70]}, max_positions=2),
    ]

    for strat in strategies:
        analysis.run_strat(strat)

    strategies_data = {
        name: {'dataframe': strat.dataframe, 'stats': strat.stats_df}
        for name, strat in analysis.strategies_dict.items()
    }

    fig = display_analysis_graph(analysis.dataframe, strategies_data)
    fig.show()
