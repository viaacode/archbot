# Archstats

> Auto-generated documentation for [archstats](../archstats.py) module.

Created on Tue Sep 12 11:31:05 2017

- [Archbot](README.md#archbot) / [Modules](MODULES.md#archbot-modules) / Archstats
    - [stats](#stats)
        - [stats().Fetch](#statsfetch)
        - [stats().Plot](#statsplot)
        - [stats().Status](#statsstatus)
    - [adjust_lightness](#adjust_lightness)
    - [connectDB](#connectdb)
    - [fdrec](#fdrec)

@author: tina

## SUM GB / type/ workflow
# stats().Status(today=False,countPlot=False, Plot=True)

## AANTAL Status is 24h
# stats().Status(today=False,countPlot=True, Plot=False)

# GB / type/workflow l&ast 4 days
#stats(stype='plot',days=3).Plot()
# ### styatus json
# print(stats(stype='all', total=True, days=3).Fetch())
## archbot's workflowplot
# stats(days=363,stype='workflowplot').Plot()
## archsbot's status'
 stats().Status()

#### Attributes

- `config` - from pprint import pprint
  # use config.yml if you want to use env vars: `ConfigParser(config_file='config.yml')`

## stats

[[find in source code]](../archstats.py#L82)

```python
class stats(object):
    def __init__(
        stype='workflow',
        days=None,
        audio=False,
        video=False,
        total=False,
        other=False,
    ):
```

Args:

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

### stats().Fetch

[[find in source code]](../archstats.py#L253)

```python
def Fetch():
```

Rerturns json not plot

### stats().Plot

[[find in source code]](../archstats.py#L347)

```python
def Plot():
```

Plots image and saves image

### stats().Status

[[find in source code]](../archstats.py#L185)

```python
def Status(Plot=False, countPlot=False):
```

Args:

- Plot: bool (creates image of plot or not, in GB)
- countPlot: bool (smae as above but nr of assets )

## adjust_lightness

[[find in source code]](../archstats.py#L72)

```python
def adjust_lightness(color, amount=0.5):
```

## connectDB

[[find in source code]](../archstats.py#L494)

```python
def connectDB():
```

connects to medaiahaven db

## fdrec

[[find in source code]](../archstats.py#L55)

```python
def fdrec(df):
```
