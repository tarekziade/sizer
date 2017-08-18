import os
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as FF
import plotly

import numpy as np
import pandas as pd


def create_graph(filename):
    df = pd.read_csv(filename)
    import pdb; pdb.set_trace()

    trace = go.Scatter(x = df['AAPL_x'], y = df['AAPL_y'],
                       name='Share Prices (in USD)')
    layout = go.Layout(title='Apple Share Prices over time (2014)',
                       plot_bgcolor='rgb(230, 230,230)', 
                       showlegend=True)
    fig = go.Figure(data=[trace], layout=layout)
    plotly.offline.plot(fig, filename='apple-stock-prices.html')


