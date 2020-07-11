# Autoresponder for Hangouts

Autoresponder is a Django project that hosts static Hangouts bots.

I originally created it to avoid unnoticed messages to my forwarding accounts, but it's also found use with employees and small business owners.

The hosted version is available at https://gchat.simon.codes.

## self-hosting

Autoresponder can also be self-hosted.

First, install the dependencies and connect your account:
```
$ pip install -r requirements.txt
$ python standalone_bot.py auth
```
You only need to run this once.
The OAuth credentials will be written to your current working directory.

Then, start the bot:
```
$ python standalone_bot.py run my-email@gmail.com 'my autoresponse'
```

To further customize your bot, modify the constructor params for StandaloneBot at the bottom of standalone\_bot.py (the arguments are documented in [lib.chatworker.bot.AutoRespondBot](https://github.com/simon-weber/gchatautorespond/blob/master/gchatautorespond/lib/chatworker/bot.py)).

### email notifications

Email notifications are not enabled by default.
To enable them you must configure [gchatautorespond/settings\_standalone.py](https://github.com/simon-weber/gchatautorespond/blob/master/gchatautorespond/settings_standalone.py) to use your mail server.
[Gmail SMTP](https://support.google.com/a/answer/176600) values are provided as an example;
to use it, set `DJ_EMAIL_HOST_USER` to your gmail address and `DJ_EMAIL_HOST_PASSWORD` to your password (or app password) as environment variables.
Then, verify your configuration with:
```
DJANGO_SETTINGS_MODULE=gchatautorespond.settings_standalone python manage.py sendtestemail from@example.com to@example.com
```
Once email sending is configured, you can enable autoresponses with notifications by running:
```
$ python standalone_bot.py notify my-email@gmail.com 'my autoresponse'
```
Or, you can just send notifications without responses with:
```
$ python standalone_bot.py notify my-email@gmail.com
```
In either case, notifications are sent from your `DJ_EMAIL_HOST_USER` to your provided email.
You can control the recipient email by changing the `notify_email` parameter to StandaloneBot.

## project layout

* ansible: deployments
* gchatautorespond/apps/autorespond: main django app
* gchatautorespond/lib/chatworker: manages chat bots
* nix: infra/config management
* secrets: prod secrets (managed with transcypt)
