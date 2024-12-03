import tornado.ioloop
import tornado.web
import tornado.websocket
import redis



redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)


clients = []

class ChatWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.append(self)
        self.write_message("Вы вошли в чат!")

        pubsub = redis_client.pubsub()
        pubsub.subscribe('chat_channel')

        tornado.ioloop.IOLoop.current().add_callback(self.listen_to_redis, pubsub)

    async def listen_to_redis(self, pubsub):
        while True:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                for client in clients:
                    client.write_message(message['data'].decode('utf-8'))
            await tornado.gen.sleep(0.1)

    def on_message(self, message):
      
        redis_client.publish('chat_channel', message)

    def on_close(self):
        clients.remove(self)

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
