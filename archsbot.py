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
import configparser
from elasticapm import Client
import elasticapm
elasticapm.instrument()
elasticapm.set_transaction_name('processor')
elasticapm.set_transaction_result('SUCCESS')
from elasticapm.handlers.logging import LoggingHandler
# client = Client({'SERVICE_NAME': 'archbot',
#                  'DEBUG': False,
#                  'SERVER_URL': 'http://apm-server-prd.apps.do-prd-okp-m0.do.viaa.be:80'} )

config = configparser.ConfigParser()
config.read('config.ini')
bot_id = config['slack_api']['bot_id']
client_token =   config['slack_api']['client_token']

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

    def Post(self):

        if self.ptype is 'status_plot':
            stats(days=0).Status(today=False, Plot=True)
        if self.ptype is 'status_countPlot':
            stats(days=0).Status(today=False, countPlot=True)
        if self.ptype is 'plot':
            stype = 'plot'
            stats(stype=stype, days=self.days).Plot()
        if self.ptype is 'workflow':
            stype = 'workflowplot'
            stats(stype=stype, days=self.days).Plot()
        if self.ptype is 'cpplot':
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


def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


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
    l = command.split()
    for i in l:
        if representsInt(i):
            found_nr = True
            days = int(i)
            LOGGER.info('found int setting days to: {}'.format(str(days)))
    if command.startswith('help'):
        response = "Usage: @archsbot " + "possible_args*['plot', 'workflowplot',"\
                    "'cpplot', 'status', 'int(nr of days)']' OR [audio,video,other,count(sum of sizes)]  followed by nr of days"

    if 'plot' in l:
        LOGGER.info('Found plot in command')
        plot = True
#    if command.startswith('plot') and not command.endswith('workflow'):
#        plot = True
    if 'workflowplot' in l:
        workflowplot = True
    if 'cpplot' in l:
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
    if 'status' in l and 'plot' not in l and 'plotcount' not in l:
        response = stats(days=0,).Status(today=True, Plot=False)
    if 'status' in l and 'plot' in l:
        plt(ptype='status_plot', days=0).Post()
    if 'status' in l and 'plotcount' in l:
        plt(ptype='status_countPlot', days=0).Post()

    def makeResponse():
        if plot:
            plt(ptype='plot', days=days).Post()
        if workflowplot:
            plt(ptype='workflow', days=days).Post()
        if cpplot:
            plt(ptype='cpplot', days=days).Post()
        if video or audio or other or total or stype is 'all':
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


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    try:
        output_list = slack_rtm_output
    except Exception:
        client.capture_exception()
        pass
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                LOGGER.info('got input to parse: {}'.format(output_list))
                # return text after the @ mention, whitespace removed
                o = output['text'].split(AT_BOT)[1].strip().lower(),\
                    output['channel']
                client.capture_message('processed %s' % output['text'])
                return o
    return None, None


if __name__ == "__main__":
    LOGGER = logging.getLogger(__name__)

    LOG_FORMAT = ('%(asctime)-15s %(levelname) -5s %(name) -5s %(funcName) '
                  '-3s %(lineno) -5d: %(message)s')
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
    client = Client({'SERVICE_NAME': 'archbot',
                 'DEBUG': False,
                 'SERVER_URL': 'http://apm-server-prd.apps.do-prd-okp-m0.do.viaa.be:80'} )        
    handler = LoggingHandler(client=client)
    handler.setLevel(logging.WARN)
    logging.getLogger('elasticapm').setLevel('INFO')
    LOGGER.addHandler(handler)
    
    
    

    try:
        formatter = logging.Formatter('%(asctime)-15s  %(levelname)-6s:'
                                      '%(message)s')
        logging.basicConfig(format=formatter, level=logging.INFO)
    except Exception:
         client.capture_exception()
    try:
        READ_WEBSOCKET_DELAY = 1  # 1 second delay reading from firehose
        if slack_client.rtm_connect():
            LOGGER.info("Bot connected and running!")
            client.capture_message('connected the bot.' )

            try:
                while True:
                    command, channel = parse_slack_output(slack_client.
                                                          rtm_read())
                    if command and channel:
                        client.begin_transaction(transaction_type='request')
                        handle_command(command, channel)
#                        elasticapm.set_user_context(command=command, channel=channel)

                        client.capture_message('got command'  )
                        client.end_transaction('processor', 200)
                   # client.begin_transaction('processors',transaction_type='request')
                    time.sleep(READ_WEBSOCKET_DELAY)
                    
            except KeyboardInterrupt:
                client.capture_exception()
                pass
        else:
            LOGGER.error("Connection failed. Invalid Slack token or bot ID?")
            client.capture_exception()

    finally:
        LOGGER.info('killing Logger and exiting bot , Bye Bye ..')
        client.capture_message('Closed and cleaned up' )
        clean_up_exit()
#    print(stats(stype='workflowplot',days=1000).Plot())
