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
import urllib

import webapp2
import os
import jinja2

import model
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
        if self.posts:
            if self.user:
                self.write(self.render_str(template, user=self.user,
                                           posts=self.posts, **kw))
            else:
                self.write(self.render_str(template, posts=self.posts, **kw))
        else:
            if self.user:
                self.write(self.render_str(template, user=self.user, **kw))
            else:
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
        self.response.delete_cookie('user_id')

    def initialize(self, *a, **kw):
        # Check if user is logged in at every request
        webapp2.RequestHandler.initialize(self, *a, **kw)
        user_id = self.read_cookie('user_id')
        self.user = user_id and model.User.by_id(int(user_id))
        posts = model.BlogPost.all().order('-created')
        if posts:
            self.posts = posts


class MainHandler(Handler):
    def get(self):
        self.render("main.html", title="Multi-User Blog")

    # Post method for debug - nothing to really post here.
    def post(self):
        self.write('MainHandler Post Method Called')


class SignUp(Handler):
    """Handle Registration
    Display signup page, then check the inputs for valid characters
    pass all error messages into reg_parms and then reload the page
    If inputs pass all input checks, check database is username is available
    if username is available, add user to database, sign user in, reload page"""
    def get(self):
        loginError = self.request.get('loginError')
        self.render('signup.html', title="Multi-User Blog Registration",
                    loginError=loginError)

    def post(self):
        self.email = self.request.get('email')
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.passwordCheck = self.request.get('passwordCheck')

        reg_params = dict(username = self.username, email = self.email)

        if not user_accounts.valid_email(self.email):
            reg_params['emailError'] = "Not a valid email address"

        if not user_accounts.valid_username(self.username):
            reg_params['usernameError'] = "Not a valid username, invalid characters"

        if not user_accounts.valid_password(self.password):
            reg_params['passwordError'] = "Not a valid password, invalid characters"

        if self.password != self.passwordCheck:
            reg_params['passwordCheckError'] = "Passwords do not match"

        if len(reg_params)>2:
            reg_params['title'] = "Registration Error"
            self.render('signup.html', **reg_params)
        else:
            if model.User.by_name(self.username):
                reg_params['usernameError'] = "Username already taken"
                reg_params['title'] = "Registration Error"
                self.render('signup.html', **reg_params)
            else:
                user = model.User.register(self.username,
                                           self.password,
                                           self.email)
                user.put()

                self.login(user)
                self.redirect('/')


class Login(Handler):
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        user = model.User.login(username, password)
        if user:
            self.login(user)
            self.redirect('/')
        else:
            query_params = {'loginError': 'Invalid Username or Password'}
            self.redirect('/signup?'+urllib.urlencode(query_params))

class Logout(Handler):
    def post(self):
        self.logout()
        self.redirect('/signup')

class BlogPost(Handler):
    def get(self):
        if self.user:

            self.render('blogPost.html', title="New Blog Post")
        else:
            query_params = {'loginError': 'Must be logged in to make a blog post'}
            self.redirect('/signup?'+urllib.urlencode(query_params))

    def post(self):
        self.write('BlogPost Post method called')
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post = model.BlogPost(subject = subject,
                                  content = content,
                                  author = self.user.userName)
            postKey = post.put()
            self.redirect('/%s' % str(postKey.id()))
        else:
            error = "Please enter a Subject and Content for the Blog Post"
            self.render('blogPost.html', title="New Blog Post", postError=error,
                        subject = subject, content = content)

class PostPage(Handler):
    def get(self, post_id):
        post = model.BlogPost.get_by_id(int(post_id))
        self.render('singlePost.html', title="Blog Post Detail", post=post)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/signup', SignUp),
    ('/login', Login),
    ('/post', BlogPost),
    ('/logout', Logout),
    (r'/([0-9]+)', PostPage),

    ], debug=True)
