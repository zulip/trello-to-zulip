# trello-to-zulip.py

A simple scrip for mirroring [Trello](https://trello.com) organization
activity [Zulip](https://zulip.com) stream.


## Configuration Parameters

Authentication, source and destination parameters can come from the environment
or an external json file. The `config_example.json` file is a complete example
with placeholder information. Parameter names below and brief descriptions below
with full details on creating them in the next section.

- TRELLO_KEY
    - Trello application key
- TRELLO_TOKEN
    - Trello user token
- TRELLO_ORG
    - Trello organization name
    (use the Orgname from your URLs, e.g. "acmeco" and not "Acme Co.")
- ZULIP_EMAIL
    - Zulip bot email
- ZULIP_KEY
    - Zulip bot API Key


## Getting Started

Visit the Trello [Getting Started Guide](https://trello.com/docs/gettingstarted/index.html#application-key)
for full details about the key and token below.

1. Trello Application Key and User Token
   
   Interacting with the Trello API requires an application key. This can be
   generated, after logging in, by visiting the link below:
   
   [https://trello.com/1/appKey/generate](https://trello.com/1/appKey/generate).

   A user token must be generated to access any private data. In the URL below,
   replace APPLICATION_KEY with the key generated in the above step. Note that
   the expiration is *never*. See the guide linked above for other intervals
   (e.g. expiration=1days):
   
   [https://trello.com/1/authorize?key=APPLICATION_KEY&name=trello-to-zulip&expiration=never&response_type=token](https://trello.com/1/authorize?key=APPLICATION_KEY&name=trello-to-zulip&expiration=never&response_type=token)

2. Zulip Bot and Stream

   Bots can be created through the settings page. Visit the
   [settings](https://zulip.com/#settings) page and create a new bot (e.g.
   FullName: TrelloBot,
   Username: trello,
   Avatar: [Trello logo](https://trello.com/c/KqVRLtGK/103-logos)).
   Once created, the bot API Key will be displayed on the settings page.
   
   A new stream is the best place to put all the messages from this new bot.
   Visit the [subscriptions](https://zulip.com/#subscriptions) page, enter
   _trello_ for the stream name and click _Create Stream_.

3. Create config.json

   Copy `config_example.json` to `config.json`. Edit `config.json` and fill
   in the placeholders with the real information you just created.

4. Run the script

   The script runs in a loop by default. This is convenient for testing or running
   in a screen session. For example,

   `./trello-to-zulip.py --config=config.json --verbose`
   
    will start the script, request Trello activity, post anything new to Zulip,
    sleep for a minute and repeat indefinitely. The `--verbose` flag echos
    received activity and created messages for simple monitoring.

5. Leaving it running

   I currently run this during 'working hours' via `cron`. The script attempts
   to be a good citizen by keeping track of the last action date, stored in
   a file named `.trello-to-zulip-date`, and sending that along  in the
   requests for activity.


## More examples

* Running without looping
    * `./trello-to-zulip.py --config=config.json --verbose --once`
* Skip creating Zulip messages
    * `./trello-to-zulip.py --config=config.json --verbose --no-post`
* Poll every 5 minutes instead of 1
    * `--sleep` interval is in seconds
    * `./trello-to-zulip.py --config=config.json --verbose --sleep=300`
* Quick test for posting to a different stream
    * Environment variables take precedence over the config file
    * `ZULIP_STREAM=my-other-stream ./trello-to-zulip.py --config=config.json --verbose --once`
* Getting all Trello history into Zulip
    * _Note: If you have significant Trello activity, this may take a while_
    * `./trello-to-zulip.py --config=config.json --verbose --all`

