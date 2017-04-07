#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
import jinja2
import user_accounts

# Create Template directory path, Initialize Jinja, set autoescape to true

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_cookie(self, name, val):
        # Create secure cookie, deletes when browser closes
        cookie_val = user_accounts.make_secure_val(val)
        self.response.headers.add_header('Set-Cookie',
                                         '%s=%s' % (name,cookie_val))

    def read_cookie(self, name):
        # First check if cookie exists then check if cookie passes
        # security test
        secure_cookie = self.request.cookies.get(name)
        return secure_cookie and user_accounts.check_secure_val(secure_cookie)

    def login(self, user):
        # Set the cookie for a logged in user
        self.set_cookie('user_id', str(user.key().id()))

    def logout(self):
        # Delete the cookie for a logged in user
        self.response.headers.add_headers('Set Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        # Check if user is logged in at every request
        webapp2.RequestHandler.initialize(self, *a, **kw)
        user_id = self.read_cookie('user_id')
        self.user = user_id and User.by_id(int(user_id)) #TODO

class MainHandler(Handler):
    def get(self):
        self.render("main.html", title="Multi-User Blog")
        user_cookie_str = self.request.cookies.get('user')
        if user_cookie_str:
            user_val = user_accounts.check_secure_val(user_cookie_str)
            # Load page as signed in user
        else:
            pass # Load page as unregisted user

    def post(self):
        self.write('MainHandler Post Method Called')


class SignUp(Handler):
    def get(self):
        self.render('signup.html', title="Multi-User Blog Registration")

    def post(self):
        self.write('SignUp Post Method Called')


class Login(Handler):
    def post(self):
        self.write('Login Called')

class BlogPost(Handler):
    def get(self):
        self.render('blogPost.html', title="New Blog Post")

    def post(self):
        self.write('BlogPost Post method called')

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/signup', SignUp),
    ('/login', Login),
    ('/post', BlogPost)
    ], debug=True)
