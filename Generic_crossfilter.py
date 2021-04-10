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



#This part should be later implemented with text inputs

# Graph_count = 8

# np.random.seed(0)
# df = pd.DataFrame({"Col " + str(i+1): np.random.rand(30) for i in range(Graph_count*2)})


full_path = PFH.print_file_path_list()

df = PFH.Raw_Data_to_Pandas_DF(full_path)

filename_list = list()

for column in df.columns:
    if 'time' not in column:
        filename_list.append(column)
Graph_count = len(filename_list)


Graph_container = html.Div(id='graph-container', children=[])

app.layout = html.Div([

    Graph_container,

], className='row')


#how to make our graph more aesthetic ?
def get_figure(df, x_col, y_col, selectedpoints, relay_value ):
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
    #margin={'l': 20, 'r': 0, 'b': 15, 't': 5},


    fig.update_layout( clickmode='event+select', title="abcd")#dragmode='select',, hovermode=False






    # y axis shouldn't be synced as each data point has different scope of value / Only x axis matters
    # if (relay_value is not None) and ('xaxis.range[0]' in relay_value):
    #     fig.update_layout(xaxis = dict(range=[relay_value['xaxis.range[0]'], relay_value['xaxis.range[1]']]))


    # fig.add_shape(dict({'type': 'rect',
    #                     'line': { 'width': 1, 'dash': 'dot', 'color': 'darkgrey' }},
    #                    **selection_bounds))
    return fig
init_graph_data = [get_figure(df, "{} time".format(filename_list[i]), "{}".format(filename_list[i]), [],
                         None) for i in range(len(filename_list))]

for i in range(Graph_count):
    Graph_container.children.append( dcc.Graph (
            id={
                'type': 'dcc_graph',
                'index': i
            },
            figure = init_graph_data[i]

            # Initial Update the graph separately,
            # Since callback should filter out the update value to none to block the circular behavior
            # figure=graph_figures[i]
        )
    )




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
     Output({'type': 'dcc_graph', 'index': ALL}, 'relayoutData'),
    ],
    [Input({'type': 'dcc_graph', 'index': ALL}, 'clickData'),
     Input({'type': 'dcc_graph', 'index': ALL}, 'relayoutData'),
     ],
    State({'type': 'dcc_graph', 'index': ALL}, 'figure')
)
def callback(arg_sel_values, arg_relay_values, fig_val):
    ctx = dash.callback_context

    # 이건 callback state로 받아오게 해도 되는 거 아닌가 싶기도 하지만.. sel ponit는 애초에 양이 많지 않으므로 큰 문제가 되지 않을수도
    Sel_PtQueue = cache.get("sel_points")
    if Sel_PtQueue is None:
        Sel_PtQueue = []

    real_relay_val = cache.get("relay_val")
    #'' is occurred at the initialization
    # if the event is selected Data // will be replced with
    if ctx.triggered[0]['prop_id'].split('.')[-1] == 'selectedData' or ctx.triggered[0]['prop_id'].split('.')[-1] == '':

        if all(elem == None for elem in arg_sel_values):
            print("A")
            # do nothing
        else:
            # Interface to add or remove selected points
            # set difference of A(Callback input)-B(Cache) will identify newly added single point
            # in case of removing selected point, we might have empty set for the above case
            # if Intersection between A(Callback input) and B(Cache) is the same as (Cache ) then
            # yes -> we keep the old log of selected points
            # no -> if cache has more than A(Callback input) we return A
            #deselect event -> [{'points': []}, None, None, None, None, None, None, None]
            #deselect event 아주 예전에 선택한 것을 deselect 한다면.. 가장 최근에 기억하는 점 하나만 딸랑 보낸다.
            #가장 최근에 택한걸 deselect하게 되면 [] 가 가버린다는 거지..
            # 1. deselect event 를 구별하는 법
            # 2. 그 담에는 한 점 씩만 지울 수 있다. 즉.. state 를 보고 값을 가공해야한다.

            # click evet 를 state로 보내야 할 수 도?


            #doesn't specify what point is deselected but just sending empty point.
            #shift click the selected dots should be defined as reset?


            selectedpoints = df.index
            # 이걸 for문으로 돌리는게 문제인듯 / intersection..
            sanityCheckCnt = 0
            for selected_data in arg_sel_values:
                #only callback from one graph where the event occurred have valid data/
                # below if statement will filter out the access of unnecessary call back data from other graphs which has empty value
                if selected_data and (selected_data['points']!=None):
                    sanityCheckCnt = sanityCheckCnt + 1

                    rawSelPtCallback = [p['customdata'] for p in selected_data['points']]

                    selPtDiff = np.setdiff1d( rawSelPtCallback, Sel_PtQueue )

            if sanityCheckCnt > 1 :
                raise Exception('only single value from callback should contain the valid value :  {} of them has shown.. weird'.format(sanityCheckCnt))
            else:
            # SanityCheck is for number of valid data from callback : should be from single graph rather than multiple ones
            # However, desection event will bypass for loop above so sanityCheckCnt will be 0

            # selPtDiff is to discern between selection case and deselection case
            # if lenth of selPtdiff is 0
            # chances are it might be deseletion case
            #
                if len(selPtDiff) == 1:
                    Sel_PtQueue.append(selPtDiff[-1])
                # in case of empty after set difference, need to check intersection to double check there is any
                elif len(selPtDiff) == 0:
                    #rawSelPtCallback and ... other..
                    Sel_PtQueue = rawSelPtCallback
                    # # really hard to implement since raw value of selected point is going to be differnt from which graph the event evoked from
                    # temp_inter = np.intersect1d(rawSelPtCallback, Sel_PtQueue)
                    #
                    #     # if the intersection value is not same as cache
                    #     # 여러 그래프에서... 다른 selected event 가 나올 수 있으니.. 아래 if 문은 옳지 않은거지
                    # if np.array_equal(temp_inter, Sel_PtQueue) == False:
                    #     Sel_PtQueue = rawSelPtCallback
                    #     print("")


                else :
                    print("unexpected scenario")

        result_1st = [get_figure(df, "{} time".format(filename_list[i]), "{}".format(filename_list[i]), Sel_PtQueue,
                                 real_relay_val) for i in range(len(filename_list))]

    # sanity check required ? theorotically only one graph will throw valid value and
    # other values should be none
    # relayoutData event is called in initialization
    # Autosize 일 경우 how to process / {'autosize': True}

    elif ctx.triggered[0]['prop_id'].split('.')[-1] == 'relayoutData':
        real_relay_val = None

        classifier = [('autosize' in relay_val.keys(), relay_val ) for relay_val in arg_relay_values if type(relay_val) == dict]

        if len(classifier) > 1 :
            print("init. nothing has to be done")
            #this means zoom in

        elif len(classifier) == 1 :
            if 'xaxis.autorange' in classifier[0][-1]:
                for fig_item in fig_val:
                    fig_item['layout']['xaxis'] = {"autorange" : True}
                    fig_item['layout']['yaxis'] = {"autorange" : True}
            elif 'xaxis.range[0]' in classifier[0][-1]:
                for fig_item in fig_val:
                    fig_item['layout']['xaxis'] = {
                        "range": [classifier[0][-1]['xaxis.range[0]'], classifier[0][-1]['xaxis.range[1]']]}
            #this means max zoom out again

        result_1st = fig_val


        # else문에서 나오는건 ndarray 형이므로 list 로 바꾼다

        #ndarray

    # 여기서 부터 로직을... 생각해보자..
    # 보통 점이 추가된다면 하나씩 추가된다. incrementally 점만 추가해주면 된다 저런 교집합은 필요없다.
    # 만일 점이 모두 초기화 되는 경우가 있을 수 있다. [] 이렇게 오는 경우.. 그냥 초기화 하면 된다.


    #since the data type coming out from else statements giving us numpy.ndarray
    cache.set( "sel_points", Sel_PtQueue)
    cache.set("relay_val", real_relay_val)


    cache.set("result_1st", result_1st)
    result_2nd = list()
    result_3rd = list()
    for i in range(len(arg_sel_values)):
            result_2nd.append(None)
            result_3rd.append(None)
    result = [result_1st, result_2nd, result_3rd]
    return result



if __name__ == '__main__':
    app.run_server(debug=True)