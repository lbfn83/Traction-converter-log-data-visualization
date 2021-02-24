import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.express as px

# Things to solve
# ex) select 1, 2 in graph1
# then select 3 in graph2
# then go back to graph1 and select 4 => 1,2,4 are selected
# Which means there must be a buffer that keeps all the selected points
# even if selectedData callback event becomes None.
# Locate this buffer and find the way to reset this buffer as well

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.config['suppress_callback_exceptions'] = True


# make a sample data frame with 6 columns
np.random.seed(0)
df = pd.DataFrame({"Col " + str(i+1): np.random.rand(30) for i in range(6)})

loop_braker_container = html.Div(id='loop_breaker_container', children=[])

app.layout = html.Div([
    html.Div(
        dcc.Graph(id='g1',  config={'displayModeBar': False}),
        className='four columns'
    ),
    html.Div(
        dcc.Graph(id='g2', config={'displayModeBar': False}),
        className='four columns'
        ),
    html.Div(
        dcc.Graph(id='g3', config={'displayModeBar': False}),
        className='four columns'
    ),

    #This is registered to prevent the potential circular callback
    loop_braker_container,
], className='row')

def get_figure(df, x_col, y_col, selectedpoints, selectedpoints_local):
    #  # The below code is to draw the ractangle line over the range of selected points
    # Can be utilized to mark the area where the points are selected

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
@app.callback(
    [Output('g1', 'figure'),
     Output('g2', 'figure'),
     Output('g3', 'figure'),
     Output('loop_breaker_container', 'children')
     ],
    [Input('g1', 'selectedData'),
     Input('g2', 'selectedData'),
     Input('g3', 'selectedData')],
    [State('loop_breaker_container', 'children')]

)
def CB_selectedData_Update(selection1, selection2, selection3, loop_breaker_container  ):
    selectedpoints = df.index

    if all([selection1 == None, selection2 == None, selection3 == None, loop_breaker_container != []]):

        return [dash.no_update, dash.no_update, dash.no_update, []]

    else:

        #이걸 for문으로 돌리는게 문제인듯 / intersection..
        for selected_data in [selection1, selection2, selection3]:
            if selected_data and selected_data['points']:
                selectedpoints = np.intersect1d(selectedpoints,
                    [p['customdata'] for p in selected_data['points']])



        return [get_figure(df, "Col 1", "Col 2", selectedpoints, selection1),
                get_figure(df, "Col 3", "Col 4", selectedpoints, selection2),
                get_figure(df, "Col 5", "Col 6", selectedpoints, selection3),
                [html.Div(id='loop_breaker')]]

@app.callback(
    [Output('g1', 'selectedData'),
     Output('g2', 'selectedData'),
     Output('g3', 'selectedData'),

     ],
    [Input('loop_breaker', 'children')]

)
def CB_following_figure_Update(*input):
    return [None, None, None]

if __name__ == '__main__':
    app.run_server(debug=True)