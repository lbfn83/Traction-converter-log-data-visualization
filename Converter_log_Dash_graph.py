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
Graph_container = html.Div(className='graph_container', id='graph-container', children=[],style={'display': 'inline-block', 'width' : '90%', 'vertical-align': 'top', })

app.layout = html.Div([
    Table_container,
    Graph_container,
],
    style={'display': 'inline-block'}
)

# The initial position for two reference lines for all columns of data
line1xPos = df.iloc[int(len(df) / 3)]
line2xPos = df.iloc[int(len(df) / 3 * 2)]

'''
Create scatter plot with dataframe values
also create two reference lines placed on each graph

PARAM :
    df => dataframe generated from log files
    x_col =>  name of column ending with 'time' that has the corresponding time stamps to the x_col values
    y_col =>  name of column that has time series values for each signal
    line1xPos =>  single row of data set that was generated at the same time where first reference line's position is set
    line2xPos =>   single row of data set that was generated at the same time where second reference line's position is set
    
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

    # autosize is disabled since it takes up a lot of memories
    fig.update_layout( clickmode='event+select', title= y_col.split('.')[0], autosize = False, width = 1500 )

    # Configure two reference lines
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
###findClosestXval####
In case of x coordinates of reference lines not being aligned with any of actual data entry, 
find the closest data entry and reposition reference lines to it

PARAM :
    xValRefline => reference line's x coordinate ( string of timestamp )
    df => Dataframe
    colname => 
    
return type : the timestamp of closest data point to reference line's x coordinate
'''
def findClosestXval(xValRefline, df, colname):
    xTimestamp = pd.Timestamp(xValRefline)
    exactmatch = df[df[colname] == xTimestamp]

    if not exactmatch.empty:

        # if there is a data entry in dataframe that has exactly same value as xTimestamp
        # reference line's position is right on top of the data entry
        # return type : numpy.datetime64('2021-04-29T08:19:57.028812000')
        return pd.Timestamp(exactmatch[colname].values[0])
    else:

        try:
            flag = 0
            # Find the greatest lower bound
            lowerBoundIdx = df[df[colname] < xTimestamp][colname].idxmax()
            flag = 1
            # Find the least upper bound
            upperBoundIdx = df[df[colname] > xTimestamp][colname].idxmin()

        except ValueError:
            # If reference line has been placed beyond the left edge of the plot, return the data entry has earliest timestamp
            if flag == 0:
                # return type : Timestamp
                return df.iloc[0][colname]
            # the line go beyond the right end of graph, ... forcefully move back to the far right point of graph
            elif flag == 1:
                return df.iloc[df.index.stop - 1][colname]

            else:
                print("Unexpected exception handling case(ValueError) : the value of flag : { }".format(flag))
        except:
            print("Unexpected exception:", sys.exc_info()[0])

    # print(" least upperbound : {} {} / greatest lowerbound {} {}".format(upperBoundIdx,  df.iloc[upperBoundIdx][colname], lowerBoundIdx,
    #                                            df.iloc[lowerBoundIdx][colname]))

    # Find the closest to the position of reference line between lowerbound and upperbound
    if (abs(df.iloc[lowerBoundIdx][colname] - xTimestamp) > abs(
            df.iloc[upperBoundIdx][colname] - xTimestamp)):
        return df.iloc[upperBoundIdx][colname]
    else:
        return df.iloc[lowerBoundIdx][colname]

# Another possibility by using MATCH ?
# The selected data event info in the past remains persistent, so the buffer for selecteddata
# should be emptied everytime. As a result, dropped idea to use selected data event
'''
Callback Function

Triggering event : relayoutData / when any of data range lines is moved
Return(Output) : This function is feeding processed data to all of plots for synchronization of the zoom area and 
                the placement of reference lines across all plots. Also data table, that displays the difference between 
                two reference range lines, is updated accordingly. 
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


    # autosize has been disabled so below event is not supposed to occur
    if len(ctx.triggered) == len(filename_list):
        print("system event")
        raise PreventUpdate

    # In case of user triggered events :
    elif len(ctx.triggered) == 1:

        if(ctx.triggered[0]['prop_id'] == '.' ) :
            print("system event2")
            # Cache for the previous figure values
            # Below codes is being executed at the init state when plots are first loaded on display
            curYaxisRangeMax = list()
            curYaxisRangeMin = list()
            for figure in figureList:
                curYaxisRangeMax.append(figure['layout']['yaxis']['range'][1])
                curYaxisRangeMin.append(figure['layout']['yaxis']['range'][0])
            print("Cache set")
            cache.set("yaxisMax", curYaxisRangeMax)
            cache.set("yaxisMin", curYaxisRangeMin)
            raise PreventUpdate
        else:
            #Extract the index number of the plot that triggered the event
            eventTrigIndex = int(ctx.triggered[0]['prop_id'].split(',')[0].split(':')[-1])
            idx = 0

            if relayValueList[eventTrigIndex] == None:
                print("None type")
                raise PreventUpdate

            # 1. When a reference line is moved, the relay event triggered from plot, that has the moved line, contains 'shapes' as a key
            # and it has x coordinate value of said line.
            # e.g. Event triggered in the first plot, the relaydata would be structured like the below
            # [{'shapes[1].x0': '2021-04-29 08:20:39.2098', 'shapes[1].x1': '2021-04-29 08:20:39.2098', 'shapes[1].y0': 0, 'shapes[1].y1': 1}, {'autosize': True}, {'autosize': True}, {'autosize': True}]
            elif all([True if 'shapes' in item else False for item in relayValueList[eventTrigIndex].keys()]):
                print("reference line has moved : {}".format(relayValueList))

                # In terms of x coordinates of data range lines, find the closest scattered data point and reposition reference lines to it
                # As all the plots share same stream of timestamp values (x axis ), it doesn't matter which idx(index) is chosen
                # for an argument of findClosestXval function

                # Dash's inconsistent behavior :
                # Difference in X axis timestamp value(figure) '2021-04-29T08:19:59.058991000' vs '2021-04-29 08:20:39.2098'
                # X coordinates from reference line that just moved doesn't have 'T' in the middle, but the other has T in it

                refline0Xval = \
                findClosestXval(figureList[eventTrigIndex]['layout']['shapes'][0]['x0'], df, "{} time".format(filename_list[idx]))

                refline1Xval = \
                findClosestXval(figureList[eventTrigIndex]['layout']['shapes'][1]['x0'], df, "{} time".format(filename_list[idx]))

                for figure in figureList:

                    # In terms of y coordinates of data range lines, when either one of them is displaced, put it back inside the plot
                    if (figure['layout']['shapes'][0]['y0'] != 0) or (figure['layout']['shapes'][0]['y1'] != 1):
                        figure['layout']['shapes'][0]['y0'] = 0
                        figure['layout']['shapes'][0]['y1'] = 1

                    if (figure['layout']['shapes'][1]['y0'] != 0) or (figure['layout']['shapes'][1]['y1'] != 1):
                        figure['layout']['shapes'][1]['y0'] = 0
                        figure['layout']['shapes'][1]['y1'] = 1

                    # print("fig date type : {}".format(type(figureList[eventTrigIndex]['layout']['shapes'][0]['x0'])))

                    figure['layout']['shapes'][0]['x0'] = refline0Xval
                    figure['layout']['shapes'][0]['x1'] = figure['layout']['shapes'][0]['x0']

                    figure['layout']['shapes'][1]['x0'] = refline1Xval
                    figure['layout']['shapes'][1]['x1'] = figure['layout']['shapes'][1]['x0']

                    idx = idx + 1

                # Update each column on Data Table
                df_Table['Line1 Value'] = \
                df[df[filename_list[0] + " time"] == figureList[0]['layout']['shapes'][0]['x0']][filename_list].values[0]
                df_Table['Line2 Value'] = \
                df[df[filename_list[0] + " time"] == figureList[0]['layout']['shapes'][1]['x0']][filename_list].values[0]
                df_Table['Diff'] = df_Table['Line2 Value'] - df_Table['Line1 Value']
                # print(df_Table)

            # 2. When any of plots has shifted along the x axis
            # e.g. [{'xaxis.range[0]': '2021-04-29 08:19:58.0455', 'xaxis.range[1]': '2021-04-29 08:21:22.3963'}, {'autosize': True}, {'autosize': True}, {'autosize': True}]
            # [{'xaxis.range[0]': '2021-04-29 08:19:54.6154', 'xaxis.range[1]': '2021-04-29 08:21:18.9662'}, None, None, None]
            elif all([True if 'xaxis.range' in item else False for item in relayValueList[eventTrigIndex].keys()]):
                print("Move the range of plot along X axis   : {}".format(relayValueList))

                for figure in figureList:
                    figure['layout']['xaxis']['range'][0] = relayValueList[eventTrigIndex]['xaxis.range[0]']
                    figure['layout']['xaxis']['range'][1] = relayValueList[eventTrigIndex]['xaxis.range[1]']
                    figure['layout']['xaxis']['autorange'] = False

            # 2. When any of plots has shifted along the y axis
            # As the range of yaxis is different from each plot, the ratio of movement compared to the range of Y axis should be calculated to get the correct amount of shift for other plots
            # e.g.[{'yaxis.range[0]': 641.9528503937007, 'yaxis.range[1]': 1486.4004173228345}, None, None, None, None]
            elif all([True if 'yaxis.range' in item else False for item in relayValueList[eventTrigIndex].keys()]):

                print("Move the range of plot along Y axis  : {}".format(relayValueList))

                prevYaxisRangeMax = cache.get("yaxisMax")


                diffValChg = relayValueList[eventTrigIndex]['yaxis.range[1]'] - prevYaxisRangeMax[eventTrigIndex]
                scopeYaxis = relayValueList[eventTrigIndex]['yaxis.range[1]'] - relayValueList[eventTrigIndex]['yaxis.range[0]']
                ratio = diffValChg / scopeYaxis

                for figure in figureList:
                    if idx != eventTrigIndex:
                        scope = figure['layout']['yaxis']['range'][1] - figure['layout']['yaxis']['range'][0]
                        diff = scope * ratio
                        figure['layout']['yaxis']['range'][1] = diff + figure['layout']['yaxis']['range'][1]
                        figure['layout']['yaxis']['range'][0] = diff + figure['layout']['yaxis']['range'][0]
                        figure['layout']['yaxis']['autorange'] = False
                    idx = idx + 1

            #4. When any of plots has been zoomed in
            # e.g. [{'xaxis.range[0]': '2021-04-29 08:20:17.0416', 'xaxis.range[1]': '2021-04-29 08:20:25.5975', 'yaxis.range[0]': -721.5874761641479, 'yaxis.range[1]': 462.0560103587825}, None, None, None]
            elif all([True if '.range' in item else False for item in relayValueList[eventTrigIndex].keys()]):
                print("zoom in : {}".format(relayValueList))
                prevYaxisRangeMax = cache.get("yaxisMax")
                prevYaxisRangeMin = cache.get("yaxisMin")

                # As the range of yaxis is different from each plot, the ratio calculated from Max value and Min Value change
                # should be used to get the correct zoom in value in terms of Y axis for other plots
                currAbsScope = relayValueList[eventTrigIndex]['yaxis.range[1]'] - relayValueList[eventTrigIndex]['yaxis.range[0]']
                prevAbsScope = prevYaxisRangeMax[eventTrigIndex] - prevYaxisRangeMin[eventTrigIndex]
                scopeRatio = currAbsScope / prevAbsScope

                #data point, positioned right in the midlle between the ranges of plot after zoom in, should be repositoned at the center of the plot
                timeStamp1 = pd.Timestamp(relayValueList[eventTrigIndex]['xaxis.range[0]'])
                timeStamp2 = pd.Timestamp(relayValueList[eventTrigIndex]['xaxis.range[1]'])
                targetTimestamp = timeStamp1 + (timeStamp2 - timeStamp1)/2.0

                for figure in figureList:
                    if idx != eventTrigIndex:

                        figure['layout']['xaxis']['range'][0] = relayValueList[eventTrigIndex]['xaxis.range[0]']
                        figure['layout']['xaxis']['range'][1] = relayValueList[eventTrigIndex]['xaxis.range[1]']
                        figure['layout']['xaxis']['autorange'] = False

                        # Get y coordinate of data point the the middle and set the range of plot based on it
                        # to put the data point right in the middle
                        prevScope = float(figure['layout']['yaxis']['range'][1]) - float(figure['layout']['yaxis']['range'][0])
                        currScope = prevScope * scopeRatio

                        datapointIdx = \
                        df[df["{} time".format(filename_list[idx])] < targetTimestamp][filename_list[idx]].index[-1]

                        targetYVal= df.iloc[datapointIdx][filename_list[idx]]
                        figure['layout']['yaxis']['range'][1] = targetYVal + (currScope / 2.0)
                        figure['layout']['yaxis']['range'][0] = targetYVal - (currScope / 2.0)
                        figure['layout']['yaxis']['autorange'] = False
                    idx = idx + 1


            # 5. When zoomed out
            elif any([True if '.autorange' in item else False for item in relayValueList[eventTrigIndex].keys()]):
                print("zoom out  : {}".format(relayValueList))
                for figure in figureList:
                    figure['layout']['xaxis']['autorange'] = True
                    figure['layout']['yaxis']['autorange'] = True

            # 6. Autosize event occurs unpredictably. it shouldn't be generated since autosize event is suppressed in config
            elif any([True if 'autosize' in item else False for item in relayValueList[eventTrigIndex].keys()]):
                print("autosize   : {}".format(relayValueList))

                raise PreventUpdate

            else :
                print("unexpected event{}".format(relayValueList))

            # Cache for the previous figure values
            curYaxisRangeMax = list()
            curYaxisRangeMin = list()
            for figure in figureList:
                curYaxisRangeMax.append(figure['layout']['yaxis']['range'][1])
                curYaxisRangeMin.append(figure['layout']['yaxis']['range'][0])
            print("Cache set")
            cache.set("yaxisMax", curYaxisRangeMax)
            cache.set("yaxisMin", curYaxisRangeMin)

            # As relayoutData buffer holds the previous value persistently,
            # Let's empty the buffer at the end of every callback
            relay_buf_reset = list()
            print(len(figureList))
            for i in range(len(figureList)):
                    relay_buf_reset.append(None)
            result = [figureList, relay_buf_reset, df_Table.to_dict('records')]
            return result

    else:
        print("Ctx's unknown event {} : two or more triggers occured at the same time", ctx.triggered)
        raise PreventUpdate


if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server()