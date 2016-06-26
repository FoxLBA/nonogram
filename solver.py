import time
import threading
from line_tools import get_full, LineProcessor


class Solver:
    run_flag = None  # type: threading.Event
    clicking = False
    speed = 0
    current_line = 0

    def click(self)->bool:
        """internal slowdown and break"""
        flag = False
        if self.run_flag is not None:
            flag = self.run_flag.is_set()
        if self.clicking:
            time.sleep(self.speed)
        return flag

    _grid = []
    _solutions = 0
    _solve = None
    _cache = False
    _assumptions = []
    _updates = [0, 0]
    _line_processor = LineProcessor()
    _solve_line = _line_processor.solve_line

    def __init__(self, conditions: (list, list)):
        self._conditions = [conditions[1], conditions[0]]
        self._size = (len(conditions[0]), len(conditions[1]))
        self.reset()

    def reset(self):
        self._solutions = 0
        self._assumptions = []
        self._cache = False
        self._line_processor.reset()
        self._solve = self._first_solve
        size_y, size_x = self._size
        self._grid = [(0, 0)]*size_y
        self._updates = [0, 0]

    def __str__(self):
        st = ''
        for lf, le in self._grid.copy():
            for c in range(self._size[1]):
                lf >>= 1
                le >>= 1
                if lf & 1:
                    st += '#'
                elif le & 1:
                    st += '.'
                else:
                    st += '?'
            st += '\n'
        return st[:-1]

    def _get_line(self, num: int, is_horizontal: bool)->(int, int):
        if is_horizontal:
            return self._grid[num]
        else:
            lf, le = 0, 0
            p = 2 << num
            for gf, ge in self._grid[::-1]:
                if gf & p:
                    lf |= 1
                if ge & p:
                    le |= 1
                lf <<= 1
                le <<= 1
            return lf, le

    def _set_line(self, line: (int, int), num: int, is_horizontal: bool)->None:
        if is_horizontal:
            self._grid[num] = line
        else:
            lf, le = line
            p = 2 << num
            for i in range(self._size[0]):
                lf >>= 1
                le >>= 1
                gf, ge = self._grid[i]
                if lf & 1:
                    gf |= p
                if le & 1:
                    ge |= p
                self._grid[i] = (gf, ge)

    def _main_solve(self)->bool:
        b = False
        valid = False
        updates = self._updates
        while updates[True] or updates[False]:
            b = not b
            u = updates[b]
            i = 0
            while u:
                u >>= 1
                if u & 1:
                    self.current_line = (b, i)
                    if self.click():
                        return False
                    line = self._get_line(i, b)
                    line, dif, valid = self._solve_line(self._conditions[b][i], line,
                                                        self._size[b], cache=self._cache)
                    if not valid:
                        return False
                    updates[not b] |= dif
                    self._set_line(line, i, b)
                i += 1
            updates[b] = 0
        return valid

    def _first_solve(self)->bool:
        # These algorithm works only on empty lines
        updates = [0, 0]
        for b in [True, False]:
            ln = self._size[not b]
            for num in range(ln):
                self.current_line = (b, num)
                if self.click():
                    return False
                condition = self._conditions[b][num]  # type: list
                l = self._size[b]
                if not len(condition):
                    lf, le = self._get_line(num, b)
                    le = get_full(l) << 1
                    updates[not b] = le
                    self._set_line((lf, le), num, b)
                else:
                    sm = l - sum(condition) - len(condition) + 1
                    if max(condition) > sm:
                        lf, le = self._get_line(num, b)
                        i = 1
                        for c in condition:
                            if c > sm:
                                lf |= get_full(c - sm) << sm + i
                            i += c + 1
                        updates[not b] |= lf
                        self._set_line((lf, le), num, b)
        self._updates = updates
        self._solve = self._main_solve
        self._solve()
        return True

    def _level_up(self, pos: (int, int)) -> None:
        """Save current grid and assume filed cell on 'pos'."""
        self._assumptions.append((self._grid.copy(), pos))
        lf, le = self._grid[pos[0]]
        lf |= 2 << pos[1]
        self._grid[pos[0]] = (lf, le)
        self._updates[True] = 2 << pos[0]
        self._updates[False] = 2 << pos[1]

    def _level_down(self) -> bool:
        """Revert grid and place 'empty' on 'pos'"""
        if not self._assumptions:
            return False
        self._grid, pos = self._assumptions.pop()
        lf, le = self._grid[pos[0]]
        le |= 2 << pos[1]
        self._grid[pos[0]] = (lf, le)
        self._updates[True] = 2 << pos[0]
        self._updates[False] = 2 << pos[1]
        return True

    def _find_unknown_position1(self)-> (int, int) or None:
        # old variant
        i = 0
        for l in self._grid:
            lf, le = l
            lf |= le
            for j in range(self._size[True]):
                lf >>= 1
                if not lf & 1:
                    return i, j
            i += 1
        return None

    def _find_unknown_position(self)-> (int, int) or None:
        # searching on sides
        ym, xm = self._size
        x2 = ym - 1
        y2 = xm - 1
        y1, x1 = 0, 0
        while x1 < x2 and y1 < y2:
            for ln in [(x1, True), (x2, True), (y1, False), (y2, False)]:
                l = self._get_line(ln[0], ln[1])
                l = l[0] | l[1] | 1
                if ln[1]:
                    mx = xm
                else:
                    mx = ym
                if l == get_full(mx+1):  # нет свободных мест.
                    continue
                for i in range(mx):
                    l >>= 1
                    if not (l & 1):
                        if ln[1]:
                            return ln[0], i
                        else:
                            return i, ln[0]
            y1 += 1
            y2 -= 1
            x1 += 1
            x2 -= 1
        return None

    def step(self)->int:
        valid = self._solve()
        pos = self._find_unknown_position()
        if not valid or pos is None:
            if valid:
                self._solutions += 1
                return self._solutions
            if not self._level_down():
                return -1  # there's no more solutions
        else:  # leveling up
            if not self._cache:
                self._cache = True
            else:
                if self._line_processor.get_cache_size() > 25000:
                    self._line_processor.clear_line_cache()
            self._level_up(pos)
        return 0

    def find_next_solution(self)->int:
        while True:
            r = self.step()
            if r == -1 or r != 0:
                return r

    def get_level(self)->int:
        return len(self._assumptions) + 1

    def get_solutions(self)->int:
        return self._solutions

    def get_conditions(self)->dict:
        return self._conditions.copy()

    def get_grid(self)->list:
        return self._grid.copy()

    def get_size(self)->(int, int):
        return self._size

    def get_updates(self)->list:
        return self._updates.copy()

    def get_assumptions(self)->list:
        return self._assumptions.copy()
