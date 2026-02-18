import matplotlib.pyplot as plt


def build_analysis_figure(price_dataframe, strategy_payload_by_name, interactive=False):
    """Build a matplotlib figure for price and strategy performance."""
    figure, price_axis = plt.subplots(figsize=(12, 6))
    price_axis.plot(price_dataframe['Date'], price_dataframe['Close'], label='Close', color='purple')
    price_axis.set_xlabel('Date')
    price_axis.set_ylabel('Close')

    if strategy_payload_by_name:
        profit_axis = price_axis.twinx()
        profit_axis.set_ylabel('Strategy Profit')
        for strategy_name, strategy_payload in strategy_payload_by_name.items():
            strategy_dataframe = strategy_payload.get('dataframe')
            if strategy_dataframe is None or strategy_dataframe.empty:
                continue
            if 'total_profit' in strategy_dataframe:
                profit_axis.plot(
                    strategy_dataframe['Date'],
                    strategy_dataframe['total_profit'],
                    label=strategy_name,
                    alpha=0.7,
                )

        price_lines, price_labels = price_axis.get_legend_handles_labels()
        profit_lines, profit_labels = profit_axis.get_legend_handles_labels()
        profit_axis.legend(price_lines + profit_lines, price_labels + profit_labels, loc='upper left')
    else:
        price_axis.legend(loc='upper left')

    figure.tight_layout()
    return figure


# Backward-compatible alias

def display_analysis_graph(dataframe, strategies_data, interactive=False):
    return build_analysis_figure(dataframe, strategies_data, interactive=interactive)
