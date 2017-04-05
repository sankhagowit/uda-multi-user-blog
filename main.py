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

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/signup', SignUp),
    ('/login', Login)
    ], debug=True)
