class Player:
    def __init__(self, startx, starty, board):
        self.board = board
        self.territory = [(startx, starty),]
        self.edges = [(startx, starty),]
        self._color = self.board.get_pos(*self.territory[0])
        self.name = ''

    def annex(self, x, y):
        self.territory.append((x, y))

    def get_score(self):
        return len(self.territory)

    def color(self, c):
        self._color = c

    def calculate_edges(self):
        self.edges = [block for block in self.territory if any(self.board.get_adjacent(*block))]
