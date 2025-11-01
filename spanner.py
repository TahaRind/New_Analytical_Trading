import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import SpanSelector

def spanner(ax1,ax2,fig,xaxis,list_axes):
    # Fixing random state for reproducibility
    
    lines2 = []
    for i, y in enumerate(list_axes):
        line, = ax2.plot([], [], label=f'Data {i+1}')
        lines2.append(line)
    ax2.legend()
    
    def onselect(xmin, xmax):
        indmin, indmax = np.searchsorted(xaxis, (xmin, xmax))
        indmax = min(len(xaxis) - 1, indmax)
        
        for i, y in enumerate(list_axes):
            region_y = y[indmin:indmax]
            if len(region_y) >= 2:
                lines2[i].set_data(xaxis[indmin:indmax], region_y)
        
        ax2.set_xlim(xaxis[indmin], xaxis[indmax-1])
        ax2.set_ylim(np.min([y[indmin:indmax] for y in list_axes]), np.max([y[indmin:indmax] for y in list_axes]))
        fig.canvas.draw_idle()
    
    span = SpanSelector(
        ax1,
        onselect,
        "horizontal",
        useblit=True,
        props=dict(alpha=0.5, facecolor="tab:blue"),
        interactive=True,
        drag_from_anywhere=True
    )
    
    return span

