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


from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, template
from google.appengine.api import memcache

import os, datetime, re

from blog import *


class MainHandler(webapp.RequestHandler):

    def get(self):

        template_values = {}

        query = Post.all()
        query.order('-date_created')
        posts = query.fetch(20)

        template_values['posts'] = posts

        path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_index.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        title = self.request.get('title')

        p = re.compile('[^a-z0-9\s]')
        stub = p.sub('', title.lower().strip())

        p = re.compile('\s+')
        stub = p.sub('-', stub)

        body = self.request.get('body')

        post = Post(author='Myles', title=title, stub=stub, body=body)
        if (self.request.get('publish')):
            post.date_published = datetime.datetime.now()
        post.put()

        memcache.delete('entries2')
        memcache.delete('blog_posts')
        memcache.delete('blog_posts_index')

        self.redirect('/admin/')


def main():
    #logging.getLogger().setLevel(logging.DEBUG)
    urls = [
        ('/admin/', MainHandler)
    ]
    application = webapp.WSGIApplication(urls,
                                       debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
