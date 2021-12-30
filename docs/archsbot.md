# Archsbot

> Auto-generated documentation for [archsbot](../archsbot.py) module.

Created on Tue Sep 12 11:02:46 2017

- [Archbot](README.md#archbot) / [Modules](MODULES.md#archbot-modules) / Archsbot
    - [plt](#plt)
        - [plt().Post](#pltpost)
    - [clean_up_exit](#clean_up_exit)
    - [handle_command](#handle_command)
    - [parse_slack_output](#parse_slack_output)
    - [representsInt](#representsint)

@author: tina

#### Attributes

- `BOT_ID` - constants: `bot_id`
- `slack_client` - instantiate Slack & Twilio clients
  slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN')): `SlackClient(client_token)`

## plt

[[find in source code]](../archsbot.py#L49)

```python
class plt(object):
    def __init__(ptype, days=2):
```

### plt().Post

[[find in source code]](../archsbot.py#L54)

```python
def Post():
```

## clean_up_exit

[[find in source code]](../archsbot.py#L28)

```python
def clean_up_exit():
```

## handle_command

[[find in source code]](../archsbot.py#L87)

```python
def handle_command(command, channel):
```

Receives commands directed at the bot and determines if they
are valid commands. If so, then acts on the commands. If not,
returns back what it needs for clarification.

## parse_slack_output

[[find in source code]](../archsbot.py#L173)

```python
def parse_slack_output(slack_rtm_output):
```

The Slack Real Time Messaging API is an events firehose.
this parsing function returns None unless a message is
directed at the Bot, based on its ID.

## representsInt

[[find in source code]](../archsbot.py#L79)

```python
def representsInt(s):
```
