from pygame import *
from pygame.locals import *
from math import floor
from sys import exit

class Engine:
    def __init__(self, width=500, height=500, caption="Application", clr=True, bg=(255, 255, 255), flags=SRCALPHA):
        init()
        self.width = width
        self.height = height
        self.clear = clr # whether to clear the screen every frame
        self.screen = display.set_mode((width, height), flags)
        self.bg = Color(*bg)
        self.backg()
        self.clock = time.Clock()
        self.framerate = 40
        display.set_caption(caption)
        self.drawloop = lambda *x: 0
        self.onkeydown = lambda: 0
        self.quit_func = lambda: 0
        self.dlargs = ()
        self.col = (0, 0, 0)
        self.keys = []
        self.font = font.Font(font.get_default_font(), 12)
        self.queue = []
        self.running = False
        self.update()
    def mainloop(self):
        self.running = True
        while self.running:
            self.clock.tick(self.framerate)
            for f in self.queue:
                if f[1] == 0 or self.clock.get_ticks() >= f[2] + f[1]:
                    f[0](*f[3])
            for e in event.get():
                if e.type == QUIT:
                    self.running = False
                    self.quit_func()
                    quit()
                    exit(0)
                if e.type == KEYDOWN:
                    self.onkeydown()
            if self.clear:
                self.backg()
                pass
            self.mouseX, self.mouseY = mouse.get_pos()
            self.drawloop(*self.dlargs)
            self.update()
    def set_quit(self, f):
        self.quit_func = f
    def rect(self, x, y, w, h):
        draw.rect(self.screen, self.col, [x, y, w, h], 0)
    def line(self, x1, y1, x2, y2, width=1):
        draw.line(self.screen, self.col, (x1, y1), (x2, y2), width)
    def poly(self, verts):
        draw.polygon(self.screen, self.col, verts)
    def getmouse(self):
        return mouse.get_pressed()
    def getmousexy(self):
        return mouse.get_pos()
    def setpos(self, x, y):
        mouse.set_pos(x, y)
    def ellipse(self, x, y, w, h):
        draw.ellipse(self.screen, self.col, (x-w/2, y-w/2, w, h))
    def color(self, *col):
        self.col = Color(*[floor(i) for i in col])
    def setloop(self, func):
        self.drawloop = func
    def setonkey(self, func):
        self.onkeydown = func
    def get_key(self, kv):
        return key.get_pressed()[eval("K_"+kv)]
    def backg(self, col=None):
        if not col:
            self.screen.fill(self.bg)
        else:
            self.screen.fill(Color(*col))
    def text(self, x, y, strn, center=True):
        w, h = self.font.size(strn)
        d = 2 if center else -1
        self.screen.blit(self.font.render(strn, True, self.col), (x - w/d, y - h/d))
    def fontsize(self, num):
        self.font = font.Font(font.get_default_font(), num)
    def update(self):
        display.flip()
        display.update()
    def exit(self):
        self.running = False
    def queue_proc(self, func, args=(), msdelay=0):
        self.queue.append((func, msdelay, self.clock.get_ticks(), args))
    def image(self, x, y, py_img):
        '''py_img should be given in pygame.image.load() object'''
        self.images.append(py_img)
        self.screen.blit(py_img, (x,y))


def in_box(x, y, x1, y1, x2, y2):
    if x2 > x > x1 and y2 > y > y1:
        return True
    return False

if __name__ == "__main__":
    engine = Engine(500, 500, "Game")
    engine.mainloop()