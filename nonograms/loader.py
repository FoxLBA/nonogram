"""
.jx format:
row_count
r1 [r2 [...]]
...
col_count
c1 [c2 [...]]
...
"""
def load_nonogram(file_name):
    sum_y = 0
    sum_x = 0
    with open(file_name, "rt") as inp:
        size_y = int(inp.readline())
        row_conditions = [0] * size_y  # type: list
        for i in range(size_y):
            row_conditions[i] = [int(j) for j in inp.readline().split()]
            sum_y += sum(row_conditions[i])
        size_x = int(inp.readline())
        col_conditions = [0] * size_x  # type: list
        for i in range(size_x):
            col_conditions[i] = [int(j) for j in inp.readline().split()]
            sum_x += sum(col_conditions[i])
        if sum_x != sum_y:
            raise ValueError("Invalid condition!")
    return row_conditions, col_conditions
