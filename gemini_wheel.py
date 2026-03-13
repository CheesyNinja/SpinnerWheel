import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import numpy as np
import random
import time
import csv
import os


class SmartSpinWheel:
    def __init__(self, root):
        self.root = root
        self.root.title("Proportional Smart Wheel")

        self.is_fullscreen = False
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.end_fullscreen)
        self.root.bind("<Configure>", self.resize_ui)

        if not os.path.exists('saves'):
            os.makedirs('saves')

        # Data State
        self.options = ["Option 1", "Option 2", "Option 3"]
        self.percentages = [33.33, 33.33, 33.34]
        self.locks = [False, False, False]

        self.colors = plt.get_cmap('tab10').colors
        self.current_angle = 0
        self.is_spinning = False

        self.setup_ui()
        self.rebuild_entries()
        self.refresh_plot()

    def setup_ui(self):
        self.root.columnconfigure(1, weight=3)
        self.root.rowconfigure(0, weight=1)

        # --- LEFT PANEL ---
        self.left_panel = tk.Frame(self.root, padx=10, pady=10, bg="#f0f0f0")
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.rowconfigure(0, weight=1)

        self.canvas_container = tk.Canvas(self.left_panel, bg="#f0f0f0", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.left_panel, orient="vertical", command=self.canvas_container.yview)
        self.rows_frame = tk.Frame(self.canvas_container, bg="#f0f0f0")

        self.rows_frame.bind("<Configure>",
                             lambda e: self.canvas_container.configure(scrollregion=self.canvas_container.bbox("all")))
        self.canvas_container.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.canvas_container.configure(yscrollcommand=self.scrollbar.set)

        self.canvas_container.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # --- BOTTOM CONTROLS ---
        self.bottom_controls = tk.Frame(self.left_panel, bg="#f0f0f0")
        self.bottom_controls.grid(row=1, column=0, columnspan=2, sticky="sew", pady=(10, 0))

        tk.Button(self.bottom_controls, text="+ Add", command=self.add_option).grid(row=0, column=0, padx=2,
                                                                                    sticky="ew")

        # Dual-Function Equalize Button
        eq_btn = tk.Button(self.bottom_controls, text="Equalize (L/R Click)")
        eq_btn.grid(row=0, column=1, padx=2, sticky="ew")
        eq_btn.bind("<Button-1>", lambda e: self.equalize_slices(force_all=False))  # Left Click
        eq_btn.bind("<Button-3>", lambda e: self.equalize_slices(force_all=True))  # Right Click

        tk.Button(self.bottom_controls, text="Sort High-Low", command=self.sort_by_percentage).grid(row=1, column=0,
                                                                                                    padx=2, pady=2,
                                                                                                    sticky="ew")
        self.spin_btn = tk.Button(self.bottom_controls, text="SPIN", bg="#4CAF50", fg="white",
                                  font=('Arial', 10, 'bold'), command=self.spin_animation)
        self.spin_btn.grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        tk.Button(self.bottom_controls, text="Save", command=self.save_to_csv).grid(row=2, column=0, padx=2,
                                                                                    sticky="ew")
        tk.Button(self.bottom_controls, text="Load", command=self.load_from_csv).grid(row=2, column=1, padx=2,
                                                                                      sticky="ew")

        self.bottom_controls.columnconfigure(0, weight=1)
        self.bottom_controls.columnconfigure(1, weight=1)

        # --- RIGHT PANEL ---
        self.right_panel = tk.Frame(self.root, bg="white")
        self.right_panel.grid(row=0, column=1, sticky="nsew")

        self.fig, self.ax = plt.subplots(figsize=(6, 6), dpi=100)
        self.fig.patch.set_facecolor('white')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

    def equalize_slices(self, force_all=False):
        self.sync_names()
        count = len(self.options)
        if count == 0: return

        if force_all:
            # Right Click: Reset everything
            self.locks = [False] * count
            avg = 100.0 / count
            self.percentages = [avg] * count
        else:
            # Left Click: Smart Equalize (Unlocked only)
            unlocked_indices = [i for i, L in enumerate(self.locks) if not L]
            if not unlocked_indices:
                messagebox.showinfo("Note", "All slices are locked. Nothing to equalize.")
                return

            locked_total = sum(self.percentages[i] for i, L in enumerate(self.locks) if L)
            available = 100.0 - locked_total

            if available <= 0:
                messagebox.showwarning("Warning", "Locked slices consume 100% of the wheel.")
                return

            avg_available = available / len(unlocked_indices)
            for i in unlocked_indices:
                self.percentages[i] = avg_available

        self.rebuild_entries()
        self.refresh_plot()

    def sort_by_percentage(self):
        self.sync_names()
        combined = sorted(zip(self.percentages, self.options, self.locks), key=lambda x: x[0], reverse=True)
        self.percentages, self.options, self.locks = map(list, zip(*combined))
        self.rebuild_entries()
        self.refresh_plot()

    def add_option(self):
        self.sync_names()
        unlocked_indices = [i for i, L in enumerate(self.locks) if not L]
        if not unlocked_indices:
            messagebox.showerror("Error", "Unlock a slice to add a new option!")
            return

        self.options.append(f"Option {len(self.options) + 1}")
        self.locks.append(False)
        self.percentages.append(0)

        total_unlocked_count = len(unlocked_indices) + 1
        locked_total = sum(self.percentages[i] for i, L in enumerate(self.locks) if L)
        available_for_unlocked = 100.0 - locked_total

        fair_share = available_for_unlocked / total_unlocked_count

        current_unlocked_total = sum(self.percentages[i] for i in unlocked_indices)
        if current_unlocked_total > 0:
            for i in unlocked_indices:
                self.percentages[i] -= (self.percentages[i] / current_unlocked_total) * fair_share

        self.percentages[-1] = fair_share
        self.rebuild_entries()
        self.refresh_plot()

    def rebuild_entries(self):
        for widget in self.rows_frame.winfo_children(): widget.destroy()
        width = self.root.winfo_width()
        scale = max(1.0, width / 1200)
        font_size = int(14 * scale)
        self.entries, self.name_entries = [], []

        for i in range(len(self.options)):
            tk.Button(self.rows_frame, text="✕", fg="red", font=('Arial', 8, 'bold'), relief=tk.FLAT,
                      bg="#f0f0f0", command=lambda idx=i: self.remove_specific_option(idx)).grid(row=i, column=0)

            var = tk.BooleanVar(value=self.locks[i])
            tk.Checkbutton(self.rows_frame, variable=var, bg="#f0f0f0",
                           command=lambda idx=i, v=var: self.update_lock(idx, v)).grid(row=i, column=1)

            ne = tk.Entry(self.rows_frame, font=('Arial', font_size), width=int(12 * scale))
            ne.insert(0, self.options[i]);
            ne.grid(row=i, column=2, padx=2, pady=5)
            self.name_entries.append(ne)

            pe = tk.Entry(self.rows_frame, width=int(5 * scale), font=('Arial', font_size, 'bold'))
            pe.insert(0, str(round(self.percentages[i], 2)))
            pe.bind("<Return>", lambda e, idx=i: self.smart_adjust(idx))
            pe.grid(row=i, column=3, padx=2, pady=5)
            self.entries.append(pe)
            tk.Label(self.rows_frame, text="%", bg="#f0f0f0", font=('Arial', font_size)).grid(row=i, column=4)

    def remove_specific_option(self, idx):
        if len(self.options) <= 2: return
        self.sync_names()
        val = self.percentages.pop(idx)
        self.options.pop(idx);
        self.locks.pop(idx)
        unlocked = [i for i, L in enumerate(self.locks) if not L]
        if unlocked:
            for i in unlocked: self.percentages[i] += val / len(unlocked)
        else:
            self.locks[0] = False;
            self.percentages[0] += val
        self.rebuild_entries();
        self.refresh_plot()

    def sync_names(self):
        if hasattr(self, 'name_entries'):
            for i in range(min(len(self.options), len(self.name_entries))):
                self.options[i] = self.name_entries[i].get()

    def update_lock(self, idx, var):
        self.locks[idx] = var.get()

    def smart_adjust(self, idx):
        self.sync_names()
        try:
            new_val = float(self.entries[idx].get())
            if not (0 <= new_val <= 100): raise ValueError
        except:
            messagebox.showerror("Error", "Enter 0-100");
            return

        others = [i for i in range(len(self.percentages)) if i != idx]
        unlocked_others = [i for i in others if not self.locks[i]]
        if not unlocked_others:
            messagebox.showwarning("Locked", "Unlock others to adjust!");
            self.rebuild_entries();
            return

        locked_total = sum(self.percentages[i] for i in others if self.locks[i])
        available = 100 - new_val - locked_total
        if available < 0:
            messagebox.showerror("Error", "No space left!");
            self.rebuild_entries();
            return

        current_unlocked_sum = sum(self.percentages[i] for i in unlocked_others)
        for i in range(len(self.percentages)):
            if i == idx:
                self.percentages[i] = new_val
            elif not self.locks[i]:
                if current_unlocked_sum > 0:
                    self.percentages[i] = (self.percentages[i] / current_unlocked_sum) * available
                else:
                    self.percentages[i] = available / len(unlocked_others)
        self.rebuild_entries();
        self.refresh_plot()

    def save_to_csv(self):
        self.sync_names()
        filename = simpledialog.askstring("Save", "Filename:")
        if not filename: return
        filepath = os.path.join('saves', f"{filename}.csv")
        with open(filepath, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Option', 'Percentage', 'Locked'])
            for i in range(len(self.options)):
                writer.writerow([self.options[i], self.percentages[i], self.locks[i]])

    def load_from_csv(self):
        filepath = filedialog.askopenfilename(initialdir="saves", filetypes=(("CSV", "*.csv"),))
        if not filepath: return
        new_o, new_p, new_L = [], [], []
        with open(filepath, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                new_o.append(row['Option'])
                new_p.append(float(row['Percentage']))
                new_L.append(row['Locked'] == 'True')
        self.options, self.percentages, self.locks = new_o, new_p, new_L
        self.rebuild_entries();
        self.refresh_plot()

    def refresh_plot(self, start_angle=0, font_size=None):
        if not hasattr(self, 'ax'): return
        if font_size is None: font_size = int(12 * (self.root.winfo_width() / 1200))
        self.ax.clear()
        self.ax.pie(self.percentages, labels=self.options, autopct='%1.1f%%', startangle=start_angle,
                    colors=self.colors, textprops={'fontsize': font_size, 'weight': 'bold'})
        arrow = patches.RegularPolygon(xy=(0, 1.1), numVertices=3, radius=0.1, orientation=np.pi, color='red')
        self.ax.add_patch(arrow);
        self.ax.axis('equal');
        self.canvas.draw()

    def spin_animation(self):
        if self.is_spinning: return
        self.sync_names();
        self.is_spinning = True
        v, decel, angle = random.uniform(30, 50), 0.975, self.current_angle
        while v > 0.2:
            angle = (angle + v) % 360
            self.refresh_plot(start_angle=angle)
            v *= decel;
            self.root.update();
            time.sleep(0.01)
        self.current_angle = angle;
        self.is_spinning = False;
        self.determine_winner(angle)

    def determine_winner(self, final_angle):
        norm = (90 - final_angle) % 360
        curr = 0
        for i, p in enumerate(self.percentages):
            curr += (p / 100) * 360
            if norm <= curr:
                win = tk.Toplevel(self.root);
                win.attributes("-topmost", True)
                tk.Label(win, text=f"WINNER:\n{self.options[i]}", font=('Arial', 36, 'bold'), padx=50, pady=50).pack()
                break

    def toggle_fullscreen(self, e=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        self.root.after(100, self.rebuild_entries)
        return "break"

    def end_fullscreen(self, e=None):
        self.is_fullscreen = False;
        self.root.attributes("-fullscreen", False)
        self.root.after(100, self.rebuild_entries);
        return "break"

    def resize_ui(self, e=None):
        w = self.root.winfo_width()
        self.refresh_plot(font_size=int(12 * (w / 1400)))


if __name__ == "__main__":
    root = tk.Tk();
    root.geometry("1100x800")
    app = SmartSpinWheel(root);
    root.mainloop()