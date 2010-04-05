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
from google.appengine.api import memcache, urlfetch
from django.utils import simplejson

import os, feedparser, datetime, time, re

from games import *
from blog import *
from twitter import *
from flickr import *

class MainHandler(webapp.RequestHandler):

	def get(self):
		refresh = False
		
		if self.request.get('refresh'):
			refresh = True
		
		template_values = {
			'entries': self.fetch_entries(refresh)
		}
				
		path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
		self.response.out.write(template.render(path, template_values))
	
	def fetch_entries(self, force_miss = False):		
		key_name = 'entries2'
		entries = memcache.get(key_name)
		if entries is not None and not force_miss:
			return entries
		else:
			entries = {}
			
			blog_posts = self.fetch_blog_posts(force_miss)
			for post in blog_posts:
				entries[post.published] = post
	
			flickr = self.fetch_flickr(force_miss)
			for photo in flickr:
				entries[photo['published']] = photo
			
			twitter = self.fetch_twitter(force_miss)
			for post in twitter:
				entries[post['published']] = post
		
			entries_sorted = []
			for key in sorted(entries.iterkeys(), reverse=True):
				entries_sorted.append(entries[key])
		
			# No more than 30 posts on the home page
			entries_sorted = entries_sorted[0:30]
		
			memcache.set(key_name, entries_sorted)
			return entries_sorted
	
	def fetch_blog_posts(self, force_miss = False):
		key_name = 'blog_posts'
		out = memcache.get(key_name)
		if out is not None and not force_miss:
			return out
		else:
			out = []
			
			query = Post.all()
			query.filter('date_published != ', None)
			query.order('-date_published')
			results = query.fetch(10)
			for result in results:
				result.published = result.date_published.strftime('%Y-%m-%dT%H:%M:%S')
				out.append(result)
			
			memcache.set(key_name, out)
			return out
	
	def fetch_twitter(self, force_miss = False):
		key_name = 'twitter_posts'
		out = memcache.get(key_name)
		if out is not None and not force_miss:
			return out
		else:
			url = 'http://twitter.com/statuses/user_timeline.atom?screen_name=Myles'
			d = feedparser.parse(url)
		
			out = []
			for item in d['items']:
				# parse @tweeter
				item['title'] = re.sub(
					r'@(\w+)',
					lambda x: "<a href='http://twitter.com/%s'>%s</a>"\
						% (x.group()[1:], x.group()),
					item['title'])

				# parse #hashtag
				item['title'] = re.sub(
					r'#(\w+)',
					lambda x: "<a href='http://twitter.com/search?q=%%23%s'>%s</a>"\
						% (x.group()[1:], x.group()),
					item['title'])
				
				out.append({
					'title': item['title'].replace('Myles: ', ''),
					'link': item['link'],
					'id': item['link'].replace('http://twitter.com/Myles/statuses/', ''),
					'published': item['published'][0:19], # 2010-02-06T17:17:27+00:00
					'published_dt': datetime.datetime.strptime(item['published'][0:19], '%Y-%m-%dT%H:%M:%S'),
					'type': 'twitter'
				})
		
			if len(out):
				memcache.set(key_name, out)
			return out
	
	def fetch_flickr(self, force_miss = False):
		key_name = 'flickr2_uploads'
		out = memcache.get(key_name)
		if out is not None and not force_miss:
			return out
		else:
			url = 'http://api.flickr.com/services/rest/?method=flickr.people.getPublicPhotos&api_key=d9cbb312cb2fed2a7c676f8803370472&user_id=35034347347%40N01&extras=date_upload,o_dims,original_format,media&format=json&nojsoncallback=1'
			result = urlfetch.fetch(url)
			
			out = []
			if result.status_code == 200:
				d = simplejson.loads(result.content)
				for photo in d['photos']['photo']:
					# {'title': 'Nap Time', 'farm': 3, 'server': '2595', 'secret': '3857b4e8f6', 'id': '4331496340', dateupload: '1265329153', o_width: '800', o_height: '600', originalsecret: '173b0a9a33', originalformat: 'jpg'}
						
					extension = photo['originalformat']
					size= 'o'
					width = int(photo['o_width'])
					height = int(photo['o_height'])
					ratio = float(height) / float(width)
					secret = photo['originalsecret']
					if width >= 1024 or height >= 1024:
						extension = 'jpg'
						size = 'b'
						secret = photo['secret']
						
						if width >= 1024:
							width = 1024
							height = int(width * ratio)
						else:
							height = 1024
							width = int(height * ratio)
					
					if width > 950:
						width = 950
						height = int(width * ratio)
						
					if photo['media'] == 'video':
						photo['is_video'] = True
						size = 'o'
						secret = photo['originalsecret']
						photo['playback_url'] = "http://www.flickr.com/photos/mylesdgrant/%s/play/hd/%s/" % (photo['id'], photo['secret'])
						logging.debug('fetch_flickr video: %s' % photo)
					else:
						photo['is_video'] = False
					
					photo['published'] = datetime.datetime.fromtimestamp(float(photo['dateupload'])).strftime('%Y-%m-%dT%H:%M:%S'),
					photo['published'] = photo['published'][0] #WTF!?
					photo['published_dt'] = datetime.datetime.strptime(photo['published'], '%Y-%m-%dT%H:%M:%S')
					photo['url'] = "http://farm%s.static.flickr.com/%s/%s_%s_%s.%s" % (photo['farm'], photo['server'], photo['id'], secret, size, extension)
					photo['width'] = width
					photo['height'] = height
					photo['ratio'] = ratio
					photo['type'] = 'flickr'
					out.append(photo)
		
				if len(out):
					memcache.set(key_name, out)
				
			return out


class Default404Handler(webapp.RequestHandler):

	def get(self):		
		self.error(404)
		path = os.path.join(os.path.dirname(__file__), 'templates', '404.html')
		self.response.out.write(template.render(path, {}))
def main():
	#logging.getLogger().setLevel(logging.DEBUG)
	urls = [
		(r'/braindump/older/([0-9]{4})/([0-9]{2})/([0-9]{2})/(.*).html', BlogPostHandler),
		(r'/braindump/?', BlogHandler),
		(r'/feed/?', BlogFeedHandler),
		('/atom.xml', BlogFeedHandler),
		(r'/twitter/([0-9]+)/?', TwitterPostHandler),
		(r'/twitter/?', TwitterHandler),
		(r'/flickr/([0-9]+)/?', FlickrPostHandler),
		(r'/flickr/?', FlickrHandler),
		('/games/', GamesHandler),
		('/', MainHandler),
		(r'/.*', Default404Handler)
	]
	application = webapp.WSGIApplication(urls,
	                                   debug=False)
	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()
