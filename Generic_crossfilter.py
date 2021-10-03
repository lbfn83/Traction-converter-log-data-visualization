import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd

from dash.dependencies import Input, Output, MATCH, ALL, State

import plotly.express as px
from flask_caching import Cache
import _PandaFileHandling as PFH
from queue import PriorityQueue as PQ
from dash.exceptions import PreventUpdate

import sys




#dash version 1.10.0
#dash renderer 1.3.0

# Things to solve
# ex) select 1, 2 in graph1
# then select 3 in graph2
# then go back to graph1 and select 4 => 1,2,4 are selected
# Which means there must be a buffer that keeps all the selected points
# even if selectedData callback event becomes None.
# Locate this buffer and find the way to reset this buffer as well

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


# Find out why we use the below line
app.config['suppress_callback_exceptions'] = True

CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'simple',
    #'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379')
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)


#directory select

#Read the list of files and put the list into variable
#and then using panda all of data aggregated in single data frame

full_path = PFH.print_file_path_list()

df = PFH.Raw_Data_to_Pandas_DF(full_path)

filename_list = list()

for column in df.columns:
    if 'time' not in column:
        filename_list.append(column)
Graph_count = len(filename_list)


Graph_container = html.Div(id='graph-container', children=[])


loop_braker_container = html.Div(id='loop_breaker_container', children=[])

app.layout = html.Div([


    Graph_container,

], className='row')


#how to make our graph more aesthetic ?
def get_figure(df, x_col, y_col, line1_x_whole_df_row, line2_x_whole_df_row ):
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
    line1_x =  line1_x_whole_df_row[x_col]
    line2_x =  line2_x_whole_df_row[x_col]
    fig = px.scatter(df, x=df[x_col], y=df[y_col], text=df.index)

    fig.update_traces(
                      customdata=df.index,
                      mode='markers+text', marker={ 'color': 'rgba(0, 116, 217, 0.7)', 'size': 20 }, unselected={'marker': { 'opacity': 0.3 }, 'textfont': { 'color': 'rgba(0, 0, 0, 0)' }})
    #margin={'l': 20, 'r': 0, 'b': 15, 't': 5},


    fig.update_layout( clickmode='event+select', title="abcd")#dragmode='select',, hovermode=False


    # y axis shouldn't be synced as each data point has different scope of value / Only x axis matters
    # if (relay_value is not None) and ('xaxis.range[0]' in relay_value):
    #     fig.update_layout(xaxis = dict(range=[relay_value['xaxis.range[0]'], relay_value['xaxis.range[1]']]))


    fig.add_shape(
        dict({'type': 'line',
              'x0': line1_x, 'x1': line1_x,
              'xref': 'x',
            #a shape can be placed relative to an axis's position on the plot by adding the string ' domain' to the axis reference in the xref or yref attributes for shapes.
              'y0': 0,
              'y1': 1,
              'yref': 'paper',

              'line': {
                  'width': 4,
                  'color': 'rgb(30, 30, 30)',
                  'dash': 'dashdot'}}),
    )

    fig.add_shape(
        dict({'type': 'line',
              'x0': line2_x, 'x1': line2_x,
              'xref': 'x',
            #a shape can be placed relative to an axis's position on the plot by adding the string ' domain' to the axis reference in the xref or yref attributes for shapes.
              'y0': 0,
              'y1': 1,
              'yref': 'paper',

              'line': {
                  'width': 4,
                  'color': 'rgb(30, 30, 30)',
                  'dash': 'dashdot'}}),
    )
    return fig
####---------------------------------------------------------------------
line1_x_whole_df_row = df.iloc[int(len(df) / 3)]
line2_x_whole_df_row = df.iloc[int(len(df) / 3 * 2)]

init_graph_data = [get_figure(df, "{} time".format(filename_list[i]), "{}".format(filename_list[i]), line1_x_whole_df_row, line2_x_whole_df_row) for i in range(len(filename_list))]



for i in range(Graph_count):
    Graph_container.children.append( dcc.Graph (
            id={
                'type': 'dcc_graph',
                'index': i

            },
            figure = init_graph_data[i],

            config={
                #'editable': True,
                'edits': {
                    'shapePosition': True
                }
    },

            # Initial Update the graph separately,
            # Since callback should filter out the update value to none to block the circular behavior
            # figure=graph_figures[i]
        )
    )

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#Table pandas DF init /

    #line1_x_whole_df_row 에서 time이 들어가지 않은 행(y 좌표 값 )의 값만 뽑아내면 되는 거니깐...
    # => line1_x_whole_df_row[filename_list].values
d = {
    'Graph name' : filename_list,
    'Line1 Value' : line1_x_whole_df_row[filename_list].values,
    'Line2 Value':line2_x_whole_df_row[filename_list].values,
    'Diff' : line2_x_whole_df_row[filename_list].values - line1_x_whole_df_row[filename_list].values
}
df_Table = pd.DataFrame(data=d)
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


#what value should be conveyed as arguments?
#value should be  "shapes[0].x0": 3.451221409677921,
#colname should be ? x1 or x2 it doesn't matter since both of graphs have same x values
def find_closest_x_val(value, df, colname):
    pd_timeval = pd.Timestamp(value)
    exactmatch = df[df[colname] == pd_timeval]

    # return value should be changed
    if not exactmatch.empty:
        #여기 처리가 자꾸 다른 type의 리턴값이 나오도록 만드느느 듯
        return str(exactmatch[colname].values[0])
    else:
        try:
            flag = 0
            lowerneighbour_ind = df[df[colname] < pd_timeval][colname].idxmax()
            flag = 1
            upperneighbour_ind = df[df[colname] > pd_timeval][colname].idxmin()
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
    print("wow {} {} lower index {} {}".format(value, type(value), lowerneighbour_ind, df.iloc[upperneighbour_ind][colname]))
    if (abs(df.iloc[lowerneighbour_ind][colname] - pd_timeval) > abs(df.iloc[upperneighbour_ind][colname] - pd_timeval)):
        return df.iloc[upperneighbour_ind][colname]
    else:
        return df.iloc[lowerneighbour_ind][colname]






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
     Output({'type': 'dcc_graph', 'index': ALL}, 'relayoutData'),
    ],
    [
     Input({'type': 'dcc_graph', 'index': ALL}, 'relayoutData'),
     ],
    State({'type': 'dcc_graph', 'index': ALL}, 'figure')
)
def callback( arg_relay_values, fig_val):
    ctx = dash.callback_context

    # just autosize => ignore/ 보통 'autosize': True 형태로 전달되지
    if len(ctx.triggered) == 5:
        print("system event")

        raise PreventUpdate

# this is the user triggered event
    elif len(ctx.triggered) == 1:
        print("ctx data {}".format(ctx.triggered))

        if(ctx.triggered[0]['prop_id'] == '.' ) :
            raise PreventUpdate
        else:
            event_trig_index = int(ctx.triggered[0]['prop_id'].split(',')[0].split(':')[-1])

            idx = 0


            #all([]) => True / what?
            if all([True if 'shapes' in item else False for item in arg_relay_values[event_trig_index].keys()  ]):

                for fig_item in fig_val:

                    if (fig_item['layout']['shapes'][0]['y0'] != 0) or (fig_item['layout']['shapes'][0]['y1'] != 1):
                        fig_item['layout']['shapes'][0]['y0'] = 0
                        fig_item['layout']['shapes'][0]['y1'] = 1

                    if (fig_item['layout']['shapes'][1]['y0'] != 0) or (fig_item['layout']['shapes'][1]['y1'] != 1):
                        fig_item['layout']['shapes'][1]['y0'] = 0
                        fig_item['layout']['shapes'][1]['y1'] = 1

                    # event triggered graph doesn't need to be updated
                    # State(fig_val) when it comes as a feedback '2020-12-28 13:50:27.3622' is transferred instead of '2020-12-28T13:50:27.952380'


                    # line1 processing / index 0
                    print("fig date type {}".format( type(fig_val[event_trig_index]['layout']['shapes'][0]['x0']) ))

                    fig_item['layout']['shapes'][0]['x0'] = find_closest_x_val(
                        fig_val[event_trig_index]['layout']['shapes'][0]['x0'], df, "{} time".format(filename_list[idx]))
                    fig_item['layout']['shapes'][0]['x1'] = fig_item['layout']['shapes'][0]['x0']
                    # "{} time".format(filename_list[i])
                    # line2 processing / index 1
                    fig_item['layout']['shapes'][1]['x0'] = find_closest_x_val(
                        fig_val[event_trig_index]['layout']['shapes'][1]['x0'], df, "{} time".format(filename_list[idx]))
                    fig_item['layout']['shapes'][1]['x1'] = fig_item['layout']['shapes'][1]['x0']

                    idx = idx + 1

               ###################################################
                #elif ctx.triggered[0]['prop_id'].split('.')[-1] == 'relayoutData':
                #real_relay_val = None

                #우린 위에서 event_trig_index 로 어떤 그래프가 이벤트를 trigger 하는지 알고 있다!

                #arg_relay_values[event_trig_index]
                #data structure : {'shapes[0].x0': '2020-12-28 13:50:27.4095', 'shapes[0].x1': '2020-12-28 13:50:27.4095', 'shapes[0].y0': 0.09354838709677415, 'shapes[0].y1': 1.0935483870967742}
                # 현재는 shape으로 오는 것과...zoom으로 오는 이벤트를 구별해야지.. moveline 참고할것
                #elif any(['True' for relay_item in relayoutData.keys() if 'xaxis' in relay_item]):

            #[{'yaxis.range[0]': 641.9528503937007, 'yaxis.range[1]': 1486.4004173228345}, None, None, None, None]


            elif any([True if 'xaxis.range' in item else False for item in arg_relay_values[event_trig_index].keys() ]):
                print("zoom")

                # if (event_trig_index != idx):
                # classifier = [('autosize' in relay_val.keys(), relay_val) for relay_val in arg_relay_values if
                #               type(relay_val) == dict]
                #
                # if len(classifier) > 1:
                #     print("init. nothing has to be done")
                #     # this means zoom in
                #
                # elif len(classifier) == 1:
                #     if 'xaxis.autorange' in classifier[0][-1]:
                #         for fig_item in fig_val:
                #             fig_item['layout']['xaxis'] = {"autorange": True}
                #             fig_item['layout']['yaxis'] = {"autorange": True}
                #     elif 'xaxis.range[0]' in classifier[0][-1]:
                #         for fig_item in fig_val:
                #             fig_item['layout']['xaxis'] = {
                #                 "range": [classifier[0][-1]['xaxis.range[0]'], classifier[0][-1]['xaxis.range[1]']]}

                ###################################################
                #zoom in out은 x axis 값만  sync해주면 됨
                for fig_item in fig_val:
                    fig_item['layout']['xaxis']['range'][0] = arg_relay_values[event_trig_index]['xaxis.range[0]']
                    fig_item['layout']['xaxis']['range'][1] = arg_relay_values[event_trig_index]['xaxis.range[1]']
                    fig_item['layout']['xaxis']['autorange'] = False
            #[{'xaxis.autorange': True, 'yaxis.autorange': True}, None, None, None, None]
            #zoomout event

            # y축을 움직여줄 경우에는... 비율로 계산하는게 최고지..
           # [{'yaxis.range[0]': 641.9528503937007, 'yaxis.range[1]': 1486.4004173228345}, None, None, None, None]
            elif all([True if 'yaxis.range' in item else False for item in arg_relay_values[event_trig_index].keys()]):

                #how much it moved from the previous? how can I calculate? use cache
                Prev_fig_list_y = cache.get("prev_fig_list_y")

                diff = arg_relay_values[event_trig_index]['yaxis.range[1]'] - Prev_fig_list_y[event_trig_index]
                scope = arg_relay_values[event_trig_index]['yaxis.range[1]'] - arg_relay_values[event_trig_index]['yaxis.range[0]']
                ratio = diff / scope
                idx = 0

                for fig_item in fig_val:
                    if idx != event_trig_index:
                        fig_item['layout']['yaxis']['range'][0] = (1 + ratio) * fig_item['layout']['yaxis']['range'][0]
                        fig_item['layout']['yaxis']['range'][1] = (1 + ratio) * fig_item['layout']['yaxis']['range'][1]
                        fig_item['layout']['yaxis']['autorange'] = False
                    idx = idx + 1

            elif any([True if '.autorange' in item else False for item in arg_relay_values[event_trig_index].keys() ]):
                for fig_item in fig_val:
                    fig_item['layout']['xaxis']['autorange'] = True
                    fig_item['layout']['yaxis']['autorange'] = True
            else :
                print("unexpected event")


            #Cache for the previous fig val to calculate the sync of vertical movement
            Curr_fig_list_y = list()

            for fig_item in fig_val:
                Curr_fig_list_y.append(fig_item['layout']['yaxis']['range'][1])

            cache.set("prev_fig_list_y",Curr_fig_list_y)

            #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
            # Table pandas DF update는?
            # if user change the location of line1 to right side and line2 to left side ?
            # should s/w automatically detect the difference and swap the datatable?
            # However, it could be confusing as well, so it is better to put the name tag on line shape object.

            # df.iloc[df[그래프 이름_time(어느것이든 상관없다. )] == line x coordi][filename_list] => 요게 Line1 Value에 들어가면 되겠지.
            #  = df.iloc[df[filename_list[]
            # df_Table['Line2 Value']
            # index[0] should be followed at the end due to "array([[9.878110e+02, 9.772094e+02, 0.000000e+00, 1.600391e+00, 4.741730e-02]])"

            df_Table['Line1 Value'] = df[df[filename_list[0] + " time"] == fig_val[0]['layout']['shapes'][0]['x0']][filename_list].values[0]
            df_Table['Line2 Value'] = df[df[filename_list[0] + " time"] == fig_val[0]['layout']['shapes'][1]['x0']][filename_list].values[0]
            df_Table['Diff'] = df_Table['Line2 Value'] - df_Table['Line1 Value']
            print(df_Table)

            relay_buf_reset = list()
            for i in range(len(fig_val)):
                    relay_buf_reset.append(None)
            result = [fig_val, relay_buf_reset ]
            return result

    else:
        print("What is this event? {}", ctx.triggered)
        raise PreventUpdate


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