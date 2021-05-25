import tornado.web
import tornado.ioloop

from .ws_handler import WSHandler

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        # self.render('index.html')
        return 'Live2p Server'
    
class SetupHandler(tornado.web.RequestHandler):
    def get(self, *args):
        self.finish()
        


app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/ws', WSHandler)
])

if __name__ == '__main__':
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()