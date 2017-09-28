import json
import os
import csv
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as FF
import plotly

import numpy as np
import pandas as pd


class DockerGraph(object):

    def __init__(self, container_name, filename):
        self.container_name = container_name
        self.filename = filename
        self.prefix = 'sensors_' + self.container_name
        self._normalize_csv()
        self._data = pd.read_csv(self.filename)

    def _normalize_csv(self):
        with open(self.filename) as input:
            reader = csv.reader(input)
            rows = 0
            with open(self.filename + '.tmp', 'w') as output:
                writer = csv.writer(output)
                for i, row in enumerate(reader):
                    if i == 0:
                        rows = len(row)
                    row = row[:rows]
                    writer.writerow(row)
        os.rename(self.filename + '.tmp', self.filename)

    def get_trace(self, name, title, field, op=None):
        xs = []
        ys = []
        for x, y in enumerate(self._data[self.prefix + '_' + name]):
            # XXX encoding ??!!
            try:
                y = json.loads(y.strip('"').replace("'", '"'))
                value = y.get(field, 0)
                if op is not None:
                    value = op(value)
                ys.append(value)
            except Exception as e:
                continue
            xs.append(x)

        return go.Scatter(x=xs, y=ys, name=title)

    def create(self, title=None):
        if title is None:
            title = '%s Resource Usage' % self.container_name
        traces = []
        for name, ltitle, field in (('cpu', 'CPU', 'total'),
                                    ('memory', 'Memory', 'usage'),
                                    ('network', 'Network RX', 'cumulative_rx'),
                                    ('network', 'Network TX', 'cumulative_tx'),
                                    ('io', 'I/O', 'usage')):
            if name == 'cpu':
                op = lambda x: x / 10.
            else:
                op = lambda x: x

            traces.append(self.get_trace(name, ltitle, field, op))

        layout = go.Layout(title=title, plot_bgcolor='rgb(230, 230,230)',
                           showlegend=True)
        fig = go.Figure(data=traces, layout=layout)
        plotly.offline.plot(fig, filename='sizer_%s.html' % self.container_name)
