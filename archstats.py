#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 11:31:05 2017

@author: tina
"""
import os
# import base64
# import numpy as np

import psycopg2
#from matplotlib import pyplot as plot
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plot
import pandas.io.sql as psql
import json
import datetime
import logging
import pandas as pd
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
bot_id = config['slack_api']['bot_id']
client_token =   config['slack_api']['client_token']


LOGGER = logging.getLogger(__name__)
LOG_FORMAT = ('%(asctime)-15s %(levelname) -5s %(name) -5s %(funcName) '
              '-5s %(lineno) -5d: %(message)s')
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)


def fdrec(df):
    drec = dict()
    ncols = df.values.shape[1]
    for line in df.values:
        d = drec
        for j, col in enumerate(line[:-1]):
            if col not in d.keys():
                if j != ncols-2:
                    d[col] = {}
                    d = d[col]
                else:
                    d[col] = line[-1]
            else:
                if j != ncols-2:
                    d = d[col]
    return drec


class stats(object):
    def __init__(self, stype='workflow', days=None, audio=False, video=False,
                 total=False, other=False):
        self.stype = stype
        self.days = days
        self.audio = audio
        self.video = video
        self.other = other
        self.total = total
        if self.days is None:
            self.days = 7
        self.sql = """SELECT  SUM(filesize)/1024/1024/1024 as GB,
        date_trunc('day', premis_events.date), workflow,sips.type
        FROM sips
        left JOIN premis_events on sips.fragment_id = premis_events.fragment_id
        WHERE archive_status = 'on_tape'
        AND premis_events.type = 'FLOW.ARCHIVED_ON_TAPE_VAULT'
        AND premis_events.date >=  current_date - interval '{}' day
        AND premis_events.outcome = 'OK'
        AND organisation not in ('testbeeld','viaa','viaa-archief','failures')
        AND sips.is_deleted = 0
        GROUP BY date_trunc('day', premis_events.date)  ,workflow,sips.type
        ORDER by date_trunc('day', premis_events.date) desc, workflow,sips.type
        """.format(self.days)
        self.sqlcp = """SELECT date_trunc('day', premis_events.date),organisation,
          SUM(filesize)/1024/1024/1024 as GB

        FROM sips
        left JOIN premis_events on sips.fragment_id = premis_events.fragment_id
        WHERE archive_status = 'on_tape'
        AND premis_events.type = 'FLOW.ARCHIVED_ON_TAPE_VAULT'
        AND premis_events.date >=  current_date - interval '{}' day
        AND premis_events.outcome = 'OK'
        AND organisation not in ('testbeeld','viaa','viaa-archief','failures')
        AND sips.is_deleted = 0
        GROUP BY date_trunc('day', premis_events.date)  ,organisation
        ORDER by date_trunc('day', premis_events.date) desc, organisation,
        SUM(filesize)/1024/1024/1024
        """.format(self.days)
        self.sqlstatus = """SELECT  count(distinct external_id),
        SUM(filesize)/1024/1024/1024 as GB,
        date_trunc('day', premis_events.date), workflow,sips.type
        FROM sips
        left JOIN premis_events on sips.fragment_id = premis_events.fragment_id
        WHERE archive_status = 'on_tape'
        AND premis_events.type = 'FLOW.ARCHIVED_ON_TAPE_VAULT'
        AND premis_events.date >=  now() - interval '24' hour
        AND premis_events.outcome = 'OK'
        AND organisation not in ('testbeeld','viaa','viaa-archief','failures')
        AND sips.is_deleted = 0
        GROUP BY date_trunc('day', premis_events.date)  ,workflow,sips.type
        ORDER by date_trunc('day', premis_events.date) desc,
        workflow,sips.type""".format(self.days)

    def Status(self, Plot=False, countPlot=False, today=False):
        LOGGER.info('Status function requested')
        try:
            data = None
            conn = connectDB()
            cursor = conn.cursor()
            cursor.execute(self.sqlstatus)
            LOGGER.info('Connected to the database, Calling Query')
            data = pd.DataFrame(cursor.fetchall(), columns=['aantal', 'GB',
                                'date_trunc', 'workflow', 'type'])

        except TypeError as e:
            LOGGER.error(str(e))
            return {'error':  str(e)}

        if data.empty is not True:
            gdata = data.groupby(['workflow', 'type'])['GB'].sum()
            g2data = data.groupby(['workflow', 'type'])['aantal'].sum()
            wdata = data.groupby(['workflow'])['GB'].sum()
            w2data = data.groupby(['workflow'])['aantal'].sum()
            tw = pd.concat([wdata, w2data], axis=1)
            t = pd.concat([g2data, gdata], axis=1)
#            j = t.unstack(level=-1)
            t['GB'] = t['GB'].astype(float)
            p = t.drop('aantal', 1)
            p2 = t.drop('GB', 1)
            if Plot is True:

                ax = p.unstack(level=0).plot(kind='barh', stacked=True,
                                             subplots=False, sharey=False,
                                             figsize=(8, 3))

                fig = ax.get_figure()
                fig.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                plot.close(fig)
            if countPlot is True:
                ax = p2.unstack(level=0).plot(kind='barh', stacked=True,
                                              subplots=False, sharey=False,
                                              figsize=(8, 3))
                fig = ax.get_figure()
                fig.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                plot.close(fig)
            if today is True:
                jtw = tw.to_json(date_format='iso', orient='index')

                today_counts = json.dumps(json.loads(jtw), indent=4,
                                          sort_keys=True)
                details = json.loads(gdata.to_json(date_format='iso',
                                                   orient='table'))

                del details['schema']
                date = datetime.datetime.now().strftime("%Y-%m-%d")
                final_json = [{"Today_counts": json.loads(today_counts),
                               "Details_last_24h": details}]
                final_json.append({'date': date})
                return json.dumps(final_json, indent=4, sort_keys=True)
            if plot is False and today is False:
                LOGGER.error('Wrong request')
                return json.dumps({'error': 'Wrong request'})

    def Fetch(self):
        try:
            data = None
            conn = connectDB()
            cursor = conn.cursor()
            cursor.execute(self.sql)
            LOGGER.info('Connected to the database')
            data = pd.DataFrame(cursor.fetchall(), columns=['GB', 'date_trunc',
                                'workflow', 'type'])
        except TypeError as e:
            LOGGER.error(str(e))
            return {'error':  str(e)}
        if data.empty is not True:
            if self.stype is 'workflow':
                if self.video:
                    LOGGER.info('Video requested')
                    v = data.type == 'video'
                    video = data[v]
                    video.sort_values(["date_trunc", "workflow"],
                                      ascending=[False, True])
                    video['GB'] = video['GB'].astype(float)
                    gvideo = video.groupby(['date_trunc', 'type',
                                            'workflow'])['GB'].sum()
                    subsets = gvideo.unstack(level=0).unstack(level=1).\
                        unstack(level=2)
                    cleansubset = subsets.dropna()
                    parsed = json.loads(cleansubset.to_json(date_format='iso',
                                                            orient='table'))
                    LOGGER.info(cleansubset)
                    return json.dumps(parsed, indent=4, sort_keys=True)
                if self.audio:
                    LOGGER.info('Audio requested')
                    a = data.type == 'audio'
                    audio = data[a]
                    audio.sort_values(["date_trunc", "workflow"],
                                      ascending=[False, True])
                    audio['GB'] = audio['GB'].astype(float)
                    gaudio = audio.groupby(['date_trunc', 'type',
                                            'workflow'])['GB'].sum()
                    subsets = gaudio.unstack(level=0).unstack(level=1).\
                        unstack(level=2)
                    cleansubset = subsets.dropna()
                    LOGGER.info(str(cleansubset))
                    parsed = json.loads(cleansubset.to_json(date_format='iso',
                                                            orient='table'))
                    return json.dumps(parsed, indent=4, sort_keys=True)
                if self.other:
                    LOGGER.info('ANY but video or audio requested')
                    av = ['audio', 'video']
                    o = lambda row: row['type'] not in av
                    other = data[data.apply(o, axis=1)]
                    other.sort_values(["date_trunc",
                                       "workflow"], ascending=[False, True])
                    other['GB'] = other['GB'].astype(float)
                    gother = other.groupby(['date_trunc', 'type',
                                            'workflow'])['GB'].sum()
                    subsets = gother.unstack(level=0).unstack(level=1).\
                        unstack(level=2)
                    cleansubset = subsets.dropna()
                    LOGGER.info(str(cleansubset))
                    parsed = json.loads(cleansubset.to_json(date_format='iso',
                                                            orient='table'))
                    return json.dumps(parsed, indent=4, sort_keys=True)
                if self.total:
                    LOGGER.info('Totals requested')
                    data.sort_values(["date_trunc", "workflow"],
                                     ascending=[False, True])
                    data.date_trunc = data.date_trunc.dt.date
                    data['GB'] = data['GB'].astype(float)
                    gdata = data.groupby(['date_trunc', 'type',
                                          'workflow'])['GB'].sum()
                    subsets = gdata.unstack(level=0).unstack(level=1).\
                        unstack(level=2)
                    cleansubset = subsets.dropna()
                    LOGGER.info(str(cleansubset))
                    parsed = json.loads(cleansubset.to_json(date_format='iso',
                                                            orient='table'))
                    return json.dumps(parsed, indent=4, sort_keys=True)
            if self.stype is 'all':
                data.sort_values(["date_trunc", "workflow"],
                                 ascending=[False, True])
                data.date_trunc = data.date_trunc.dt.date
                data['GB'] = data['GB'].astype(float)
                gdata = data.groupby(['date_trunc'])['GB'].sum()
                cleansubset = gdata.dropna()
                LOGGER.info(str(cleansubset))
                parsed = json.loads(cleansubset.to_json(date_format='iso',
                                                        orient='table'))
                return json.dumps(parsed, indent=4, sort_keys=True)
        else:
            return {'error': 'emptydata, no results'}
        conn.close()

    def Plot(self):
        try:
            os.remove('/tmp/plot.png')
        except:
            pass
        if self.stype is 'plot':
            try:
                conn = connectDB()
                cursor = conn.cursor()
                cursor.execute(self.sql)
                data = pd.DataFrame(cursor.fetchall(),
                                    columns=['gb', 'date_trunc', 'workflow',
                                             'type'])

            except TypeError as e:
                LOGGER.error(str(e))

                return {'error':  str(e)}

            if data.empty is not True:
                data.sort_values(["date_trunc", "workflow"],
                                 ascending=[False, True])
                data.date_trunc = data.date_trunc.dt.date
                data['gb'] = data['gb'].astype(float)
                gdata = data.groupby(['date_trunc', 'type',
                                      'workflow'])['gb'].sum()
                subsets = gdata.unstack(level=0).\
                    unstack(level=1).unstack(level=2)
                cleansubset = subsets.dropna()
                x_offset = -0.01
                y_offset = -0.06
                ax = cleansubset.plot(legend=False, kind='barh', stacked=True,
                                      subplots=False, figsize=(20, 14),
                                      width=0.89)
                for p in ax.patches:
                            b = p.get_bbox()
                            val = "{:.0f}".format(b.x1-b.x0)
                            ax.annotate(val, ((b.x0 + b.x1)/2 + x_offset,
                                              (b.y1)/(1) + y_offset),
                                        verticalalignment='top',
                                        horizontalalignment='left')
                fig = ax.get_figure()
                fig.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                plot.close(fig)
            else:
                LOGGER.info('no results, empty DataFrame')
                return {'error': 'emptydata, no results'}
        if self.stype is 'workflowplot':
            try:
                data = None
                conn = connectDB()
                cursor = conn.cursor()
                cursor.execute(self.sql)
                data = pd.DataFrame(cursor.fetchall(),
                                    columns=['gb', 'date_trunc', 'workflow',
                                             'type'])
            except TypeError as e:
                LOGGER.error(str(e))
                return {'error':  str(e)}

            if data.empty is not True:

                data.sort_values(["date_trunc", "workflow"],
                                 ascending=[False, True])
                data.date_trunc = data.date_trunc.dt.date
                data['gb'] = data['gb'].astype(float)
                gdata = data.groupby(['date_trunc', 'workflow'])['gb'].sum()
                subsets = gdata.unstack(level=0).unstack(level=1)
                cleansubset = subsets.dropna()
                d = gdata.unstack(level=-1)
                ax = d.plot(legend=True, kind='area', subplots=False,
                            stacked=True, figsize=(16, 8))
                fig = ax.get_figure()
                fig.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                plot.close(fig)
            else:
                LOGGER.error('no results, empty DataFrame')
                return {'error': 'emptydata, no results'}
        if self.stype is 'cpplot':

            conn = connectDB()
            df = None
            df = psql.read_sql(self.sqlcp, conn)
            LOGGER.info('ran dataFrame SQL read')
            if df.empty is not True:

                o = df.groupby(['date_trunc', 'organisation'],
                               sort=False)['gb'].sum()

                ax = o.unstack(level=-1).plot(figsize=(12, 8), kind='bar',
                                              subplots=False, stacked=True,
                                              colormap='jet')

                fig = ax.get_figure()
                fig.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                plot.close(fig)
            else:
                LOGGER.error('no results, empty DataFrame')
                return {'error': 'emptydata, no results'}
        try:
            conn.close()
        except Exception as e:
            LOGGER.error(str(e))

            pass


def connectDB():
    try:

        db_name = config['mh_db']['db_name']
        db_user = config['mh_db']['user']
        db_passwd = config['mh_db']['passwd']
        conn = psycopg2.connect(dbname=db_name,
                                port=1433,
                                user=db_user,
                                host='dg-prd-dbs-m0.dg.viaa.be',
                                password=db_passwd)

        return conn
    except TimeoutError as e:
        LOGGER.error('error: ' + str(e))
        return False
#
print(stats(days=0,).Status(today=False,countPlot=False, Plot=True))
# print(stats(stype='workflowplot',days=6).Plot())
# ###
# print(stats(stype='workflow', total=True, days=0).Fetch())
