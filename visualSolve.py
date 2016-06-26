import solver
import nonograms.loader as jx_loader
import threading
import tkinter as tk
from time import sleep
from math import floor

# ------------------------------ #
file_name = 'nonograms/test_set/winter.jx'  # default
solver_sleep_time = 0.02  # sleep time between lines solving
# ------------------------------ #
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
# ------------------------------ #


class App(tk.Frame):
    _scale = 1
    is_final = False

    def __init__(self, master, sl: solver.Solver):
        tk.Frame.__init__(self, master, bd=5, relief=tk.SUNKEN)
        self._solver = sl
        self.pack(fill="both", expand=True)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        canvas.bind('<Configure>', self._canvas_resize)
        self._canvas = canvas
        self.solution = cross.get_grid()
        self._calc_offsets()

    def _calc_offsets(self):
        """Calculate size of blank space on top left corner"""
        c = self._solver.get_conditions()
        my = 0
        for i in c[True]:
            my = max(my, len(i))
        mx = 0
        for i in c[False]:
            mx = max(mx, len(i))
        self._offsets = (my, mx)

    def _draw_conditions(self):
        """Draw grid and numbers.
           Also calculate scale."""
        cv = self._canvas
        offsets = self._offsets
        cv.delete('all')
        w, h = cv.winfo_width(), cv.winfo_height()
        conditions = self._solver.get_conditions()
        x = len(conditions[False]) + offsets[0]
        y = len(conditions[True]) + offsets[1]
        scale = floor(min(w / x, h / y))
        self._scale = scale
        for i in range(offsets[0], x + 1):  # Горизонтальные линии
            cv.create_line(i * scale, 0,
                           i * scale, scale * y,
                           tags='condition')
        for i in range(offsets[1], y + 1):  # вертикальные линии
            cv.create_line(0, i * scale,
                           scale * x, i * scale,
                           tags='condition')
        cn = conditions[True]
        for i in range(len(cn)):
            l = len(cn[i])
            o = offsets[0] - l
            for k in range(l):
                cv.create_text((o + k + 0.5) * scale, (offsets[1] + i + 0.5) * scale,
                               text=str(cn[i][k]), tags='condition')
        cn = conditions[False]
        for i in range(len(cn)):
            l = len(cn[i])
            o = offsets[1] - l
            for k in range(l):
                cv.create_text((offsets[0] + i + 0.5) * scale, (o + k + 0.5) * scale,
                               text=str(cn[i][k]), tags='condition')

    def _draw_cell(self, x: int, y: int, cell: str):
        scale = self._scale
        if cell == '#':  # filed
            self._canvas.create_rectangle(x, y, x + scale, y + scale, tags="grid", fill='black')
        elif cell == '.':  # cross
            self._canvas.create_line(x, y, x + scale, y + scale, tags="grid", fill='black')
            self._canvas.create_line(x, y + scale, x + scale, y, tags="grid", fill='black')

    def _draw_current_line(self, line: (bool, int) or int, color: str):
        """Draw small triangle on a side"""
        scale = self._scale
        if line == 0:
            return
        if line[0]:  # Left side
            y = (self._offsets[1] + line[1]) * scale
            self._canvas.create_polygon(0, y,
                                        scale // 2, y + scale // 2,
                                        0, y + scale,
                                        fill=color, tags='grid')
        else:  # Top side
            x = (self._offsets[0] + line[1]) * scale
            self._canvas.create_polygon(x, 0,
                                        x + scale // 2, scale // 2,
                                        x + scale, 0,
                                        fill=color, tags='grid')

    def draw_current_state(self, grid=None):
        cv = self._canvas
        offsets = self._offsets
        scale = self._scale
        sl = self._solver
        is_final = self.is_final
        cv.delete('grid')
        self.draw_solution()
        if not is_final:
            b = False
            for u in sl.get_updates():
                i = 0
                while u:
                    u >>= 1
                    if u & 1:
                        self._draw_current_line((b, i), 'gray')
                    i += 1
                b = not b
                self._draw_current_line(sl.current_line, "red")
            cv.create_text(0, cv.winfo_height() - 14, tags="grid", anchor=tk.NW,
                           text='lv={}'.format(sl.get_level()))
        else:
            global solution
            grid = solution

        if grid is None:
            grid = sl.get_grid()
        size = sl.get_size()
        for i in range(size[False]):
            y = (offsets[1] + i) * scale
            lf, le = grid[i]
            for j in range(size[True]):
                lf >>= 1
                le >>= 1
                if lf & 1:
                    cell = '#'
                elif le & 1:
                    cell = '.'
                else:
                    cell = '?'
                x = (offsets[0] + j) * scale
                self._draw_cell(x, y, cell)
        i = 0
        for _, pos in sl.get_assumptions():
            y, x = pos
            i += 1
            cv.create_text((x + offsets[0] + 0.5) * scale,
                           (y + offsets[1] + 0.5) * scale,
                           tags='grid', text=str(i),
                           fill='red')

    def _canvas_resize(self, _):
        self._draw_conditions()
        self.draw_current_state()

    def draw_solution(self):
        """Draw miniature on top left corner"""
        canvas = self._canvas
        sl = self._solver
        global solution

        w, h = self._offsets
        h *= self._scale
        w *= self._scale
        y, x = sl.get_size()
        mini_scale = min(w / x, h / y)
        dy = h - mini_scale * y
        dx = w - mini_scale * x
        if sl.get_solutions() == 0:
            solution = sl.get_grid()
        canvas.delete('solution')
        for i in range(y):
            lf, le = solution[i]
            for j in range(x):
                lf >>= 1
                if lf & 1:
                    canvas.create_rectangle(dx + j * mini_scale, dy + i * mini_scale,
                                            dx + (j + 1) * mini_scale, dy + (i + 1) * mini_scale,
                                            tags='solution', fill='black')


def solve(sl: solver.Solver):
    """These will run on separate thread"""
    global solution
    s = 0
    while s != -1:
        s = sl.find_next_solution()
        if s != -1:
            print('Solution#', s)
            solution = sl.get_grid()
    print('end')

cross = solver.Solver(jx_loader.load_nonogram(file_name))  # type: solver.Solver
run_flag = threading.Event()
cross.run_flag = run_flag  # internal break
cross.speed = solver_sleep_time
cross.clicking = True  # Activate slowdown

solution = cross.get_grid()  # Init miniature

root = tk.Tk()
root.title("Nonogram solver")
root.geometry('500x500')
app = App(root, cross)

t = threading.Thread(target=solve, args=(cross,))
t.start()

try:
    while 1:
        app.draw_current_state()
        root.update()
        if not t.is_alive():
            app.is_final = True
            app.draw_current_state()
            root.mainloop()
            break
        sleep(0.04)  # 0.04 = 25 fps
except tk.TclError:
    run_flag.set()
    pass  # to avoid errors when the window is closed
