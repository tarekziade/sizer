import json
import os
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as FF
import plotly

import numpy as np
import pandas as pd


def create_graph(filename, container_name):
    prefix = 'docker_' + container_name
    df = pd.read_csv(filename)
    xs = []
    ys = []
    for x, y in enumerate(df[prefix + '_cpu']):
        xs.append(x)
        # XXX encoding ??!!
        y = json.loads(y.strip('"').replace("'", '"'))
        ys.append(y['total'])

    trace = go.Scatter(x=xs, y=ys, name='CPU')
    layout = go.Layout(title='%s load' % container_name,
                       plot_bgcolor='rgb(230, 230,230)', 
                       showlegend=True)
    fig = go.Figure(data=[trace], layout=layout)
    plotly.offline.plot(fig, filename='sizer_%s.html' % container_name)


if __name__ == '__main__':
    create_graph('/tmp/sizerdata/glances.csv', 'quirky_kalam')
