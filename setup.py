#!/usr/bin/python

import os
import glob
from distutils.core import setup

from DistUtilsExtra.command import *
from lib.constants import VERSION

for file in glob.glob('share/*.*'):
    os.chmod(file, 0644)

setup(name = 'gfeedline',
      version = VERSION,
      description = 'GFeedLine',
      long_description = 'A Social Networking Client',
      author = 'Yoshizumi Endo',
      author_email = 'y-endo@ceres.dti.ne.jp',
      url = 'http://code.google.com/p/gfeedline/',
      license = 'GPL3',
      package_dir = {'gfeedline' : 'lib'},
      packages = ['gfeedline', 'gfeedline.utils',
                  'gfeedline.preferences', 'gfeedline.twittytwister',
                  'gfeedline.plugins', 'gfeedline.plugins.twitter', ],
      scripts = ['gfeedline'],
      data_files = [('share/gfeedline', ['share/assistant_twitter.glade',
                                         'share/filters.glade',
                                         'share/feedsource.glade',
                                         'share/gfeedline.glade',
                                         'share/preferences.glade',
                                         'share/retweet.glade',
                                         'share/update.glade', ]),
                    ('share/gfeedline/html', 
                     [ 'share/html/default.css',
                       'share/html/base.html',
                       'share/html/retweet.png',
                       'share/html/gfeedline.js',
                       'share/html/scrollsmoothly.js', ]),
                    ('share/gfeedline/html/theme', 
                     [ 'share/html/theme/chat.html',
                       'share/html/theme/chat.css',
                       'share/html/theme/twitter.html',
                       'share/html/theme/twitter.css', ])],
      cmdclass = {"build" : build_extra.build_extra,
                  "build_i18n" : build_i18n.build_i18n,
                  "build_icons" : build_icons.build_icons}
      )
