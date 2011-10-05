from google.appengine.ext import webapp
import os, datetime, re
from google.appengine.ext.webapp import template
from google.appengine.api import memcache, urlfetch
from django.utils import simplejson


class TwitterPostHandler(webapp.RequestHandler):

    def get(self, id):
        template_values = {}

        status = self.fetch_twitter(id)
        if not status:
            self.error(404)
            path = os.path.join(os.path.dirname(__file__), 'templates', '404.html')
            self.response.out.write(template.render(path, template_values))
        else:
            template_values['status'] = status

            path = os.path.join(os.path.dirname(__file__), 'templates', 'twitter_post.html')
            self.response.out.write(template.render(path, template_values))

    def fetch_twitter(self, id):
        key_name = "twitter_post_%s" % id
        out = memcache.get(key_name)
        if out is None:
            url = "http://twitter.com/statuses/show/%s.json" % id
            result = urlfetch.fetch(url)

            if result.status_code == 200:
                d = simplejson.loads(result.content)

                # {"contributors":null,"in_reply_to_screen_name":null,"in_reply_to_user_id":null,"source":"<a href=\"http://www.atebits.com/\" rel=\"nofollow\">Tweetie</a>","created_at":"Sat Feb 13 01:33:45 +0000 2010","geo":null,"in_reply_to_status_id":null,"favorited":false,"user":{"geo_enabled":true,"description":"","profile_text_color":"000000","screen_name":"Myles","verified":false,"profile_background_image_url":"http://a3.twimg.com/profile_background_images/2623937/lion-2048x1536.jpg","url":"http://www.mylesgrant.com/","notifications":false,"profile_link_color":"0000ff","profile_background_tile":true,"created_at":"Thu Jul 20 15:59:48 +0000 2006","profile_background_color":"9ae4e8","followers_count":211,"time_zone":"Pacific Time (US & Canada)","friends_count":123,"profile_sidebar_fill_color":"e0ff92","protected":false,"statuses_count":1022,"location":"San Carlos, CA","name":"Myles","lang":"en","favourites_count":93,"profile_sidebar_border_color":"87bc44","id":2662,"contributors_enabled":false,"following":true,"utc_offset":-28800,"profile_image_url":"http://a1.twimg.com/profile_images/438135716/3557440086_d5667d6d00_m_normal.jpg"},"truncated":false,"id":9035284803,"text":"\"What is hiking? Is that like a game?\""}

                # parse @tweeter
                d['text'] = re.sub(
                    r'@(\w+)',
                    lambda x: "<a href='http://twitter.com/%s'>%s</a>"\
                        % (x.group()[1:], x.group()),
                    d['text'])

                # parse #hashtag
                d['text'] = re.sub(
                    r'#(\w+)',
                    lambda x: "<a href='http://twitter.com/search?q=%%23%s'>%s</a>"\
                        % (x.group()[1:], x.group()),
                    d['text'])

                out = {
                    'title': d['text'],
                    'link': "http://twitter.com/Myles/status/%s" % id,
                    'id': id,
                    'published': d['created_at'],  # Sat Feb 13 01:33:45 +0000 2010
                    'published_dt': datetime.datetime.strptime(d['created_at'], '%a %b %d %H:%M:%S +0000 %Y'),
                }

                memcache.set(key_name, out)
            else:
                return None

        return out


class TwitterHandler(webapp.RequestHandler):

    def get(self):
        self.redirect("http://www.twitter.com/myles", permanent=True)
