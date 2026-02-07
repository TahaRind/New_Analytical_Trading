import matplotlib.pyplot as plt


def display_analysis_graph(dataframe, strategies_data, interactive=False):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dataframe['Date'], dataframe['Adj Close'], label='Adj Close', color='purple')
    ax.set_xlabel('Date')
    ax.set_ylabel('Adj Close')

    if strategies_data:
        ax2 = ax.twinx()
        ax2.set_ylabel('Strategy Profit')
        for strat_name, strat_payload in strategies_data.items():
            strategy_df = strat_payload.get('dataframe')
            if strategy_df is None or strategy_df.empty:
                continue
            if 'total_profit' in strategy_df:
                ax2.plot(strategy_df['Date'], strategy_df['total_profit'], label=strat_name, alpha=0.7)

        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper left')
    else:
        ax.legend(loc='upper left')

    fig.tight_layout()
    return fig
