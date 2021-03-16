import tkinter as tk
from tkinter import filedialog
import os
import pandas as pd
import datetime

#using Tkinter, pop up the window to choose the directory and as an output send out the list of path + file names should be returned

#input : directory selected
#output : list of files inside the directory
#여기서 file list를 받아주고.
def convert_matlab_timestamp(raw_tp):

    stdtime_matlab = datetime.datetime(1, 1, 1, 0, 0, 0, 0)
    time_result = stdtime_matlab + datetime.timedelta(0, int(raw_tp / 10000000), raw_tp % 10000000 / 10)
    return time_result

def print_file_path_list() :
    root = tk.Tk()
    root.withdraw()
    """Withdraw this widget from the screen such that it is unmapped
            and forgotten by the window manager. Re-draw it with wm_deiconify."""

    #shell:MyComputerFolder => CLSID
    file_path = filedialog.askdirectory(initialdir ='shell:MyComputerFolder')
    print(file_path)
    ## Extract file names and path

    full_path = []
    fname_list= []
    for top, subdir, files in os.walk(file_path):
        # print ("****Name of Sub Directory****")
        # print("=> " + top)
        # print("   *List of file entries")]
        path = top.replace("/", "\\")
        if files != None :
            for fname in files:
#아무래도 여기서 리스트로 모두 받아줘야 하지 않을까?
                tmp =(path , fname)
                full_path.append("\\".join(tmp))
                fname_list.append(fname)
        else :
            print("Directory is empty")
    return full_path
# 여기 input에서는 column 이름들을 받도록 해주는게 좋지 않을까?
def Raw_Data_to_Pandas_DF(filepath):
    # f = open(filepath, 'r')
    # f.close()
    df2 = pd.read_csv('C:\\Users\\lbfn8\\Desktop\\A End 12292020\\Transient Recorder\\TranRecA-269\\1-UL_AUX.log', header = None, delimiter=';',
                     index_col=0)
    df3 = pd.read_csv('C:\\Users\\lbfn8\\Desktop\\A End 12292020\\Transient Recorder\\TranRecA-269\\1-UL_AUX.log',
                     header=None, delimiter=';')

    # 현재 문제는 empty file 일 때 ... read_csv가 에러로 빠져나간다
    # with랑 같이 사용할 경우에는... 뭔가 제대로 되지 않는 느낌이다
    #_enter_ 라는 magic keyword 때문인가/

    #     Traceback(most
    #     recent
    #     call
    #     last):
    #     File
    #     "C:\Program Files\JetBrains\PyCharm Community Edition 2020.3.3\plugins\python-ce\helpers\pydev\_pydevd_bundle\pydevd_exec2.py", line
    #     3, in Exec
    #     exec(exp, global_vars, local_vars)
    #
    #
    # File
    # "<string>", line
    # 1, in < module >
    # AttributeError: __enter__

    df = pd.DataFrame()
    for file_item in filepath:

        if os.path.getsize(file_item) > 0:
            try:
                # with pd.read_csv(filepath, header=None, delimiter=';') as df:
                #     df.columns = ["Col {}".format(2 * idx - 1), "Col {}".format(2 * idx)]
                df_indv = pd.read_csv(file_item, header=None, delimiter=';')
                column_name = file_item.split("\\")[-1]
                df_indv.columns = ["{}".format(column_name), "{} time".format(column_name)]
                df_indv['{} time'.format(column_name)]=df_indv['{} time'.format(column_name)].apply(convert_matlab_timestamp)

                # axis = 0 => stack dataframe vertically / axis = 1 => stack dataframe horizontally
                df = pd.concat([df, df_indv], axis=1)

            except:
                print('Could not open {}'.format(filepath))




    # column name을 fname과 연관된 걸로 만들자
    # 근데 이건 callback과 연관이 있기 때문에.. 좀 더 고민할 필요


# return을 할 내용들은? 아무래도 pandas를 보내면 될것 같은데 말이지.
    return df
if __name__ == '__main__':

    #fname은 graph 이름 정의 할 때 필요. 그리고 maybe column name for panda dataframe
    full_path = print_file_path_list()
    #filename_list.append(item.split("\\")[-1])

    # 만일 yield/generator 를 사용하고 싶다면

    pd_df = Raw_Data_to_Pandas_DF(full_path)
    print(pd_df)

    # how to aggregate all the dataframes into one single dataframe

    #temp = pd.DataFrame(full_path)
