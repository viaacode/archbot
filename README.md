# archbot
- slackbot for viaa ingest status

## configure
add a file config.yaml like below fior env vars or fill in the file:

```
viaa:
  logging:
    level: INFO

app:
  slack_api:
    bot_id: !ENV ${BOT_ID}
    client_token: !ENV ${CLIENT_TOKEN}
  mh_db:
    db_name: !ENV ${DB_NAME}
    user: !ENV ${DB_USER}
    passwd: !ENV ${DB_PASSWD}
    host: !ENV ${DB_HOST}

```
## Installation and run
```
install the requirements.txt (this needs to be cleaned )
run it as docker container (consult Dockerfile)
run archsbot.py
```
