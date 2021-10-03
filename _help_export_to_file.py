import sys
import pandas as pd

def output_help_to_file(filepath):
    f = open(filepath, 'r')

    df = pd.read_csv('C:\\Users\\lbfn8\\Desktop\\A End 12292020\\Transient Recorder\\TranRecA-269\\1-UL_AUX.log', header = None, delimiter=';',
                     index_col=0)
    df = pd.read_csv('C:\\Users\\lbfn8\\Desktop\\A End 12292020\\Transient Recorder\\TranRecA-269\\1-UL_AUX.log',
                     header=None, delimiter=';')
    f.close()
    sys.stdout = sys.__stdout__
    return

if __name__ == '__main__':
    output_help_to_file('C:\\Users\\lbfn8\\Desktop\\A End 12292020\\Transient Recorder\\TranRecA-269\\1-UL_AUX.log')