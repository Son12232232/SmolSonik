import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

# ----- GridCanvas і BoundText прямо тут -----
class GridCanvas(tk.Canvas):
    def __init__(self, master, rows, cols, cellsize=60, **kwargs):
        width = cols * cellsize
        height = rows * cellsize
        super().__init__(master, width=width, height=height, **kwargs)
        self.rows = rows
        self.cols = cols
        self.cellsize = cellsize
        self._highlight_items = []
        self._draw_grid()

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
        x1, y1 = x0 + self.cellsize, y0 + self.cellsize
        rect = self.create_rectangle(x0, y0, x1, y1, outline=color, width=3)
        self._highlight_items.append(rect)

    def unhighlight_all(self):
        for item in self._highlight_items:
            self.delete(item)
        self._highlight_items.clear()

class BoundText:
    def __init__(self, canvas, text="", font=None):
        self.canvas = canvas
        self.item = self.canvas.create_text(0, 0, text=text, font=font)

    def place(self, x, y, anchor="center"):
        self.canvas.coords(self.item, x, y)
        self.canvas.itemconfig(self.item, anchor=anchor)

    def config(self, **kwargs):
        self.canvas.itemconfig(self.item, **kwargs)

# ----- решта коду мережевих шахів -----
UNICODE = {
    'r': '\u265C','n': '\u265E','b': '\u265D','q': '\u265B',
    'k': '\u265A','p': '\u265F',
    'R': '\u2656','N': '\u2658','B': '\u2657','Q': '\u2655',
    'K': '\u2654','P': '\u2659','.': ''
}
START_POS = [
    list("rnbqkbnr"),
    list("pppppppp"),
    list("........"),
    list("........"),
    list("........"),
    list("........"),
    list("PPPPPPPP"),
    list("RNBQKBNR"),
]

class NetworkChess:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Мережева гра в шахи")
        self._ask_connection()
        self.board = [row[:] for row in START_POS]
        self.turn = 'white'
        self.selected = None
        self._build_ui()
        threading.Thread(target=self._network_loop, daemon=True).start()
        self.root.mainloop()

    def _ask_connection(self):
        host = simpledialog.askstring("Host чи Client",
                                      "IP хоста (порожньо → сервер):")
        if not host:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.conn.bind(('0.0.0.0', 54321))
            self.conn.listen(1)
            self.sock, _ = self.conn.accept()
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, 54321))

    def _build_ui(self):
        self.gc = GridCanvas(self.root, rows=8, cols=8, cellsize=60)
        self.gc.pack()
        self.texts = [[None]*8 for _ in range(8)]
        for r in range(8):
            for c in range(8):
                txt = BoundText(self.gc, text=UNICODE[self.board[r][c]],
                                font=("Arial", 32))
                txt.place(x=c*60+30, y=r*60+30)
                self.texts[r][c] = txt
        self.gc.bind("<Button-1>", self._on_click)

    def _on_click(self, evt):
        c, r = evt.x//60, evt.y//60
        if not (0 <= r < 8 and 0 <= c < 8): return
        piece = self.board[r][c]
        if self.selected is None:
            if (self.turn=='white' and piece.isupper()) or \
               (self.turn=='black' and piece.islower()):
                self.selected = (r, c)
                self.gc.highlight_cell(r, c)
        else:
            r0, c0 = self.selected
            self._make_move(r0, c0, r, c)
            try:
                self.sock.sendall(f"{r0}{c0}{r}{c}".encode())
            except:
                messagebox.showerror("Помилка", "Втрачено зв’язок")
            self.gc.unhighlight_all()
            self.selected = None

    def _make_move(self, r0, c0, r1, c1):
        self.board[r1][c1] = self.board[r0][c0]
        self.board[r0][c0] = '.'
        self.texts[r1][c1].config(text=UNICODE[self.board[r1][c1]])
        self.texts[r0][c0].config(text="")
        self.turn = 'black' if self.turn=='white' else 'white'

    def _network_loop(self):
        while True:
            data = self.sock.recv(16)
            if not data: break
            r0,c0,r1,c1 = map(int, data.decode())
            self._make_move(r0, c0, r1, c1)

if __name__ == "__main__":
    NetworkChess()
