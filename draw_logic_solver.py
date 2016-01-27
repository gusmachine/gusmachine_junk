#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Draw logic solver using z3.

Usage:
$ cat input.txt
5 3
3
1 1
3
1
1 1
1 1
1 1
1

$ python draw_logic_solver.py < input.txt
_xxx_
x___x
_xxx_
"""

import sys

import z3


class DrawLogic(object):
    """A class to solve draw-logic puzzle, or nonogram.

    Typical usage is like the following.
    d = DrawLogic(horizontal_hints, vertical_hints)
    answer = d.solve()  # Gets the answer.
    d.print_answer()  # Just prints out the answer.

    Attributes:
      _horizontal_hints, _vertical_hints: A list of lists of int. input spec.
      _solved: Whether we already called _solve or not.
      _answer: The cached answer. Filled if _solved is true.
      _field: z3 array of booleans to hold the answer.
      _solver: Z3 solver to solve the puzzle.
    """

    def __init__(self, horizontal, vertical):
        """Constructs DrawLogic with puzzle specifications."""
        self._horizontal_hints = horizontal
        self._vertical_hints = vertical
        self._solved = False
        self._answer = None

    def solve(self):
        """Solves and returns the puzzle answer."""
        if not self._solved:
            self._solved = True
            self._answer = self._solve()
        return self._answer

    def _solve(self):
        self._field = z3.Array('f', z3.IntSort(), z3.BoolSort())
        self._solver = z3.Solver()
        width = len(self._vertical_hints)
        height = len(self._horizontal_hints)
        for i, c in enumerate(self._horizontal_hints):
            self._add_column(c, 1, i * width, width, 'h%d' % i)

        for i, c in enumerate(self._vertical_hints):
            self._add_column(c, width, i, height, 'v%d' % i)
        res = self._solver.check()
        if str(res) != 'sat':
            return None
        m = self._solver.model()
        f0 = [[False for i in xrange(height)] for j in xrange(width)]
        for j in xrange(height):
            for i in xrange(width):
                f0[i][j] = str(m.eval(self._field[j * width + i])) == 'True'
        return f0

    def _add_column(self, numbers, skip, base, size, prefix):
        """Converts numbers in one line into assertions for self._solver.

        Args:
          numbers: A list of constraint numbers in one
                   (either horizontal or vertical) line.
          skip, base, size: Specifies the line where the numbers come from.
          prefix: The name prefix of the new variables used in the assertion.

        Retunes: None.

        This provides set of assertions into self._solver.
        This is only expected to be called from the _solve() method."""

        if numbers == []:
            # No numbers. All the field in this line should be False.
            for i in xrange(size):
                self._solver.add(z3.Not(self._field[base + skip * i]))
            return

        # Variables for the position of the sequence in the line.
        # If numbers = [4,6], v[0] is the index of the 4-length sequence,
        # v[1] is the index for the 6-length sequence.
        v = [z3.Int('%s%d' % (prefix, i)) for i in range(len(numbers))]

        # Assertions for v[].
        # 0 <= v[0], v[0] + n[0] < v[1], ..., v[len-1] + n[len-1] <= size.
        self._solver.add(v[0] >= 0)
        for i in xrange(len(numbers) - 1):
            self._solver.add(v[i] + numbers[i] < v[i + 1])
        self._solver.add(v[-1] + numbers[-1] <= size)

        # Assertions for filled fields.
        for s, c in zip(v, numbers):
            for i in xrange(c):
                self._solver.add(self._field[base + (s + i) * skip])

        # Assertions for unfilled fields.
        fa = z3.Int('%s__1' % prefix)
        self._solver.add(z3.ForAll(
            [fa], z3.Or(fa < 0, v[0] <= fa,
                        z3.Not(self._field[base + skip * fa]))))
        for i in xrange(len(numbers) - 1):
            fa = z3.Int('%s_%d' % (prefix, i))
            self._solver.add(z3.ForAll(
                [fa],
                z3.Or(fa < v[i] + numbers[i], v[i + 1] <= fa,
                      z3.Not(self._field[base + skip * fa]))))
        fa = z3.Int('%s_%d' % (prefix, len(numbers)))
        self._solver.add(z3.ForAll(
            [fa], z3.Or(fa < v[-1] + numbers[-1], size <= fa,
                        z3.Not(self._field[base + skip * fa]))))

    def print_answer(self, fout):
        """Outputs the answer to fout."""
        q = self.solve()
        if q is None:
            fout.write('No solutions!\n')
            return
        for j in xrange(len(q[0])):
            for i in xrange(len(q)):
                if q[i][j]:
                    fout.write('x')
                else:
                    fout.write('_')
            fout.write('\n')


def read_input(fin):
    """Reads input from fin, parse and return as horizontal/vertical hints.

    Args:
      fin: input stream.

    Returns: A tuple of (horizontal_hints, vertical_hints).
      Each hint is a list of lists of positive integers holding the hints.
    """
    first = fin.readline().split()
    width = int(first[0])
    height = int(first[1])
    horizontal_hints = [
        [int(hint) for hint in fin.readline().split()]
        for _ in xrange(height)]
    vertical_hints = [
        [int(hint) for hint in fin.readline().split()]
        for _ in xrange(width)]
    return (horizontal_hints, vertical_hints)


def main():
    horizontal, vertical = read_input(sys.stdin)
    DrawLogic(horizontal, vertical).print_answer(sys.stdout)

if __name__ == '__main__':
    main()
