import tkinter as tk
from tkinter import messagebox

class VectorInputDialog(tk.Toplevel):
    def __init__(self, parent, n, title="Введіть вектор"):
        super().__init__(parent)
        self.parent = parent
        self.n = n
        self.title(title)
        self.vector = None
        self._build_ui()
        self.grab_set()
        self.transient(parent)
        self.wait_window()

    def _build_ui(self):
        tk.Label(self, text=f"Введіть {self.n} компонент(у/ів) вектора:").pack(padx=10, pady=(10,0))
        self.entries = []
        frame = tk.Frame(self)
        frame.pack(padx=10, pady=5)
        for i in range(self.n):
            lbl = tk.Label(frame, text=f"x{i+1} =")
            lbl.grid(row=i, column=0, sticky="e", padx=2, pady=2)
            ent = tk.Entry(frame, width=10)
            ent.grid(row=i, column=1, padx=2, pady=2)
            self.entries.append(ent)
        btn = tk.Button(self, text="OK", command=self._on_ok)
        btn.pack(pady=(0,10))

    def _on_ok(self):
        vals = []
        try:
            for ent in self.entries:
                txt = ent.get().strip()
                if txt == "":
                    raise ValueError
                vals.append(float(txt))
        except ValueError:
            messagebox.showerror("Помилка", "Всі поля мають містити дійсні числа.")
            return
        self.vector = vals
        self.destroy()

class ScalarProductApp:
    def __init__(self, root):
        self.root = root
        root.title("Скалярний добуток двох векторів")
        self._build_ui()

    def _build_ui(self):
        frm = tk.Frame(self.root, padx=10, pady=10)
        frm.pack()
        tk.Label(frm, text="Кількість компонент n:").grid(row=0, column=0, sticky="e")
        self.n_entry = tk.Entry(frm, width=5)
        self.n_entry.grid(row=0, column=1, sticky="w")
        btn = tk.Button(frm, text="Ввести вектори та обчислити", command=self.on_compute)
        btn.grid(row=1, column=0, columnspan=2, pady=10)
        tk.Label(frm, text="Вектор 1:").grid(row=2, column=0, sticky="nw")
        self.lb1 = tk.Listbox(frm, height=10, width=15)
        self.lb1.grid(row=2, column=1, pady=5)
        tk.Label(frm, text="Вектор 2:").grid(row=3, column=0, sticky="nw")
        self.lb2 = tk.Listbox(frm, height=10, width=15)
        self.lb2.grid(row=3, column=1, pady=5)
        self.result_label = tk.Label(frm, text="Скалярний добуток: —")
        self.result_label.grid(row=4, column=0, columnspan=2, pady=(10,0))

    def on_compute(self):
        self.lb1.delete(0, tk.END)
        self.lb2.delete(0, tk.END)
        self.result_label.config(text="Скалярний добуток: —")
        try:
            n = int(self.n_entry.get())
            if n <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Помилка", "n має бути додатним цілим числом.")
            return
        dlg1 = VectorInputDialog(self.root, n, title="Введіть вектор 1")
        if dlg1.vector is None:
            return
        dlg2 = VectorInputDialog(self.root, n, title="Введіть вектор 2")
        if dlg2.vector is None:
            return
        v1, v2 = dlg1.vector, dlg2.vector
        for x in v1:
            self.lb1.insert(tk.END, f"{x:.3f}")
        for x in v2:
            self.lb2.insert(tk.END, f"{x:.3f}")
        scalar = sum(a*b for a,b in zip(v1, v2))
        self.result_label.config(text=f"Скалярний добуток: {scalar:.3f}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScalarProductApp(root)
    root.mainloop()
