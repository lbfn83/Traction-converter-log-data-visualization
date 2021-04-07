import json
from textwrap import dedent as d
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from flask_caching import Cache
import re

app = dash.Dash(__name__)

CACHE_CONFIG = {
    'CACHE_TYPE': 'simple',
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)


app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/dZVMbK.css'})

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowX': 'scroll'}}

app.layout = html.Div(className='row', children=[
    dcc.Graph(
        id='basic-interactions',
        className='six columns',
        figure={
            'data': [{
                'x': [1, 2, 3, 4],
                'y': [4, 1, 3, 5],
                'text': ['a', 'b', 'c', 'd'],
                'customdata': ['c.a', 'c.b', 'c.c', 'c.d'],
                'name': 'Trace 1',
                'mode': 'markers',
                'marker': {
                    'size': 12
                }
            }, {
                'x': [1, 2, 3, 4],
                'y': [9, 4, 1, 4],
                'text': ['w', 'x', 'y', 'z'],
                'customdata': ['c.w', 'c.x', 'c.y', 'c.z'],
                'name': 'Trace 2',
                'mode': 'markers',
                'marker': {
                    'size': 12
                }
            }],
            'layout': {
                'shapes': [{
                    'type': 'line',

                    'x0': 0.5,
                    'x1': 0.5,
                    'xref': 'paper',
                    #a shape can be placed relative to an axis's position on the plot by adding the string ' domain' to the axis reference in the xref or yref attributes for shapes.

                    'y0': 0,
                    'y1': 1,
                    'yref': 'paper',

                    'line': {
                        'width': 4,
                        'color': 'rgb(30, 30, 30)',
                        'dash': 'dashdot'
                    }
                },
{
                    'type': 'line',

                    'x0': 0.8,
                    'x1': 0.8,
                    'xref': 'paper',
                    #a shape can be placed relative to an axis's position on the plot by adding the string ' domain' to the axis reference in the xref or yref attributes for shapes.

                    'y0': 0,
                    'y1': 1,
                    'yref': 'paper',

                    'line': {
                        'width': 4,
                        'color': 'rgb(30, 30, 30)',
                        'dash': 'dashdot'
                    }
                }
                ]
            }
        },
        config={
            'editable': True,
            'edits': {
                'shapePosition': True
            }
        }
    ),
    html.Div(
        className='six columns',
        children=[
            html.Div(
                [
                    dcc.Markdown(
                        d("""
                **Zoom and Relayout Data**

            """)),
                    html.Pre(id='relayout-data', style=styles['pre']),
                ]
            )
        ]
    )
])


@app.callback(
    [Output('relayout-data', 'children'),
    Output('basic-interactions', 'figure')],

    [Input('basic-interactions', 'relayoutData')],
    State('basic-interactions', 'figure')
)
def display_selected_data(relayoutData, fig):
    ctx = dash.callback_context
    #fig['layout']['yaxis']['range']
    #fig['layout']['shapes'][0]['y0']

    # if (fig['layout']['yaxis']['range'][0] != fig['layout']['shapes'][0]['y0']) or (fig['layout']['yaxis']['range'][1] != fig['layout']['shapes'][0]['y1']):
    #     fig['layout']['shapes'][0]['y0'] = fig['layout']['yaxis']['range'][0]
    #     fig['layout']['shapes'][0]['y1'] = fig['layout']['yaxis']['range'][1]

    if (fig['layout']['shapes'][0]['y0'] != 0) or (fig['layout']['shapes'][0]['y1'] != 1):
        fig['layout']['shapes'][0]['y0'] = 0
        fig['layout']['shapes'][0]['y1'] = 1

    if (fig['layout']['shapes'][1]['y0'] != 0) or (fig['layout']['shapes'][1]['y1'] != 1):
        fig['layout']['shapes'][1]['y0'] = 0
        fig['layout']['shapes'][1]['y1'] = 1

    if '' or None is relayoutData:
        print("none")
    elif 'autosize' in relayoutData.keys():
        print("autosize")

    elif any([ 'True' for relay_item in relayoutData.keys() if 'shapes' in relay_item ])  :
        print("shapes")

    elif any(['True' for relay_item in relayoutData.keys() if 'xaxis' in relay_item]):
        print("zoom")

    print("relayoutData:" + str(relayoutData))
    # figure['layout']['yaxis']['range']
    # figure.update_layout
    return [json.dumps(relayoutData, indent=2), fig]
# what is the condition?
#
#def retrieve_line()

if __name__ == '__main__':
    app.run_server(debug=True)