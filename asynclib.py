from socket import *
from threading import Thread
from time import sleep

class Client:
    def __init__(self, host, port, sock=None):
        self.socket = sock
        if sock is None:
            self.socket = socket()
        self.host = host
        self.port = port
        self.encoding = 'UTF-8'
        self.rbuffer = []
        self.wbuffer = []
        self.buffer = 1024
        self.wthread = Thread(target=self.wloop, daemon=True)
        self.rthread = Thread(target=self.rloop, daemon=True)

    def connect(self):
        self.socket.connect((self.host, self.port))

    def close(self):
        self.socket.close()

    def is_open(self):
        return self.socket.fileno() != -1

    def initiate_iothreads(self):
        self.wthread.start()
        self.rthread.start()

    def recv(self):
        try:
            return self.socket.recv(self.buffer).decode()
        except:
            self.close()
            return 'quit'

    def send(self, s):
        try:
            self.socket.send(s.encode(self.encoding))
        except:
            self.close()
            return 1

    def write(self, s):
        self.wbuffer.insert(0, s)

    def read(self, wait=True, delete=True):
        try:
            if delete:
                return self.rbuffer.pop()
            return self.rbuffer[-1]
        except IndexError:
            if not wait:
                return None
        while wait:
            try:
                if delete:
                    return self.rbuffer.pop()
                return self.rbuffer[-1]
            except IndexError:
                if not wait:
                    return None
            sleep(0.01)

    def wait_for(self, conn):
        while self.rbuffer[0][0] != conn:
            sleep(0.001)

    def wloop(self):
        while self.is_open():
            try:
                self.send(self.wbuffer.pop())
            except IndexError:
                pass
            sleep(0.01)

    def rloop(self):
        while self.is_open():
            self.rbuffer.insert(0, self.recv())
            sleep(0.01)

class Server:
    def __init__(self, host, port, sock=None, max_conns=20):
        self.socket = sock
        if sock is None:
            self.socket = socket()
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.host = host
        self.port = port
        self.socket.bind((host, port))
        self.connections = []
        self.conn_object = None
        # conn_object must have a *send(bytes)* and *recv(buffer) -> bytes*
        self.rbuffer = []
        self.wbuffer = []
        self.buffer = 1024
        self.max_people = max_conns
        self.encoding = 'UTF-8'
        self.sthread = Thread(target=self.servloop, daemon=True)
        self.wthread = Thread(target=self.wloop, daemon=True)
        self.rthreads = []
        self.on_accept = lambda *x: 0

    def open(self):
        self.socket.listen(self.max_people)
        self.sthread.start()

    def initiate_wthread(self):
        self.wthread.start()

    def run_uninitiated_rthreads(self):
        delete = []
        for thread in self.rthreads:
            if not thread.isAlive():
                try:
                    thread.start()
                except RuntimeError:
                    delete.append(thread)
        for thread in delete:
            self.rthreads.remove(thread)

    def is_open(self):
        return self.socket.fileno() != -1

    def accept(self):
        c,a = self.socket.accept()
        co = self.conn_object(c, a)
        self.connections.append(co)
        self.on_accept(co)

    def wait_for(self, conn):
        while True:
            try:
                while self.rbuffer[0][0] != conn:
                    sleep(0.001)
                break
            except IndexError:
                continue

    def send(self, conn, s):
        try:
            conn.send(s.encode(self.encoding))
        except:
            return 1

    def recv(self, conn):
        try:
            return conn.recv(self.buffer).decode(self.encoding)
        except:
            return 'quit'

    def write(self, conn, s):
        self.wbuffer.insert(0, (conn, s))

    def read(self, targets=None, wait=True, delete=True):
        if targets is None:
            try:
                if delete:
                    return self.rbuffer.pop()
                return self.rbuffer[-1]
            except IndexError:
                if not wait:
                    return None, None
            sleep(0.01)
            while wait:
                try:
                    if delete:
                        return self.rbuffer.pop()
                    return self.rbuffer[-1]
                except IndexError:
                    if not wait:
                        return None, None
                sleep(0.01)
        else:
            for msg in reversed(self.rbuffer):
                if msg[0] in targets:
                    if delete:
                        self.rbuffer.remove(msg)
                    return msg
            while wait:
                # print(self.rbuffer)
                for msg in reversed(self.rbuffer):
                    if msg[0] in targets:
                        if delete:
                            self.rbuffer.remove(msg)
                        return msg
                sleep(0.01)
            return None, None

    def wloop(self):
        while self.is_open():
            try:
                self.send(*self.wbuffer.pop())
            except IndexError:
                pass
            sleep(0.01)

    def rloop(self, conn_obj):
        while self.is_open() and conn_obj.is_open():
            self.rbuffer.insert(0, (conn_obj, self.recv(conn_obj)))
            sleep(0.01)

    def gen_rthread(self, conn):
        self.rthreads.append(Thread(target=self.rloop, args=(conn,), daemon=True))

    def servloop(self):
        while True:
            self.accept()
            sleep(0.01)

    def set_conn_object(self, obj):
        self.conn_object = obj

    def close(self):
        self.socket.close()