import json
from textwrap import dedent as d
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from flask_caching import Cache
import re
from pandas import DataFrame
import sys
import dash_table

app = dash.Dash(__name__)

CACHE_CONFIG = {
    'CACHE_TYPE': 'simple',
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)


#app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/dZVMbK.css'})

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowX': 'scroll'}}
#panda dataframe
x1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
y1 = [4, 1, 3, 5, 6, 2, 12, 45, 2, 6, 7]
x2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
y2 = [9, 4, 1, 4, 3, 9, 13, 23, 11, 3, 2]

aggr_list = [x1, y1, x2, y2]

df = DataFrame(aggr_list).transpose()
df.columns = ['x1', 'y1','x2', 'y2']

line1_x = int(len(x1)/3)
line2_x = int(len(x1)*2/3)

app.layout = html.Div( children =[

                html.Div(className='table', children= [
                    dash_table.DataTable(id='table',
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict('records'))
                ], style={'display': 'inline-block', 'width' : "20%", 'border': '3px solid black' }),
                          #'width': '350px','height': '100px','vertical-align': 'top', 'margin-left': '3vw', 'margin-top': '3vw'}),

                html.Div(className='Graph and Zoom data', children=[

                        html.Div(className='row', children=[
                            dcc.Graph(
                                id='basic-interactions',
                                className='six columns',
                                figure={
                                    'data': [
                                        {
                                        'x': df['x1'],
                                        'y': df['y1'],

                                        'name': 'Trace 1',
                                        'mode': 'markers',
                                        'marker': {
                                            'size': 12}
                                        },
                                        {
                                        'x': df['x2'],
                                        'y': df['y2'],

                                        'name': 'Trace 2',
                                        'mode': 'markers',
                                        'marker': {
                                            'size': 12}
                                        }
                                    ],
                                    'layout': {
                                        'shapes': [
                                            {
                                            'type': 'line',

                                            'x0': line1_x,
                                            'x1': line1_x,
                                            'xref': 'x',
                                            #a shape can be placed relative to an axis's position on the plot by adding the string ' domain' to the axis reference in the xref or yref attributes for shapes.

                                            'y0': 0,
                                            'y1': 1,
                                            'yref': 'paper',

                                            'line': {
                                                'width': 4,
                                                'color': 'rgb(30, 30, 30)',
                                                'dash': 'dashdot'}
                                            },
                                            {
                                            'type': 'line',

                                            'x0': line2_x,
                                            'x1': line2_x,
                                            'xref': 'x',
                                            #a shape can be placed relative to an axis's position on the plot by adding the string ' domain' to the axis reference in the xref or yref attributes for shapes.

                                            'y0': 0,
                                            'y1': 1,
                                            'yref': 'paper',

                                            'line': {
                                                'width': 4,
                                                'color': 'rgb(30, 30, 30)',
                                                'dash': 'dashdot'}
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
                            )
                        ]),

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
                ],style={'display': 'inline-block', 'width' : '70%', 'vertical-align': 'top', })
                         #'width': '1400px','height': '1000px','vertical-align': 'top', 'margin-left': '3vw', 'margin-top': '3vw'} )
])

#what should be the return value of this function
# fig['layout']['shapes'][0]['x0'] = func ()
# if this is what you want..... return value shouldn't be index but specific value

#what value should be conveyed as arguments?
#value should be  "shapes[0].x0": 3.451221409677921,
#colname should be ? x1 or x2 it doesn't matter since both of graphs have same x values
def find_closest_x_val(value, df, colname):
    exactmatch = df[df[colname] == value]
    # return value should be changed
    if not exactmatch.empty:
        return exactmatch[colname].values[0]
    else:
        try:
            flag = 0
            lowerneighbour_ind = df[df[colname] < value][colname].idxmax()
            flag = 1
            upperneighbour_ind = df[df[colname] > value][colname].idxmin()
        #if the x coordinate of line is out of range
        except ValueError:
            #far left
            if flag == 0:
                return df.iloc[0][colname]
            #far right
            elif flag == 1:
                return df.iloc[df.index.stop-1][colname]
            else:
                print("Unexpected error1")
        except :
            print("Unexpected error2:", sys.exc_info()[0])

    if (abs(df.iloc[lowerneighbour_ind][colname] - value) > abs(df.iloc[upperneighbour_ind][colname] - value)):
        return df.iloc[upperneighbour_ind][colname]
    else:
        return df.iloc[lowerneighbour_ind][colname]


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

    # Below is to limit the vertical movement of lines
    if (fig['layout']['shapes'][0]['y0'] != 0) or (fig['layout']['shapes'][0]['y1'] != 1):
        fig['layout']['shapes'][0]['y0'] = 0
        fig['layout']['shapes'][0]['y1'] = 1

    if (fig['layout']['shapes'][1]['y0'] != 0) or (fig['layout']['shapes'][1]['y1'] != 1):
        fig['layout']['shapes'][1]['y0'] = 0
        fig['layout']['shapes'][1]['y1'] = 1

    #line1 processing / index 0
    fig['layout']['shapes'][0]['x0'] = find_closest_x_val(fig['layout']['shapes'][0]['x0'] , df, 'x1')
    fig['layout']['shapes'][0]['x1'] = fig['layout']['shapes'][0]['x0']

    # line2 processing / index 1
    fig['layout']['shapes'][1]['x0'] = find_closest_x_val(fig['layout']['shapes'][1]['x0'], df, 'x1')
    fig['layout']['shapes'][1]['x1'] = fig['layout']['shapes'][1]['x0']


    #bind value of x axis in the lines to x axis of the closest point


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