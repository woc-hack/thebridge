#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains Web Application
"""
from __future__ import print_function

import os

import tornado.ioloop
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.gen
import tornado.log

from tornado.options import options, define, parse_command_line

import oscar


define('debug', default=False)
define("http_port", default=9001)
define('static_path', default=os.path.join(os.path.dirname(__file__), 'static'))


class BaseWebHandler(tornado.web.RequestHandler):
    """ Basic class for web handlers, implements auth requirement for all
    handlers and uniform retrieval of auth info
    """
    def data_received(self, chunk):
        """ This method is not supported in admin console """
        pass


class IndexPageHandler(BaseWebHandler):

    def get(self):
        # Web interface (except admin console is built to support static
        # templates, so it does not use any template variables. All information
        # in web UI is rendered by means of REST API
        # The only reason to have separate handler instead of redirect to static
        # file is to wrap .get() method in authenticated decorator
        self.render("index.html")


class ProjectCommitsHandler(BaseWebHandler):
    def get(self, project_name):
        project = oscar.Project(project_name.encode('utf8'))
        self.finish('\n'.join(project.commit_shas))


class ProjectAuthorsHandler(BaseWebHandler):
    def get(self, project_name):
        project = oscar.Project(project_name.encode('utf8'))
        self.finish('\n'.join(project.author_names))


class ProjectTreesHandler(BaseWebHandler):
    def get(self, project_name):
        project = oscar.Project(project_name.encode('utf8'))

        def gen():
            for commit in project.commits:
                yield commit.tree.sha

        self.finish('\n'.join(gen()))


def main():
    settings = {
        'debug': options.debug,
        # 'default_handler_class': PageNotFoundHandler,
        'static_url_prefix': '/static/',
        'static_handler_class': tornado.web.StaticFileHandler,
        'static_path': options.static_path,
        # 'templae_path': options.template_path,
        'login_url': '/login',
    }

    application = tornado.web.Application([
        (r"/", IndexPageHandler, None, 'home'),
        (r"/api/v0/p2c/(.*)", ProjectCommitsHandler, None, 'project2commits'),
        (r"/api/v0/p2a/(.*)", ProjectAuthorsHandler, None, 'project2authors'),
        (r"/api/v0/p2t/(.*)", ProjectTreesHandler, None, 'project2trees'),
    ], **settings)

    application.listen(options.http_port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    parse_command_line()
    main()
