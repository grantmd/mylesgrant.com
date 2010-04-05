import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader

class Post(db.Model):
	author = db.StringProperty()
	title = db.StringProperty()
	stub = db.StringProperty()
	body = db.TextProperty()
	date_created = db.DateTimeProperty(auto_now_add=True)
	date_published = db.DateTimeProperty()

class Comment(db.Model):
	post = db.ReferenceProperty()
	author = db.StringProperty()
	email = db.StringProperty()
	url = db.StringProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	body = db.TextProperty()

class BlogPostsLoader(bulkloader.Loader):
	def __init__(self):
		# author, title, stub, body, date_created, date_published
		bulkloader.Loader.__init__(self, 'Post',
			[('author', str),
			('title', str),
			('stub', str),
			('body', str),
			('date_created',
				lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')),
			('date_published',
				lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
			])

class CommentsLoader(bulkloader.Loader):
	def __init__(self):
		# post, author, email, url, date, body
		bulkloader.Loader.__init__(self, 'Comment',
			[('post', self.findPost),
			('author', str),
			('email', str),
			('url', str),
			('date',
				lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')),
			('body', str)
			])
	
	def findPost(self, stub):
		query = Post.all()
		query.filter('stub =', stub)
		post = query.get()
		return Post.all().filter('stub =', stub).get().key()

loaders = [BlogPostsLoader, CommentsLoader]