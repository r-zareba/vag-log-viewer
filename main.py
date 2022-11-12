import base64
import io

import plotly.graph_objects as go
from dash import Dash, html, dcc, Output, Input, State

from vaglog import VagLogReaderFactory

app = Dash(__name__)


app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '30%',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Don't allow multiple files to be uploaded at once
        multiple=False
    ),

    dcc.Graph(
        id='table-graph'
    ),

    # dcc.Graph(
    #     id='example-graph2',
    #     figure=plot_figure
    # ),
])


# TODO Make Callback for data plot as well
# TODO Add index column to the Table!
@app.callback(
    Output('table-graph', 'figure'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'))
def update_table(contents, filename):
    if not contents or not filename:
        return go.Figure()

    # TODO Move to separate function
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    decoded_content = io.StringIO(decoded.decode('utf-8'))

    vaglog = VagLogReaderFactory(decoded_content).generate_vaglog()
    data = dict()

    for measure_group in vaglog.data:
        data = data | vaglog.data[measure_group]

    return go.Figure(
        data=[go.Table(
            header=dict(values=list(data.keys()),
                        fill_color='paleturquoise',
                        align='center'),
            cells=dict(values=list(data.values()),
                       fill_color='lavender',
                       align='center'))],
        layout={
            'title': 'My Table',
            'height': 800
            }
        )


if __name__ == '__main__':
    app.run_server(debug=True)
