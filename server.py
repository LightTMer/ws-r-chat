import tornado.ioloop
import tornado.web
import tornado.websocket
import redis
import uuid



redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
clients = {}
pubsub = redis_client.pubsub()

class ChatWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        client_id = str(uuid.uuid4())
        clients[self] = client_id
        self.write_message(f"Вы вошли в чат с ID: {client_id}")
        self.send_online_clients()

      
        if not hasattr(self, 'is_subscribed'):
            pubsub.subscribe('chat_channel')
            tornado.ioloop.IOLoop.current().add_callback(self.listen_to_redis)

    async def listen_to_redis(self):
        while True:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                for client in clients.keys():
                    client.write_message(message['data'].decode('utf-8'))
            await tornado.gen.sleep(0.1)

    def on_message(self, message):
        redis_client.publish('chat_channel', f"{clients[self]}: {message}")

    def on_close(self):
        del clients[self]
        self.send_online_clients()

    def send_online_clients(self):
        online_clients = [f"id: {client_id}" for client_id in clients.values()]
        online_clients_message = f"Онлайн клиенты: {', '.join(online_clients)}"
        for client in clients.keys():
            client.write_message(online_clients_message)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

def make_app():
    return tornado.web.Application([
        (r"/websocket", ChatWebSocket),
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Сервер запущен на http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()
