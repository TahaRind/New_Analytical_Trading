import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from matplotlib.widgets import CheckButtons
from matplotlib.widgets import TextBox
from matplotlib.dates import DateFormatter

class display_analysis_graph():
    def __init__(self, stock_analysis, _type, strategies):
        self.stock_analysis = stock_analysis
        self.graphs = [stock_analysis.strategies_dict[strat] for strat in strategies]
                  
    def create_graph(self):
             

        fig = plt.figure(figsize=(20, 12))  # Setting the figure size
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])  # Creating grid for subplots
        ax = fig.add_subplot(gs[0])
        ax2 = ax.twinx()
        ax.set_xlabel('Dates')
        ax.set_ylabel('Primary Y-axis', color='blue')
        ax2.set_ylabel('Secondary Y-axis', color='red')
        
        list_of_graphs = {'normal':{},
                          'long':{},
                          'short':{},
                          'long_scatter':{},
                          'short_scatter':{}
                          }

        
        xaxis = self.stock_analysis.dataframe['Date']
        
        ax2.plot(xaxis, self.stock_analysis.dataframe['Adj Close'], lw=2)
        graph_sims = [",","o","v","^","<",">","1","2","3","4","8","s","p","P","*","h","H","+","x","X","D","d","|","_",0,1,2,3,4,5,6,7,8,9,10,11]
        count = 0      
                   
        for graph in self.graphs:
            list_of_graphs['normal'][graph.name], = ax.plot(xaxis, graph.dataframe['total_profit'], visible=False, label=graph.name)
            list_of_graphs['long'][graph.name], = ax.plot(xaxis, graph.dataframe['total_profit_l'], visible=False, label=graph.name)
            list_of_graphs['short'][graph.name], = ax.plot(xaxis, graph.dataframe['total_profit_s'], visible=False, label=graph.name)
            buy_signals = graph.dataframe[graph.dataframe['signal'] == 1]
            sell_signals = graph.dataframe[graph.dataframe['signal'] == -1]
            list_of_graphs['long_scatter'][graph.name] = ax2.scatter(buy_signals['Date'], buy_signals['Adj Close'], visible=False,marker = graph_sims[count],s=20,color = 'green', label=graph.name)
            list_of_graphs['short_scatter'][graph.name] = ax2.scatter(sell_signals['Date'], sell_signals['Adj Close'], visible=False,marker = graph_sims[count],s=20,color = 'red', label=graph.name)
            count+=1
            
        # Make checkbuttons with all plotted lines with correct visibility
        rax = ax.inset_axes([0.0, 0.0, 0.2, 0.2])
        check = CheckButtons(
            ax=rax,
            labels = list_of_graphs['normal'].keys()
        )
        
        rax2 = ax.inset_axes([0.0, 0.2, 0.12, 0.2])
        modes = CheckButtons(
            ax=rax2,
            labels=['short','long','short_scatter','long_scatter']
        )
        
        def callback(label):
            ln = list_of_graphs['normal'][label]
            ln.set_visible(not ln.get_visible())
        
        def modes_callback(label):
            
            checked_labels = check.get_checked_labels()
            
            for val in checked_labels:
                ln = list_of_graphs[label][val]
                ln.set_visible(not ln.get_visible())
                  
        l, = ax2.plot(xaxis, self.stock_analysis.dataframe['Adj Close'],visible = False )
        
        def submit(expression):

            try:
                ydata = self.stock_analysis.dataframe[expression]
                l.set_ydata(ydata)
                l.set_visible(True)
                ax.relim()
                ax.autoscale_view()
                plt.draw()
            except:
                print(f"An exception occurred,{expression} may not exist")
            

        axbox = fig.add_axes([0.2, 0.2, 0.2, 0.05])
        text_box = TextBox(axbox, "Evaluate indicator", textalignment="center")
        
        
        return text_box,submit,modes,modes_callback,check,callback,plt