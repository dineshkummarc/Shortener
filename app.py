# -*- coding: utf-8 -*-
import base64
import datetime
import hmac
import sha
import time
import urllib
import urllib2

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

# Some Global Variables..

# Set to True if stack traces should be shown in the browser, etc.
_DEBUG = False
_GA_ID = 'UA-XXXXXXXX-X'

def make_request_uri(hostname, api_method, secret, **parameters):
  """Constructs a signed api request to the Short Links API.

  Args:
    hostname: the name of the domain that short links is installed at
    api_method: the api method to be called, like get_or_create_hash
    secret: the api (hmac) secret to be used
    parameters: additional arguments that should be passed to the api-method
  Returns:
    A signed URL that the short links server would understand.
  """
  # What is the url (without parameters)?
  base_url = 'http://%s/js/%s' % (hostname.lower(), api_method)

  # What is the base query string?
  parameters['oauth_signature_method'] = 'HMAC-SHA1'
  parameters['timestamp'] = str(
      time.mktime(datetime.datetime.now().timetuple()))
  param_array = [(k, v) for k, v in parameters.items()]
  param_array.sort()
  keyvals = ['%s=%s' % (urllib.quote(a, ''), urllib.quote(str(b), ''))
             for a, b in param_array]
  unsecaped = '&'.join(keyvals)
  signature_base_string = 'GET&%s&%s' % (
      urllib.quote(base_url, ''), urllib.quote(unsecaped, ''))

  # Create oauth secret
  signature = urllib.quote(base64.b64encode(
      hmac.new(secret, signature_base_string, sha).digest()), '')

  # Return the result
  return '%s?%s&oauth_signature=%s' % (base_url, unsecaped, signature)

def getQuote():
  """Returns a randomized quotation"""
  libraryFile=open('static/quotes.txt','r')
  library=libraryFile.readlines()
  return (random.choice(library)).split(';')


class PageHandler(webapp.RequestHandler):
  """Renders the Front Page."""

  def get(self,argument):
    """Callback for GET requests."""

    template_file = os.path.abspath('templates/index.html')
    
    quote=getQuote()
    
    vars = { 'quotation': quote[0],
             'quotation_author': quote[1],
             'quotation_link': quote[2],
             'title': argument or 'home',
             'analytics_id': _GA_ID ,
             }
    try:
    	rendered = webapp.template.render(template_file, vars, debug=_DEBUG)
    except:
    	rendered = webapp.template.render(template_fallback, vars, debug=_DEBUG)
    
    logging.info('Home Page accessed.')
    self.response.out.write(rendered)

class ShortenHandler(webapp.RequestHandler):
  """For the URL shorten request bullshit."""

  def get(self, argument):
    """Callback for GET requests."""

    template_file = os.path.abspath('templates/action.html')
    template_fallback = os.path.abspath('templates/ohshit.html')
    
    quote=getQuote()

    #options = parse_options() TODO
    for field in ('server', 'action', 'hmac', 'email', 'url', 'shortcut_name'):
        if getattr(options, field, None) is None:
            logging.warning('%s not set' % field)
            return
    request_url = make_request_uri(
        options.server,
        options.action,
        options.hmac,
        user=options.email,
        url=options.url,
        shortcut=options.shortcut_name,
        is_public=str(options.is_public).lower())

    logging.info('Connecting to %s...' % options.server)
    logging.info('(full request url is %s )' % request_url)
    try:
        response = urllib2.urlopen(request_url)
        logging.info('result: %s' % response.read())
    except:
        logging.warning('terrible shit happened... :(')

    
    vars = { 'quotation': quote[0],
             'quotation_author': quote[1],
             'quotation_link': quote[2],
             'title': 'home',
             'analytics_id': '',
             }
    try:
    	rendered = webapp.template.render(template_file, vars, debug=_DEBUG)
    except:
    	rendered = webapp.template.render(template_fallback, vars, debug=_DEBUG)
    
    logging.info('Home Page accessed.')
    self.response.out.write(rendered)


# Map url's to handlers
urls = [
    (r'/', PageHandler),
    (r'/make.*', ShortenHandler),
    (r'/hash.*', ShortenHandler),
]

application = webapp.WSGIApplication(urls, debug=_DEBUG)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
