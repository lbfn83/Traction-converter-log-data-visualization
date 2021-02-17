import dash
import dash_core_components as dcc
import dash_html_components as html
import datetime
import random
from dash.dependencies import Output, Input, State
import pandas as pd
import numpy as np
import plotly.express as px
import json
import _help_export_to_file
import plotly

app = dash.Dash()


graph_names = ["foo", "bar", "baz"]



# custom fig를 직접 빌드 하는건데... 내가 만들고자 하는 건.
# dataframe은 global 변수로 만들어서 관리하고.. 매번 콜백이 나올 때마다 fig를 생성해주는 걸로.

# graph_figures = [{'data': [{'x': [0, 1, 2], 'y': random_points(3),  'name': '{} widgets'.format(name), 'selectedpoints': [], "mode": "markers",'marker': {'size': 20}}] ,
#                   'layout': {'title': name , 'clickmode': 'event+select'}} for name in graph_names]
#지금은 random으로 만들어주지만... 추후에는... 텍스트에서 긁어온 데이터 엔트리들이 들어가야겠지.
df_sub1 = pd.DataFrame({"Col " + str(i): i**i*i*np.random.rand(300) for i in (2, 4, 6) })
df_sub2 = pd.DataFrame({"Col " + str(i): np.arange(0,300) for i in (1, 3, 5) })
df = pd.concat([df_sub1, df_sub2], axis=1)
pre_style = {"backgroundColor": "#ddd", "fontSize": 20, "padding": "10px", "margin": "10px"}
hidden_style = {"display": "none"}

#children's setting will be affected by parent's setting. display none can be declared only in here to hide the object
# rather than going through all the children settings
hidden_inputs = html.Div(id="hidden-inputs",  children=[]) #style={'display': 'none'},
hidden_inputs_relay = html.Div(id="hidden_inputs_relay", children=[]) #, style={'display': 'none'}


#initialization of graph
# fig1 = px.scatter(df, x=df['Col 1'], y=df['Col 2'], text=df.index)
# fig2 = px.scatter(df, x=df['Col 3'], y=df['Col 4'], text=df.index)
# fig3 = px.scatter(df, x=df['Col 5'], y=df['Col 6'], text=df.index)
# fig1.update_layout(clickmode = 'event+select')
# fig2.update_layout(clickmode = 'event+select')
# fig3.update_layout(clickmode = 'event+select')
# fig1.update_traces(selectedpoints=[],
#                   customdata=df.index,
#                   mode='markers+text', marker={'color': 'rgba(0, 116, 217, 0.7)', 'size': 20},
#                   unselected={'marker': {'opacity': 0.3}, 'textfont': {'color': 'rgba(0, 0, 0, 0)'}})
# fig2.update_traces(selectedpoints=[],
#                   customdata=df.index,
#                   mode='markers+text', marker={'color': 'rgba(0, 116, 217, 0.7)', 'size': 20},
#                   unselected={'marker': {'opacity': 0.3}, 'textfont': {'color': 'rgba(0, 0, 0, 0)'}})
# fig3.update_traces(selectedpoints=[],
#                   customdata=df.index,
#                   mode='markers+text', marker={'color': 'rgba(0, 116, 217, 0.7)', 'size': 20},
#                   unselected={'marker': {'opacity': 0.3}, 'textfont': {'color': 'rgba(0, 0, 0, 0)'}})

#figure는 layout에서 define하지 않는다.
app.layout = html.Div(children=[
    dcc.Graph(id='foo',className="four columns"),
    dcc.Graph(id='bar', className="four columns"),
    dcc.Graph(id='baz', className="four columns"),
    html.Label('Most recent clickdata'),
    html.Pre(id='update-on-click-data', style=pre_style),
    hidden_inputs,
    hidden_inputs_relay,
    html.Div([
        dcc.Markdown("""
        **Zoom and Relayout Data**

        Click and drag on the graph to zoom or click on the zoom
        buttons in the graph's menu bar.
        Clicking on legend items will also fire
        this event.
    """),
        html.Pre(id='relayout-data'),
    ], className='three columns')
])
#,figure =  fig1
dash_input_keys = sorted(list(graph_names))
last_clicked_id = "last-clicked"
last_clicked_id2  = "second-last-clicked"

input_clicktime_trackers = [key + "_clicktime" for key in dash_input_keys]
hidden_inputs.children.append(dcc.Input(id=last_clicked_id,  value = None ))#,value=None
hidden_inputs.children.append(dcc.Input(id=last_clicked_id2, value = None ))

for hidden_input_key in input_clicktime_trackers:
    hidden_inputs.children.append(dcc.Input(id=hidden_input_key,  value=None))

############# relay time handling / sync the area of zoom in for each graph ##### below
relaytime_tracker = [key2 + "_relaytime" for key2 in dash_input_keys]
for relay_tracker_id in relaytime_tracker:
    hidden_inputs_relay.children.append(dcc.Input(id=relay_tracker_id, value = None ))#, style={'display':'none'}

hidden_inputs_relay.children.append(dcc.Input(id='last_zoomed_obj', value=None))#, style={'display':'none'}

# three call back will be created
for graph_name, relay_obj_name in zip(dash_input_keys, relaytime_tracker):
        @app.callback(Output(relay_obj_name, 'value'),
                      [Input(graph_name, 'relayoutData')])
        def update_relay_obj_invoked_time(relay_data):
            print("zoom size: {}".format(relay_data))
            result = {
                "timestamp": datetime.datetime.now().timestamp(),
                "zoom_size": relay_data,
            }
            json_result = json.dumps(result)
            return json_result

cb_output = Output('last_zoomed_obj', 'value')
cb_inputs = [Input(relay_obj_name, 'value') for relay_obj_name in relaytime_tracker]
cb_current_state = State('last_zoomed_obj', 'value')
# use the outputs generated in the callbacks above _instead_ of clickData
@app.callback(cb_output, cb_inputs, [cb_current_state])
def latest_relay_obj_invoked_time_callback(*inputs_and_state):
    relay_obj_values = inputs_and_state[:-1]

    last_state = [json.loads(inputs_and_state[-1]) if inputs_and_state[-1] is not None else inputs_and_state[-1]]

    print("state of last_zoomed_obj {}".format(last_state))
    if last_state[0] is None:
        last_state[0] = {
            "timestamp": None,
            "zoom_size": None,
        }
    else:
        latest_timestamp = -1
        latest_data = None
        for relay_obj_val in relay_obj_values:
            #####clicktime_input => json.dump로 인코딩 되어 있는 상태
            single_data = json.loads(relay_obj_val)

            timestamp_single = int(single_data['timestamp'])
            if single_data['zoom_size'] and timestamp_single > latest_timestamp:
                #this is for final data entry
                latest_data = single_data
                #this is for comparison of timestamp / update of latest timestamp variable
                latest_timestamp = timestamp_single
        if latest_timestamp:
            last_state[0]['timestamp'] = latest_data['timestamp']
            last_state[0]['zoom_size'] = latest_data['zoom_size']

    return json.dumps(last_state[0])
# 0@app.callback([,
#                Output('foo', 'figure'),
#                Output('bar', 'figure'),
#                Output('baz', 'figure')],
#               [Input(last_clicked_id, 'value')],
#               [State('last_zoomed_obj', 'value')])
# def update_zoom_callback(*raw_last_clickdata):
#
#     return 0;

############# relay time handling / sync the area of zoom in for each graph ##### above

# set up simple callbacks that just append the time of click to clickData
# three call back will be created
for graph_key, clicktime_out_key in zip(dash_input_keys, input_clicktime_trackers):
        @app.callback(Output(clicktime_out_key, 'value'),
                      [Input(graph_key, 'selectedData')],
                      [State(graph_key, 'id')])
        def update_clicktime(selectdata, graph_id):
            print("selectedData: {}".format(selectdata))

            # if clickdata is None:
            #             #     clickdata = None
            #11292020 selectedData에서 가장 최근에 선택된 단 한 개의 점 정보만
            #relay 될 수 있도록 비교문을 만든다.

            result = {
                "select time": datetime.datetime.now().timestamp(),
                "select data": selectdata,
                "id": graph_id
            }
            json_result = json.dumps(result)
            return json_result
# one call back with multiple input will be created
cb_output = [Output(last_clicked_id, 'value'), Output(last_clicked_id2, 'value')]
cb_inputs = [Input(clicktime_out_key, 'value') for clicktime_out_key in input_clicktime_trackers]
cb_current_state = State(last_clicked_id, 'value')
# use the outputs generated in the callbacks above _instead_ of clickData
@app.callback(cb_output, cb_inputs, [cb_current_state])
def last_clicked_callback(*inputs_and_state):

    clicktime_inputs = inputs_and_state[:-1]





    last_state = [json.loads(inputs_and_state[-1]) if inputs_and_state[-1] is not None else inputs_and_state[-1] ]



    print(last_state)
    if last_state[0] is None:
        last_state[0] = {
            "last_clicked": None,
            "last_clicked_data": None,
            # "last_clicked": None,
            # "last_clicked_data": None,
        }
    else:
        largest_clicktime = -1
        largest_clicktime_input = None
        for raw_clicktime_input in clicktime_inputs:
            #####clicktime_input => json.dump로 인코딩 되어 있는 상태
            clicktime_input = json.loads(raw_clicktime_input)

            click_time = int(clicktime_input['select time'])
            if clicktime_input['select data'] and click_time > largest_clicktime:
                largest_clicktime_input = clicktime_input
                largest_clicktime = click_time
        if largest_clicktime:
            last_state[0]['last_clicked'] = largest_clicktime_input['id']
            last_state[0]['last_clicked_data'] = largest_clicktime_input['select data']

    return [json.dumps(last_state[0]), inputs_and_state[-1]]


#################################
def get_figure(df, x_col, y_col, selectedpoints, selectedpoints_local, latest_relay_val):
    print(selectedpoints)
    fig = px.scatter(df, x=df[x_col], y=df[y_col], text=df.index)

    fig.update_traces(selectedpoints=selectedpoints,

                      mode='markers+text', marker={ 'color': 'rgba(0, 116, 217, 0.7)', 'size': 20 }, unselected={'marker': { 'opacity': 0.3 }, 'textfont': { 'color': 'rgba(0, 0, 0, 0)' }})
#customdata=df.index,
    fig.update_layout(margin={'l': 20, 'r': 0, 'b': 15, 't': 5},clickmode = 'event+select')

#latest_relay_val 의 timestamp를 봐줘야지.. 만일 none 이라고 하더라도.. last_zoom_obj에 값을 보낼 방도는 없을 듯...

    # if (latest_relay_val is not None) and (latest_relay_val['zoom_size'] is not None):
    if (latest_relay_val is not None) and (latest_relay_val['zoom_size'] is not None):
        if 'xaxis.range[0]' in latest_relay_val['zoom_size']:
            fig.update_layout(xaxis = dict(range=[latest_relay_val['zoom_size']['xaxis.range[0]'], latest_relay_val['zoom_size']['xaxis.range[1]']]))
        # _help_export_to_file.output_help_to_file("C:\\Users\\WonjaeLee\\Desktop\\b.txt", fig)
        # _help_export_to_file.output_help_to_file("C:\\Users\\WonjaeLee\\Desktop\\c.txt", plotly.graph_objs.layout.xaxis)xaxis
        # _help_export_to_file.output_help_to_file("C:\\Users\\WonjaeLee\\Desktop\\d.txt", dcc.Graph)
        #yaxis = dict(range=[latest_relay_val['zoom_size']['yaxis.range[0]'], latest_relay_val['zoom_size']['yaxis.range[1]']]),
#, dragmode='select'
#, hovermode=False
    return fig


###########################
# @app.callback([Output('foo', 'selectedData'),
#                Output('bar', 'selectedData'),
#                Output('baz', 'selectedData')],
#               [Input('foo', 'clickData'),
#                Input('bar', 'clickData'),
#                Input('baz', 'clickData')])
# def trial(*input):
#     return [None, None, None]




########################################



# 여기다가 최종   output 이 변하면... 곧바로 추가 콜백으로 이걸 그래프의 셀렉티드 데이터에 넣어주는 거는거지..
@app.callback([Output('update-on-click-data', 'children'),
               Output('foo', 'figure'),
               Output('bar', 'figure'),
               Output('baz', 'figure')],
              [Input(last_clicked_id, 'value'), Input('last_zoomed_obj', 'value')],
              [State(last_clicked_id2, 'value')])

def update_onclick_callback(*raw_last_clickdata):
    last_clickdata = json.loads(raw_last_clickdata[:-1][0])
    latest_relay_val = [json.loads(raw_last_clickdata[-1]) if raw_last_clickdata[-1] is not None else raw_last_clickdata[-1]][0]
    click_data = last_clickdata["last_clicked_data"]
    clicked_id = last_clickdata["last_clicked"]

    #section for selected points
    selectedpoints = []

    if click_data and click_data['points']:
            selectedpoints = df.index
            selectedpoints = np.intersect1d(selectedpoints, [p['pointIndex'] for p in click_data['points']])
    #section for relay zoom data

    return ["{} was last clicked and contains clickdata:\n{}".format(clicked_id, click_data), get_figure(df, "Col 1", "Col 2", selectedpoints, last_clickdata["last_clicked_data"], latest_relay_val),
            get_figure(df, "Col 3", "Col 4", selectedpoints, last_clickdata["last_clicked_data"], latest_relay_val), get_figure(df, "Col 5", "Col 6", selectedpoints, last_clickdata["last_clicked_data"], latest_relay_val)]


@app.callback(
    Output('relayout-data', 'children'),
    [Input('foo', 'relayoutData'),
     Input('bar', 'relayoutData'),
     Input('baz', 'relayoutData')])
def last_relayout_data(*relayoutData):
    return json.dumps(relayoutData, indent=2)


if __name__ == '__main__':
    app.run_server(debug=True)