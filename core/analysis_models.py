import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import pandas as pd
import yfinance as yf
import pandas_ta as ta


def masker(start,end,df):
    return (df >= start) & (df <= end)
    

class Strategiser():
  def __init__(self, name, indicator_strategies ,max_positions = 1,stop_loss = -1):
    self.name = name + '_strat'
    self.indicator_strategies_dict = indicator_strategies
    self.max_positions = max_positions
    self.stop_loss = stop_loss
    self.dataframe = None
    self.profit_frame = {'both' : [0,0],
                         'long' : [0,0],
                         'short' : [0,0]
                         }
    
  def update_profit_stats(self):
      cols = ['duration','profit','profit_l','profit_s']
      df = self.dataframe[cols].describe()
      
      normalised_profit = [None]
      for key in self.profit_frame:
          total_positions, total_profit = self.profit_frame[key]
          normalised_profit.append(total_profit / total_positions if total_positions else 0)
      
      df.loc['total_normalised'] = normalised_profit
      
      self.stats_df = df
      
class StockAnalyser():
    def __init__(self, analysis_input):
      """
      Initialise stock analysis.
      
      Parameters:
      - analysis_input: Dictionary containing info to configure analysis
                The dictionary consists of name,indicators,outliers)
                - name: Name of stock analysis instance. (string)
                - indicators: list of indicators to add
                - outliers: whether or not outliers should be produced
      """
      self.name = analysis_input['name']
      if isinstance(self.name, (list, tuple)):
          self.name = self.name[0] if self.name else ""
      self.name = str(self.name)

      self.dataframe = self._fetch_data()
      if self.dataframe.empty:
          raise ValueError(f"No data returned for ticker '{self.name}'. Please check the symbol and try again.")
      if 'Close' not in self.dataframe.columns:
          if 'Adj Close' in self.dataframe.columns:
              self.dataframe['Close'] = self.dataframe['Adj Close']
          else:
              raise ValueError(f"Ticker '{self.name}' data is missing a Close column.")
      self.dataframe['Day Change'] = (
          self.dataframe['Close'].astype(float)
          - self.dataframe['Close'].shift(1).astype(float)
      )
      self.initial_dataframe = self.dataframe.copy()
      self.outliers_dict = {}
      self.signals_dict = {}
      self.strategies_dict = {}
      self.add_ind(analysis_input['indicators'])
      self.outliers(analysis_input['outliers'])

    def _fetch_data(self):
      try:
          dataframe = yf.Ticker(self.name).history(period='max')
      except Exception:
          dataframe = pd.DataFrame()

      if dataframe.empty:
          try:
              dataframe = yf.download(self.name, period='max', progress=False, threads=False)
          except Exception:
              dataframe = pd.DataFrame()

      return dataframe
    
    def add_ind(self,indicators):
      """
      Add indicators to the dataset.
      
      Parameters:
      - indicators: dictionary containing indicators to add.
                     The dictionary consists of name, args.
                     - name: Name of the new indicator column. (string)
                     - instances: Instances of the indicator. (list of variabls)
      """
      
      for name,instances in indicators.items():
      
        for instance in instances:
          args = [int(i) for i in instance.split()]
      
          indicator_result = getattr(ta,name)(self.dataframe['Close'],*args)
          self.dataframe = pd.concat([self.dataframe, indicator_result], axis=1)
      
      self.dataframe.dropna(inplace=True)
      self.dataframe.reset_index(inplace = True)
    
    def outliers(self, detect):
      """
      Detect outliers in the 'Close' column of the dataset.
      
      Parameters:
      - detect: Boolean indicating whether or not to detect outliers.
      """
      
      if not detect:
          return
      
      outliers_dict = {}
      
      # Detect outliers using percentiles
      lower_percentile = 5
      upper_percentile = 95
      lower_threshold = np.percentile(self.dataframe['Close'], lower_percentile)
      upper_threshold = np.percentile(self.dataframe['Close'], upper_percentile)
      outliers_dict["outliers_percentile"] = self.dataframe['Close'].apply(lambda x: x < lower_threshold or x > upper_threshold)
      
      # Detect outliers using IQR
      quartile_1, quartile_3 = np.percentile(self.dataframe['Close'], [25, 75])
      iqr = quartile_3 - quartile_1
      lower_bound = quartile_1 - (1.5 * iqr)
      upper_bound = quartile_3 + (1.5 * iqr)
      outliers_dict["outliers_iqr"] = self.dataframe['Close'].apply(lambda x: x < lower_bound or x > upper_bound)
      
      # Detect outliers using z-score
      threshold = 3
      mean = np.mean(self.dataframe['Close'])
      std_dev = np.std(self.dataframe['Close'])
      z_scores = (self.dataframe['Close'] - mean) / std_dev
      outliers_dict["outliers_zscore"] = z_scores.abs() > threshold
      
      self.outliers_dict = outliers_dict
    
    def cross_over(self,A,B):
    
      # Generate crossover signals
      cross_up = ta.cross(self.dataframe[A], self.dataframe[B])
      cross_down = ta.cross(self.dataframe[B], self.dataframe[A])
      
      return cross_up,cross_down
    
    def out_of_range(self,A,lowerlim,upperlim):
      lower = self.dataframe[A] <= lowerlim
      upper = self.dataframe[A] >= upperlim
      
      return lower,upper
    
    #Function to generate signals
    def signal_generator(self,strat):
      """
      generate buy or sell signals for combined indicator in the strategy.
      
      Parameters:
      - signal_indicators: list of indicators to use when generating signals.
      
      """
      combined_signals = []
      
      for strategy_type, params in strat.indicator_strategies_dict.items():
        if strategy_type == 'cross': #if cross indicator i.e. EMA cross
          indicator_name, comparison_name = params
          signal_key = f"{strategy_type}:{indicator_name}:{comparison_name}"
          if signal_key not in self.signals_dict:
            var1, var2 = self.cross_over(indicator_name, comparison_name)
            self.signals_dict[signal_key] = [0] * len(self.dataframe) #no signal
            self.signals_dict[signal_key] = np.where(var1, 1, self.signals_dict[signal_key]) #buy signal
            self.signals_dict[signal_key] = np.where(var2, -1, self.signals_dict[signal_key]) #sell signal
          combined_signals.append(self.signals_dict[signal_key])
        elif strategy_type == 'range': #if range indicator i.e within RSI bounds
          indicator_name, lower_limit, upper_limit = params
          signal_key = f"{strategy_type}:{indicator_name}:{lower_limit}:{upper_limit}"
          if signal_key not in self.signals_dict:
            var1, var2 = self.out_of_range(indicator_name, lower_limit, upper_limit)
            self.signals_dict[signal_key] = [0] * len(self.dataframe) #no signal
            self.signals_dict[signal_key] = np.where(var1, 1, self.signals_dict[signal_key]) #buy signal
            self.signals_dict[signal_key] = np.where(var2, -1, self.signals_dict[signal_key]) #sell signal
          combined_signals.append(self.signals_dict[signal_key])
          
      if len(combined_signals) != 1: 
          combined_signals_trans = zip(*combined_signals)
          strat.dataframe['signal'] = [0 if sum(column) == 0 else column[0] or column[1] for column in combined_signals_trans] # hold if sum of signals is 0 otherwise buy or sell
      else:
          strat.dataframe['signal'] = combined_signals[0] # combined signal only contains one so is the first instance
            
    def calculate_profit(self,strat):
        max_positions = strat.max_positions
        stop_loss = strat.stop_loss
        if 'profit' not in strat.dataframe:
            strat.dataframe['profit'] = 0.0
            strat.dataframe['profit_l'] = 0.0
            strat.dataframe['profit_s'] = 0.0
            strat.dataframe['duration'] = 0

        temp_list = list(strat.dataframe['signal'])
        if 1 not in temp_list and -1 not in temp_list:
            return

        first_buy = temp_list.index(1) if 1 in temp_list else None
        first_sell = temp_list.index(-1) if -1 in temp_list else None
        if first_buy is None:
            index = first_sell
        elif first_sell is None:
            index = first_buy
        else:
            index = min(first_buy, first_sell)
        previous_date = strat.dataframe.loc[index, 'Date']
        previous_position = strat.dataframe.loc[index, 'signal']
        positions = 0
        stop_losses = []
        opened_positions =  pd.DataFrame({'Date' : [previous_date],'signal': [previous_position]})
        opened_positions['duration'] = opened_positions['profit'] = 0

        #finalised_positions = pd.DataFrame() #empty dataframe to contain final positions
        l_duration = 0
        s_duration = 0
        t_duration = 0
        
        def trigger_stop_loss(opened_positions, profit_type):
            #stop loss
            condition = opened_positions['profit'] < stop_loss * current_price
            stop_losses = opened_positions[condition]
            if len(stop_losses) > 0 :
                strat.dataframe.loc[index, profit_type] = sum(stop_losses['profit'])
                strat.dataframe.loc[index, 'profit'] = sum(stop_losses['profit'])
                opened_positions = opened_positions[~condition].copy()
            return sum(stop_losses['duration']), opened_positions
            
        def add_position(opened_positions, current_date, current_position):
            new_position = pd.DataFrame(
                {'Date': [current_date], 'signal': [current_position], 'duration': [0], 'profit': [0]}
            )
            return pd.concat([opened_positions, new_position], ignore_index=True)

        def close_all_positions(opened_positions,profit_type):

            #close all positions
            strat.dataframe.loc[index, profit_type] = sum(opened_positions['profit'])
            strat.dataframe.loc[index, 'profit'] = sum(opened_positions['profit'])
    
            #new positions
            opened_positions =  pd.DataFrame({'Date' : [current_date],'signal': [current_position]})
            opened_positions['profit'] = opened_positions['duration'] = 0
            return sum(opened_positions['duration']),opened_positions
        
        for index,row in strat.dataframe[index+1:].iterrows():
            current_date = row['Date']
            current_position = row['signal']
            current_daychange = self.dataframe['Day Change'].iloc[index]
            current_price = self.dataframe['Close'].iloc[index]
            opened_positions['duration'] += (current_date - previous_date).days
            
            if current_position == 1:
                if previous_position == 1:
                    #calculate profit + duration
                    opened_positions['profit'] += current_daychange
    
                    #stop loss
                    duration, opened_positions = trigger_stop_loss(opened_positions, 'profit_l')
                    l_duration += duration
                        
                    #new positions
                    if len(opened_positions) < max_positions:
                        opened_positions = add_position(opened_positions, current_date, current_position)
                        
                else:
                    
                    #calculate profit + duration
                    opened_positions['profit'] -= current_daychange
                    
                    #close all positions
                    duration , opened_positions = close_all_positions(opened_positions,'profit_s')
                    s_duration += duration
    
    
            elif current_position == -1:
    
                if previous_position <= 0:
                    #calculate profit + duration
                    opened_positions['profit'] -= current_daychange
    
                    #stop loss
                    duration, opened_positions = trigger_stop_loss(opened_positions, 'profit_s')
                    s_duration += duration
                        
                    #new positions
                    if len(opened_positions) < max_positions:
                        opened_positions = add_position(opened_positions, current_date, current_position)
                        
                else:
                    #calculate profit + duration
                    opened_positions['profit'] += current_daychange
                    
                    #close all positions
                    duration , opened_positions = close_all_positions(opened_positions,'profit_l')
                    l_duration += duration
    
            else:
                if previous_position == 1:
                    opened_positions['profit'] += current_daychange
                    #stop loss
                    duration, opened_positions = trigger_stop_loss(opened_positions, 'profit_l')
                    l_duration += duration
                    
                else:
                    opened_positions['profit'] -= current_daychange
                    #stop loss
                    duration, opened_positions = trigger_stop_loss(opened_positions, 'profit_s')
                    s_duration += duration
        
            previous_date,previous_position = current_date,current_position

        total_profit = float(strat.dataframe['profit'].sum())
        long_profit = float(strat.dataframe['profit_l'].sum())
        short_profit = float(strat.dataframe['profit_s'].sum())
        total_positions = int((strat.dataframe['signal'] != 0).sum())
        long_positions = int((strat.dataframe['signal'] == 1).sum())
        short_positions = int((strat.dataframe['signal'] == -1).sum())
        strat.profit_frame['both'] = [total_positions, total_profit]
        strat.profit_frame['long'] = [long_positions, long_profit]
        strat.profit_frame['short'] = [short_positions, short_profit]
    def run_strat(self,strat):
    
      """
      Create and run a strategy
      
      Parameters:
      - stratname: name of strategy
      - strategies: list of strategies to consider
      - graph: whether or not to produce a profit graph
      
      """
      strat.dataframe = self.dataframe[['Date', 'Close']].copy()
      self.signal_generator(strat)
      self.calculate_profit(strat)
      strat.update_profit_stats()
      strat.dataframe['total_profit'] = strat.dataframe['profit'].fillna(0).cumsum()
      strat.dataframe['total_profit_l'] = strat.dataframe['profit_l'].fillna(0).cumsum()
      strat.dataframe['total_profit_s'] = strat.dataframe['profit_s'].fillna(0).cumsum()
      
      self.strategies_dict[strat.name] = strat  
        
    
    def create_plot(self,start,end,ms,*graphs):
    
        
      fig = plt.figure(figsize=(20, 12))  # Setting the figure size
      gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])  # Creating grid for subplots
      
      ax1 = fig.add_subplot(gs[0])
      
      #plt.figure(figsize=(20,12))  # Setting the figure size
      
      #ax1 = plt.gca()
      
      # Set the x-axis major ticks format and interval
      #ax1.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
      #ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
      
      # Enable both horizontal and vertical grid lines
      #ax1.grid(True, which='both')
      
      ax2 = ax1.twinx()
      
      ax1.set_xlabel('X-axis')
      ax1.set_ylabel('Primary Y-axis', color='blue')
      ax2.set_ylabel('Secondary Y-axis', color='red')
      
      
      mask = masker(start,end,self.dataframe['Date'])
      dataframe_filtered =  self.dataframe[mask]
      
      
      ax1.plot(dataframe_filtered['Date'],dataframe_filtered['Close'], label = 'Close',color='purple',marker = 'o', markersize=ms)
      
      #graph_sims = ['o','+','x','*','a','b','c','d','e','f','g','h','i','z']
      graph_sims = [".",",","o","v","^","<",">","1","2","3","4","8","s","p","P","*","h","H","+","x","X","D","d","|","_",0,1,2,3,4,5,6,7,8,9,10,11]
      
      count = -1
      for graph in graphs:
        
        if graph._type == 'scatter':
          count+=1
          df = self.strategies_dict[graph.name].dataframe[mask]
      
          # Filter buy and sell signals
          buy_signals = df['signal'] == 1
          sell_signals = df['signal'] == -1
      
          ax1.scatter(dataframe_filtered['Date'][buy_signals], dataframe_filtered['Close'][buy_signals], label='Buy Signal' + ' ' + graph.name, color='green',marker = graph_sims[count], s=20)
          ax1.scatter(dataframe_filtered['Date'][sell_signals], dataframe_filtered['Close'][sell_signals], label='Sell Signal' + ' ' + graph.name, color='red',marker = graph_sims[count], s=20)
      
        elif graph.name == 'rsi':
          ax3 = fig.add_subplot(gs[1], sharex=ax1)
          ax3.set_ylabel('RSI', color='purple')
      
      
          ax3.plot(dataframe_filtered['Date'], dataframe_filtered['rsi'], label='RSI', color='purple',marker = 'o', markersize=ms)
          ax3.axhline(60, color='red', linestyle='--')  # Overbought line
          ax3.axhline(40, color='green', linestyle='--')  # Oversold line
          ax3.legend()
      
        elif graph._type == 'line':
      
          ax = ax1 if graph.dataframe_ID else ax2
          Yaxis = dataframe_filtered[graph.name] if graph.dataframe_ID else self.strategies_dict[graph.name].dataframe['profit'][mask]
      
          ax.plot(dataframe_filtered['Date'], Yaxis, label = graph.name, marker = 'o', markersize=ms)
          prof = Yaxis.iloc[-1]
          print(f"{graph.name} : {prof}")
        
      
      # Combine legends from both axes
      lines, labels = ax1.get_legend_handles_labels()
      lines2, labels2 = ax2.get_legend_handles_labels()
      ax1.legend(lines + lines2, labels + labels2)
      
      plt.title(self.name)
      plt.show()
      
