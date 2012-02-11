# -*- coding: utf-8 -*-

# for initializing oAuth token
import base64
import hmac
import sha

# for preparing timestamp
import datetime
import time

# escaping URL params
import urllib

# connecting to Short Links server
import urllib2

# environment vars
import os

import random
import logging

# webapp utilities
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

# Some Global Variables.
_DEBUG = False                  # Set to True if stack traces should be shown in the browser, etc
_GA_ID = 'UA-XXXXXXXX-X'        # Google Analytics Code
_EMAIL = 'diwank-admin@diwank.name'    # Your email account
_CNAME = 'singh'                # Domain CNAME where Short Links is installed (NOT this app!)
_PUBLIC_FLAG = True             # Whether shrtnr links are public or require signin


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
  # the url (without parameters)
  base_url = 'http://%s/js/%s' % (hostname.lower(), api_method)

  # the base query string
  parameters['oauth_signature_method'] = 'HMAC-SHA1'
  parameters['timestamp'] = str(time.mktime(
                                    datetime.datetime.now().timetuple()))

  # extract parameters as (key, value) pairs
  param_array = [(k, v) for k, v in parameters.items()]
  param_array.sort()

  key_val_pairs = ['%s=%s' % (urllib.quote(a, ''),
                              urllib.quote(str(b), '')
                              )
                   for a, b in param_array
                   ]

  # building params string
  param_string = '&'.join(key_val_pairs)
  signature_base_string = 'GET&%s&%s' % (urllib.quote(base_url, ''),
                                         urllib.quote(param_string, '')
                                         )

  # Create oauth secret
  signature = urllib.quote(base64.b64encode(
                              hmac.new(secret, signature_base_string, sha).digest()), '')

  # Return the result
  return '%s?%s&oauth_signature=%s' % (base_url, param_string, signature)



def getQuote():
  """Returns an awesome randomized quotation."""
  libraryFile=open('static/quotes.txt','r')
  library=libraryFile.readlines()
  return (random.choice(library)).split(';')


class PageHandler(webapp.RequestHandler):
  """Renders the Front Page."""

  def get(self):
    """Callback for GET requests to / ."""

    # template variables
    template_file = os.path.abspath('templates/index.html')
    
    quote=getQuote()

    vars = { 'quotation': quote[0],
             'quotation_author': quote[1],
             'quotation_link': quote[2],
             'title': 'Shrtnr: ' + 'home',
             'analytics_id': _GA_ID ,
             }
    
    rendered = webapp.template.render(template_file, vars, debug=_DEBUG)
    
    logging.info('Ze Home Page waz accessed... recently. :P')
    
    self.response.out.write(rendered)

class ShortenHandler(webapp.RequestHandler):
  """For the URL shorten request bullshit."""

  def get(self, request):
    """Callback for GET requests to the rest.
            Args:
             - request: the request. [Sigh.]
    """
    
    # divide and rule. ;)
    arguments = request.lower().split('/')
    
    # dirty hack #1: stupid url-params extension
    while len(arguments) < 4:
        arguments.append('doesnotexist')
    
    # allowed action requests
    actions = {}
    actions['make'] = 'get_or_create_shortlink'
    actions['hash'] = 'get_or_create_hash'
    actions['blah'] = 'get_details'

    # setting up the field
    ## TODO: As of this writing, We ain't filtering requests from idiots.
    ## Beware: Dangerous stuff is coming through.
    options = {}
    options['hmac'] = arguments[0]
    options['server'] = _CNAME + '.' + os.environ['SERVER_NAME']
    
    if arguments[1] not in actions.keys(): arguments[1] = 'blah'
    options['action'] = actions[arguments[1]]
    
    options['shortcut'] = arguments[2]
    options['url'] = 'http://' + '/'.join(arguments[3:])   # to catch the entire url: www.path.to/subdir
    options['user'] = _EMAIL
    options['is_public'] = _PUBLIC_FLAG

    # just-in-case..
    for field in ('server', 'action', 'hmac', 'user', 'url', 'shortcut'):
        if not options[field]:
            logging.warning('%s not set' % field)
            return

    # preparing the request
    request_url = make_request_uri(
                        options['server'],
                        options['action'],
                        options['hmac'],
                        user=options['user'],
                        url=options['url'],
                        shortcut=options['shortcut'],
                        is_public=str(options['is_public']).lower())

    logging.info('(full request url is %s )' % request_url)
    
    # here we go!
    try:
        logging.info('Connecting to %s...' % options['server'])
        response = urllib2.urlopen(request_url)
        logging.info('Ze request resulted in ze following mess:\n %s' % response.read())
        logging.info('LOL!')
    except:
        logging.warning('terrible shit happened... :(')
        response = open('static/sucks.txt','r')             # response has to have a read() function

    # template variables
    template_file = os.path.abspath('templates/action.html')
    template_fallback = os.path.abspath('templates/ohshit.html')

    quote=getQuote()

    vars = { 'quotation': quote[0],
             'quotation_author': quote[1],
             'quotation_link': quote[2],
             'title': 'Shrtnr - ' + arguments[1],
             'analytics_id': _GA_ID,
             'response': response.read()
             }

    try:
    	rendered = webapp.template.render(template_file, vars, debug=_DEBUG)
    except:
        logging.error('Webapp is an Ass. Couldn\'t even load a template.')
    	rendered = webapp.template.render(template_fallback, vars, debug=_DEBUG)
    
    logging.info('Some bloke tried to initiate a ' + arguments[1] + ' ' + arguments[1] + ' on ' + arguments[2])
    logging.info('Meh!')
    
    self.response.out.write(rendered)


# Map url's to handlers
urls = [
    (r'/', PageHandler),        # serves the index page
    (r'/(.+)', ShortenHandler), # handles actions
]

application = webapp.WSGIApplication(urls, debug=_DEBUG)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
