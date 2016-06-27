import nonograms.loader as jx_loader
from solver import Solver

file_name = 'nonograms/test_set/winter.jx'  # default
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        file_name = sys.argv[1]

conditions = jx_loader.load_nonogram(file_name)
sl = Solver(conditions)
if -1 == sl.find_next_solution():
    print('Invalid conditions')
else:
    print(sl)
