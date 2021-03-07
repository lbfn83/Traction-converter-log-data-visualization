import tkinter as tk
from tkinter import filedialog
import os

#using Tkinter, pop up the window to choose the directory and as an output send out the list of path + file names should be returned

#input : directory selected
#output : list of files inside the directory
def proto() :
    root = tk.Tk()
    root.withdraw()
    """Withdraw this widget from the screen such that it is unmapped
            and forgotten by the window manager. Re-draw it with wm_deiconify."""

    file_path = filedialog.askdirectory(initialdir ='shell:MyComputerFolder')
    print(file_path)
    ## Extract file names and path
    for top, subdir, files in os.walk(file_path):
        # print ("****Name of Sub Directory****")
        # print("=> " + top)
        # print("   *List of file entries")
        if files != None :
            for fname in files:
#아무래도 여기서 리스트로 모두 받아줘야 하지 않을까?

                print("    =>" + fname)
        else :
            print("    => None")
        print("    **************************")
        print()

    return

if __name__ == '__main__':
    proto()