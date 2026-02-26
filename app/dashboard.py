from pathlib import Path
import sys

import streamlit as st

# Ensure project root is importable when running:
#   streamlit run app/dashboard.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.analysis_service import (
    create_stock_analysis,
    prepare_analysis_view_data,
    run_selected_strategies,
)
from core.persistence import load_analysis_from_file, save_analysis_to_file
from core.plotting import build_analysis_figure

st.set_page_config(
    page_title="Stock Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Interactive Stock Analysis Dashboard")

if 'active_analysis' not in st.session_state:
    st.session_state.active_analysis = None
if 'active_analysis_name' not in st.session_state:
    st.session_state.active_analysis_name = None
if 'show_create_form' not in st.session_state:
    st.session_state.show_create_form = False

analysis_name_input = st.text_input(
    "Enter Stock Analysis Name (e.g., 'MyUALAnalysis')",
    key="analysis_name_input",
)

load_column, create_column = st.columns(2)

with load_column:
    if st.button("Load Analysis"):
        if not analysis_name_input:
            st.warning("Please enter an analysis name to load.")
        else:
            try:
                st.session_state.active_analysis = load_analysis_from_file(f"{analysis_name_input}.pkl")
                st.session_state.active_analysis_name = analysis_name_input
                st.success(f"Successfully loaded analysis: {analysis_name_input}")
            except FileNotFoundError:
                st.exception(FileNotFoundError(f"Analysis '{analysis_name_input}' not found. Please create it first."))
            except Exception as error:
                st.exception(error)

with create_column:
    if st.button("Create New Analysis"):
        st.session_state.show_create_form = True

    if st.session_state.show_create_form:
        if not analysis_name_input:
            st.warning("Please enter a name for the new analysis.")
        else:
            default_indicators = {'ema': ['5', '10'], 'rsi': ['14']}
            with st.form("create_analysis_form"):
                ticker_text = st.text_input(
                    "Enter Stock Tickers (comma-separated, e.g., 'UAL,AAPL,MSFT')",
                    key="stock_name_input_create",
                )
                create_submitted = st.form_submit_button("Add stock")

            if create_submitted:
                cleaned_tickers = [
                    ticker.strip().strip("'\"")
                    for ticker in ticker_text.split(',')
                    if ticker.strip()
                ]
                if not cleaned_tickers:
                    st.warning("Please enter at least one stock ticker to create a new analysis.")
                else:
                    if len(cleaned_tickers) > 1:
                        st.info("Multiple tickers detected. Creating analysis for the first ticker only.")
                    primary_ticker = cleaned_tickers[0].upper()
                    try:
                        st.session_state.active_analysis = create_stock_analysis(
                            primary_ticker,
                            default_indicators,
                            False,
                        )
                        st.session_state.active_analysis_name = analysis_name_input
                        st.session_state.show_create_form = False
                        st.success(f"New analysis '{analysis_name_input}' created successfully for {primary_ticker}.")
                    except Exception as error:
                        st.exception(error)

active_analysis = st.session_state.active_analysis
if active_analysis:
    st.write(f"**Current Active Analysis:** {active_analysis.name}")
else:
    st.info("No active stock analysis. Load or create one to proceed.")

if active_analysis:
    st.header("Configure Analysis Parameters")
    st.write(f"**Analyzing Stock:** {active_analysis.name}")

    indicator_choices = st.multiselect(
        "Choose technical indicators:",
        options=["EMA", "RSI", "MACD"],
        default=["EMA", "RSI"],
        key="indicator_select",
    )

    indicator_params = {}
    for indicator_name in indicator_choices:
        if indicator_name == "EMA":
            ema_period_text = st.text_input(
                f"Enter EMA periods for {active_analysis.name} (comma-separated, e.g., '5,10,20')",
                value="5,10,20",
                key=f"ema_periods_{active_analysis.name}",
            )
            indicator_params['ema'] = [value.strip() for value in ema_period_text.split(',') if value.strip()]
        elif indicator_name == "RSI":
            rsi_period_text = st.text_input(
                f"Enter RSI periods for {active_analysis.name} (comma-separated, e.g., '14,21')",
                value="14,21",
                key=f"rsi_periods_{active_analysis.name}",
            )
            indicator_params['rsi'] = [value.strip() for value in rsi_period_text.split(',') if value.strip()]
        elif indicator_name == "MACD":
            macd_param_text = st.text_input(
                "Enter MACD params as fast slow signal (comma-separated sets, e.g., '12 26 9,8 21 5')",
                value="12 26 9",
                key=f"macd_params_{active_analysis.name}",
            )
            indicator_params['macd'] = [value.strip() for value in macd_param_text.split(',') if value.strip()]

    strategy_names = []
    if "EMA" in indicator_choices and "RSI" in indicator_choices:
        if indicator_params.get('ema') and indicator_params.get('rsi'):
            strategy_names.append(f"EMA_{indicator_params['ema'][0]}-RSI_{indicator_params['rsi'][0]}")
    elif "MACD" in indicator_choices and indicator_params.get('macd'):
        for macd_set in indicator_params['macd']:
            try:
                fast_period, slow_period, signal_period = macd_set.split()
                strategy_names.append(f"MACD_{fast_period}_{slow_period}_{signal_period}")
            except ValueError:
                st.warning(f"Invalid MACD parameter set: '{macd_set}'. Expected format: fast slow signal")
    elif "EMA" in indicator_choices and indicator_params.get('ema'):
        strategy_names.extend([f"EMA_{period}" for period in indicator_params['ema']])
    elif "RSI" in indicator_choices and indicator_params.get('rsi'):
        strategy_names.extend([f"RSI_{period}" for period in indicator_params['rsi']])

    if strategy_names:
        st.write("Proposed Strategies:", ", ".join(strategy_names))
    else:
        st.info("Select indicators to propose strategies.")

    if st.button("Run Analysis & Update Strategies"):
        try:
            st.session_state.active_analysis = run_selected_strategies(
                active_analysis,
                indicator_params,
                strategy_names,
            )
            st.success("Analysis and strategies updated successfully!")
        except Exception as error:
            st.exception(error)

if st.session_state.active_analysis:
    st.header("Analysis Results")
    analysis_view_data = prepare_analysis_view_data(st.session_state.active_analysis)

    if analysis_view_data:
        st.subheader("Price and Strategy Performance Chart")
        figure = build_analysis_figure(
            analysis_view_data['dataframe'],
            analysis_view_data['strategies_data'],
            interactive=True,
        )
        st.pyplot(figure)

        st.subheader("Strategy Performance Metrics")
        if st.session_state.active_analysis.strategies_dict:
            for strategy_name, strategy in st.session_state.active_analysis.strategies_dict.items():
                if getattr(strategy, 'stats_df', None) is not None:
                    st.write(f"**{strategy_name} Performance:**")
                    st.dataframe(strategy.stats_df)
                else:
                    st.info(f"No performance data available for strategy: {strategy_name}")
        else:
            st.info("Run analysis to see strategy performance metrics.")

if st.session_state.active_analysis:
    st.header("Save Current Analysis")
    if st.button("Save Analysis"):
        try:
            filename_root = st.session_state.active_analysis_name or st.session_state.active_analysis.name
            save_analysis_to_file(st.session_state.active_analysis, f"{filename_root}.pkl")
            st.success(f"Analysis '{filename_root}' saved successfully!")
        except Exception as error:
            st.exception(error)
