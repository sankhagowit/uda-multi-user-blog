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
        message = self.request.get('message')
        if self.posts:
            if self.user:
                self.write(self.render_str(template, user=self.user,
                                           posts=self.posts, message=message, **kw))
            else:
                self.write(self.render_str(template, posts=self.posts, **kw))
        else:
            if self.user:
                self.write(self.render_str(template, user=self.user, message=message, **kw))
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
        # Check database for posts at every request to render on aside list
        posts = model.BlogPost.all().order('-created')
        if posts:
            self.posts = posts # Now available in all views


class MainHandler(Handler):
    def get(self):
        self.render("main.html", title="Multi-User Blog")


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
        # Grab sign up parameters
        self.email = self.request.get('email')
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.passwordCheck = self.request.get('passwordCheck')

        reg_params = dict(username = self.username, email = self.email)
        # run signin info through regex validation, error handling for failures
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
                # Signup information has passed all tests, create new user in
                # datastore
                user = model.User.register(self.username,
                                           self.password,
                                           self.email)
                user.put()

                self.login(user)
                self.redirect('/')


class Login(Handler):
    def post(self):
        # post method handling log in information
        username = self.request.get('username')
        password = self.request.get('password')
        # Validate Login Information
        user = model.User.login(username, password)
        if user:
            self.login(user)
            self.redirect('/')
        else:
            query_params = {'loginError': 'Invalid Username or Password'}
            self.redirect('/signup?'+urllib.urlencode(query_params))

class Logout(Handler):
    def post(self):
        # Logout by calling handler instance method
        self.logout()
        self.redirect('/signup')

class BlogPost(Handler):
    """get and post methods to display form to create new blog post and push
    new blog post after error checking to the data store"""
    def get(self):
        # render page for new blog post
        if self.user:
            self.render('blogPost.html', title="New Blog Post")
        else:
            query_params = {'loginError': 'Must be logged in to make a blog post'}
            self.redirect('/signup?'+urllib.urlencode(query_params))

    def post(self):
        # Get new post subject and content
        if self.user:
            subject = self.request.get('subject')
            content = self.request.get('content')

            if subject and content:
                # push new blogpost to datastore
                post = model.BlogPost(subject = subject,
                                      content = content,
                                      author = self.user.userName)
                postKey = post.put()
                self.redirect('/%s' % str(postKey.id()))
            else:
                error = "Please enter a Subject and Content for the Blog Post"
                self.render('blogPost.html', title="New Blog Post", postError=error,
                            subject = subject, content = content)
        else:
            #user is not signed in.
            query_params = {'loginError': "You must be signed in to make a blog post"}
            self.redirect('/signup?%s' % (urllib.urlencode(query_params)))


class PostPage(Handler):
    """PostPage displays a single blog post at a time with the comments. From 
    this page a user can like a post or add a comment
    heavily using the get call here via redirects on other handlers and passing
    the error messages through get parameters called modifyError and commentError"""
    def get(self, post_id):
        # Pass Errors from incorrect users attempting to modify or comment
        # a blog post in the URI get parameters.
        modifyError = self.request.get('modifyError')
        commentError = self.request.get('commentError')
        post = model.BlogPost.get_by_id(int(post_id))
        comments = model.Comment.get_comments_by_blogID(post_id)
        self.render('singlePost.html', title="Blog Post Detail", post=post,
                    comments=comments, modifyError=modifyError,
                    commentError=commentError)

    def post(self, post_id):
        # This post method is used by the like button to increase the number
        # of likes a blogpost has. The likes are stored as a StringListProperty
        # of the users who have liked the blogpost.

        post = model.BlogPost.exists(post_id)
        if post:
            if self.user: # must be logged in to use the like button
                if post.author != self.user.userName: # Cant like own post
                    if not self.user.userName in post.likes:
                        post.addLike(self.user.userName) # add user to list
                        query_params = {'commentError': ""}
                    else:
                        query_params = {'commentError': "You've already liked the post! Cannot like it again!"}
                else:
                    query_params = {'commentError': "You cannot like your own post!"}
            else:
                query_params = {'commentError': "You must be signed in to like a post!"}
            self.redirect('/%s?%s' % (post_id, urllib.urlencode(query_params)))
        else:
            query_params = {'message': "Like failed - that post does not exist"}
            self.redirect('/?%s' % (urllib.urlencode(query_params)))



class ModifyBlog(Handler):
    def get(self, post_id):
        """ModifyBlog get call is used to modify an existing Blog Post. Only 
        the user who created the blog post can edit or delete that post
        The ID of the post is passed in the URI after /modify/"""
        post = model.BlogPost.exists(post_id)
        if post:
            if post.author != self.user.userName: # Cant modify someone elses post
                query_params = {'modifyError': "Sorry - Cannot modify a post you did not author"}
                self.redirect('/%s?%s' % (post_id, urllib.urlencode(query_params)))
            else:
                # display blogPost page with previous content for modification
                self.render('blogPost.html', title="Modify Blog Post",
                            subject=post.subject, content=post.content, id=post_id)
        else:
            query_params = {'message': "That blog post does not exist"}
            self.redirect('/?%s' % (urllib.urlencode(query_params)))

    def post(self, post_id):
        """ModifyBlog post call used to delete an existing blog post or push
        updated blog content to an existing blog post. Only the user
        who created the blog post can edit or delete that post
        The ID of the post is passed in the URI as the BlogPosts ID"""
        if self.user:
            delete = self.request.get('Delete') # the post flag if we are deleting
            post = model.BlogPost.exists(post_id)
            if post:
                if post.author != self.user.userName:
                    query_params = {'modifyError': "Sorry - Cannot delete a post you did not author"}
                    self.redirect('/%s?%s' % (post_id, urllib.urlencode(query_params)))
                else:
                    if delete:
                        post.delete() #delete the blog post and all associated comments
                        comments = model.Comment.get_comments_by_blogID(post_id)
                        for comment in comments:
                            comment.delete()
                        query_params = {'message': "Blog Post Deleted. "
                                                   "Page may need to be refreshed to reflect changes"}
                        self.redirect('/?%s' % urllib.urlencode(query_params))
                    else:
                        # Save the blog updates.
                        subject = self.request.get('subject')
                        content = self.request.get('content')
                        if subject and content:
                            post.subject = subject
                            post.content = content
                            post.put()
                            self.redirect('/%s' % post_id)
                        else:
                            # Error handling for updating blog post.
                            error = "Blog Post must have a subject and content"
                            self.render('blogPost.html', title="Modify Blog Post", postError=error,
                                        subject=subject, content=content)
            else:
                query_params = {'message': "That blog post does not exist"}
                self.redirect('/?%s' % (urllib.urlencode(query_params)))
        else:
            query_params = {'loginError': "You must be signed in to delete or modify a blog post"}
            self.redirect('/signup?%s' % (urllib.urlencode(query_params)))

class CommentBlog(Handler):
    """Methods to add and review comments.
    Would be much easier if it was its own page..."""
    def get(self, post_id):
        # Get method activates tempate to display comment box
        post = model.BlogPost.exists(post_id)
        if post:
            if self.user:
                self.render('singlePost.html', title="Add Comment", commentActive=True, post=post)
            else:
                query_params = {'commentError': "You must be signed in to comment on a post!"}
                self.redirect('/%s?%s' % (post_id, urllib.urlencode(query_params)))
        else:
            query_params = {'message': "That blog post does not exist"}
            self.redirect('/?%s' % (urllib.urlencode(query_params)))

    def post(self, post_id):
        # Post method pushes comment content to data store
        commentContent = self.request.get("commentContent")
        post = model.BlogPost.exists(post_id)
        if post:
            if self.user:
                if commentContent:
                    comment = model.Comment(blogPost= int(post_id),
                                            content= commentContent,
                                            author = self.user.userName)
                    comment.put()
                    post.comments += 1
                    post.put()
                    self.redirect('/%s' % post_id) #reload page with comment
                else:
                    commentError = "Comment must have content in order to submit"
                    self.render('singlePost.html', title="Add Comment",
                                commentActive=True, post=post, commentError=commentError)
            else:
                query_params = {
                    'loginError': "You must be signed in to create a comment"}
                self.redirect('/signup?%s' % (urllib.urlencode(query_params)))
        else:
            query_params = {'message': "That blog post does not exist"}
            self.redirect('/?%s' % (urllib.urlencode(query_params)))

class ModifyComment(Handler):
    """ModifyComment class used to modify existing comments. Jinja2 html template
    contains logic to display the edit and delete buttons only on comments the
    signed in user made."""
    def get(self, comment_id):
        comment = model.Comment.exists(comment_id)
        post = model.BlogPost.exists(comment.blogPost)
        if comment:
            self.render('singlePost.html', title="Modify Comment", post=post,
                        commentActive=True, commentContent=comment.content,
                        modifyComment=comment_id)
            # modifyComment flag changes the action of the submit form to ModifyComment
            # post method opposed to CommentBlog post method
        else:
            query_params = {'message': "Cannot retrieve comment, it does not exist"}
            self.redirect('/?%s' % (urllib.urlencode(query_params)))

    def post(self, comment_id):
        # Post method handles individual comment deletion or pushes updated comment
        # content to an existing comment.
        delete = self.request.get('delete') # This is the delete flag
        comment = model.Comment.get_by_id(int(comment_id))
        if comment:
            post = model.BlogPost.get_by_id(comment.blogPost)
            # don't need to check post - if the comment exists, then the
            # comment.blogPost attribute will be live - if it is deleted the
            # comment is also deleted
            blogID = str(comment.blogPost)  # Save blogID for redirect at end
            if self.user:
                if self.user.userName == comment.author:
                    if delete: # Delete the comment
                        comment.delete()
                        post.comments -= 1
                        post.put()
                        query_params = {'commentError': "Comment Deleted. May need to refresh page"}
                    else:
                        commentContent = self.request.get('commentContent')
                        if commentContent:
                            comment.content = commentContent
                            comment.put()
                            query_params = {'commentError': "Comment Updated. May need to refresh page"}
                        else:
                            query_params = {'commentError': "Cannot update a comment with no content"}
                    self.redirect('/%s?%s' % (blogID, urllib.urlencode(query_params)))
                    # query_params used to pass status of comment deletion throughout posts
                else:
                    # you can not modify a comment you did not make
                    query_params = {
                        'commentError': "Cannot update comment you did not create"}
                    self.redirect(
                        '/%s?%s' % (blogID, urllib.urlencode(query_params)))
            else:
                query_params = {
                    'loginError': "You must be signed in to delete or modify a comment"}
                self.redirect('/signup?%s' % (urllib.urlencode(query_params)))

        else:
            query_params = {'message': "Cannot modify comment, it does not exist"}
            self.redirect('/?%s' % (urllib.urlencode(query_params)))



app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/signup', SignUp),
    ('/login', Login),
    ('/post', BlogPost),
    ('/logout', Logout),
    (r'/([0-9]+)', PostPage),
    (r'/modify/([0-9]+)', ModifyBlog),
    (r'/comment/([0-9]+)', CommentBlog),
    (r'/modifycomment/([0-9]+)', ModifyComment)
    ], debug=True)
