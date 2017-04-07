"""user """
import hashlib
import hmac
import random
import re
import string

SECRET = 'imsosecret'

# Hashing for cookies
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()


def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

# User Account Hashing
def make_salt(length = 5):
    return ''.join(random.choice(string.letters) for x in xrange(length))


def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)


def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)

# Registration Validation Functions
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(name):
    return name and USER_RE.match(name)

PW_RE = re.compile(r"^.{3,20}$")
def valid_password(pw):
    return pw and PW_RE.match(pw)

EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return email and EMAIL_RE.match(email)

