from board import *
import socket
import threading
import random
from time import sleep, time
from asynclib import Server

host = '192.168.1.83' # 192.168.1.226 192.168.1.83 10.1.3.159 192.168.1.225
port = 37379
s = Server(host, port, max_conns=30)

games = {}

class Connection:
    def __init__(self, c, a):
        self.c = c
        self.addr = a
        self.name = 'user'
        self.id = 0

    def send(self, msg):
        try:
            self.c.send(msg)
        except:  # Someone quit
            return "quit"

    def recv(self, buf=1024):
        try:
            return self.c.recv(buf)
        except:  # Someone quit
            return b"quit"

    def close(self):
        self.c.close()

    def is_open(self):
        return self.c.fileno() != -1

class GameInstance:
    def __init__(self, id):
        self.board = Board()
        self.base_board = None
        self.board.scramble()
        self.end = False
        self.quit = False
        self.players = []
        self.chat = []
        self.log = []
        self.id = id
        self.turn = 0
        self.running = True
        self.mainthread = threading.Thread(target=self.mainloop, daemon=True)
        self.mainthread.start()

    def add_player(self, pobj):
        pobj.id = len(self.players)
        self.players.append(pobj)

    def sendall(self, msg):
        for p in self.players:
            s.write(p, msg)

    def mainloop(self):
        print('Game waiting...')
        while len(self.players) < 2:
            # print(self.players)
            m = s.read(targets=self.players, wait=False, delete=False)
            if m[0] in self.players and m[1] == 'quit':
                self.quit = True
                self.running = False
                break
            sleep(0.01)
        if self.running:
            print('! All players ready.')
            print('! Game started.')
            self.sendall('name '+' '.join([p.name for p in self.players]))
            ready_players = set()
            while ready_players != set(self.players):
                for p in self.players:
                    if s.read([p])[1] == 'y':
                        ready_players.add(p)
                sleep(0.01)
            print('Game started.')
        while self.running:
            # print('$', self.turn)



            waiting = self.players[self.turn % len(self.players)]
            ptemp = self.players.copy()
            ptemp.remove(waiting)

            # Tell everyone else to wait for the current player
            for not_waiting in ptemp:
                s.write(not_waiting, 'wait ' + waiting.name)
            s.write(waiting, 'go')
            print('Told players to wait.')

            # Get color changes
            # s.wait_for(waiting)
            moves = None, None
            while moves[0] != waiting:
                sleep(0.01)
                moves = s.read(targets=self.players, wait=False)
                if moves[0] is None:
                    continue
                print(moves)
                if moves[1] and moves[1].strip().split(' ')[0] == 'quit':
                    print(moves)
                    print(self.players)
                    self.quit = True
                    break
                elif moves[1] and moves[1].strip().split(' ')[0] == 'end':
                    self.end = True

            moves = moves[1]  # color Color# P#
            print('Player moved.')

            self.log.append(moves)
            if self.end:
                #for not_waiting in ptemp:
                    #s.write(not_waiting, 'f'+moves)
                self.running = False
                print('Game completed.')
            elif self.quit:
                self.sendall('quit')
                self.running = False
                print('Game terminated')

            if self.running:
                for not_waiting in ptemp:
                    s.write(not_waiting, moves)

            ready_players = set()
            while ready_players != set(self.players):
                for p in self.players:
                    if s.read([p])[1] == 'y':
                        ready_players.add(p)
                sleep(0.01)

            self.turn += 1

        print('Game died.')
        for p in self.players:
            p.close()


def set_up_player(preliminary):
    global base_board
    print(games)
    print('Putting player in game...')
    s.gen_rthread(preliminary)
    s.run_uninitiated_rthreads()
    r = s.read([preliminary], wait=True)[1]  # join(1234,Name)
    # print(r)
    if r[:4] == 'join':
        gid, usr = r[4:].strip('.').split(',')
        preliminary.name = usr
        game = games.get(gid)
        if game is None:
            game = games[gid] = GameInstance(gid)
        if len(game.players) == 2:
            preliminary.close()
            return
        game.add_player(preliminary)
        print(game.players)

        if not game.base_board:
            g = game.board.grid
            for row in range(len(g)):
                # print(g[row])
                g[row] = ','.join(map(str, g[row]))
            new = game.base_board = '|'.join(g)
            game.log.append(new)
            print(new)
            s.send(preliminary, new)
            print('Created game.')
            return
        s.send(preliminary, game.base_board)
        print('Joined game.')


# On the second round of a lobby, _waiting_ can't quit
#


s.conn_object = Connection
s.open()
s.on_accept = lambda co: threading.Thread(target=set_up_player, args=(co,), daemon=True).start()
s.initiate_wthread()
print('Server open on %s:%s...' % (host, port))

try:
    while True:
        gv = list(games.values())
        for game in gv:  # Clean up finished games
            if game is not None and not game.running:
                f = open('logs/'+str(time())+'.log', 'w')
                f.write('_'.join([p.name for p in game.players])+'\n'+'\n'.join(game.log))
                f.close()
                games[game.id] = None
                print('Killed a game.')
        sleep(0.01)
except KeyboardInterrupt:
    exit(0)