#%%imports

from SA_classes import *
from graph_manager import grapher

#%%Initalise and Run strat

indicators = {'ema' : ['5','10','20','50','100','200'],
                             'rsi' : ['9','14','21']}

graph_list = []

stock_input = {'name':'ual',
                  'indicators':indicators,
                  'outliers':False
                  }

ual = StockAnalyser(stock_input)

for key,values in indicators.items():
    for val in values:
        name = key.upper() + '_' + val

        if key =='ema':
            strat = Strategiser(name,{'cross':[name,'Adj Close']})
        elif key =='rsi':
            strat = Strategiser(name,{'range':[name,30,70]})
            
        ual.run_strat(strat)

strat = Strategiser('EMA5-RSI9',{'cross':['EMA_5','Adj Close'],'range':['RSI_9',30,70]})
ual.run_strat(strat)

strat = Strategiser('EMA5-RSI9_2',{'cross':['EMA_5','Adj Close'],'range':['RSI_9',30,70]},positions = 2)
ual.run_strat(strat)
#%%
strat = Strategiser('EMA5-RSI9_3',{'cross':['EMA_5','Adj Close'],'range':['RSI_9',30,70]},positions = 3)
ual.run_strat(strat)

#%%graphs
g1 = grapher(ual,'profit',['EMA_5_strat','RSI_9_strat','EMA5-RSI9_strat','EMA5-RSI9_2_strat','EMA5-RSI9_3_strat'])

text_box,submit,modes,modes_callback,check,callback,plt = g1.create_graph()

check.on_clicked(callback)
modes.on_clicked(modes_callback)
text_box.on_submit(submit)

plt.show()
        
#%%Graph strat

g1 = grapher('EMA_20_strat',0,'line')
g2 = grapher('EMA_20_strat',0,'scatter')
g3 = grapher('EMA_20',1,'line')


g4 = grapher('EMA_20_RSI_20_strat',0,'line')
g5 = grapher('EMA_20_RSI_20_strat',0,'scatter')

g6 = grapher('EMA_7_strat',0,'line')
g7 = grapher('EMA_7_strat',0,'scatter')


start = '2020-01-01'
#start = analysis1.dataframe['Date'].iloc[0]

# #end = '2021-01-01'
# end = analysis1.dataframe['Date'].iloc[-1]

# stocks_dict['ual'].create_plot(start,end,0,g1,g3,g4,g5)

# strat3 = strategiser('EMA_7_strat',{'cross':['EMA_7_v_Adj','Adj Close','EMA_7']},False)

# stocks_dict['ual'].run_strat(strat3)

# stocks_dict['ual'].create_plot(start,end,1,g1,g2,g6,g7)
