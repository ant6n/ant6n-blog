#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Ant6n'
SITENAME = u'Ant6n'
SITESUBTITLE = 'Dubrau'
SITEURL = 'http://ant6n.ca'

PATH = 'content'

TIMEZONE = 'America/Montreal'

DEFAULT_LANG = u'en'
DEFAULT_CATEGORY = 'blog'
DEFAULT_DATE_FORMAT = '%a %Y-%b-%d'

DEFAULT_METADATA = {
    'status': 'draft',
}

# Feed generation is usually not desired when developing
#FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# article url definitions
ARTICLE_URL = '{date:%Y}-{date:%m}-{date:%d}-{slug}'
ARTICLE_SAVE_AS = '{date:%Y}-{date:%m}-{date:%d}-{slug}/index.html'

PAGE_URL = 'pages/{slug}/'
PAGE_SAVE_AS = 'pages/{slug}/index.html'

CATEGORY_URL = 'category/{slug}/'
CATEGORY_SAVE_AS = 'category/{slug}/index.html'

TAG_URL = 'tag/{slug}/'
TAG_SAVE_AS = 'tag/{slug}/index.html'

TAGS_URL = 'tags.html'
TAGS_SAVE_AS = 'tags.html'

# archives
YEAR_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/{date:%b}/index.html'

# path specific metadata
STATIC_PATHS = ['images', 'extra/robots.txt', 'extra/favicon.png']
EXTRA_PATH_METADATA = {
    'extra/robots.txt': {'path': 'robots.txt'},
    'extra/favicon.png': {'path': 'favicon.png'}
}


# set up menu
DISPLAY_CATEGORIES_ON_MENU = False
DISPLAY_PAGES_ON_MENU = False

MENUITEMS = (
    ('Home', '/'),
    ('About Me','/pages/about-me/'),
    ('Projects','/pages/projects/'),
    ('Archives', '/archives.html'),
    #('Tags', '/tags.html'),
)



TYPOGRIFY = True


# Blogroll
#LINKS = (('Pelican', 'http://getpelican.com/'),
#         ('Python.org', 'http://python.org/'),
#         ('Jinja2', 'http://jinja.pocoo.org/'),
#         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (
#    ('github', 'http://github.com/Ant6n'),
    ('twitter', 'http://twitter.com/Ant6n'),

    #('You can add links in your config file', '#'),
    #('Another social link', '#'),
)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

# pelican-octropress-theme settings
THEME = 'themes/notmyidea'
#THEME = 'pelican-octopress-theme'
TWITTER_USER = 'ant6n'
FACEBOOK_LIKE = False
TWITTER_TWEET_BUTTON = True
TWITTER_FOLLOW_BUTTON = False
GOOGLE_PLUS_ONE = True
GOOGLE_ANALYTICS = 'UA-31803699-1'

TWITTER_USERNAME = 'ant6n'
