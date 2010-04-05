from google.appengine.ext import webapp
import os, datetime, time, logging
from google.appengine.ext.webapp import template
from google.appengine.api import memcache, urlfetch
from django.utils import simplejson

class FlickrPostHandler(webapp.RequestHandler):

	def get(self, id):	
		template_values = {}
		
		photo = self.get_photo(id)
		if not photo or photo['invalid']:
			self.error(404)
			path = os.path.join(os.path.dirname(__file__), 'templates', '404.html')
			self.response.out.write(template.render(path, template_values))
		else:
			template_values['photo'] = photo
	
			path = os.path.join(os.path.dirname(__file__), 'templates', 'flickr_post.html')
			self.response.out.write(template.render(path, template_values))
	
	def get_photo(self, id, force_miss = False):
		key_name = "flickr2_photo_%s" % id
		photo = memcache.get(key_name)
		if photo is None or force_miss:
			url = "http://api.flickr.com/services/rest/?method=flickr.photos.getInfo&api_key=d9cbb312cb2fed2a7c676f8803370472&photo_id=%s&format=json&nojsoncallback=1" % id
			result = urlfetch.fetch(url)
			#logging.debug('get_photo urlfetch result: %s' % result.status_code)
		
			if result.status_code == 200:
				d = simplejson.loads(result.content)
				#logging.debug('get_photo simplejson: %s' % d)
				if d['stat'] == 'ok':
					photo = d['photo']
			
					if photo['owner']['nsid'] == "35034347347@N01":
						# {"photo":{"id":"4350641052", "secret":"56e1969636", "server":"2683", "farm":3, "dateuploaded":"1265948259", "isfavorite":0, "license":"1", "rotation":0, "originalsecret":"f4fa1fe264", "originalformat":"jpg", "owner":{"nsid":"35034347347@N01", "username":"Myles!", "realname":"Myles Grant", "location":"San Carlos, CA, United States"}, "title":{"_content":"They give him magical powers"}, "description":{"_content":""}, "visibility":{"ispublic":1, "isfriend":0, "isfamily":0}, "dates":{"posted":"1265948259", "taken":"2010-02-11 20:12:48", "takengranularity":"0", "lastupdate":"1265962983"}, "views":"86", "editability":{"cancomment":0, "canaddmeta":0}, "usage":{"candownload":1, "canblog":0, "canprint":0, "canshare":0}, "comments":{"_content":"3"}, "notes":{"note":[]}, "tags":{"tag":[{"id":"5930-4350641052-1486", "author":"35034347347@N01", "raw":"moblog", "_content":"moblog", "machine_tag":0}, {"id":"5930-4350641052-176591", "author":"35034347347@N01", "raw":"iphone", "_content":"iphone", "machine_tag":0}, {"id":"5930-4350641052-52127784", "author":"26887305@N00", "raw":"Cal 'Lucky Charms' Henderson", "_content":"calluckycharmshenderson", "machine_tag":0}, {"id":"5930-4350641052-8178032", "author":"60065287@N00", "raw":"they're magically delicious", "_content":"theyremagicallydelicious", "machine_tag":0}]}, "location":{"latitude":37.787166, "longitude":-122.416667, "accuracy":"16", "context":"0", "neighbourhood":{"_content":"Lower Nob Hill", "place_id":"m.idZT6cBJWOMx65IA", "woeid":"55970959"}, "locality":{"_content":"San Francisco", "place_id":"kH8dLOubBZRvX_YZ", "woeid":"2487956"}, "county":{"_content":"San Francisco", "place_id":"hCca8XSYA5nn0X1Sfw", "woeid":"12587707"}, "region":{"_content":"California", "place_id":"SVrAMtCbAphCLAtP", "woeid":"2347563"}, "country":{"_content":"United States", "place_id":"4KO02SibApitvSBieQ", "woeid":"23424977"}, "place_id":"m.idZT6cBJWOMx65IA", "woeid":"55970959"}, "geoperms":{"ispublic":1, "iscontact":0, "isfriend":0, "isfamily":0}, "urls":{"url":[{"type":"photopage", "_content":"http:\/\/www.flickr.com\/photos\/mylesdgrant\/4350641052\/"}]}, "media":"photo"}, "stat":"ok"}
		
						photo['invalid'] = 0
						
						sizes = self.get_sizes(id, force_miss)
						original = sizes[len(sizes)-1]
							
						if photo.has_key('video'):
							photo['is_video'] = True
							photo['playback_url'] = original['source']
							photo['url'] = sizes[4]['source']
							
							photo['width'] = int(original['width'])
							photo['height'] = int(original['height'])
						else:
							photo['is_video'] = False
							
							if int(original['width']) >= 1024 or int(original['height']) >= 1024:
								large = sizes[len(sizes)-2]
								photo['url'] = large['source']
								photo['width'] = int(large['width'])
								photo['height'] = int(large['height'])
							else:
								photo['url'] = original['source']
								photo['width'] = int(original['width'])
								photo['height'] = int(original['height'])

						if photo['width'] > 950:
							photo['height'] = int(950 * float(photo['height']) / float(photo['width']))
							photo['width'] = 950
						
						photo['published'] = datetime.datetime.fromtimestamp(float(photo['dateuploaded'])).strftime('%Y-%m-%dT%H:%M:%S'),
						photo['published'] = photo['published'][0] #WTF!?
						photo['published_dt'] = datetime.datetime.strptime(photo['published'], '%Y-%m-%dT%H:%M:%S')
						photo['title'] = photo['title']['_content']
					else:
						photo['invalid'] = 1
					
					logging.debug('get_photo photo: %s' % photo)
						
					memcache.set(key_name, photo)
				else:
					return None
			else:
				return None
						
		return photo
	
	def get_sizes(self, id, force_miss = False):
		key_name = "flickr2_sizes_%s" % id
		sizes = memcache.get(key_name)
		if sizes is None or force_miss:
			url = "http://api.flickr.com/services/rest/?method=flickr.photos.getSizes&api_key=d9cbb312cb2fed2a7c676f8803370472&photo_id=%s&format=json&nojsoncallback=1" % id
			result = urlfetch.fetch(url)
			#logging.debug('get_sizes urlfetch result: %s' % result.status_code)
		
			if result.status_code == 200:
				d = simplejson.loads(result.content)
				#logging.debug('get_sizes simplejson result: %s' % d)
				if d['stat'] == 'ok':
					sizes = d['sizes']['size']
			
					# {"sizes":{"canblog":0, "canprint":0, "candownload":1, "size":[{"label":"Square", "width":75, "height":75, "source":"http:\/\/farm3.static.flickr.com\/2683\/4350641052_56e1969636_s.jpg", "url":"http:\/\/www.flickr.com\/photos\/mylesdgrant\/4350641052\/sizes\/sq\/", "media":"photo"}, {"label":"Thumbnail", "width":"100", "height":"75", "source":"http:\/\/farm3.static.flickr.com\/2683\/4350641052_56e1969636_t.jpg", "url":"http:\/\/www.flickr.com\/photos\/mylesdgrant\/4350641052\/sizes\/t\/", "media":"photo"}, {"label":"Small", "width":"240", "height":"180", "source":"http:\/\/farm3.static.flickr.com\/2683\/4350641052_56e1969636_m.jpg", "url":"http:\/\/www.flickr.com\/photos\/mylesdgrant\/4350641052\/sizes\/s\/", "media":"photo"}, {"label":"Medium", "width":"500", "height":"375", "source":"http:\/\/farm3.static.flickr.com\/2683\/4350641052_56e1969636.jpg", "url":"http:\/\/www.flickr.com\/photos\/mylesdgrant\/4350641052\/sizes\/m\/", "media":"photo"}, {"label":"Original", "width":"800", "height":"600", "source":"http:\/\/farm3.static.flickr.com\/2683\/4350641052_f4fa1fe264_o.jpg", "url":"http:\/\/www.flickr.com\/photos\/mylesdgrant\/4350641052\/sizes\/o\/", "media":"photo"}]}, "stat":"ok"}
					
					memcache.set(key_name, sizes)
				else:
					return None
			else:
				return None
			
		return sizes
		
class FlickrHandler(webapp.RequestHandler):

	def get(self):
		self.redirect("http://www.flickr.com/photos/mylesdgrant/", permanent=True)