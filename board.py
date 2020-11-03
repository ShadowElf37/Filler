import random

WHITE = (255,) * 3
RED = (250, 10, 30)
GREEN = (50, 240, 10)
BLUE = (50, 170, 250)
PURPLE = (180, 20, 220)
YELLOW = (240, 240, 20)
BLACK = (40,) * 3

COLORS = [WHITE,  # 0
          RED,  # 1
          GREEN,  # 2
          BLUE,  # 3
          PURPLE,  # 4
          YELLOW,  # 5
          BLACK,  # 6
          ]


class Board:
    def __init__(self, x=8, y=8):
        self.grid = [([0]*x).copy() for i in range(y)]
        self.owned = self.grid.copy()
        self.owned_master = self.owned.copy()
        self.x_dim = x
        self.y_dim = y

    def get_pos(self, x, y):
        # Returns (x,y,c)
        try:
            return x, y, self.grid[x][y]
        except IndexError:
            return None

    def set_pos(self, x, y, c):
        self.grid[x][y] = c

    def set_owned(self, x, y):
        self.owned[x][y] = 1

    def all_owned(self):
        for y in self.owned:
            for x in y:
                if x == 0:
                    return False
        return True

    def get_adjacent(self, x, y):
        return (
            self.get_pos(x, y-1),
            self.get_pos(x-1, y),
            self.get_pos(x, y+1),
            self.get_pos(x+1, y),
        )

    def scramble(self):
        # Scrambles the board colors
        self.owned = self.owned_master
        for y in range(self.y_dim):
            for x in range(self.x_dim):
                palette = list(range(1, len(COLORS)))
                for block in self.get_adjacent(x,y):  # Removes colors of adjacent blocks so no same-colors are adjacent
                    if block is not None and block[2] in palette:
                        palette.remove(block[2])
                self.set_pos(x, y, random.choice(palette))  # picks color and sets it

    def pretty_print(self):
        print(*[str(row)+'\n' for row in self.grid], end='')

if __name__ == "__main__":
    t = Board(8, 8)
    t.pretty_print()
    t.scramble()
    t.pretty_print()