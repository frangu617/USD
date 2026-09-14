"""Interactive independent rain simulations. Run with: python rain_probability.py"""

import math
import random
import time
import tkinter as tk
from tkinter import messagebox, ttk


def simulate(probability, days, seed=None):
    """Yield (day, rain today, total rain) for independent Bernoulli trials."""
    rng = random.Random(seed)
    total = 0
    for day in range(1, days + 1):
        rain = rng.random() < probability
        total += rain
        yield day, rain, total


class RainApp:
    def __init__(self, root):
        self.root = root
        root.title("Rain probability lab")
        root.geometry("1100x980")
        root.minsize(950, 900)
        self.points = []
        self.target = 0.2
        self.days = 7
        self.running = False
        self.pending_step = None
        self.history_days = 7
        self.history_totals = []
        self.range_controls = []
        self.probability = tk.StringVar(value="20")
        self.day_count = tk.StringVar(value="7")
        self.run_count = tk.StringVar(value="1")
        self.batch_status = tk.StringVar(value="Choose how many runs to simulate.")
        self.seed = tk.StringVar()
        self.status = tk.StringVar(value="Choose a chance and simulation range, then click Simulate.")
        self.log_scale = tk.BooleanVar(value=True)

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Rain probability lab", font=("Segoe UI", 23, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Explore why a probability describes a long-run frequency.").pack(anchor="w", pady=(0, 16))
        controls = ttk.Frame(frame)
        controls.pack(fill="x")
        for column, (label, variable, width) in enumerate([
            ("Chance of rain (%)", self.probability, 16),
            ("Range: number of days", self.day_count, 20),
            ("Random seed (optional)", self.seed, 20),
        ]):
            ttk.Label(controls, text=label).grid(row=0, column=column, sticky="w", padx=(0, 18))
            entry = ttk.Entry(controls, textvariable=variable, width=width)
            entry.grid(row=1, column=column, sticky="w", padx=(0, 18))
            self.range_controls.append(entry)
        self.run_button = ttk.Button(controls, text="Simulate", command=self.start)
        self.run_button.grid(row=1, column=3, padx=6)
        self.stop_button = ttk.Button(controls, text="Stop", command=self.stop, state="disabled")
        self.stop_button.grid(row=1, column=4)

        presets = ttk.Frame(frame)
        presets.pack(fill="x", pady=12)
        ttk.Label(presets, text="Try a range:").pack(side="left")
        for count in (1, 7, 10, 100, 1000, 10000, 100000, 1000000):
            button = ttk.Button(presets, text=f"{count:,}", command=lambda n=count: self.day_count.set(str(n)))
            button.pack(side="left", padx=3)
            self.range_controls.append(button)
        batches = ttk.Frame(frame)
        batches.pack(fill="x", pady=(0, 8))
        ttk.Label(batches, text="Number of runs:").pack(side="left")
        run_entry = ttk.Entry(batches, textvariable=self.run_count, width=12)
        run_entry.pack(side="left", padx=8)
        self.range_controls.append(run_entry)
        for count in (1, 10, 100, 1000):
            button = ttk.Button(batches, text=f"{count:,} runs", command=lambda n=count: self.run_count.set(str(n)))
            button.pack(side="left", padx=3)
            self.range_controls.append(button)
        ttk.Label(frame, textvariable=self.batch_status).pack(anchor="w")
        self.progress = ttk.Progressbar(frame, maximum=100)
        self.progress.pack(fill="x", pady=(4, 8))
        ttk.Label(frame, textvariable=self.status, font=("Segoe UI", 11), wraplength=900).pack(anchor="w", pady=(0, 8))
        ttk.Checkbutton(frame, text="Logarithmic day axis (makes early fluctuations easier to see)", variable=self.log_scale, command=self.draw).pack(anchor="w")
        self.canvas = tk.Canvas(frame, background="#f8fafc", height=280, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=8)
        self.canvas.bind("<Configure>", lambda event: self.draw())
        ttk.Label(frame, text="First 28 days — blue = rain, light gray = no rain").pack(anchor="w")
        self.day_canvas = tk.Canvas(frame, height=42, background="#ffffff", highlightthickness=0)
        self.day_canvas.pack(fill="x", pady=(4, 8))
        self.day_canvas.bind("<Configure>", lambda event: self.draw_days())
        self.first_days = []
        summary = ttk.LabelFrame(frame, text="Run history statistics", padding=(12, 6))
        summary.pack(fill="x", pady=(0, 8))
        self.summary_label = tk.StringVar()
        ttk.Label(summary, textvariable=self.summary_label).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))
        for column, title in enumerate(("Measure", "Average", "Lowest", "Highest")):
            summary.columnconfigure(column, weight=1)
            ttk.Label(summary, text=title, font=("Segoe UI", 10, "bold")).grid(row=1, column=column, sticky="w", padx=(0, 16))
        self.summary_values = {}
        for row, measure in enumerate(("Rainy days", "Observed rain %"), start=2):
            ttk.Label(summary, text=measure).grid(row=row, column=0, sticky="w", pady=2)
            for column, statistic in enumerate(("average", "lowest", "highest"), start=1):
                variable = tk.StringVar(value="—")
                self.summary_values[measure, statistic] = variable
                ttk.Label(summary, textvariable=variable).grid(row=row, column=column, sticky="w", pady=2)
        self.update_summary()
        notebook = ttk.Notebook(frame)
        notebook.pack(fill="x")
        history_frame = ttk.Frame(notebook)
        milestones_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="Run history")
        notebook.add(milestones_frame, text="Current run milestones")
        self.history_label = tk.StringVar(value="Results for 7 days — changing the number of days clears this log.")
        ttk.Label(history_frame, textvariable=self.history_label).pack(anchor="w", pady=4)
        self.history = ttk.Treeview(history_frame, columns=("run", "days", "rain", "proportion", "chance"), show="headings", height=5)
        for name, title in zip(self.history["columns"], ("Run", "Days", "Rainy days", "Observed rain %", "Chosen chance %")):
            self.history.heading(name, text=title)
            self.history.column(name, width=130, anchor="center")
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history.yview)
        self.history.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.history.pack(side="left", fill="x", expand=True)
        self.day_count.trace_add("write", self.range_changed)
        self.table = ttk.Treeview(milestones_frame, columns=("days", "rain", "proportion", "expected"), show="headings", height=6)
        for name, title in zip(self.table["columns"], ("Days simulated", "Rainy days", "Observed rain %", "Chosen chance %")):
            self.table.heading(name, text=title)
            self.table.column(name, width=150, anchor="center")
        self.table.pack(fill="x")
        ttk.Label(frame, text="Each day is independent with the same chance of rain. Short runs may differ greatly from that chance.\nLonger runs tend to stabilize, but do not necessarily get closer at every step. This is a model, not a weather forecast.", wraplength=920).pack(anchor="w", pady=(10, 0))

    def range_changed(self, *args):
        try:
            days = int(self.day_count.get().replace(",", ""))
        except ValueError:
            return  # Allow temporarily blank or unfinished input while typing.
        if 1 <= days <= 1000000 and days != self.history_days:
            self.history.delete(*self.history.get_children())
            self.history_totals.clear()
            self.history_days = days
            self.update_summary()
            self.history_label.set(f"Results for {days:,} days — changing the number of days clears this log.")

    def update_summary(self):
        count = len(self.history_totals)
        self.summary_label.set(f"{count:,} completed runs of {self.history_days:,} days each (all chances in the log)")
        if not count:
            for variable in self.summary_values.values():
                variable.set("—")
            return
        values = {
            "average": sum(self.history_totals) / count,
            "lowest": min(self.history_totals),
            "highest": max(self.history_totals),
        }
        for statistic, value in values.items():
            self.summary_values["Rainy days", statistic].set(f"{value:,.4f}" if statistic == "average" else f"{value:,}")
            self.summary_values["Observed rain %", statistic].set(f"{100 * value / self.history_days:.4f}%")

    def start(self):
        if self.running:
            return
        try:
            probability = float(self.probability.get()) / 100
            days = int(self.day_count.get().replace(",", ""))
            seed = int(self.seed.get()) if self.seed.get().strip() else None
            runs = int(self.run_count.get().replace(",", ""))
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("Chance must be between 0 and 100 percent.")
            if not 1 <= days <= 1000000:
                raise ValueError("Choose between 1 and 1,000,000 days.")
            if not 1 <= runs <= 100000:
                raise ValueError("Choose between 1 and 100,000 runs.")
        except ValueError as error:
            messagebox.showerror("Check your inputs", f"{error}\nUse a numeric chance, whole numbers of days and runs, and an optional integer seed.")
            return
        self.target, self.days = probability, days
        self.batch_runs, self.batch_finished = runs, 0
        self.batch_seed = seed
        self.batch_started = time.perf_counter()
        self.checkpoints = {n for n in (7, 100, 1000, 10000, 100000, 1000000, days) if n <= days}
        # Sample logarithmically for plotting; every trial still contributes to totals.
        self.plot_days = {1, days} | {round(math.exp(i * math.log(days) / 1200)) for i in range(1201)}
        self.prepare_run()
        self.running = True
        for control in self.range_controls:
            control.configure(state="disabled")
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.update_batch_status()
        self.step()

    def prepare_run(self):
        self.points, self.first_days = [], []
        self.table.delete(*self.table.get_children())
        # Distinct seeds give distinct streams while reproducing the whole batch.
        seed = None if self.batch_seed is None else self.batch_seed + self.batch_finished
        self.trials = simulate(self.target, self.days, seed)
        self.completed = self.total = 0
        self.run_logged = False

    @staticmethod
    def duration(seconds):
        seconds = max(0, math.ceil(seconds))
        hours, rest = divmod(seconds, 3600)
        minutes, seconds = divmod(rest, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

    def update_batch_status(self, stopped=False):
        done = self.batch_finished * self.days + (0 if self.run_logged else self.completed)
        total = self.batch_runs * self.days
        elapsed = time.perf_counter() - self.batch_started
        self.progress["value"] = 100 * done / total
        if stopped:
            timing = f"Stopped after {self.duration(elapsed)}; completed runs kept."
        elif self.batch_finished == self.batch_runs:
            timing = f"Complete in {self.duration(elapsed)}."
        elif elapsed < 0.25 or not done:
            timing = "Estimating time remaining..."
        else:
            timing = f"Estimated time remaining: {self.duration(elapsed * (total - done) / done)}"
        self.batch_status.set(f"Batch: {self.batch_finished:,} / {self.batch_runs:,} runs complete | {100 * done / total:.1f}% | {timing}")

    def add_row(self, day, total):
        self.table.insert("", "end", values=(f"{day:,}", f"{total:,}", f"{100 * total / day:.4f}%", f"{100 * self.target:g}%"))

    def step(self):
        self.pending_step = None
        if not self.running:
            return
        if self.run_logged:
            self.prepare_run()
        for _ in range(10000):
            trial = next(self.trials, None)
            if trial is None:
                self.finish()
                return
            day, rain, total = trial
            self.completed, self.total = day, total
            if day <= 28:
                self.first_days.append(rain)
            if day in self.plot_days:
                self.points.append((day, total / day))
            if day in self.checkpoints:
                self.add_row(day, total)
        self.update_status("Simulating")
        self.update_batch_status()
        self.draw()
        self.draw_days()
        self.pending_step = self.root.after(1, self.step)

    def update_status(self, prefix):
        self.status.set(f"{prefix}: {self.total:,} rainy days out of {self.completed:,} | Observed: {100 * self.total / self.completed:.4f}% | Chosen chance: {100 * self.target:g}%")

    def finish(self, stopped=False):
        if not self.running:
            return
        if self.pending_step is not None:
            self.root.after_cancel(self.pending_step)
            self.pending_step = None
        if self.completed and not self.run_logged:
            if self.points[-1][0] != self.completed:
                self.points.append((self.completed, self.total / self.completed))
            if self.completed not in self.checkpoints:
                self.add_row(self.completed, self.total)
            self.update_status("Stopped" if stopped else "Complete")
            if self.completed == self.days and self.days == self.history_days:
                row = self.history.insert("", "end", values=(
                    len(self.history.get_children()) + 1,
                    f"{self.days:,}", f"{self.total:,}",
                    f"{100 * self.total / self.completed:.4f}%", f"{100 * self.target:g}%",
                ))
                self.history.see(row)
                self.history_totals.append(self.total)
                self.update_summary()
                self.run_logged = True
                self.batch_finished += 1
        self.update_batch_status(stopped=stopped)
        self.draw()
        self.draw_days()
        if not stopped and self.batch_finished < self.batch_runs:
            self.pending_step = self.root.after(1, self.step)
            return
        self.running = False
        for control in self.range_controls:
            control.configure(state="normal")
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def stop(self):
        if self.running:
            self.finish(stopped=True)

    def draw_days(self):
        c = self.day_canvas
        c.delete("all")
        width = min(32, max(1, (c.winfo_width() - 4) / 28))
        for index, rain in enumerate(self.first_days):
            left = 2 + index * width
            c.create_rectangle(left, 2, left + width - 2, 32, fill="#2563eb" if rain else "#e2e8f0", outline="")
            c.create_text(left + (width - 2) / 2, 17, text=str(index + 1), fill="white" if rain else "#334155", font=("Segoe UI", 9))

    def draw(self):
        c = self.canvas
        c.delete("all")
        width, height = max(c.winfo_width(), 200), max(c.winfo_height(), 180)
        left, top, right, bottom = 58, 30, width - 24, height - 42
        def x(day):
            fraction = math.log(day) / math.log(max(2, self.days)) if self.log_scale.get() else (day - 1) / max(1, self.days - 1)
            return left + fraction * (right - left)
        def y(value):
            return bottom - value * (bottom - top)
        for percentage in (0, 20, 40, 60, 80, 100):
            yy = y(percentage / 100)
            c.create_line(left, yy, right, yy, fill="#dbe3ec")
            c.create_text(left - 8, yy, text=f"{percentage}%", anchor="e")
        ticks = {1, self.days}
        if self.log_scale.get():
            ticks.update(10 ** exponent for exponent in range(1, 7) if 10 ** exponent < self.days / 1.5)
        else:
            ticks.update(round(1 + i * (self.days - 1) / 4) for i in range(1, 4))
        for day in sorted(ticks):
            c.create_text(x(day), bottom + 14, text=f"{day:,}")
        c.create_text((left + right) / 2, height - 9, text="Number of days simulated")
        c.create_text(left, 12, anchor="w", text="Blue: cumulative rain proportion     Orange dashed: chosen probability", fill="#334155")
        c.create_line(left, y(self.target), right, y(self.target), fill="#ea580c", width=2, dash=(6, 4))
        if len(self.points) > 1:
            coordinates = [coordinate for day, value in self.points for coordinate in (x(day), y(value))]
            c.create_line(*coordinates, fill="#2563eb", width=2)
        elif self.points:
            day, value = self.points[0]
            xx, yy = x(day), y(value)
            c.create_oval(xx - 3, yy - 3, xx + 3, yy + 3, fill="#2563eb", outline="")


if __name__ == "__main__":
    root = tk.Tk()
    RainApp(root)
    root.mainloop()
