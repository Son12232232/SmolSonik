import tkinter as tk

class GridCanvas(tk.Canvas):
    def __init__(self, master, rows, cols, cellsize=60, **kwargs):
        width = cols * cellsize
        height = rows * cellsize
        super().__init__(master, width=width, height=height, **kwargs)
        self.rows = rows
        self.cols = cols
        self.cellsize = cellsize
        self._draw_grid()
        self._highlight_items = []

    def _draw_grid(self):
        for i in range(self.rows + 1):
            y = i * self.cellsize
            self.create_line(0, y, self.cols * self.cellsize, y)
        for j in range(self.cols + 1):
            x = j * self.cellsize
            self.create_line(x, 0, x, self.rows * self.cellsize)

    def highlight_cell(self, r, c, color="yellow"):
        x0 = c * self.cellsize
        y0 = r * self.cellsize
        x1 = x0 + self.cellsize
        y1 = y0 + self.cellsize
        rect = self.create_rectangle(x0, y0, x1, y1, outline=color, width=3)
        self._highlight_items.append(rect)

    def unhighlight_all(self):
        for item in self._highlight_items:
            self.delete(item)
        self._highlight_items.clear()

class BoundText:
    def __init__(self, canvas, text="", font=None):
        self.canvas = canvas
        self.font = font
        self.item = self.canvas.create_text(0, 0, text=text, font=self.font)

    def place(self, x, y, anchor="center"):
        self.canvas.coords(self.item, x, y)
        self.canvas.itemconfig(self.item, anchor=anchor)

    def config(self, **kwargs):
        self.canvas.itemconfig(self.item, **kwargs)
