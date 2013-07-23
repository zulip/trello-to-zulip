#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from datetime import datetime
from time import sleep
import json
import os
import sys

import requests


DATE_FILE           = '.trello-to-zulip-date'
ZULIP_URL           = 'https://zulip.com/api/v1/messages'
ZULIP_SUBJECT_MAX   = 60

parser = ArgumentParser(description='Read actions from Trello and post to Zulip')
parser.add_argument('-a', '--all',      action='store_true',                help='read all available actions')
parser.add_argument('-n', '--no-post',  action='store_true',                help='do not post messages')
parser.add_argument('-o', '--once',     action='store_true',                help='read actions once and exit')
parser.add_argument('-v', '--verbose',  action='store_true',                help='verbose progress output')
parser.add_argument('-c', '--config',   metavar='C', type=FileType('r'),    help='file to load settings (ENV takes priority)') 
parser.add_argument('-s', '--sleep',    metavar='S', type=int, default=60,  help='seconds to sleep between reading (default: 60)')
parser.add_argument('file',             type=FileType('r'), nargs='*',      help='read from file(s) instead of Trello')

ARGS = parser.parse_args()


def shorten_subject(s):
    if len(s) > ZULIP_SUBJECT_MAX:
        return s[:ZULIP_SUBJECT_MAX - 3] + '...'
    return s

def verbose(s):
    if ARGS.verbose:
        print str(s)

def stderr(s):
    sys.stderr.write(s)
    sys.stderr.write('\n')


class Config(object):
    def __init__(self):
        self.params = {}
        primary = os.environ
        secondary = {}
        if ARGS.config:
            secondary = json.loads(ARGS.config.read())
            ARGS.config.close()
        settings = ['TRELLO_KEY', 'TRELLO_TOKEN', 'TRELLO_ORG', 'ZULIP_EMAIL', 'ZULIP_KEY', 'ZULIP_STREAM']
        for s in settings:
            if s in primary:
                self.params[s] = primary[s]
            elif s in secondary:
                self.params[s] = secondary[s]
            else:
                stderr("Setting not present in config: %s" % (s,))
                sys.exit(1)
    #
    # Config parameters
    #
    def trello_key(self):
        return self.params['TRELLO_KEY']
    def trello_token(self):
        return self.params['TRELLO_TOKEN']
    def trello_org(self):
        return self.params['TRELLO_ORG']
    def zulip_email(self):
        return self.params['ZULIP_EMAIL']
    def zulip_key(self):
        return self.params['ZULIP_KEY']
    def zulip_stream(self):
        return self.params['ZULIP_STREAM']
    #
    # Derived
    #
    def trello_url(self):
        return 'https://api.trello.com/1/organization/%s' % (self.trello_org(),)
    def zulip_auth(self):
        return (self.zulip_email(), self.zulip_key())


CONFIG = Config()


class Action(object):
    def __init__(self, json):
        self.json = json
    def __getitem__(self, key):
        return self.json[key]
    def type(self):
        return self.json['type']
    def date(self):
        return self.json['date']
    def data(self):
        return self.json['data']
    def board_name(self):
        return self.data()['board']['name']
    def has_board_name(self):
        data = self.data()
        return ('board' in data) and ('name' in data['board'])
    def has_card_name(self):
        data = self.data()
        return ('card' in data) and ('name' in data['card'])
    def card_name(self):
        return self.data()['card']['name']
    def board_url(self):
        #return '[%s](https://trello.com/board/%s)' % (board['name'], board['id'])
        board = self.data()['board']
        return 'https://trello.com/board/%s' % (board['id'],)
    def card_url(self):
        card = self.data()['card']
        return 'https://trello.com/c/%s' % (card['id'],)
    def creator_name(self):
        member = self.json.get('memberCreator', None)
        if member is None:
            return '<unknown>'
        return member['fullName']
    def derive_subject(self):
        subject = '<unknown>'
        if self.has_card_name():
            subject = self.card_name()
        elif self.has_board_name():
            subject = self.board_name()
        return shorten_subject(subject)


class ActionPrinter(object):
    # 
    # Helpers
    #
    def get_message(self, action):
        t = action.type()
        handler = getattr(self, t, None)
        if handler is None:
            handler = self._unknown_action
        msg = handler(action)
        return msg
    #
    # Methods map directly to action name and used for lookup.
    # No direct documentation, but list of names here:
    # https://trello.com/docs/api/board/index.html
    #
    def _unknown_action(self, a):
        if a.has_board_name():
            name = a.board_name()
            url = a.board_url()
        if a.has_card_name():
            name = a.card_name()
            url = a.card_url()
        return '%s performed %s on [%s](%s)' % (
            a.creator_name(),
            a.type(),
            name,
            url
        )
    def addAttachmentToCard(self, a):
        attachment = a.data()['attachment']
        return '%s added [%s](%s) attachment to card [%s](%s)' % (
            a.creator_name(),
            attachment['name'],
            attachment['url'],
            a.card_name(),
            a.card_url()
        )
    def addChecklistToCard(self, a):
        return '%s added checklist **%s** to card [%s](%s)' % (
            a.creator_name(),
            a.data()['checklist']['name'],
            a.card_name(),
            a.card_url()
        )
    def addMemberToBoard(self, a):
        # Contains ['data']['idMemberAdded'] if we wanted to look it up
        return None
    def addMemberToCard(self, a):
        return '%s added **%s** to card [%s](%s)' % (
            a.creator_name(),
            a['member']['fullName'],
            a.card_name(),
            a.card_url()
        )
    def createBoard(self, a):
        return '%s created board [%s](%s)' % (
            a.creator_name(),
            a.board_name(),
            a.board_url()
        )
    def createCard(self, a):
        return '%s created card [%s](%s)' % (
            a.creator_name(),
            a.card_name(),
            a.card_url()
        )
    def createList(self, a):
        return '%s created list **%s** on board [%s](%s)' % (
            a.creator_name(),
            a.data()['list']['name'],
            a.board_name(),
            a.board_url()
        )
    def commentCard(self, a):
        state = 'commented'
        if a.data().get('dateLastEdited', None) is not None:
            state = 'edited comment'
        return '%s %s on card [%s](%s) \n>%s\n\n' % (
            a.creator_name(),
            state,
            a.card_name(),
            a.card_url(),
            a.data()['text'].replace('\n', '\n>')
        )
    def moveCardToBoard(self, a):
        # Any card move is also going to trigger a moveCardFromBoard
        # event, which will report what we want.
        pass
    def moveCardFromBoard(self, a):
        return '%s moved card [%s](%s) from **%s** to **%s**' % (
            a.creator_name(),
            a.card_name(),
            a.card_url(),
            a.board_name(),
            a.data()['boardTarget']['name']
        )
    def removeMemberFromCard(self, a):
        return '%s removed **%s** from card [%s](%s)' % (
            a.creator_name(),
            a['member']['fullName'],
            a.card_name(),
            a.card_url()
        )
    def updateBoard(self, a):
        # Many possibilities, signified through contents of a.data()['old']
        old = a.data()['old']
        name = old.get('name', None)
        if name is not None:
            return '%s renamed from **%s** to **%s**' % (
                a.creator_name(),
                name,
                a.board_name()
            )
        return self._unknown_action(a)
    def updateCard(self, a):
        # Many possibilities, signified through contents of a.data()['old']
        old = a.data()['old']
        id_list = old.get('idList', None)
        if id_list is not None:
            return '%s moved card [%s](%s) from **%s** to **%s**' % (
                a.creator_name(),
                a.card_name(),
                a.card_url(),
                a.data()['listBefore']['name'],
                a.data()['listAfter']['name']
            )
        closed = old.get('closed', None)
        if closed is not None:
            new_state = a.data()['card']['closed'] and 'archived' or 're-opened' 
            return '%s %s card [%s](%s)' % (
                a.creator_name(),
                new_state,
                a.card_name(),
                a.card_url()
            )
        name = old.get('name', None)
        if name is not None:
            return '%s renamed card from **%s** to [%s](%s)' % (
                a.creator_name(),
                name,
                a.card_name(),
                a.card_url()
            )
        desc = old.get('desc', None)
        if desc is not None:
            # Note: new description is not included
            return '%s updated description for card [%s](%s)' % (
                a.creator_name(),
                a.card_name(),
                a.card_url()
            )
        due = old.get('due', False)
        if due is not False:
            new_due = a.data()['card']['due']
            state = 'added due date **%s** to' % (new_due,)
            if new_due is None:
                state = 'removed due date from'
            return '%s %s card [%s](%s)' % (
                a.creator_name(),
                state,
                a.card_name(),
                a.card_url()
            )
        pos = old.get('pos', None)
        if pos is not None:
            # Always accompanies a list move, so just ignore
            return None
        return self._unknown_action(a)
    def updateCheckItemStateOnCard(self, a):
        checked_state = 'checked'
        if a.data()['checkItem']['state'] == 'incomplete':
            checked_state = 'unchecked'
        return '%s %s  **%s** on card [%s](%s)' % (
            a.creator_name(),
            checked_state,
            a.data()['checkItem']['name'],
            a.card_name(),
            a.card_url()
        )


class Loader(object):
    def __init__(self):
        self.last_date = None

    def _load_date(self):
        date = datetime.utcnow().isoformat() + 'Z'
        try:
            with open(DATE_FILE) as f:
                date = f.read()
        except IOError:
            pass
        return date

    def _save_date(self, date_str):
        if not ARGS.no_post:
            self.last_date = date_str
            with open(DATE_FILE, 'w') as f:
                f.write(date_str)

    def _from_files(self):
        for f in ARGS.file:
            text = f.read()
            f.close()
            yield text

    def _from_trello(self):
        post_params = {
            'key' : CONFIG.trello_key(),
            'token' : CONFIG.trello_token(),
            'actions' : 'all',
            'actions_limit' : '1000',
            'fields' : 'none',
            'boards' : 'organization',
            'board_fields' : 'name',
            'board_actions' : 'all',
            'board_actions_limit' : '1000',
            'board_actions_since' : None # Replaced in run loop
        }
        if ARGS.all:
            verbose('Loading all available actions')
            self.last_date = '1970-01-01T00:00:00Z'
        else:
            self.last_date = self._load_date()
            verbose('Loading actions since %s' % (self.last_date,))
        first = True
        while first or (not ARGS.once):
            if not first:
                if self.last_date is not None:
                    self._save_date(self.last_date)
                try:
                    sleep(ARGS.sleep)
                except KeyboardInterrupt:
                    # Silence stack trace
                    print ''
                    sys.exit(0)
            else:
                first = False
            if self.last_date is not None:
                post_params['board_actions_since'] = self.last_date
            r = requests.get(CONFIG.trello_url(), params=post_params)
            if r.status_code == 200:
                yield r.text.encode('utf-8')
            else:
                stderr('Error making Trello request: %d %s' % (r.status_code, r.text))

    def load_func(self):
        if ARGS.file:
            func = self._from_files
        else:
            func = self._from_trello
        for t in func():
            yield t

    def saw_action(self, action):
        if not ARGS.file:
            self.last_date = action.date()

#
# Run loop
#
printer = ActionPrinter()
loader = Loader()
for json_text in loader.load_func():
    verbose(json_text)
    json_dict = json.loads(json_text)
    boards = json_dict['boards']
    actions = []
    for b in boards:
        actions = actions + b['actions']
    actions.sort(lambda x,y: cmp(x['date'], y['date']))
    for a in actions:
        action = Action(a)
        loader.saw_action(action)
        msg = printer.get_message(action)
        if msg is None:
            continue
        verbose(msg.replace('\n', '\t'))
        post_params = {
            'type' : 'stream',
            'to' : CONFIG.zulip_stream(),
            'subject' : action.derive_subject(),
            'content' : msg
        }
        if not ARGS.no_post:
            r = requests.post(ZULIP_URL, auth=CONFIG.zulip_auth(), data=post_params)
            if r.status_code != 200:
                stderr('Error %d POSTing to Zulip: %s' % (r.status_code, r.text))
    sys.stdout.flush()

