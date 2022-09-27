#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 11:02:46 2017

@author: tina
"""
import logging
import time
from slackclient import SlackClient
from archstats import stats
# import configparser
# from elasticapm import Client
# import elasticapm
# elasticapm.instrument()
# elasticapm.set_transaction_name('processor')
# elasticapm.set_transaction_result('SUCCESS')
# from elasticapm.handlers.logging import LoggingHandler

from viaa.configuration import ConfigParser

# config = ConfigParser()
config = ConfigParser(config_file="config.yml")

bot_id = config.app_cfg['slack_api']['bot_id']
client_token = config.app_cfg['slack_api']['client_token']


def clean_up_exit():
    handlers = LOGGER.handlers[:]
    for handler in handlers:
        handler.close()
        LOGGER.removeHandler(handler)
# constants


BOT_ID = bot_id
AT_BOT = "<@" + BOT_ID + ">"
ALL = "all"
DAY = 'day'
WEEK = 'week'
MONTH = 'month'
VIDEO = 'video'
AUDIO = 'audio'
OTHER = 'other'
GB = 'count'
# instantiate Slack & Twilio clients
# slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
slack_client = SlackClient(client_token)


class plt(object):
    def __init__(self, ptype, days=2):
        self.ptype = ptype
        self.days = days

    # @elasticapm.capture_span()
    def Post(self):

        if self.ptype == 'status_plot':
            stats().Status(Plot=True)
        if self.ptype == 'status_countPlot':
            stats().Status(countPlot=True)
        if self.ptype == 'plot':
            stype = 'plot'
            stats(stype=stype, days=self.days).Plot()
        if self.ptype == 'workflow':
            stype = 'workflowplot'
            stats(stype=stype, days=self.days).Plot()
        if self.ptype == 'cpplot':
            stype = 'cpplot'
            stats(stype=stype, days=self.days).Plot()
        try:
            f = open('/tmp/plot.png', 'rb')
            slack_client.api_call('files.upload', channels='G72H2N1CN',
                                  filename='pic.png', file=f)
        except Exception as e:
            return {'info': 'no file to upload',
                    'error': str(e)
                    }

# @elasticapm.capture_span()


def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# @elasticapm.capture_span()


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """

    response = ''
    plot = False
    video = False
    audio = False
    other = False
    total = False
    found_nr = False
    days = 7
    workflowplot = False
    cpplot = False
    stype = 'workflow'
    lst = command.split()
    for i in lst:
        if representsInt(i):
            found_nr = True
            days = int(i)
            LOGGER.info('found int setting days to: {}'.format(str(days)))
    if command.startswith('help'):
        response = "Usage: @archsbot " + "possible_args*['plot', 'workflowplot',"\
            "'cpplot', 'status', 'int(nr of days)']' OR [audio,video,other,count(sum of sizes)]  followed by nr of days"

    if 'plot' in lst:
        LOGGER.info('Found plot in command')
        plot = True
#    if command.startswith('plot') and not command.endswith('workflow'):
#        plot = True
    if 'workflowplot' in lst:
        workflowplot = True
    if 'cpplot' in lst:
        cpplot = True
    if command.startswith(VIDEO):
        video = True
    if command.startswith(AUDIO):
        audio = True
    if command.startswith(OTHER):
        other = True
    if command.startswith(ALL):
        total = True
    if command.startswith(GB):
        stype = 'all'
    if 'status' in lst and 'plot' not in lst and 'plotcount' not in lst:
        response = stats().Status()
    if 'status' in lst and 'plot' in lst:
        plt(ptype='status_plot', days=0).Post()
    if 'status' in lst and 'plotcount' in lst:
        plt(ptype='status_countPlot', days=0).Post()

    def makeResponse():
        if plot:
            plt(ptype='plot', days=days).Post()
        if workflowplot:
            plt(ptype='workflow', days=days).Post()
        if cpplot:
            plt(ptype='cpplot', days=days).Post()
        if video or audio or other or total or stype == 'all':
            response = stats(stype=stype, days=days, video=video, audio=audio,
                             other=other, total=total).Fetch()
            return slack_client.api_call("chat.postMessage", channel=channel,
                                         text=response, as_user=True)
    if command.endswith(DAY):
        days = 1
        makeResponse()

    if command.endswith(WEEK):
        days = 7
        makeResponse()
    if command.endswith(MONTH):
        days = 30
        makeResponse()
    if command.endswith('today'):
        days = 0
        makeResponse()
    if found_nr:
        makeResponse()

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


# @elasticapm.capture_span()
def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                LOGGER.info('got input to parse: {}'.format(output_list))
                # return text after the @ mention, whitespace removed
                o = output['text'].split(AT_BOT)[1].strip().lower(),\
                    output['channel']
                # client.capture_message('processed %s' % output['text'])
                return o
    return None, None


if __name__ == "__main__":
    LOGGER = logging.getLogger(__name__)

    LOG_FORMAT = ('%(asctime)-15s %(levelname) -5s %(name) -5s %(funcName) '
                  '-3s %(lineno) -5d: %(message)s')
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
    # client = Client({'SERVICE_NAME': 'archbot',
    #              'DEBUG': True,
    #              'SERVICE_NAME': 'archbot',
    #              'SECRET_TOKEN': 'aC00NFNJRUJTSVdreTlNT2hsaGs6VHp6cWhQSV9Tb21YTGVxT1MyWU1kdw==',
    #              'SERVER_URL': 'http://do-prd-elk-01:8200'} )
    # handler = LoggingHandler(client=client)
    # handler.setLevel(logging.WARN)
    # logging.getLogger('elasticapm').setLevel('INFO')
    # LOGGER.addHandler(handler)

    formatter = logging.Formatter('%(asctime)-15s  %(levelname)-6s:'
                                  '%(message)s')
    logging.basicConfig(format=formatter, level=logging.INFO)

    try:
        READ_WEBSOCKET_DELAY = 1  # 1 second delay reading from firehose
        if slack_client.rtm_connect():
            LOGGER.info("Bot connected and running!")
            # client.capture_message("message":"connected the bot." )
            while True:
                command, channel = parse_slack_output(slack_client.
                                                      rtm_read())
                if command and channel:
                    # client.begin_transaction(transaction_type='request')
                    handle_command(command, channel)
#                        elasticapm.set_user_context(command=command, channel=channel)
                    #client.capture_message('got command'  )
                    #client.end_transaction('processor', 200)
                # client.begin_transaction('processors',transaction_type='request')
                time.sleep(READ_WEBSOCKET_DELAY)

        else:
            LOGGER.error("Connection failed. Invalid Slack token or bot ID?")
            # client.capture_exception()

    finally:
        LOGGER.info('killing Logger and exiting bot , Bye Bye ..')
        # client.capture_message('Closed and cleaned up' )
        clean_up_exit()
