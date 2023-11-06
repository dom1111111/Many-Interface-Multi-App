import tkinter as tk

def center_window(window_object:tk.Tk, width:int, height:int):
    # get dimensions of computer screen
    screen_width = window_object.winfo_screenwidth()
    screen_height = window_object.winfo_screenheight()
    # make sure the window can't be bigger than 90% of the screen
    if width > screen_width * 0.90:
        width = int(screen_width * 0.90)
    if height > screen_height * 0.90:
        height = int(screen_height * 0.90)
    # find center coordinates of screen, and top-left coordinates of window relative to center
    center_x = int(screen_width/2 - width/2)
    center_y = int(screen_height/2 - height/2)
    # set geometry
    window_object.geometry(f'{width}x{height}+{center_x}+{center_y}')   # argument is the starting size of the window in pixels (width, height) and position of top-left corner on the computer screen (x, y) 

def set_geometry_sensibly(window_object:tk.Tk, percentage:int):
    """
    This will create a window which is horizontally centered, and just above the vertical center, on the screen
    - `percentage` is the percentage of the screen's dimensions that the window's dimensions will take up
        - This is limited to 90%
    """
    # set percentage limit to 90
    if percentage > 90:
        percentage = 90
    # get dimensions of computer screen
    screen_width = window_object.winfo_screenwidth()
    screen_height = window_object.winfo_screenheight()
    width = int(screen_width * percentage/100)
    height = int(screen_height * percentage/100)
    # find center coordinates of screen, and top-left coordinates of window relative to center
    center_x = int(screen_width/2 - width/2)
    center_y = int((screen_height/5 * 2) - height/2)    # makes sure window y-position is near between top and middle of screen
    if center_y < 0:                                    # makes sure that window won't go off screen
        center_y = 0
    # set window height, width, and x/y coordinates of its top-left corner - all in pixels
    window_object.geometry(f'{width}x{height}+{center_x}+{center_y}')
    # set minimum height and width of window to be 25% of screen's height and width
    window_object.minsize(int(screen_width*0.25), int(screen_height*0.25))
