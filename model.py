from google.appengine.ext import db
import user_accounts

class User(db.Model):
    """User Class is db.Model Entity database which stores the 
    clear text user name, clear text date created, password of the form 
    hashed password,salt. The hashed password contains the 
    username+password+salt see user_accounts.py for more on hash
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
    Entitiy for the main blog posts. Requires a subject which is a searchable
    StringProperty, content, author, a list of users who have liked it, the number
    of comments, creation and modification dates
    """
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    author = db.StringProperty(required = True)
    likes = db.StringListProperty()
    comments = db.IntegerProperty(default=0)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def likesLength(self):
        # Used to display the number of likes in jinja template
        return len(self.likes)

    def addLike(self, userName):
        # Add a username to the likes list, adding a like.
        self.likes.append(userName)
        self.put()

    @classmethod
    def exists(cls, blogID):
        # Check if a given blogID exists before performing any operation on it
        # If it does exist return True otherwise return None
        post = cls.get_by_id(int(blogID))
        if post:
            return post


class Comment(db.Model):
    """
    Comment entity used to store comments for a given blog post. Every comment
    contains the ID of the blogpost the comment pertains to.
    
    Also contains the class method to search through the comment entities for
    the comments which match a blogID.
    """
    blogPost = db.IntegerProperty(required = True)
    content = db.TextProperty(required = True)
    author =  db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def get_comments_by_blogID(cls, blogID):
        return db.GqlQuery("SELECT * FROM Comment WHERE blogPost = %s" % blogID)

    @classmethod
    def exists(cls, commentID):
        # Check if a given commentID exists before performing any operation on
        # it. If it does exist return True otherwise return None
        comment = cls.get_by_id(int(commentID))
        if comment:
            return comment