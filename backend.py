import json
import sys
from threading import Lock
from tornado import ioloop, web, websocket
from tornado.options import define, options, parse_command_line


define("port", default=8888, type=int)
#define("room_template", type=str)


class Board(object):
    """
    Stores current drawer board which shared between users
    """

    _lock_object = Lock()
    _lines = {}

    def add_lines(self, lines):
        """
        Add new lines on board
        """
        self._lock_object.acquire()
        for line in lines:
            x, y = line
            x, y = int(x), int(y)
            key = self._make_key(x, y)
            self._lines[key] = (x, y,)
        self._lock_object.release()

    def clean(self):
        """
        Clean current board
        """
        self._lock_object.acquire()
        Board._lines = {}
        self._lock_object.release()

    def get_lines(self):
        """
        Return lines stored on board
        """
        return self._lines.values()

    def _make_key(self, x, y):
        return "%d_%d" % (x, y)


class ClientsHolder(object):
    """
    Stores users who works with the service
    """

    _lock_object = Lock()
    _clients = {}
    _last_id = 0

    def add_client(self, obj):
        self._lock_object.acquire()
        client_id = ClientsHolder._last_id
        ClientsHolder._last_id += 1
        self._lock_object.release()
        self._clients[client_id] = obj
        return client_id

    def del_client(self, client_id, callback):
        if client_id in self._clients:
            self._lock_object.acquire()
            del self._clients[client_id]
            self._lock_object.release()
        callback()

    def get_all_clients_data(self):
        self._lock_object.acquire()
        result = []
        for client_id, record in self._clients.items():
            ua = record.request.headers.get('User-Agent', 'Unknown')
            result.append({'ip': record.request.remote_ip, 'ua': ua})
        self._lock_object.release()
        return result

    def __iter__(self):
        for id, cl in self._clients.items():
            yield (id, cl)

clients = ClientsHolder()
board = Board()


def new_line_worker(data, socket):
    board.add_lines(data)
    socket.update_lines()


class RoomHandler(web.RequestHandler):

    def get(self):
        self.write(open(sys.argv[1]).read())
        self.finish()


class WsHandler(websocket.WebSocketHandler):

    workers = {'lines': new_line_worker}
    action_key = 'action'

    def open(self, *args):
        self.stream.set_nodelay(True)
        client_id = clients.add_client(self)
        self.write_message(str(client_id))
        self.id = client_id
        self.send_new_clients_list()
        self.send_lines()

    def send_new_clients_list(self):
        data = clients.get_all_clients_data()
        self.broadcast(json.dumps({self.action_key: 'clients', 'data': data}))

    def update_lines(self):
        data = board.get_lines()
        self.broadcast(json.dumps({self.action_key: 'update_lines', 'data': data}, True))

    def send_lines(self):
        data = board.get_lines()
        self.write_message({self.action_key: 'update_lines', 'data': data})

    def broadcast(self, data, ignore_self=False):
        for client_id, cl in clients:
            if self.id == client_id and ignore_self:
                continue
            try:
                cl.write_message(data)
            except websocket.WebSocketClosedError:
                pass

    def on_message(self, message):
        data = json.loads(message)
        action = data['action']
        self.workers[action](data['data'], self)

    def on_close(self):
        clients.del_client(self.id, self.send_new_clients_list)

app = web.Application([
    (r'/room/', RoomHandler),
    (r'/ws/', WsHandler),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    io_loop = ioloop.IOLoop.current()
    io_loop.start()
