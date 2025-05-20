import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages

class DataReportGenerator:
    """
    Програма з графічним інтерфейсом для аналізу даних:
    - Завантаження CSV/Excel у два масиви
    - Методи додавання елементів, векторів, парного та випадкового додавання
    - Відображення статистичних показників і графіків
    - Збереження результатів у CSV та PDF-звіт
    """
    def __init__(self):
        self.exp_data = None      # експериментальні дані (DataFrame з двома колонками)
        self.model_data = None    # дані моделі (DataFrame з двома колонками)

        self.root = tk.Tk()
        self.root.title("Генератор звітів з аналізу даних")
        self._create_widgets()
        self.root.mainloop()

    def _create_widgets(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        buttons = [
            ("Завантажити CSV", self.load_csv),
            ("Завантажити Excel", self.load_excel),
            ("Додати елемент", self.add_element),
            ("Парне додавання", self.pairwise_add),
            ("Додати вектор", self.add_vector),
            ("Додати випадкові", self.add_random),
            ("Показати статистику", self.show_stats),
            ("Показати графіки", self.show_plots),
            ("Зберегти CSV", self.save_csv),
            ("Згенерувати PDF", self.generate_report),
        ]
        for (text, cmd) in buttons:
            tk.Button(control_frame, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        # Поле для графіків
        self.plot_frame = tk.Frame(self.root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = None

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV файли", "*.csv")])
        if not path:
            return
        df = pd.read_csv(path)
        self._assign_data(df)

    def load_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel файли", "*.xlsx;*.xls")])
        if not path:
            return
        df = pd.read_excel(path)
        self._assign_data(df)

    def _assign_data(self, df):
        # Вибрати перші дві числові колонки
        nums = df.select_dtypes(include=[np.number])
        if nums.shape[1] < 2:
            messagebox.showerror("Помилка", "Дані мають містити щонайменше дві числові колонки")
            return
        cols = nums.columns[:2]
        self.exp_data = nums[cols].copy()
        self.model_data = self.exp_data.copy()
        messagebox.showinfo("Готово", "Дані успішно завантажено")

    def add_element(self):
        if self.model_data is None:
            messagebox.showerror("Помилка", "Спочатку завантажте дані")
            return
        # Додати по одному значенню в кожний масив (дві колонки)
        v1 = simpledialog.askfloat("Додати елемент", "Введіть значення для першого масиву:")
        if v1 is None:
            return
        v2 = simpledialog.askfloat("Додати елемент", "Введіть значення для другого масиву:")
        if v2 is None:
            return
        new_row = pd.DataFrame({self.model_data.columns[0]: [v1],
                                self.model_data.columns[1]: [v2]})
        self.model_data = pd.concat([self.model_data, new_row], ignore_index=True)
        messagebox.showinfo("Готово", "Елемент додано до обох масивів")

    def pairwise_add(self):
        if self.model_data is None:
            messagebox.showerror("Помилка", "Спочатку завантажте дані")
            return
        # Парне додавання: елемент i-го масиву додається до іншого
        a_col, b_col = self.model_data.columns[:2]
        a_old = self.model_data[a_col].copy()
        self.model_data[a_col] = self.model_data[a_col] + self.model_data[b_col]
        self.model_data[b_col] = self.model_data[b_col] + a_old
        messagebox.showinfo("Готово", "Парне додавання виконано для обох масивів")

    def add_vector(self):
        if self.model_data is None:
            messagebox.showerror("Помилка", "Спочатку завантажте дані")
            return
        col = simpledialog.askstring("Вибір масиву", \
            f"Введіть назву колонки для додавання вектору ({', '.join(self.model_data.columns[:2])}):")
        if col not in self.model_data.columns[:2]:
            messagebox.showerror("Помилка", "Невірна назва колонки")
            return
        vec_str = simpledialog.askstring("Вектор", "Введіть елементи вектору через кому:")
        if not vec_str:
            return
        try:
            vec = np.array([float(v.strip()) for v in vec_str.split(',')])
        except ValueError:
            messagebox.showerror("Помилка", "Невірний формат вектору")
            return
        if len(vec) != len(self.model_data):
            messagebox.showerror("Помилка",
                f"Довжина вектору ({len(vec)}) повинна збігатися з довжиною масиву ({len(self.model_data)})")
            return
        self.model_data[col] = self.model_data[col] + vec
        messagebox.showinfo("Готово", f"Вектор додано до колонки {col}")

    def add_random(self):
        if self.model_data is None:
            messagebox.showerror("Помилка", "Спочатку завантажте дані")
            return
        n = simpledialog.askinteger("Випадкові дані", "Кількість випадкових елементів:")
        if n is None or n <= 0:
            return
        mu = simpledialog.askfloat("Параметр mu", "Введіть середнє (mu):")
        if mu is None:
            return
        sigma = simpledialog.askfloat("Параметр sigma", "Введіть стандартне відхилення (sigma):")
        if sigma is None:
            return
        # Згенерувати та додати для обох колонок
        cols = self.model_data.columns[:2]
        rand1 = np.random.normal(mu, sigma, n)
        rand2 = np.random.normal(mu, sigma, n)
        new_df = pd.DataFrame({cols[0]: rand1, cols[1]: rand2})
        self.model_data = pd.concat([self.model_data, new_df], ignore_index=True)
        messagebox.showinfo("Готово", f"Додано {n} випадкових елементів до обох масивів")

    def show_stats(self):
        if self.exp_data is None:
            messagebox.showerror("Помилка", "Немає даних для аналізу")
            return
        stats = []
        for name, df in [("Експериментальні", self.exp_data), ("Модельні", self.model_data)]:
            for col in df.columns[:2]:
                series = df[col]
                stats.append(
                    f"{name} - {col}: mean={series.mean():.3f}, median={series.median():.3f}, "
                    f"var={series.var():.3f}, std={series.std():.3f}"
                )
        messagebox.showinfo("Статистичні показники", "\n".join(stats))

    def show_plots(self):
        if self.exp_data is None:
            messagebox.showerror("Помилка", "Немає даних для побудови графіків")
            return
        # Очистити попередній графік
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        fig, axes = plt.subplots(2, 2, figsize=(6, 4))
        cols = self.exp_data.columns[:2]
        # гістограми
        axes[0, 0].hist(self.exp_data[cols[0]], bins=20)
        axes[0, 0].set_title(f"Експериментальні {cols[0]}")
        axes[0, 1].hist(self.model_data[cols[0]], bins=20)
        axes[0, 1].set_title(f"Модельні {cols[0]}")
        axes[1, 0].hist(self.exp_data[cols[1]], bins=20)
        axes[1, 0].set_title(f"Експериментальні {cols[1]}")
        axes[1, 1].hist(self.model_data[cols[1]], bins=20)
        axes[1, 1].set_title(f"Модельні {cols[1]}")
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def save_csv(self):
        if self.exp_data is None:
            messagebox.showerror("Помилка", "Немає даних для збереження")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV файли", "*.csv")])
        if not path:
            return
        cols = self.exp_data.columns[:2]
        df = pd.DataFrame({
            f'exp_{cols[0]}': self.exp_data[cols[0]],
            f'exp_{cols[1]}': self.exp_data[cols[1]],
            f'mod_{cols[0]}': self.model_data[cols[0]],
            f'mod_{cols[1]}': self.model_data[cols[1]],
        })
        df.to_csv(path, index=False)
        messagebox.showinfo("Готово", f"Результати збережено в {path}")

    def generate_report(self):
        if self.exp_data is None:
            messagebox.showerror("Помилка", "Немає даних для звіту")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF файли", "*.pdf")])
        if not path:
            return
        cols = self.exp_data.columns[:2]
        with PdfPages(path) as pdf:
            # Сторінка зі статистикою
            stats = []
            for name, df in [("Експериментальні", self.exp_data), ("Модельні", self.model_data)]:
                for col in cols:
                    series = df[col]
                    stats.append(
                        f"{name} - {col}: mean={series.mean():.3f}, median={series.median():.3f}, "
                        f"var={series.var():.3f}, std={series.std():.3f}"
                    )
            fig_text = plt.figure(figsize=(8, 6))
            plt.axis('off')
            plt.text(0.01, 0.99, "Статистичні показники", fontsize=14, va='top')
            for i, line in enumerate(stats, start=1):
                plt.text(0.01, 0.99 - i*0.03, line, va='top')
            pdf.savefig(fig_text)
            plt.close(fig_text)

            # Гістограми
            fig, axes = plt.subplots(2, 2, figsize=(8, 6))
            axes[0, 0].hist(self.exp_data[cols[0]], bins=20)
            axes[0, 0].set_title(f"Експериментальні {cols[0]}")
            axes[0, 1].hist(self.model_data[cols[0]], bins=20)
            axes[0, 1].set_title(f"Модельні {cols[0]}")
            axes[1, 0].hist(self.exp_data[cols[1]], bins=20)
            axes[1, 0].set_title(f"Експериментальні {cols[1]}")
            axes[1, 1].hist(self.model_data[cols[1]], bins=20)
            axes[1, 1].set_title(f"Модельні {cols[1]}")
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

        messagebox.showinfo("Готово", f"PDF звіт збережено в {path}")

if __name__ == '__main__':
    DataReportGenerator()
