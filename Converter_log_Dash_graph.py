from dash import html, dcc, dash_table, Dash, callback_context
from dash.dependencies import Input, Output, MATCH, ALL, State
from dash.exceptions import PreventUpdate

import pandas as pd
import plotly.express as px
from flask_caching import Cache
import FileUtil
import sys

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

#ignore the exception raised by Dash
app.config['suppress_callback_exceptions'] = True


CACHE_CONFIG = {
    'CACHE_TYPE': 'simple',
    # try 'filesystem' if you don't want to setup redis
    #'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379')
}

cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

full_path, filename_list  = FileUtil.getFilePathList()

df = FileUtil.RawDataAggregationToDF(full_path)

Table_container = html.Div(className='table_container', children=[], style={'display': 'inline-block', 'width' : "70%" }) #'border': '3px solid black'
Graph_container = html.Div(className='graph_container', id='graph-container', children=[],style={'display': 'inline-block', 'width' : '70%', 'vertical-align': 'top', })

app.layout = html.Div([
    Table_container,
    Graph_container,
],
    style={'display': 'inline-block'}
)

# The initial position for two date range lines for all columns of data
line1xPos = df.iloc[int(len(df) / 3)]
line2xPos = df.iloc[int(len(df) / 3 * 2)]

'''
Create scatter plot with dataframe values
also create two date range lines placed on each graph

PARAM :
    df => dataframe generated from log files
    x_col =>  name of column ending with 'time' that has the corresponding time stamps to the x_col values
    y_col =>  name of column that has time series values for each signal
    line1xPos =>  single row of data set that was generated at the same time where first date range line's position is set
    line2xPos =>   single row of data set that was generated at the same time where second date range line's position is set
    
return type : plotly scatter plot
'''
def get_figure(df, x_col, y_col, line1xPos, line2xPos):

    # cf) for selectedpoints properties, Please refer to the below link
    # https://medium.com/@plotlygraphs/notes-from-the-latest-plotly-js-release-b035a5b43e21

    line1_x = line1xPos[x_col]
    line2_x = line2xPos[x_col]

    fig = px.scatter(df, x=df[x_col], y=df[y_col], text=df.index)

    fig.update_traces(
        customdata=df.index,
        mode='markers+text', marker={'color': 'rgba(0, 116, 217, 0.7)', 'size': 20},
        unselected={'marker': {'opacity': 0.3}, 'textfont': {'color': 'rgba(0, 0, 0, 0)'}})
    # other parameters for update_layout
    # margin={'l': 20, 'r': 0, 'b': 15, 't': 5},
    # dragmode='select',, hovermode=False
    fig.update_layout( clickmode='event+select', title= y_col.split('.')[0])

    # Configure two date range lines
    # Param : yref => paper
    # the `y` position refers to the distance from the left of the plotting area in
    # normalized coordinates where 0 (1) corresponds to the left (right).
    fig.add_shape(
        dict({'type': 'line',
              'x0': line1_x, 'x1': line1_x,
              'xref': 'x',
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
              'y0': 0,
              'y1': 1,
              'yref': 'paper',
              'line': {
                  'width': 4,
                  'color': 'rgb(30, 30, 30)',
                  'dash': 'dashdot'}}),
    )
    return fig

#Create all the required number of Scatter plots
init_graph_data = [get_figure(df, "{} time".format(filename_list[i]), "{}".format(filename_list[i]), line1xPos, line2xPos) for i in range(len(filename_list))]

for i in range(len(filename_list)):
    Graph_container.children.append(
        dcc.Graph(
            id={
                #pattern matching callback
                'type': 'dcc_graph',
                'index': i
            },
            figure=init_graph_data[i],
            config={
                # 'editable': True,
                'edits': {
                    'shapePosition': True
                }
            },
        )
    )

#Data entries for Table object that shows difference in value between selected data range lines
tableData = {
    'Graph name': filename_list,
    'Line1 Value': line1xPos[filename_list].values,
    'Line2 Value': line2xPos[filename_list].values,
    'Diff': line2xPos[filename_list].values - line1xPos[filename_list].values
}
df_Table = pd.DataFrame(data=tableData)

Table_container.children.append(
    dash_table.DataTable(id='table',
                         columns=[{"name": i, "id": i} for i in df_Table.columns],
                         data=df_Table.to_dict('records'))
)

'''
'''

# what value should be conveyed as arguments?
# value should be  "shapes[0].x0": 3.451221409677921,
# colname should be ? x1 or x2 it doesn't matter since both of graphs have same x values

def find_closest_x_val(value, df, colname):
    pd_timeval = pd.Timestamp(value)
    exactmatch = df[df[colname] == pd_timeval]

    # return value should be changed
    if not exactmatch.empty:
        # 여기 처리가 자꾸 다른 type의 리턴값이 나오도록 만드느느 듯
        return str(exactmatch[colname].values[0])
    else:
        try:
            flag = 0
            lowerneighbour_ind = df[df[colname] < pd_timeval][colname].idxmax()
            flag = 1
            upperneighbour_ind = df[df[colname] > pd_timeval][colname].idxmin()

        except ValueError:
            # the line go beyond the left end of graph, make it forcefully move back to the first element at the far left
            if flag == 0:
                return df.iloc[0][colname]
            # the line go beyond the right end of graph, ... forcefully move back to the far right point of graph
            elif flag == 1:
                return df.iloc[df.index.stop - 1][colname]

            else:
                print("Unexpected ValueError/ the value of flag : { }".format(flag))
        except:
            print("Unexpected error!:", sys.exc_info()[0])

    print("wow {} {} lower index {} {}".format(value, type(value), lowerneighbour_ind,
                                               df.iloc[upperneighbour_ind][colname]))
    if (abs(df.iloc[lowerneighbour_ind][colname] - pd_timeval) > abs(
            df.iloc[upperneighbour_ind][colname] - pd_timeval)):
        return df.iloc[upperneighbour_ind][colname]
    else:
        return df.iloc[lowerneighbour_ind][colname]

# Another possibility by using MATCH ?
# The selected data event info in the past remains persistent, so the buffer for selecteddata
# should be emptied everytime. As a result, dropped idea to use selected data event
'''
Callback Function

Triggering event : relayoutData / when any of data range lines is moved
Return(Output) : This function is feeding processed data to all of plots for synchronization of the zoom area and 
                the placement of date range lines across all plots. Also data table, that displays the difference between 
                two date range lines, is updated accordingly. 
'''
@app.callback(
    [
        Output({'type': 'dcc_graph', 'index': ALL}, 'figure'),
        Output({'type': 'dcc_graph', 'index': ALL}, 'relayoutData'),
        Output('table', 'data')
    ],
    [
        Input({'type': 'dcc_graph', 'index': ALL}, 'relayoutData'),
    ],
    State({'type': 'dcc_graph', 'index': ALL}, 'figure')
)
def callback(relayValueList, figureList):
    ctx = callback_context

    # autosize request generated at some internally defined refresh rate,
    # but it is okay to ignore / the Callback input contains {'value': {'autosize': True}}}
    if len(ctx.triggered) == len(filename_list):
        print("system event")
        raise PreventUpdate

    # In case of user triggered event :
    elif len(ctx.triggered) == 1:

        if(ctx.triggered[0]['prop_id'] == '.' ) :
            print("system event2")
            raise PreventUpdate
        else:
            #Extract the index number of the plot that triggered the event
            eventTrigIndex = int(ctx.triggered[0]['prop_id'].split(',')[0].split(':')[-1])
            idx = 0
            # 1. When Date range line is moved, only the relay event value generated from event triggered plot has 'shapes' as a key
            #  which indicates either one of date range line's coordinates that just moved

            # e.g. Event triggered in the first plot, the relaydata would be structured like the below
            # [{'shapes[1].x0': '2021-04-29 08:20:39.2098', 'shapes[1].x1': '2021-04-29 08:20:39.2098', 'shapes[1].y0': 0, 'shapes[1].y1': 1}, {'autosize': True}, {'autosize': True}, {'autosize': True}]
            if relayValueList[eventTrigIndex] == None:
                print("None type")
            if all([True if 'shapes' in item else False for item in relayValueList[eventTrigIndex].keys()]):
                print("Date range line has moved : {}".format(relayValueList[eventTrigIndex]))

                for figure in figureList:

                    # In terms of y coordinates of data range lines, when either one of them is displaced, put it back inside the plot
                    if (figure['layout']['shapes'][0]['y0'] != 0) or (figure['layout']['shapes'][0]['y1'] != 1):
                        figure['layout']['shapes'][0]['y0'] = 0
                        figure['layout']['shapes'][0]['y1'] = 1

                    if (figure['layout']['shapes'][1]['y0'] != 0) or (figure['layout']['shapes'][1]['y1'] != 1):
                        figure['layout']['shapes'][1]['y0'] = 0
                        figure['layout']['shapes'][1]['y1'] = 1

                    # print("fig date type : {}".format(type(figureList[eventTrigIndex]['layout']['shapes'][0]['x0'])))

                    # In terms of x coordinates of data range lines, find the closest data point and move lines to it
                    # Dash's inconsistent behavior :
                    # Difference in X axis timestamp value(figure) '2021-04-29T08:19:59.058991000' vs '2021-04-29 08:20:39.2098'
                    # X coordinates from date line that just moved doesn't have 'T' in the middle, but the other has T in it

                    figure['layout']['shapes'][0]['x0'] = find_closest_x_val(
                        figureList[eventTrigIndex]['layout']['shapes'][0]['x0'], df, "{} time".format(filename_list[idx]))
                    figure['layout']['shapes'][0]['x1'] = figure['layout']['shapes'][0]['x0']

                    figure['layout']['shapes'][1]['x0'] = find_closest_x_val(
                        figureList[eventTrigIndex]['layout']['shapes'][1]['x0'], df, "{} time".format(filename_list[idx]))
                    figure['layout']['shapes'][1]['x1'] = figure['layout']['shapes'][1]['x0']

                    idx = idx + 1

                #arg_relay_values[event_trig_index]
                #data structure : {'shapes[0].x0': '2020-12-28 13:50:27.4095', 'shapes[0].x1': '2020-12-28 13:50:27.4095', 'shapes[0].y0': 0.09354838709677415, 'shapes[0].y1': 1.0935483870967742}

                #elif any(['True' for relay_item in relayoutData.keys() if 'xaxis' in relay_item]):
            #[{'yaxis.range[0]': 641.9528503937007, 'yaxis.range[1]': 1486.4004173228345}, None, None, None, None]

            # 2. When any of plots is either zoomed in or out, only the relay event value generated from event triggered plot has 'shapes' as a key
    #x 축만 움직이거나

            # e.g.
            # {'xaxis.range[0]': '2021-04-29 08:19:51.575', 'xaxis.range[1]': '2021-04-29 08:20:30.3982', 'yaxis.range[0]': -202.5462810383475, 'yaxis.range[1]': 645.1285302706506}
            elif all([True if 'xaxis.range' in item else False for item in relayValueList[eventTrigIndex].keys()]):

                print("Move the range of plot along X axis   : {}".format(relayValueList[eventTrigIndex]))

                #zoom in out은 x axis 값만  sync해주면 됨
                for figure in figureList:
                    figure['layout']['xaxis']['range'][0] = relayValueList[eventTrigIndex]['xaxis.range[0]']
                    figure['layout']['xaxis']['range'][1] = relayValueList[eventTrigIndex]['xaxis.range[1]']
                    figure['layout']['xaxis']['autorange'] = False
            #[{'xaxis.autorange': True, 'yaxis.autorange': True}, None, None, None, None]
            #zoomout event

            # y축을 드래그 했을 경우
            # cache를 이용해서 비율로 해야만함
            # y 축의 범위가 각 plot마다 다르기 때문이지


           # [{'yaxis.range[0]': 641.9528503937007, 'yaxis.range[1]': 1486.4004173228345}, None, None, None, None]
            elif all([True if 'yaxis.range' in item else False for item in relayValueList[eventTrigIndex].keys()]):

                print("Move the range of plot along Y axis or Zoom in  : {}".format(relayValueList[eventTrigIndex]))
                #how much it moved from the previous? how can I calculate? use cache
                Prev_fig_list_y = cache.get("prev_fig_list_y")

                if(Prev_fig_list_y != None):
                    diffValChg = relayValueList[eventTrigIndex]['yaxis.range[1]'] - Prev_fig_list_y[eventTrigIndex]
                    scopeYaxis = relayValueList[eventTrigIndex]['yaxis.range[1]'] - relayValueList[eventTrigIndex]['yaxis.range[0]']
                    ratio = diffValChg / scopeYaxis
                    idx = 0

                    for figure in figureList:
                        if idx != eventTrigIndex:
                            scope =  figure['layout']['yaxis']['range'][1] - figure['layout']['yaxis']['range'][0]
                            diff = scope * ratio
                            figure['layout']['yaxis']['range'][0] = diff + figure['layout']['yaxis']['range'][0]
                            figure['layout']['yaxis']['range'][1] = diff + figure['layout']['yaxis']['range'][1]
                            figure['layout']['yaxis']['autorange'] = False
                        idx = idx + 1
            #4. When zoomed in
            elif all([True if '.range' in item else False for item in relayValueList[eventTrigIndex].keys()]):
                print("zoom in : {}".format(relayValueList[eventTrigIndex]))
                Prev_fig_list_y = cache.get("prev_fig_list_y")

                diffValChg = relayValueList[eventTrigIndex]['yaxis.range[1]'] - Prev_fig_list_y[eventTrigIndex]
                scopeYaxis = relayValueList[eventTrigIndex]['yaxis.range[1]'] - relayValueList[eventTrigIndex][
                    'yaxis.range[0]']
                ratio = diffValChg / scopeYaxis
                idx = 0
                for figure in figureList:
                    if idx != eventTrigIndex:
                        figure['layout']['xaxis']['range'][0] = relayValueList[eventTrigIndex]['xaxis.range[0]']
                        figure['layout']['xaxis']['range'][1] = relayValueList[eventTrigIndex]['xaxis.range[1]']
                        figure['layout']['xaxis']['autorange'] = False

                        figure['layout']['yaxis']['range'][0] = (1 + ratio) * figure['layout']['yaxis']['range'][0]
                        figure['layout']['yaxis']['range'][1] = (1 + ratio) * figure['layout']['yaxis']['range'][1]
                        figure['layout']['yaxis']['autorange'] = False
                    idx = idx + 1


            # zoom out 햇을 때
            elif any([True if '.autorange' in item else False for item in relayValueList[eventTrigIndex].keys()]):
                print("zoom out  : {}".format(relayValueList[eventTrigIndex]))
                for figure in figureList:
                    figure['layout']['xaxis']['autorange'] = True
                    figure['layout']['yaxis']['autorange'] = True
            else :
                print("unexpected event")


            #Cache for the previous figures
            Curr_fig_list_y = list()

            for figure in figureList:
                Curr_fig_list_y.append(figure['layout']['yaxis']['range'][1])
            print("Cache set")
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

            df_Table['Line1 Value'] = df[df[filename_list[0] + " time"] == figureList[0]['layout']['shapes'][0]['x0']][filename_list].values[0]
            df_Table['Line2 Value'] = df[df[filename_list[0] + " time"] == figureList[0]['layout']['shapes'][1]['x0']][filename_list].values[0]
            df_Table['Diff'] = df_Table['Line2 Value'] - df_Table['Line1 Value']
            # print(df_Table)

            relay_buf_reset = list()
            for i in range(len(figureList)):
                    relay_buf_reset.append(None)
            result = [figureList, relay_buf_reset, df_Table.to_dict('records')]
            return result

    else:
        print("Unknown event {}", ctx.triggered)
        raise PreventUpdate


if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server()