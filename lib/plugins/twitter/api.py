#
# gfeedline - Gnome Social Feed Reader
#
# Copyright (c) 2012, Yoshizumi Endo.
# Licence: GPL3

import os
import sys
import re
from string import Template

import dateutil.parser
from BeautifulSoup import BeautifulStoneSoup
from gi.repository import GLib

from ...utils.usercolor import UserColor
from ...utils.settings import SETTINGS_TWITTER
from authtoken import AuthedTwitterRestAPI, AuthedTwitterFeedAPI, set_auth

user_color = UserColor()

class TwitterAPIToken(object):

    def __init__(self):
        self.api =  {
            'Home TimeLine':  TwitterAPIHomeTimeLine,
            'List TimeLine':  TwitterAPIListTimeLine,
            'Mentions': TwitterAPIMentions,
    
            'User Stream': TwitterAPIUserStream,
            'Track':  TwitterAPITrack,
            }

class TwitterAPIBase(object):

    def create_obj(self, view, params):
        obj = self.output(self.api, view, params)
        return obj

class TwitterAPIHomeTimeLine(TwitterAPIBase):

    def __init__(self, authed):
        self.api = authed.rest.home_timeline
        self.output = TwitterOutput
        self.name = 'Home TimeLine'

class TwitterAPIListTimeLine(TwitterAPIBase):

    def __init__(self, authed):
        self.api = authed.rest.list_timeline
        self.output = TwitterOutput
        self.name = 'List TimeLine'

class TwitterAPIMentions(TwitterAPIBase):

    def __init__(self, authed):
        self.api = authed.rest.mentions
        self.output = TwitterOutput
        self.name = 'Mentions'

class TwitterAPIUserStream(TwitterAPIBase):

    def __init__(self, authed):
        self.api = authed.feed.userstream
        self.output = TwitterFeedOutput
        self.name = 'User Stream'

class TwitterAPITrack(TwitterAPIBase):

    def __init__(self, authed):
        self.api = authed.feed.track
        self.output = TwitterFeedOutput
        self.name = 'Track'
    

class TwitterTime(object):

    def __init__(self, utc_str):
        dt = dateutil.parser.parse(utc_str)
        self.datetime = dt.replace(tzinfo=dateutil.tz.tzutc()
                                   ).astimezone(dateutil.tz.tzlocal())

    def get_local_time(self):
        return self.datetime.strftime('%H:%M:%S')

class TwitterOutput(object):

    def __init__(self, api, view=None, params={}):
        self.all_entries = []
        self.last_id = 0
        self.view = view.webview
        self.api = api
        self.params = params

        SETTINGS_TWITTER.connect("changed::access-secret", self._restart)

    def got_entry(self, msg, *args):
        self.all_entries.append(msg)

    def conv(self, text):
        return BeautifulStoneSoup(
            text, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)

    def print_all_entries(self):
        for entry in reversed(self.all_entries):
            self.print_entry(entry)
        self.all_entries = []

    def print_entry(self, entry):
        time = TwitterTime(entry.created_at)

        body = self._add_links_to_body(entry.text)
        body = body.replace('"', '&quot;')
        body = body.replace('\n', '<br>')

        template_file = os.path.abspath('html/status.html')
        file = open(template_file).read()
        temp = Template(unicode(file, 'utf-8', 'ignore'))
        text = temp.substitute(
            datetime=time.get_local_time(),
            id=entry.id,
            image_uri=entry.user.profile_image_url.replace('_normal.', '_mini.'),
            user_name=entry.user.screen_name,
            user_color=user_color.get(entry.user.id),
            status_body=body)

        #print text
        self.last_id = entry.id
        self.view.update(text)

    def _add_links_to_body(object, text):

        link_pattern = re.compile(r"(s?https?://[-_.!~*'a-zA-Z0-9;/?:@&=+$,%#]+)", re.IGNORECASE | re.DOTALL)
        nick_pattern = re.compile("\B@([A-Za-z0-9_]+|@[A-Za-z0-9_]$)")
        hash_pattern = re.compile(r'(\A|\s|\b)(?:#|\uFF03)([a-zA-Z0-9_\u3041-\u3094\u3099-\u309C\u30A1-\u30FA\u3400-\uD7FF\uFF10-\uFF19\uFF20-\uFF3A\uFF41-\uFF5A\uFF66-\uFF9E]+)')

        text = link_pattern.sub(r"<a href='\1'>\1</a>", text)
        text = nick_pattern.sub(r"<a href='https://twitter.com/\1'>@\1</a>", text)
        text = hash_pattern.sub(r"\1<a href='https://twitter.com/search?q=%23\2'>#\2</a>", text)

        return text

    def error(self, e):
        print e

    def start(self, interval=180):
        if not AuthedTwitterRestAPI.use_oauth:
            print "not authorized"
            return

        if self.last_id:
            self.params['since_id'] = str(self.last_id)

        api = self.api(self.got_entry, params=self.params)
        api.addErrback(self.error).addBoth(lambda x: self.print_all_entries())

        print AuthedTwitterRestAPI.rate_limit_remaining
        # print AuthedTwitterRestAPI.rate_limit_limit
        # print AuthedTwitterRestAPI.rate_limit_reset

        GLib.timeout_add_seconds(interval, self.start, interval)

    def _restart(self, *args):
        print "restart!"
        set_auth()
        self.start()

class TwitterFeedOutput(TwitterOutput):

    def got_entry(self, msg, *args):
        self.print_entry(msg)

    def conv(self, text):
        return text

    def start(self, interval=False):
        if not AuthedTwitterFeedAPI.use_oauth:
            return

        self.api(self.got_entry, self.params).\
            addErrback(self.error)#.\
#            addBoth(lambda x: self.print_entry())