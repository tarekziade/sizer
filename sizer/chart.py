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


def get_trace(container_name, data, name, title, field):
    prefix = 'docker_' + container_name
    xs = []
    ys = []
    for x, y in enumerate(data[prefix + '_' + name]):
        xs.append(x)
        # XXX encoding ??!!
        y = json.loads(y.strip('"').replace("'", '"'))
        ys.append(y.get(field, 0))

    return go.Scatter(x=xs, y=ys, name=title)

def create_graph(filename, container_name):
    normalize_csv(filename, container_name)
    prefix = 'docker_' + container_name
    df = pd.read_csv(filename)
    cpu_trace = get_trace(container_name, df, 'cpu', 'CPU', 'total')
    memory_trace = get_trace(container_name, df, 'memory', 'Memory', 'usage')
    rx_trace = get_trace(container_name, df, 'network', 'Network RX', 'cumulative_rx')
    tx_trace = get_trace(container_name, df, 'network', 'Network TX', 'cumulative_tx')
    io_trace = get_trace(container_name, df, 'io', 'I/O', 'usage')
    
    layout = go.Layout(title='%s Resource Usage' % container_name,
                       plot_bgcolor='rgb(230, 230,230)', 
                       showlegend=True)
    fig = go.Figure(data=[cpu_trace, memory_trace, rx_trace, tx_trace, io_trace], layout=layout)
    plotly.offline.plot(fig, filename='sizer_%s.html' % container_name)


if __name__ == '__main__':
    create_graph('/tmp/sizerdata/glances.csv', 'thirsty_austin')
