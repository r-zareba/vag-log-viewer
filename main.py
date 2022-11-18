import base64
import io

import plotly.graph_objects as go
from dash import Dash, html, dcc, Output, Input, dash_table

from vaglog import VagLogReaderFactory

app = Dash(__name__)


def decode_csv_file_content(content: str) -> io.StringIO:
    _, content_string = content.split(",")
    decoded = base64.b64decode(content_string)
    return io.StringIO(decoded.decode("utf-8"))


def merge_data(data: dict) -> dict:
    final_data = dict()
    for measure_group in data:
        final_data = final_data | data[measure_group]
    return final_data


def append_index_to_data(data: dict) -> dict:
    first_key = tuple(data)[0]
    rows_len = len(tuple(data[first_key]))
    final_dict = {"Index": tuple(range(1, rows_len + 1))}
    return final_dict | data


def get_vaglog_data_from_csv_content(content: str) -> dict:
    decoded_content = decode_csv_file_content(content)
    vaglog = VagLogReaderFactory(decoded_content).generate_vaglog()
    return merge_data(vaglog.data)


app.layout = html.Div(
    children=[
        html.H1(children="Hello Dash"),
        html.Div(
            children="""
        Dash: A web application framework for your data.
    """
        ),
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
            style={
                "width": "100%",
                "height": "30%",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Don't allow multiple files to be uploaded at once
            multiple=False,
        ),
        dash_table.DataTable(
            id="dash-table",
            export_format="xlsx",
            fixed_rows={"headers": True},
            style_table={"height": 400},
            style_cell={
                "height": "auto",
                # all three widths are needed
                "minWidth": "80px",
                "width": "80px",
                "maxWidth": "80px",
                "whiteSpace": "normal",
            },
        ),
        dcc.Graph(id="table-graph"),
        dcc.Graph(id="plot-graph"),
    ]
)


@app.callback(
    Output("dash-table", "data"),
    Input("upload-data", "contents"))
def update_table(contents: str):
    if not contents:
        return [{}]

    data = get_vaglog_data_from_csv_content(contents)
    data = append_index_to_data(data)

    l = list()
    first_row = tuple(data)[0]

    for idx, _ in enumerate(data[first_row]):
        d = dict()
        for key in data.keys():
            d[key] = data[key][idx]
        l.append(d)

    return l


@app.callback(
    Output("plot-graph", "figure"),
    Input("upload-data", "contents"))
def update_plot(contents: str):
    figure = go.Figure()
    if not contents:
        return figure

    data = get_vaglog_data_from_csv_content(contents)
    timestamp = data[tuple(data)[0]]

    for x in data:
        if "TIME" in x.upper() or "CZAS" in x.upper():
            continue
        figure.add_trace(go.Scatter(x=timestamp, y=data[x], mode="lines", name=x))

    return figure


if __name__ == "__main__":
    app.run_server(debug=True)
