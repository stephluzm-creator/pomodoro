import tkinter as tk
import threading
import time
import subprocess


class PomodoroTimer:
    WORK = 25 * 60
    SHORT_BREAK = 5 * 60
    LONG_BREAK = 15 * 60
    CYCLE_LENGTH = 4

    PALETTE = {
        'work':        '#E05252',
        'short_break': '#52B788',
        'long_break':  '#5271E0',
        'bg':          '#1E1E2E',
        'surface':     '#2A2A3E',
        'text':        '#FFFFFF',
        'muted':       '#888899',
        'ring_bg':     '#3A3A4E',
    }

    MODE_LABEL = {
        'work':        'POMODORO',
        'short_break': 'SHORT BREAK',
        'long_break':  'LONG BREAK',
    }

    def __init__(self, root):
        self.root = root
        self.root.title('Pomodoro')
        self.root.resizable(False, False)
        self.root.configure(bg=self.PALETTE['bg'])

        self.mode = 'work'
        self.completed = 0
        self.running = False
        self.time_left = self.WORK

        self._build_ui()
        self._refresh()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        self.mode_lbl = tk.Label(
            self.root, text='', font=('Helvetica', 13, 'bold'),
            bg=self.PALETTE['bg'], fg=self.PALETTE['work'],
        )
        self.mode_lbl.pack(pady=(28, 4))

        self.canvas = tk.Canvas(
            self.root, width=260, height=260,
            bg=self.PALETTE['bg'], highlightthickness=0,
        )
        self.canvas.pack()

        dot_frame = tk.Frame(self.root, bg=self.PALETTE['bg'])
        dot_frame.pack(pady=12)
        self.dots = []
        for _ in range(self.CYCLE_LENGTH):
            lbl = tk.Label(dot_frame, text='●', font=('Helvetica', 14),
                           bg=self.PALETTE['bg'], fg=self.PALETTE['muted'])
            lbl.pack(side=tk.LEFT, padx=5)
            self.dots.append(lbl)

        btn_frame = tk.Frame(self.root, bg=self.PALETTE['bg'])
        btn_frame.pack(pady=16)
        kw = dict(font=('Helvetica', 12, 'bold'), relief='flat', bd=0,
                  bg=self.PALETTE['surface'], fg=self.PALETTE['text'],
                  padx=18, pady=9, cursor='hand2', width=7)
        self.start_btn = tk.Button(btn_frame, text='START',
                                   command=self.toggle, **kw)
        self.start_btn.grid(row=0, column=0, padx=6)
        tk.Button(btn_frame, text='RESET', command=self.reset,
                  **kw).grid(row=0, column=1, padx=6)
        tk.Button(btn_frame, text='SKIP',  command=self.skip,
                  **kw).grid(row=0, column=2, padx=6)

        self.stats_lbl = tk.Label(
            self.root, text='', font=('Helvetica', 11),
            bg=self.PALETTE['bg'], fg=self.PALETTE['muted'],
        )
        self.stats_lbl.pack(pady=(2, 24))

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        self.canvas.delete('all')
        cx = cy = 130
        r = 110
        color = self.PALETTE[self.mode]

        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=self.PALETTE['ring_bg'], width=12, fill=self.PALETTE['bg'],
        )

        frac = self.time_left / self._total()
        extent = frac * 359.9
        if extent > 0:
            self.canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=90, extent=extent,
                outline=color, width=12, style='arc',
            )

        m, s = divmod(self.time_left, 60)
        self.canvas.create_text(cx, cy - 12, text=f'{m:02d}:{s:02d}',
                                font=('Helvetica', 46, 'bold'),
                                fill=self.PALETTE['text'])
        sub = 'FOCUS' if self.mode == 'work' else 'BREAK'
        self.canvas.create_text(cx, cy + 36, text=sub,
                                font=('Helvetica', 11),
                                fill=self.PALETTE['muted'])

    def _refresh(self):
        color = self.PALETTE[self.mode]
        self.mode_lbl.config(text=self.MODE_LABEL[self.mode], fg=color)
        self._draw()

        in_cycle = self.completed % self.CYCLE_LENGTH
        for i, dot in enumerate(self.dots):
            dot.config(fg=color if i < in_cycle else self.PALETTE['muted'])

        n = self.completed
        self.stats_lbl.config(
            text=f"Completed: {n} pomodoro{'s' if n != 1 else ''}")

        m, s = divmod(self.time_left, 60)
        self.root.title(f'Pomodoro — {m:02d}:{s:02d}')

    # ── Timer logic ───────────────────────────────────────────────────────────

    def _total(self):
        return {'work': self.WORK,
                'short_break': self.SHORT_BREAK,
                'long_break': self.LONG_BREAK}[self.mode]

    def toggle(self):
        if self.running:
            self.running = False
            self.start_btn.config(text='START')
        else:
            self.running = True
            self.start_btn.config(text='PAUSE')
            threading.Thread(target=self._tick, daemon=True).start()

    def _tick(self):
        while self.running and self.time_left > 0:
            time.sleep(1)
            if self.running:
                self.time_left -= 1
                self.root.after(0, self._refresh)
        if self.time_left == 0 and self.running:
            self.root.after(0, self._finish)

    def _finish(self):
        self.running = False
        self.start_btn.config(text='START')
        subprocess.Popen(['afplay', '/System/Library/Sounds/Glass.aiff'])
        if self.mode == 'work':
            self.completed += 1
            if self.completed % self.CYCLE_LENGTH == 0:
                self.mode = 'long_break'
                self.time_left = self.LONG_BREAK
            else:
                self.mode = 'short_break'
                self.time_left = self.SHORT_BREAK
        else:
            self.mode = 'work'
            self.time_left = self.WORK
        self._refresh()

    def reset(self):
        self.running = False
        self.start_btn.config(text='START')
        self.time_left = self._total()
        self._refresh()

    def skip(self):
        self.running = False
        self.start_btn.config(text='START')
        if self.mode == 'work':
            self.mode = 'short_break'
            self.time_left = self.SHORT_BREAK
        else:
            self.mode = 'work'
            self.time_left = self.WORK
        self._refresh()


if __name__ == '__main__':
    root = tk.Tk()
    PomodoroTimer(root)
    root.mainloop()
