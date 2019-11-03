#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file contains Web Application
"""
from __future__ import print_function

import io
import os

import tornado.ioloop
import tornado.httpserver
import tornado.web
import tornado.websocket
import tornado.gen
import tornado.log

from tornado.options import options, define, parse_command_line

import pandas as pd
from sqlalchemy import create_engine

USER = 'ghtorrent_user'
PASSWORD = 'ghtorrent_password'
HOST = '127.0.0.1'  # localhost won't work
OPTIONS = 'charset=utf8mb4&unix_socket=/var/run/mysqld/mysql.sock'
DATABASE = 'ghtorrent-2018-03'

conn_string = 'mysql+mysqldb://{user}:{password}@{host}/{db}?{options}'.format(
    user=USER, password=PASSWORD, host=HOST, db=DATABASE, options=OPTIONS)
engine = create_engine(conn_string, pool_recycle=3600)

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
    def get(self, owner, project):
        df = pd.read_sql(
            """
            SELECT c.sha as sha, u2.login as author
            FROM projects p, users u, commits c
            LEFT JOIN users u2 ON c.author_id = u2.id
            WHERE u.login=%(user)s
                AND p.name=%(repo)s
                AND p.owner_id = u.id
                AND c.project_id = p.id
            """,
            engine,
            params={'user': owner, 'repo': project}
        )
        s = io.StringIO()
        df.to_csv(s, index=False)
        self.finish(s.getvalue())


class ProjectIssuesHandler(BaseWebHandler):
    def get(self, owner, project):
        df = pd.read_sql(
            """
            SELECT i.issue_id as issue_id, 
                u2.login as reporter, 
                i.created_at as created_at
            FROM projects p, users u, issues i
            JOIN users u2 ON i.reporter_id = u2.id
            WHERE u.login=%(user)s
                AND p.name=%(repo)s
                AND p.owner_id = u.id
                AND i.repo_id = p.id
                AND NOT i.pull_request
            """,
            engine,
            params={'user': owner, 'repo': project}
        )
        s = io.StringIO()
        df.to_csv(s, index=False)
        self.finish(s.getvalue())


class ProjectPRHandler(BaseWebHandler):
    def get(self, owner, project):
        df = pd.read_sql(
            """
            SELECT pr.pullreq_id as pr_id, 
                c.sha as base_commit, c2.sha as head_commit, 
                i.created_at as created_at, 
                CONCAT(u2.login, "/", p.name) as head_repo 
            FROM users u, projects p, pull_requests pr, issues i, 
                commits c, commits c2, projects p2, users u2 
            WHERE p.name=%(repo)s
                AND u.login=%(user)s 
                AND p.owner_id = u.id 
                AND i.repo_id=p.id 
                AND pr.base_repo_id=p.id 
                AND i.issue_id = pr.pullreq_id 
                AND c.id=pr.base_commit_id 
                AND c2.id=pr.head_commit_id 
                AND p2.id = pr.head_repo_id 
                AND u2.id=p2.owner_id;""",
            engine,
            params={'user': owner, 'repo': project}
        )
        s = io.StringIO()
        df.to_csv(s, index=False)
        self.finish(s.getvalue())


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
        (r"/repos/([^/]*)/([^/]*)/commits", ProjectCommitsHandler, None, 'commits'),
        (r"/repos/([^/]*)/([^/]*)/issues", ProjectIssuesHandler, None, 'issues'),
        (r"/repos/([^/]*)/([^/]*)/prs", ProjectPRHandler, None, 'pull_requests'),
    ], **settings)

    application.listen(options.http_port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    parse_command_line()
    main()
