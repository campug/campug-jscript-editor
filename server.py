#! /usr/bin/env python
import os
import collections
import json
import uuid
import tornado.ioloop
import tornado.web
import jedi

from tornado.escape import json_encode


sessions = {}


class Session(object):
    '''An object with arbitrary attributes holding user session data.'''
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class SessionsMixin(object):
    def new_session(self):
        # lines: a list of the document lines, without newlines.
        return Session(lines=[u''], filename=u'')

    def get_session(self):
        uid = self.get_cookie('uid', None)
        if uid is None:
            uid = str(uuid.uuid4())
            self.set_cookie('uid', uid)
        if uid not in sessions:
            sessions[uid] = self.new_session()
        return sessions[uid]


Edit = collections.namedtuple('Edit',
                              'action row col endrow endcol text lines')


class MainHandler(tornado.web.RequestHandler, SessionsMixin):
    def get(self):
        session = self.get_session()
        self.render('index.html', document='\n'.join(session.lines))


class EditorHandler(tornado.web.RequestHandler, SessionsMixin):
    def post(self):
        e = json.loads(self.request.body)
        edit = Edit(action=e['action'],
                    row=e['range']['start']['row'],
                    col=e['range']['start']['column'],
                    endrow=e['range']['end']['row'],
                    endcol=e['range']['end']['column'],
                    text=e.get('text'),
                    lines=e.get('lines'))
        session = self.get_session()
        # Apply the edit action to session.lines (i.e. update the document).
        # 'Text' edits are either a single newline or don't contain newlines.
        # This code probably mirrors Document.applyDeltas() in the javascript.
        if edit.action == 'insertText':
            if edit.text == u'\n':
                line = session.lines[edit.row]
                session.lines[edit.row] = line[:edit.col]
                session.lines.insert(edit.endrow, line[edit.col:])
            else:
                line = session.lines[edit.row]
                line = line[:edit.col] + edit.text + line[edit.col:]
                session.lines[edit.row] = line
        elif edit.action == 'removeText':
            if edit.text == u'\n':
                session.lines[edit.row] += session.lines[edit.row + 1]
                del session.lines[edit.row + 1]
            else:
                line = session.lines[edit.row]
                line = line[:edit.col] + line[edit.endcol:]
                session.lines[edit.row] = line
        elif edit.action == 'insertLines':
            session.lines[edit.row:edit.row] = edit.lines
        elif edit.action == 'removeLines':
            session.lines[edit.row:edit.endrow] = []


class CompletionHandler(tornado.web.RequestHandler, SessionsMixin):
    def post(self):
        session = self.get_session()
        source = ''.join(session.lines)
        # TEMP HACK: always be at the end
        line = source.count('\n')
        column = source.rfind('\n')
        script = jedi.Script(source, line, column, session.filename)
        completions = script.complete()
        data = {'completions': [c.complete for c in completions]}
        self.write(json_encode(data))


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/edit", EditorHandler),
    (r"/completions", CompletionHandler),
])


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

