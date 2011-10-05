from google.appengine.ext import webapp
import os
from google.appengine.ext.webapp import template


class GamesHandler(webapp.RequestHandler):

    def get(self):
        template_values = {
        }

        path = os.path.join(os.path.dirname(__file__), 'templates', 'games_index.html')
        self.response.out.write(template.render(path, template_values))
