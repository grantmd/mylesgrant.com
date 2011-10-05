from google.appengine.ext import webapp, db
import os, logging
from google.appengine.ext.webapp import template
from google.appengine.api import memcache


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


class BlogPostHandler(webapp.RequestHandler):

    def get(self, year, month, day, stub):
        template_values = {}

        force_miss = False
        if self.request.get('refresh'):
            force_miss = True

        logging.debug('blog post stub: %s' % stub)

        key_name = "blog_post_%s" % stub
        post = memcache.get(key_name)
        if post is None or force_miss:
            query = Post.all()
            query.filter('stub =', stub)
            post = query.get()

            memcache.set(key_name, post)

        logging.debug('blog post: %s' % post)

        if not post:
            self.error(404)
            path = os.path.join(os.path.dirname(__file__), 'templates', '404.html')
            self.response.out.write(template.render(path, template_values))
        else:
            template_values['post'] = post

            key_name = "blog_post_%s_comments" % stub
            comments = memcache.get(key_name)
            if comments is None or force_miss:
                query = Comment.all()
                query.filter('post =', post)
                query.filter('date_published != ', None)
                comments = query.fetch(1000)

                memcache.set(key_name, comments)

            template_values['comments'] = comments

            path = os.path.join(os.path.dirname(__file__), 'templates', 'blog_post.html')
            self.response.out.write(template.render(path, template_values))


class BlogHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        force_miss = False
        if self.request.get('refresh'):
            force_miss = True

        key_name = "blog_posts_index"
        posts = memcache.get(key_name)
        if posts is None or force_miss:
            query = Post.all()
            query.filter('date_published != ', None)
            query.order('-date_published')
            posts = query.fetch(20)

            memcache.set(key_name, posts)

        template_values['posts'] = posts

        path = os.path.join(os.path.dirname(__file__), 'templates', 'blog.html')
        self.response.out.write(template.render(path, template_values))


class BlogFeedHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        force_miss = False
        if self.request.get('refresh'):
            force_miss = True

        key_name = "blog_posts_index"
        posts = memcache.get(key_name)
        if posts is None or force_miss:
            query = Post.all()
            query.filter('date_published != ', None)
            query.order('-date_published')
            posts = query.fetch(20)

            memcache.set(key_name, posts)

        template_values['posts'] = posts

        path = os.path.join(os.path.dirname(__file__), 'templates', 'blog_feed.xml')
        self.response.out.write(template.render(path, template_values))
