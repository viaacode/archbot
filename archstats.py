#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 11:31:05 2017

@author: tina


"""
from viaa.configuration import ConfigParser
import pandas as pd
import logging
import datetime
import json
import pandas.io.sql as psql
import matplotlib.pyplot as plot
import os
# import base64
# import numpy as np

import psycopg2
#from matplotlib import pyplot as plot
# remove'agg' for inline plotting
import matplotlib
matplotlib.use('agg')
# from pprint import pprint
# use config.yml if you want to use env vars
config = ConfigParser(config_file="config.yml")
bot_id = config.app_cfg['slack_api']['bot_id']
client_token = config.app_cfg['slack_api']['client_token']
db_name = config.app_cfg['mh_db']['db_name']
db_user = config.app_cfg['mh_db']['user']
db_passwd = config.app_cfg['mh_db']['passwd']
db_host = config.app_cfg['mh_db']['host']
LOGGER = logging.getLogger(__name__)
LOG_FORMAT = ('%(asctime)-15s %(levelname) -5s %(name) -5s %(funcName) '
              '-5s %(lineno) -5d: %(message)s')
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


def fdrec(df):
    drec = dict()
    ncols = df.values.shape[1]
    for line in df.values:
        d = drec
        for j, col in enumerate(line[:-1]):
            if col not in d.keys():
                if j != ncols - 2:
                    d[col] = {}
                    d = d[col]
                else:
                    d[col] = line[-1]
            else:
                if j != ncols - 2:
                    d = d[col]
    return drec


def adjust_lightness(color, amount=0.5):
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], max(0, min(1, amount * c[1])), c[2])


class stats(object):
    '''Args:

        - stype: one of [workflowplot,cpplot, plot]
        - days: nr of days to process (starts with 0)
        - audio: bool (only audio) if true
        - video: bool (only video if true)
        - other: bool (other type then audio/video)
        - total (just count totals)

    Description:
        - Uses mediahaven SIPS database to fetch data
        - workflow: all mediahaven workflows all types in plot
        - cpplot: subplot/cp
        - plot: type/workflow/days
      subfunctions:
          - Plot (to plot data)

              - examples:
                  - archbots plot:
                      stats(days=363,stype='workflowplot').Plot()
                  - subplots (type/cp):
                      stats(days=3,stype='plot').Plot()
                  - cpplot
                      stats(days=3,stype='cpplot').Plot()



          - Fetch (returns json)

              - examples:
                  - print(stats(stype='all', total=True, days=3).Fetch())

                  - print(stats(video=True).Fetch())
          - Status (json last 24h or plot of 24h if Plot is set true)
            - Args:
                -  Plot: bool (GB)
                - countPlot: bool (nr aantal assets )

            - examples:
                - SUM GB / type/ workflow:
                    stats().Status(countPlot=False, Plot=True)


                - AANTAL Status is 24h:
                    stats().Status(countPlot=True, Plot=False)

    '''

    def __init__(self, stype='workflow', days=None, audio=False, video=False,
                 total=False, other=False):
        self.stype = stype
        self.days = days
        self.audio = audio
        self.video = video
        self.other = other
        self.total = total
        if self.days is None:
            self.days = 6
        if self.days < 6:
            self.days = 6
        self.sql = """SELECT  SUM(filesize)/1000/1000/1000 as GB -- change from GiB to GB
		,date_trunc('day', premis_events.date), workflow,sips.type
        FROM sips
        left JOIN premis_events on sips.fragment_id = premis_events.fragment_id
        WHERE archive_status = 'on_tape'
        AND premis_events.type = 'ARCHIVED_ON_TAPE' -- generated by scheduler
        AND premis_events.date >=  current_date - interval '{}' day
        AND premis_events.outcome = 'OK'
        AND organisation not in ('testbeeld','viaa','viaa-archief','failures')
        AND sips.is_deleted = 0
        GROUP BY date_trunc('day', premis_events.date)  ,workflow,sips.type
        ORDER by date_trunc('day', premis_events.date) desc, workflow,sips.type;
        """.format(self.days)
        self.sqlcp = """SELECT date_trunc('day', premis_events.date),organisation,
          SUM(filesize)/1024/1024/1024 as GB

        FROM sips
        left JOIN premis_events on sips.fragment_id = premis_events.fragment_id
        WHERE archive_status = 'on_tape'
        AND premis_events.type = 'ARCHIVED_ON_TAPE'
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
        AND premis_events.type = 'ARCHIVED_ON_TAPE'
        AND premis_events.date >=  now() - interval '24' hour
        AND premis_events.outcome = 'OK'
        AND organisation not in ('testbeeld','viaa','viaa-archief','failures')
        AND sips.is_deleted = 0
        GROUP BY date_trunc('day', premis_events.date)  ,workflow,sips.type
        ORDER by date_trunc('day', premis_events.date) desc,
        workflow,sips.type""".format(self.days)

    def Status(self, Plot=False, countPlot=False):
        """ Args:

            - Plot: bool (creates image of plot or not, in GB)
            - countPlot: bool (smae as above but nr of assets )

        """
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
            return {'error': str(e)}

        if data.empty is not True:
            gdata = data.groupby(['workflow', 'type'])['GB'].sum()
            g2data = data.groupby(['workflow', 'type'])['aantal'].sum()
            wdata = data.groupby(['workflow'])['GB'].sum()
            w2data = data.groupby(['workflow'])['aantal'].sum()
            tw = pd.concat([wdata, w2data], axis=1)
            t = pd.concat([g2data, gdata], axis=1)
            t['GB'] = t['GB'].astype(float)
            p = t.drop('aantal', 1)
            p2 = t.drop('GB', 1)
            width = 24

            if Plot is True:
                n = len(p.columns)
                height = int(n) * 6
                ax = p.unstack(level=0).plot(kind='barh', stacked=True,
                                             subplots=True, sharey=True,
                                             sharex=True,
                                             figsize=(width, height))
                plot.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
            if countPlot is True:
                n = len(p2.columns)
                height = int(n) * 6
                ax = p2.unstack(level=0).plot(kind='barh', stacked=True,
                                              subplots=False, sharey=False,
                                              figsize=(width, height))
                fig = ax.get_figure()
                fig.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                plot.close(fig)
            else:
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

    def Fetch(self):
        """ Rerturns json not plot"""
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
            return {'error': str(e)}
        if data.empty is not True:
            if self.stype == 'workflow':
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
                    def o(row): return row['type'] not in av
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
            if self.stype == 'all':
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
        """Plots image and saves image"""
        try:
            os.remove('/tmp/plot.png')
        except:
            pass
        if self.stype == 'plot':
            try:
                conn = connectDB()
                cursor = conn.cursor()
                cursor.execute(self.sql)
                data = pd.DataFrame(cursor.fetchall(),
                                    columns=['gb', 'date_trunc', 'workflow',
                                             'type'])

            except TypeError as e:
                LOGGER.error(str(e))

                return {'error': str(e)}

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

                height = len(gdata) * 3
                ax = cleansubset.plot(legend=False, kind='barh', stacked=True,
                                      subplots=False, figsize=(32, height),
                                      width=0.89, sharey=False)
                for p in ax.patches:
                    b = p.get_bbox()
                    val = "{:.0f}".format(b.x1 - b.x0)
                    ax.annotate(val, ((b.x0 + b.x1) / 2 + x_offset,
                                      (b.y1) / (1) + y_offset),
                                verticalalignment='top',
                                horizontalalignment='left')
                fig = ax.get_figure()
                fig.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                plot.close(fig)
            else:
                LOGGER.info('no results, empty DataFrame')
                return {'error': 'emptydata, no results'}
        if self.stype == 'workflowplot':
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
                return {'error': str(e)}

            if data.empty is not True:
                height = 8
                width = 16
                mean = 5
                if self.days >= 30:
                    width = self.days
                    height = 10
                    mean = 8
                if self.days >= 100:
                    width = 72
                    height = 18
                    mean = 20
                if self.days >= 250:
                    width = 160
                    height = 24
                    mean = 60

                data.sort_values(["date_trunc", "workflow"],
                                 ascending=[False, True])
                data.date_trunc = data.date_trunc.dt.date
                data['gb'] = data['gb'].astype(float)
                gdata = data.groupby(['date_trunc', 'workflow'])['gb'].sum()
                # avergae rolling mean over X days
                gdata_mean = gdata.rolling(mean).mean().fillna(value=0)
                d = gdata.unstack(level=-1).fillna(value=0)
                d2 = gdata_mean.unstack(level=-1)
                plot.style.use('ggplot')
                fig = plot.figure(figsize=(width, height))
                ax = fig.add_subplot()
                ax2 = ax.twiny()
                ax2.set_title('Ingest workflow')
                ax2.set_ylabel("GB", loc='center')
                d2.plot(legend=True, kind='area', ax=ax, subplots=False,
                        stacked=True, figsize=(width, height), colormap='summer')

                ax.legend(loc='upper left')
                d.plot(legend=True, kind='line', ax=ax2, subplots=False, linewidth=5.0,
                       stacked=False, sharey=True, figsize=(width, height))

                fig.get_figure()
                # plot.show()
                fig.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                plot.close(fig)
            else:
                LOGGER.error('no results, empty DataFrame')
                return {'error': 'emptydata, no results'}
        if self.stype == 'cpplot':

            conn = connectDB()
            df = None
            df = psql.read_sql(self.sqlcp, conn)
            LOGGER.info('ran dataFrame SQL read')
            if df.empty is not True:

                o = df.groupby(['date_trunc', 'organisation'],
                               sort=False)['gb'].sum()
                u = o.unstack(level=-1)
                n = len(u.columns)
                height = int(n) * 6
                ax = u.plot(figsize=(32, height), kind='area',
                            subplots=True, stacked=False,
                            colormap='Accent')

                # plot.show()
                plot.savefig('/tmp/plot.png')
                LOGGER.info('saved image')
                # plot.close(plot)
            else:
                LOGGER.error('no results, empty DataFrame')
                return {'error': 'emptydata, no results'}
        try:
            conn.close()
        except Exception as e:
            LOGGER.error(str(e))

            pass


def connectDB():
    """connects to medaiahaven db"""
    try:
        conn = psycopg2.connect(dbname=db_name,
                                port=1433,
                                user=db_user,
                                host=db_host,
                                password=db_passwd)

        return conn
    except TimeoutError as e:
        LOGGER.error('error: ' + str(e))
        return False
#
# SUM GB / type/ workflow
#stats().Status(countPlot=False, Plot=True)

# stats(days=9,stype='workflowplot').Plot()
# AANTAL Status is 24h
# stats().Status(countPlot=True, Plot=False)

# GB / type/workflow l&ast 4 days
# stats(stype='plot',days=6).Plot()
# ### styatus json
#print(stats(stype='all', total=True, days=3).Fetch())
# archbots workflowplot
# stats(days=3,stype='cpplot').Plot()
#
# print(stats(video=True).Fetch())
# stats().Status(countPlot=True, Plot=False)
