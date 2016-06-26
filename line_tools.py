"""
Params for line solvers: (condition, line, len, cache) -> line, dif, is_valid
Input:
condition - blocks length on current line
line - binary representation of a line ('lf' - sure filed, 'le' - sure empty)
len - line length
cache - boolean, use caching or not

Output:
line - result
dif - changed cells
is_valid - 'False' when conflict with condition
"""

fulls = [0, 1]


def get_full(ln: int)->int:
    """return int with 'ln' bits set
       >>>get_full(5) == pow(2, 5)-1
       True"""
    global fulls
    if ln < len(fulls):
        return fulls[ln]
    full = fulls[-1]
    for _ in range(ln - len(fulls) + 1):
        full |= full << 1
        fulls.append(full)
    return full


def _line_processor(program: list, lf: int, le: int, l: int, end: int) -> (int, int, int, bool, bool):
    """Used in LineProcessor class"""
    full = get_full(l + 1)
    fill, empty = 0, 0
    count = 0
    s = program[0]
    s[0] = l - s[5]
    step = 0
    # program step: 0-index, 1-end_index, 2-result, 3-pf, 4-pe, 5-condition
    while step >= 0:
        while (s[0] >= s[1]) and ((s[3] << s[0] & le) or (s[4] << s[0] & lf)):  # applying a template for block.
            if lf & (2 << s[0] + s[5]):
                step -= 1  # There is no point to check further.
                s = program[step]
            else:
                s[0] -= 1  # pattern does not match. next step.
        if s[0] < s[1]:
            step -= 1  # end index. step back
            s = program[step]
        else:
            c = (s[3] << s[0]) | s[2]  # result
            s[0] -= 1
            if step == end:  # line is ready
                if not (c ^ (c | lf)):  # result line can contain unnecessary blocks
                    fill |= c
                    empty |= c ^ full
                count += 1
                if count > 250000:  # too many variants
                    return lf, le, 0, True, True
            else:
                i = s[0]
                step += 1
                s = program[step]
                s[2] = c  # save result
                s[0] = i - s[5]

    # Checking results
    cache = count > 1000
    if not fill:
        return 0, 0, 0, False, cache  # invalid line
    empty = (empty | 1) ^ 1  # clear first bit
    c = fill ^ empty
    dif = c ^ (lf | le)
    return fill & c, empty & c, dif, True, cache


class LineProcessor:
    _program_cache = {}
    _line_cache = {}
    _cache_stat = [0, 0, 0]

    def solve_line(self, condition: list, line: (int, int), l, cache=False) -> ((int, int), int, bool):
        lf, le = line
        ch = 0
        if cache:
            ch = (l, lf, le, str(condition))
            self._cache_stat[0] += 1
            if ch in self._line_cache:
                self._cache_stat[1] += 1
                return self._line_cache[ch]
        # Check all possible variants
        lf, le, dif, valid, cache_needed = _line_processor(self._get_program(condition),
                                                           lf, le, l, len(condition) - 1)

        if cache and cache_needed:
            self._line_cache[ch] = ((lf, le), dif, valid)
            self._cache_stat[2] = len(self._line_cache)
        return (lf, le), dif, valid

    def _get_program(self, line_condition: list):
        str_condition = str(line_condition)
        if str_condition in self._program_cache:
            program = self._program_cache[str_condition]
        else:
            end = len(line_condition) - 1
            program = [[0] * 6 for _ in range(end + 2)]
            # program step: 0-index, 1-end_index, 2-result, 3-pf, 4-pe, 5-condition
            for i in range(end, -1, -1):
                c = line_condition[~i]
                s = program[i]
                program[i - 1][1] = s[1] + c + 1
                s[3] = get_full(c) << 1
                s[4] = s[3] + 3
                s[5] = c
            self._program_cache[str_condition] = program
        return program

    def reset(self):
        self._program_cache.clear()
        self._line_cache.clear()

    def clear_line_cache(self):
        self._line_cache.clear()

    def get_cache_size(self):
        return len(self._line_cache)

    def get_cache_statistic(self):
        return self._cache_stat.copy()


def generate_valid_permutation(condition: list, lf: int, le: int, lim: int, step=0, index=0):
    if step == len(condition):
        yield 0
        return
    if lim > 0:  # negative values used inside recursion.
        lim = sum(condition) + len(condition) - 2 - lim
    c = condition[step]
    f = get_full(c)
    for i in range(index, -lim):
        # To the left of the block must be blank cell.
        if lf & 1:
            break
        lf >>= 1
        le >>= 1
        # Inside the block can not be blank cell.
        if f & le:
            continue
        # On the right is also must be blank cell.
        if (1 << c) & lf:  # нужен 1 конкретный бит в lf
            continue
        # In the last step from the right must be completely empty.
        if (step == len(condition) - 1) and lf >> c+1:
            continue

        for l in generate_valid_permutation(condition, lf >> c, le >> c, lim-c-1, step+1, i+c+1):
            l <<= c+1
            l |= f
            l <<= i - index
            yield l


def solve_line1(condition: list, line: (int, int), l: int, cache=False)->((int, int), int, bool):
    lf, le = line
    fill, empty = 0, 0
    search_result = True
    '''if cache is not None:
        c = (l, lf, le, str(condition))
        if c in cache:
            fill, empty = cache[c]
            search_result = False'''

    full = get_full(l)
    if search_result:
        count = 0
        for ln in generate_valid_permutation(condition, lf, le, l):
            count += 1
            if count > 100000:
                return (lf, le), 0, True
            fill |= ln
            empty |= ln ^ full
            '''if cache is not None and count > 1000:
                    cache[c] = (fill, empty)'''

    if not fill:
        return (0, 0), 0, False  # invalid line
    fill <<= 1
    empty <<= 1
    c = fill ^ empty
    dif = c ^ (lf | le)
    return (fill & c, empty & c), dif, True
