

import streamlit as st
#import debugpy
# if "debugger_attached" not in st.session_state:
#     debugpy.listen(("localhost", 5679))
#     st.session_state.debugger_attached = True
# print("Waiting for debugger attach...")
# debugpy.breakpoint()





import os # Still useful for checking file existence, though SA_manager will handle the core logic
from SA_orchestrator import create_analysis, run_strategies, get_analysis_data
from SA_manager import load_analysis, save_analysis
from graph_manager import display_analysis_graph

# Page configuration
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Interactive Stock Analysis Dashboard")

# Initialize session state for the stock_analyser object if it doesn't exist
if 'stock_analyser_obj' not in st.session_state:
    st.session_state.stock_analyser_obj = None

analysis_name = st.text_input("Enter Stock Analysis Name (e.g., 'MyUALAnalysis')", key="analysis_name_input")

col1, col2 = st.columns(2)

with col1:
    if st.button("Load Analysis"):
        if analysis_name:
            try:
                # Call the new load_analysis from SA_manager
                st.session_state.stock_analyser_obj = load_analysis(f"{analysis_name}.pkl")
                st.success(f"Successfully loaded analysis: {analysis_name}")
            except FileNotFoundError:
                st.error(f"Analysis '{analysis_name}' not found. Please create it first.")
            except Exception as e:
                st.error(f"Error loading analysis: {e}")
                print(e)
        else:
            st.warning("Please enter an analysis name to load.")

with col2:
    if st.button("Create New Analysis"):
        if analysis_name:
            # Placeholder for initial indicators, will be configured later
            initial_indicators = {'ema': ['5', '10'], 'rsi': ['14']}
            stock_names = st.text_input("Enter Stock Tickers (comma-separated, e.g., 'UAL,AAPL,MSFT')", key="stock_name_input_create")
            
            if st.button("Add stock"):
                if stock_names:
                    try:
                        # Call the new create_analysis from SA_orchestrator
                        st.session_state.stock_analyser_obj = create_analysis(stock_names.upper(), initial_indicators, False)
                        st.success(f"New analysis '{analysis_name}' created successfully for {stock_names.upper()}.")
                    except Exception as e:
                        st.error(f"Error creating analysis: {e}")
                else:
                    st.warning("Please enter at least one stock ticker to create a new analysis.")
            else:
                st.warning("Please enter a name for the new analysis.")

            

# Display current active analysis
if st.session_state.stock_analyser_obj:
    st.write(f"**Current Active Analysis:** {st.session_state.stock_analyser_obj.name}")
else:
    st.info("No active stock analysis. Load or create one to proceed.")


if st.session_state.stock_analyser_obj:
    st.header("Configure Analysis Parameters")

    # Stock Ticker Selection (assuming 'name' in stock_analyser is the primary ticker)
    # For a more robust solution, you might allow adding multiple tickers or changing the primary.
    st.write(f"**Analyzing Stock:** {st.session_state.stock_analyser_obj.name}")

    # Indicator Selection
    st.subheader("Select Indicators")
    available_indicators = ["EMA", "RSI", "MACD"] # This could be dynamic from SA_classes
    selected_indicators = st.multiselect(
        "Choose technical indicators:",
        options=available_indicators,
        default=["EMA", "RSI"],
        key="indicator_select"
    )

    # Placeholder for indicator-specific parameters (e.g., EMA periods, RSI ranges)
    # This would require more detailed UI elements based on selected_indicators
    indicator_params = {}
    for indicator in selected_indicators:
        if indicator == "EMA":
            ema_periods_str = st.text_input(f"Enter EMA periods for {st.session_state.stock_analyser_obj.name} (comma-separated, e.g., '5,10,20')", value="5,10,20", key=f"ema_periods_{st.session_state.stock_analyser_obj.name}")
            indicator_params['ema'] = [p.strip() for p in ema_periods_str.split(',') if p.strip()]
        elif indicator == "RSI":
            rsi_periods_str = st.text_input(f"Enter RSI periods for {st.session_state.stock_analyser_obj.name} (comma-separated, e.g., '14,21')", value="14,21", key=f"rsi_periods_{st.session_state.stock_analyser_obj.name}")
            indicator_params['rsi'] = [p.strip() for p in rsi_periods_str.split(',') if p.strip()]
        # Add more logic for other indicators like MACD

    # Strategy Configuration (simplified for now)
    st.subheader("Define Strategies")
    # This section would be more complex, allowing users to define rules
    # For now, let's assume simple strategies based on selected indicators
    strategies_to_run = []
    if "EMA" in selected_indicators and "RSI" in selected_indicators:
        if indicator_params.get('ema') and indicator_params.get('rsi'):
            strategies_to_run.append(f"EMA_{indicator_params['ema'][0]}-RSI_{indicator_params['rsi'][0]}")
    elif "EMA" in selected_indicators and indicator_params.get('ema'):
        for period in indicator_params['ema']:
            strategies_to_run.append(f"EMA_{period}")
    elif "RSI" in selected_indicators and indicator_params.get('rsi'):
        for period in indicator_params['rsi']:
            strategies_to_run.append(f"RSI_{period}")

    if strategies_to_run:
        st.write("Proposed Strategies:", ", ".join(strategies_to_run))
    else:
        st.info("Select indicators to propose strategies.")

    # Button to apply changes and run analysis
    if st.button("Run Analysis & Update Strategies"):
        if st.session_state.stock_analyser_obj:
            try:
                # Update indicators and run strategies via the orchestrator
                st.session_state.stock_analyser_obj = run_strategies(
                    st.session_state.stock_analyser_obj,
                    indicator_params, # Pass the detailed indicator parameters
                    strategies_to_run # Pass the list of strategies to run
                )
                st.success("Analysis and strategies updated successfully!")
            except Exception as e:
                st.error(f"Error running analysis: {e}")
        else:
            st.warning("No active analysis to run. Please load or create one.")


if st.session_state.stock_analyser_obj:
    st.header("Analysis Results")

    # Get data for plotting from the orchestrator (or directly from stock_analyser if exposed)
    analysis_data = get_analysis_data(st.session_state.stock_analyser_obj)

    if analysis_data:
        st.subheader("Price and Strategy Performance Chart")
        # Call the graph_manager to display the graph
        fig = display_analysis_graph(
            analysis_data['dataframe'],
            analysis_data['strategies_data'], # This would be a structured dict/list of strategy results
            interactive=True # Assuming spanner.py provides interactivity
        )
        st.pyplot(fig)

        st.subheader("Strategy Performance Metrics")
        # Display simplified profit statistics
        if hasattr(st.session_state.stock_analyser_obj, 'strategies_dict') and st.session_state.stock_analyser_obj.strategies_dict:
            for strat_name, strategy_obj in st.session_state.stock_analyser_obj.strategies_dict.items():
                if hasattr(strategy_obj, 'stats_df') and strategy_obj.stats_df is not None:
                    st.write(f"**{strat_name} Performance:**")
                    st.dataframe(strategy_obj.stats_df)
                else:
                    st.info(f"No performance data available for strategy: {strat_name}")
        else:
            st.info("Run analysis to see strategy performance metrics.")
    else:
        st.info("No data available to display. Run analysis first.")

if st.session_state.stock_analyser_obj:
    st.header("Save Current Analysis")
    if st.button("Save Analysis"):
        try:
            # Call the new save_analysis from SA_manager
            save_analysis(st.session_state.stock_analyser_obj, f"{st.session_state.stock_analyser_obj.name}.pkl")
            st.success(f"Analysis '{st.session_state.stock_analyser_obj.name}' saved successfully!")
        except Exception as e:
            st.error(f"Error saving analysis: {e}")
