from google.appengine.ext import db

class Users(db.Model):
    """User Class is a Google app engine Entity database which stores the 
    clear text user name, clear text date created, password of the form 
    hashed password|salt. The hashed password contains the 
    username,email,password
    
    should the username also be hashed that way if the database is stolen,
    well lets assume this situation where they steal the password then they also
    will have the python file with the secret and hashing algorithm..hmm"""
    userName = db.StringProperty(required = True)
    # email = db.StringProperty(required = True)
    password = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True)

class Blog(db.Model):
    """
    Explain the blog class/entity
    """
    created = db.DateTimeProperty(auto_now_add = True)