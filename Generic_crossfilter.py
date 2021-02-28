import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State,MATCH, ALL
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Find out why we use the below line
app.config['suppress_callback_exceptions'] = True

#directory select

#Read the list of files and put the list into variable

#and then using panda all of data aggregated in single data frame



#This part should be later implemented with text inputs
Graph_count = 8

np.random.seed(0)
df = pd.DataFrame({"Col " + str(i+1): np.random.rand(30) for i in range(Graph_count*2)})


Graph_container = html.Div(id='graph-container', children=[])

app.layout = html.Div([

    Graph_container,

], className='row')


for i in range(Graph_count):
    Graph_container.children.append( dcc.Graph (
            id={
                'type': 'dcc_graph',
                'index': i
            },

        )
    )

#how to make our graph more aesthetic ?
def get_figure(df, x_col, y_col, selectedpoints, selectedpoints_local):
    #drag 해서 생성된 사각형 범주를 가리키는 건데... 이건 내가 만들려는 것과
    #관계가 없기 때문에... 삭제 가능

    # if selectedpoints_local and selectedpoints_local['range']:
    #     ranges = selectedpoints_local['range']
    #     selection_bounds = {'x0': ranges['x'][0], 'x1': ranges['x'][1],
    #                         'y0': ranges['y'][0], 'y1': ranges['y'][1]}
    # else:
    #     selection_bounds = {'x0': np.min(df[x_col]), 'x1': np.max(df[x_col]),
    #                         'y0': np.min(df[y_col]), 'y1': np.max(df[y_col])}

    # set which points are selected with the `selectedpoints` property
    # and style those points with the `selected` and `unselected`
    # attribute. see
    # https://medium.com/@plotlygraphs/notes-from-the-latest-plotly-js-release-b035a5b43e21
    # for an explanation

    fig = px.scatter(df, x=df[x_col], y=df[y_col], text=df.index)

    fig.update_traces(selectedpoints=selectedpoints,
                      customdata=df.index,
                      mode='markers+text', marker={ 'color': 'rgba(0, 116, 217, 0.7)', 'size': 20 }, unselected={'marker': { 'opacity': 0.3 }, 'textfont': { 'color': 'rgba(0, 0, 0, 0)' }})

    fig.update_layout(margin={'l': 20, 'r': 0, 'b': 15, 't': 5}, clickmode='event+select')#dragmode='select',, hovermode=False

    # fig.add_shape(dict({'type': 'rect',
    #                     'line': { 'width': 1, 'dash': 'dot', 'color': 'darkgrey' }},
    #                    **selection_bounds))
    return fig

# this callback defines 3 figures
# as a function of the intersection of their 3 selections
# we saparately define the reflection of our data to the graph
# as when first boot up, this call back will invoke the get figure without any selected points
# and populate the graph


# Another possibility is using MATCH /
# internal logic should be more refined to implement in that regard, though.
# especailly for argument that should be sent to get_figure func
# but really? how MATCH in Output function works?
# What we will need is ctx for that.

#The selected Data event in the past is persistent, so gotta make sure that the selecteddata events turning into Null everytime this callback activated
@app.callback(
    [Output({'type': 'dcc_graph', 'index': ALL}, 'figure'),
     Output({'type': 'dcc_graph', 'index': ALL}, 'selectedData'),
    ],
    [Input({'type': 'dcc_graph', 'index': MATCH}, 'selectedData')],
    [State({'type': 'dcc_graph', 'index': MATCH}, 'id')]
)
def callback(sel_values, id):
    ctx = dash.callback_context


    selectedpoints = df.index

    #이걸 for문으로 돌리는게 문제인듯 / intersection..


    if sel_values == None:
        return_1h = [get_figure(df, "Col {}".format(2 * (i + 1) - 1), "Col {}".format(2 * (i + 1)), [], sel_values) for i in range(Graph_count)]
        return [return_1h, None, None, None, None]
    else:
        # dictionary and for loop
        # https://realpython.com/iterate-through-dictionary-python/
        # sel_values 의 값이 어떻게 오는지 잘 확인하련...

        for selected_data in sel_values:
            if selected_data and selected_data['points']:
                selectedpoints = np.intersect1d(selectedpoints,
                    [p['customdata'] for p in selected_data['points']])

        return_1h = [get_figure(df, "Col {}".format(2 * (i + 1) - 1), "Col {}".format(2 * (i + 1)), selectedpoints, sel_values) for i in range(Graph_count)  ]
        return [return_1h, None, None, None, None]


if __name__ == '__main__':
    app.run_server(debug=True)