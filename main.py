from board import *
from player import *
from graphics import *
import pygame
from time import sleep, time
import random
import socket
from sys import exit
from threading import Thread
from tkinter import *
from asynclib import Client

host = '192.168.1.226'
port = 37378
lobby = '1000'
name = 'Yovel'
submitted = False

# BOOTSTRAP SOME TKINTER (only used for loading screen; rest is graphics.Engine())
root = Tk()
root.geometry('200x300')
root.title('Filler')

host_label = Label(text="Host")
host_entry = Entry()
port_label = Label(text="Port")
port_entry = Entry()
lobby_label = Label(text="Lobby #")
lobby_entry = Entry()
name_label = Label(text="Name")
name_entry = Entry()

# DEFAULTS
host_entry.insert(END, "73.166.38.74")
port_entry.insert(END, "80")
lobby_entry.insert(END, "")
name_entry.insert(END, "")

def submit_cmd():
    global host, port, lobby, name, submitted
    host = host_entry.get()
    port = int(port_entry.get())
    lobby = lobby_entry.get()
    name = name_entry.get()
    if host and port and name and lobby.isnumeric():
        submitted = True

submit_button = Button(text="Connect", command=submit_cmd)

[item.pack() for item in (host_label, host_entry, port_label, port_entry, lobby_label, lobby_entry, name_label, name_entry, submit_button)]

while not submitted:
    try:
        root.update()
        root.update_idletasks()
        sleep(0.025)
    except TclError:
        exit()

root.destroy()

client = Client(host, port)

width = 500  #+300
height = 700
grid_x = 100
grid_y = 50
tilesize = 40
BIGCOLOR = (25, 50, 250)

app = Engine(width, height, caption="Filler")

board = Board()
board.scramble()

waiting = True
player_quit = False
victory = False
wait_id = 'players'

mouse_down = 0
icon = Surface((32, 32))
icon.blit(image.load_basic('favicon.bmp').convert(), (0,0))
pygame.display.set_icon(icon)


def handle_msg(msg):
    global mouse_down, players, waiting, turn, wait_id, player_quit, victory

    msg = msg.split(' ')
    print('Got a message:', msg)
    """
    if msg[0] == 'fcolor':
        print('FCOLOR')
        c = msg[1]
        id = msg[2]
        if msg[2] == wait_id:
            waiting = False
        print('! ID:', id)
        print('! Play:', c)
        take_turn(int(id), int(c))
        print('A player won.')
        victory = True
        waiting = False
    """
    if msg[0] == 'color':
        print('COLOR')
        c = msg[1]
        id = msg[2]
        if msg[2] == wait_id:
            waiting = False
        print('! ID:', id)
        print('! Play:', c)
        take_turn(int(id), int(c))
        print('turn taken')
        client.write('y')

    elif msg[0] == 'wait':
        print('WAIT')
        wait_id = msg[1]
        waiting = True

    elif msg[0] == 'go':
        print('I can go now.')
        waiting = False

    elif msg[0] == 'quit' or msg[0] == '':
        print('A player quit and the game should be exited.')
        player_quit = True
        waiting = False

def draw(do_tests=True):
    global mouse_down, players, waiting, turn, wait_id, player_quit, victory

    # Chat divider
    # app.color(0, 0, 0)
    # dy = 30
    # app.line(525, dy, 525, height-dy, width=1)

    # Chat box
    # app.color(100, 100, 100)
    # app.rect(550, 575, 225, 40)
    # app.fontsize(20)
    # app.text(585, 555, "Chat")
    # app.color(255, 255, 255)
    # app.rect(551, 576, 223, 38)

    # Board
    for y in range(board.y_dim):
        for x in range(board.x_dim):
            gp = board.get_pos(x, y)[2]
            app.color(*COLORS[int(gp)])
            app.rect(grid_x + x * tilesize, grid_y + y * tilesize, tilesize, tilesize)

    # Palette background
    app.color(200, 200, 200)
    app.rect(60, 400, 400, 80)

    # Generate palette
    for color in range(1, len(COLORS)):
        app.color(*COLORS[color])
        if color in [player._color for player in players]:
            app.rect(35 + color * 60, 425, tilesize-10, tilesize-10)
        else:
            app.rect(30 + color * 60, 420, tilesize, tilesize)

    # Scores
    app.fontsize(36)
    app.text(100, 600, players[0].name + ' - %s' % players[0].get_score())
    app.text(400, 600, players[1].name + ' - %s' % players[1].get_score())

    # Check server comms
    if do_tests and not (victory or player_quit):
        m = client.read(wait=False)
        if m is not None:
            print(client.rbuffer)
            handle_msg(m)

    # Check for clicks on palette
    if app.getmouse()[0] and not mouse_down and not (waiting or victory or player_quit) and do_tests:
        mouse_down = 1
        coords = app.getmousexy()
        cx = [50 + color * 60 for color in range(1, len(COLORS))]
        try:
            box = [in_box(coords[0], coords[1], x-tilesize/2, 420, x+tilesize/2, 460) for x in cx].index(True) + 1
        except ValueError:
            box = None

        # Can't select those colors
        if box and box not in [player._color for player in players]:
            client.write('color '+str(box)+' '+str(get_turn()))
            take_turn(get_turn(), box)
            print('turn taken')
            client.write('y')

    elif not app.getmouse()[0]:
        mouse_down = 0

    if waiting and not (victory or player_quit):
        app.fontsize(48)
        app.color(*BIGCOLOR)
        app.text(250, 250, 'Waiting for %s...' % wait_id)

    elif victory:
        app.fontsize(48)
        app.color(250, 200, 20)
        app.text(250, 250, ((max(players, key=lambda p: p.get_score()).name if players[0].get_score() != players[1].get_score() else 'No one ')+' has won.'))

    elif player_quit:
        app.fontsize(48)
        app.color(*BIGCOLOR)
        app.text(250, 250, 'Another player quit.')

    if sum([p.get_score() for p in players]) == board.x_dim*board.y_dim and not victory:
        victory = True
        client.write('end')


def get_turn():
    return turn % len(players)
turn = 0

players = list()

for p in players:
    p.color(board.get_pos(*p.territory[0])[2])

my_turn = False

def take_turn(pix, color):
    global turn
    print('$', turn)

    turn += 1
    player = players[pix]

    for x,y in player.edges:
        for block in board.get_adjacent(x, y):
            if block and block[2] == color and board.x_dim > block[0] > -1 and board.y_dim > block[1] > -1 and tuple(block[:2]) not in player.territory:
                player.annex(*block[:2])

    player.color(color)
    for x,y in player.territory:
        board.set_pos(x, y, color)
    player.calculate_edges()


client.connect()
client.initiate_iothreads()
client.write('join.'+lobby+','+name+'.')
b = client.read(wait=True)
print(b)
b_init = [list(map(int, row.split(','))) for row in b.split('|')]
board.grid = b_init

players.append(Player(0, board.y_dim-1, board))
players.append(Player(board.x_dim-1, 0, board))
# players.append(Player(0, 0, board))
# players.append(Player(7, 7, board))

draw(False)
app.update()

# import atexit

def quitf():
    global client
    client.write('quit')
    while client.wbuffer and client.is_open():
        sleep(0.01)
    client.close()
    print('Application closed manually.')
app.set_quit(quitf)
# atexit.register(quitf)

print('WAITING')
while len(client.rbuffer) == 0:
    for e in event.get():
        if e.type == QUIT:
            app.running = False
            app.quit_func()
            exit(0)
    # print('doot')
    app.clock.tick(app.framerate)
    app.update()

msg = client.read()
print('GOT MSG')

# No one can communicate in-game after the first game.

if msg[:4] == 'name':
    print('PREPARE')
    names = msg.split(' ')
    print(names)
    i = 1
    for player in players:
        player.name = names[i]
        i += 1
    print('NAMES')
    client.write('y')

app.setloop(draw)
app.mainloop()

exit(0)
