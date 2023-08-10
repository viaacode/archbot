#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 13:50:51 2022
event:
    {'type': 'message',
     'user': 'U02HFGKFY',
     'channel': 'G72H2N1CN',
     'text': 'test',
     'blocks': [{'type': 'rich_text',
                 'block_id': 'nqTWP',
                 'elements': [{'type': 'rich_text_section',
                               'elements': [{'type': 'text',
                                             'text': 'test'}]}]}],
     'client_msg_id': 'ac19d122-b2cf-470f-83e6-cf1df01510d3',
     'team': 'T02HE0C8B',
     'source_team': 'T02HE0C8B',
     'user_team': 'T02HE0C8B', '
     suppress_notification': False,
     'event_ts': '1664458122.341449',
     'ts': '1664458122.341449'}
usage:
    upload  a file:
        - upload('./plot.png')

@author: tina
"""
import logging
from slack_sdk.rtm_v2 import RTMClient
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from viaa.configuration import ConfigParser
from archstats import stats

config = ConfigParser(config_file="config.yml")
token = config.app_cfg['slack_api']['client_token']

logger = logging.getLogger(__name__)
LOG_FORMAT = ('%(asctime)-15s %(levelname) -5s %(name) -5s %(funcName) '
              '-5s %(lineno) -5d: %(message)s')
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

rtm = RTMClient(token=token)


def upload(filepath):
    client = WebClient(token=token)
    logger.info(f'Uploading file: {filepath}')
    try:
        response = client.files_upload(
            channels='#archbot',
            file=filepath)
        assert response["file"]  # the uploaded file
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        # str like 'invalid_auth', 'channel_not_found'
        assert e.response["error"]
        print(f"Got an error: {e.response['error']}")
    return True


class plt(object):
    def __init__(self, ptype, days=2):
        self.ptype = ptype
        self.days = days

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
            # f = open('/tmp/plot.png', 'rb')
            upload('/tmp/plot.png')
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


def test_con():
    client = WebClient(token=token)
    try:
        response = client.chat_postMessage(
            channel='#archbot', text="Bot connected!")
        assert response["message"]["text"] == "Bot connected!"
        logger.info('Posted test msg, success')
        return True
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        # str like 'invalid_auth', 'channel_not_found'
        assert e.response["error"]
        logger.error(f"Got an error: {e.response['error']}")
        return False


@rtm.on("message")
def handle(client: RTMClient, event: dict):
    found_nr = False
    workflowplot = False
    cpplot = False
    if event['text'] and event['channel'] == 'G72H2N1CN':
        logger.debug(str(event['text']))
        lst = event['text'].split()
        if 'workflowplot' in lst:
            workflowplot = True
            logger.info('Using workflowplot')
        if 'cpplot' in lst:
            cpplot = True
            logger.info('Using cpplot')
        for i in lst:
            if representsInt(i):
                found_nr = True
                days = int(i)
                logger.info('found int setting days to: {}'.format(str(days)))
        if workflowplot and found_nr:
            logger.info('workflowplot')
            plt(ptype='workflow', days=days).Post()
        if cpplot and found_nr:
            logger.info('workflowplot')
            plt(ptype='cpplot', days=days).Post()
        if 'status' in lst:
            logger.info(str(event['channel']))
            channel_id = event['channel']
            # thread_ts = event['ts']
            # User ID (the format is either U*** or W***)
            user = event['user']
            response = stats().Status()
            client.web_client.chat_postMessage(
                channel=channel_id,
                text=f"Hi <@{user}>! {response}",
            )


if __name__ == "__main__":
    logger.info(test_con())
    rtm.start()
