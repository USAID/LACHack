#!/usr/bin/python

###############################################################################
# Access the twitter API using python. For more information about how to get
# set up with the API, see 
# https://github.com/USAID/LACHack/blob/master/Twitter_API.Rmd
#
# This requires installing the python-twitter package, which you will find at
# https://code.google.com/p/python-twitter/. You can get documentation by 
# running 'pydoc twitter.Api' or at:
# https://python-twitter.googlecode.com/hg/doc/twitter.html
#
# The installation is fairly painless, but requires you to install three other 
# packages which can be found at
# http://cheeseshop.python.org/pypi/simplejson 
# http://code.google.com/p/httplib2/
# http://github.com/simplegeo/python-oauth2
# 
# In each case, download the archive, extract to a directory, and run
#   python setup.py build
#   sudo python setup.py install
# and you should be ready to go!
###############################################################################

import twitter

# These are my (corrupted) Twitter access keys; replace with your own
key = 'aZolKBH3BUotTNpf5p1gk5SJ3'
secret = 'S8wSc8KNImq12Ho1ydkzM7HkUX3GRx13JkFipWli4Bvw0mP8ER'
access = '862564638-2vhtPUVAR5NVHzduKe9396jw1ipToSkT1k7KoFdQ'
access_secret = '1wH5xEwB6Y7PrtnTa6GNegFuDU6HOzIq17KMB0q3ib0e9Z'

# Connect to the API using your access keys
api = twitter.Api(consumer_key=key, consumer_secret=secret, 
        access_token_key=access, access_token_secret=access_secret)

# These are your credentials; they should look familiar
# see https://python-twitter.googlecode.com/hg/doc/twitter.html#Api-VerifyCredentials
cred = api.VerifyCredentials() 
print "Name:",cred.name
print "Screen name:",cred.screen_name
print "Location:",cred.location
print "Description:",cred.description
print "Recent post:",cred.status.text

# Let's see what people are saying about LACHack.
# see https://python-twitter.googlecode.com/hg/doc/twitter.html#Api-GetSearch
# Note that the documentation on googlecode.com seems to be a little out of
# date; I'd trust 'pydoc twitter.Api' more.
print
lachack = api.GetSearch(term="LACHack",count=5)
for x in lachack:
  print '@' + x.user.screen_name
  print x.text
  print

# We can also use geocodes, very similar to what we did in R. Looking
# again at San Pedro Sula, Honduras.
sps = api.GetSearch(geocode=(15.5,-88.03,"20km"),count=5)
for x in sps:
  print '@' + x.user.screen_name
  print x.text
  print

# This should be enough to get you started; please feel free to add to this 
# with more examples and tips!
