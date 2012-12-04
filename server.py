#! /usr/bin/env python
import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        with open('example.html') as fd:
            self.write(fd.read())

class EditorHandler(tornado.web.RequestHandler):
    def post(self):
        #self.write(self.get_argument("data"))
        print self.request.body

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/test", EditorHandler),
], debug=True)  # debug means reload this file when it changes...

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

