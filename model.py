from google.appengine.ext import db

class Users(db.Model):
    """User Class is a Google app engine Entity database which stores the 
    clear text user name, clear text date created, password of the form 
    hashed password,salt. The hashed password contains the 
    username+password+salt
    """
    userName = db.StringProperty(required = True)
    email = db.StringProperty(required = True)
    passwordHash = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True)

class Blog(db.Model):
    """
    Explain the blog class/entity
    """
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now_add = True)
