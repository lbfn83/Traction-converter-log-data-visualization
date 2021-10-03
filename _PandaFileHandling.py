import tkinter as tk
from tkinter import filedialog
import os
import pandas as pd
import datetime
import pandas as pd
#using Tkinter, pop up the window to choose the directory and as an output send out the list of path + file names should be returned


#Convert Matlab's raw timestamp to YYYY-MM-DD 00:00:00
def convert_matlab_timestamp(raw_tp):

    #Matlab timestamp start to count up the date from 0001-01-01 00:00:00
    stdtime_matlab = datetime.datetime(1, 1, 1, 0, 0, 0, 0)
    # order is days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
    time_result = stdtime_matlab + datetime.timedelta(0, int(raw_tp / 10000000), raw_tp % 10000000 / 10)

    # try to make data consistent with pd.Timestamp that is mainly used in Generic crossfilter.py . can be taken out when it comes to using this module with other program
    return pd.Timestamp(time_result)


#input : directory selected
#output : list of files inside the directory
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
    #generator!
    for top, subdir, files in os.walk(file_path):
        # print ("****Name of Sub Directory****")
        # print("=> " + top)
        # print("   *List of file entries")]
        path = top.replace("/", "\\")
        if files != None :
            for fname in files:
                tmp =(path , fname)
                full_path.append("\\".join(tmp))
                fname_list.append(fname)
        else :
            print("Directory is empty")
    return full_path


def Raw_Data_to_Pandas_DF(filepath):

    df = pd.DataFrame()

    for file_item in filepath:
        #empty file filtering
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
                print('Could not open {}'.format(file_item))

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
