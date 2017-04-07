from google.appengine.ext import db
import user_accounts

class User(db.Model):
    """User Class is a Google app engine Entity database which stores the 
    clear text user name, clear text date created, password of the form 
    hashed password,salt. The hashed password contains the 
    username+password+salt
    """
    userName = db.StringProperty(required = True)
    email = db.StringProperty()
    passwordHash = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True)
    # Add Homepage visits?

    @classmethod
    def by_id(cls, user_id):
        return cls.get_by_id(user_id, parent=users_key())

    @classmethod
    def by_name(cls, userName):
        return cls.all().filter('userName =', userName).get()

    @classmethod
    def register(cls, name, password, email=None):
        passwordHash = user_accounts.make_pw_hash(name, password)
        return User(parent = users_key(),
                    userName = name,
                    passwordHash = passwordHash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        userName = cls.by_name(name)
        if userName and user_accounts.valid_pw(name, pw, userName.passwordHash):
            return userName

def users_key(group = 'default'):
    # group parameter for future user groups
    return db.Key.from_path('users', group)

def blog_key(name = 'default'):
    # group parameter for future blog groups
    return db.Key.from_path('blogs', name)

class BlogPost(db.Model):
    """
    Explain the blog class/entity
    """
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now_add = True)
