# trello-to-zulip.py

A simple scrip to mirro [Trello](https://trello.com) activity to a [Zulip](https://zulip.com) stream.


## Configuration Parameters

Authentication, source and destination parameters can come from the environment or an external json file. There is an example, `config_example.json`, in the repo. Parameter names and brief descriptions below. See *Getting Started* below for where these come from.

- TRELLO_KEY
    - Trello application key
- TRELLO_TOKEN
    - Trello user token
- TRELLO_ORG
    - Trello organization name.
- ZULIP_EMAIL
    - Zulip bot email
- ZULIP_KEY
    - Zulip bot API Key.


## Getting Started

Visit the Trello [Getting Started Guide](https://trello.com/docs/gettingstarted/index.html#application-key) for full details about the key and token below.

1. Trello Application Key and User Token
   
   Interacting with the Trello API requires an application key. This can be generated, after logging in, by visiting the link below.
   
   [https://trello.com/1/appKey/generate](https://trello.com/1/appKey/generate).

   A user token must be generated to access any private data. In the URL below, replace APPLICATION_KEY with the key generated in the above step. Note that the expiration is *never*. See the guide linked above for other intervals (e.g. 1days).
   
   [https://trello.com/1/authorize?key=APPLICATION_KEY&name=trello-to-zulip&expiration=never&response_type=token](https://trello.com/1/authorize?key=APPLICATION_KEY&name=trello-to-zulip&expiration=never&response_type=token)

2. Zulip Bot and Stream

   Bots can be created through the settings page. Visit the [settings](https://zulip.com/#settings) page and create a new bot (e.g. FullName: TrelloBot, Username: trello, Avatar: [Trello logo](https://trello.com/c/KqVRLtGK/103-logos)). Once created, the bot API Key will be displayed on the settings page.
   
   A new stream is the best place to put all the messages from this new bot. Visit the [subscriptions](https://zulip.com/#subscriptions) page, enter _trello_ for the stream name and click _Create Stream_.

3. Create config.json

   Copy `config_example.json` to `config.json` and fill in the placeholders with the real information you just created.

4. Run the script

   The script runs in a loop by default. This is convenient for testing or running in a screen session. For example,

   `./trello-to-zulip.py --config=config.json --verbose`
   
    will start the script, request Trello activity, post anything new to Zulip, sleep for a minute and repeat indefinitely. The `--verbose` flag echos received activity and created messages for simple monitoring.
