import json
import os
import csv
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as FF
import plotly

import numpy as np
import pandas as pd


def normalize_csv(filename, container_name):
    prefix = 'docker_' + container_name

    with open(filename) as input:
        reader = csv.reader(input)
        rows = 0
        with open(filename + '.tmp', 'w') as output:
            writer = csv.writer(output)
            for i, row in enumerate(reader):
                if i == 0:
                    rows = len(row)
                row = row[:rows]
                writer.writerow(row)        
    os.rename(filename + '.tmp', filename)


def create_graph(filename, container_name):
    normalize_csv(filename, container_name)
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
    create_graph('/tmp/sizerdata/glances.csv', 'thirsty_austin')
