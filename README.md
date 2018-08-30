# Autoresponder for Google Chat and Hangouts

Autoresponder is a Django project that hosts static Google Chat/Hangouts bots.

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

To further customize your bot, modify the constructor params for [AutoRespondBot](https://github.com/simon-weber/gchatautorespond/blob/master/gchatautorespond/lib/chatworker/bot.py)
in standalone\_bot.py

Email notifications are not currently supported when self-hosting ([#7](https://github.com/simon-weber/gchatautorespond/issues/7)).

## project layout

* gchatautorespond/apps/autorespond: main django app
* gchatautorespond/lib/chatworker: manages chat bots
* test: tests
* ops: ansible config (3rd party roles vendorized)
* secrets: prod secrets (managed with transcypt)
* assets: served with nginx (and dj-static locally)

## development

To create a new dev environment:

* create a new virtualenv
* `pip install -r test_requirements.txt`
* `DJANGO_SETTINGS_MODULE=gchatautorespond.settings_dev python manage.py migrate`

Then:

* run locally: `DJANGO_SETTINGS_MODULE=gchatautorespond.settings_dev python manage.py supervisor`
* run tests: `DJANGO_SETTINGS_MODULE=gchatautorespond.settings_dev ./manage.py test test/`
