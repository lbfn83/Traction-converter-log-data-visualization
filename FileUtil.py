import tkinter as tk
from tkinter import filedialog
import os
import datetime
import pandas as pd

'''
Return type : List of target files ending with log extension in a selected directory with and without absolute path
'''
def getFilePathList() :
    root = tk.Tk()
    # tk's default root window should be hidden.
    root.withdraw()

    # shell:MyComputerFolder => CLSID
    filePath = filedialog.askdirectory(initialdir ='shell:MyComputerFolder')
    #print(filePath)

    fullPathList = []
    fnameList= []
    # Platform independent paths collection => normalizePath
    for topdir, subdir, files in os.walk(os.path.normpath(filePath)):

        if files != None :
            for fname in files:
                if fname.endswith('log'):
                    fullPathList.append(os.path.join(topdir, fname))
                    fnameList.append(fname)
        else :
            print("Directory is empty")
    return [fullPathList, fnameList]

'''
Aggregate contents of multiple log files in a single panda DataFrame

param => filePath : list of files selected
return type : single dataframe
'''
def RawDataAggregationToDF(filePath):

    df = pd.DataFrame()
    for fileItem in filePath:
        #filtering out empty files
        if os.path.getsize(fileItem) > 0:
            try:
                # Format of log file : "data;timestamp"
                df_indv = pd.read_csv(fileItem, header=None, delimiter=';')
                column_name = fileItem.split(os.sep)[-1]
                df_indv.columns = ["{}".format(column_name), "{} time".format(column_name)]

                df_indv['{} time'.format(column_name)] = df_indv['{} time'.format(column_name)].apply(convertMatlabTimestamp)

                # axis = 0 => stack dataframe vertically / axis = 1 => stack dataframe horizontally
                df = pd.concat([df, df_indv], axis=1)

            except:
                print('Could not open {}'.format(fileItem))
    return df

'''
convert_matlab_timestamp : Convert Matlab's intrinsic timestamp ( generated from Traction Converter ) to Python's timestamp 
param => rawTS : timestamp that is extracted from log files, which is written 0.1 microseconds / Refer to log files located in Sample_Data_Normal data load folder  
return type : panda Timestamp
'''
def convertMatlabTimestamp(rawTS):

    # Matlab timestamp start to count up the date from 0001-01-01 00:00:00
    stdtime_matlab = datetime.datetime(1, 1, 1, 0, 0, 0, 0)

    # parameters for timedelta : days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
    time_result = stdtime_matlab + datetime.timedelta(0, int(rawTS / 10000000), rawTS % 10000000 / 10)

    return pd.Timestamp(time_result)

if __name__ == '__main__':

    # Below codes are kept for Debug
    full_path, fnameList = getFilePathList()
    print(full_path)
    print('===========')
    print(fnameList)
    pd_df = RawDatatoPandasDF(full_path)
    # print(pd_df)

