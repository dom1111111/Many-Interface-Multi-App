import tkinter as tk
from tkinter import ttk
from ctypes import windll
from .tkinter_tools import set_geometry_sensibly
from .core_UI import CoreUI

#---------

class tkTextBoxGUI(CoreUI):
    def __init__(self, title:str):
        super().__init__()                              # initiate parent class

        try:
            windll.shcore.SetProcessDpiAwareness(1)     # this makes it so that text is not blury!
        except:
            pass

        # create GUI window
        self.window = tk.Tk()                           # create root tk window wdiget    
        self.window.title = title                       # set title of root window
        set_geometry_sensibly(self.window, 60)          # set the window to start in the center, and take up 60% of the screen
        self.window.configure(background='black', padx=5, pady=5)   # set background colour and padding

        # configure column and row of both the window and any frames if you want things to be resizeable
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=4)
        self.window.rowconfigure(1, weight=0)
        
        # create/adjust widget styles
        # ...

        # create and setup widgets
        self.main_view = tk.Text(self.window, font=("Seoge 12"), bg='black', padx=20, pady=10, spacing1=20, state='disabled')
        self.main_view.tag_configure("left", foreground="blue")
        self.main_view.tag_configure("right", foreground="grey", justify="right")

        self.entry_box = ttk.Entry(self.window, width=100, font=("Seoge 20"))
            # self.entry_box = tk.Text(self.window, height=3, bg='#313631', fg='#d3e6eb', padx=4, pady=4, state='normal')
        self.entry_box.bind('<Return>', self._collect_text_entry_input) # bind the enter key to entry widget

        # Layout widgets using `grid` geometry manager
        self.main_view.grid(row=0, column=0, sticky=('n','s','e','w'))
        self.entry_box.grid(row=1, column=0, sticky=('n','s','e','w'))

    #---------
    # methods which change GUI while running

    def start_listening(self):
        self.window.configure(background='green')
        return super().start_listening()
    # override original methods to add visual notification
    def stop_listening(self):
        self.window.configure(background='black')
        return super().stop_listening()

    def _collect_text_entry_input(self, event):
        i = self.entry_box.get()                        # get contents of entry box
        if i:
            self.entry_box.delete(0, 'end')             # immediately delete contents
            self._store_input("TEXT", i)                # put contents and type ('TEXT') in input queue

    def mainview_append(self, text:str, tag_name:str):
        """Append a string of text to the main view, specifying the name of 
        the text tag to use to format the text. Behaves like a terminal.
        
        - 'left' = append text justified to the left
        - 'right' = append text justified to the right
        """
        self.main_view.config(state='normal')           # state must be normal in order for anything to happen to the log
        self.main_view.insert('end', text+'\n', tag_name)   # 'end' is the index for the end of the text, and the other string is the text to insert
        self.main_view.see('end')                       # makes sure the view is always at the end index (it scrolls to the bottom: the newest message)
        self.main_view.config(state='disabled')         # then disable the text box, so that no editing can occur (read-only)

    def clear_mainview(self):
        """Reset the main view to be blank"""
        self.main_view.config(state='normal')
        self.main_view.delete('1.0', 'end')             # the two arguments are the start and end index
        self.main_view.config(state='disabled')

    #---------
    # methods which start or stop running GUI

    def run(self):
        """this must be called from the main thread, and will persist - will not return!"""
        self.start_wakeword_detection()                 # start listening for voice audio
        self.window.mainloop()

    def stop(self):
        """stops running the GUI and all other UI components"""
        #self.stop_listening()
        self.silence()
        self.window.quit()

    def terminate(self):
        """CAN ONLY CALL THIS ONCE"""
        self.window.destroy()

#---------

if __name__ == "__main__":
    tb_gui = tkTextBoxGUI("a test GUI")
    tb_gui.run()
