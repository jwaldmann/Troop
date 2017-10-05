import Tkinter as Tk

class LineNumbers(Tk.Canvas):
    def __init__(self, master, *args, **kwargs):
        Tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = master
        
        self.redraw()

    def redraw(self, *args):
        '''redraw line numbers'''
        self.delete("all")

        # Draw a line

        w = self.winfo_width() - 5
        h = self.winfo_height()

        self.create_line(w, 0, w, h, fill="black")

        i = self.textwidget.index("@0,0")
        
        while True:

            dline=self.textwidget.dlineinfo(i)

            if dline is None:
                break

            y = dline[1]

            linenum = str(i).split(".")[0]

            self.create_text(w - 4, y, anchor="ne",
                             justify=Tk.RIGHT,
                             text=linenum,
                             font="Font",
                             fill="gray")

            i = self.textwidget.index("%s+1line" % i)

        self.after(30, self.redraw)
