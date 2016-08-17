# Autoresponder for Google Chat and Hangouts

Autoresponder is a Django project that hosts static Google Chat/Hangouts bots.

It's intended for people who have multiple Google accounts which forward email to one main account.
In this setup, chat messages sent to a forwarding account will never be seen.
Autoresponder lets them set up a response directing people elsewhere, and optionally notifying them of a new message.

If you'd like to use it, sign up at https://gchat.simon.codes.

## project layout

* gchatautorespond/apps/autorespond: main django app
* gchatautorespond/lib/chatworker: manages chat bots
* test: tests
* ops: ansible config (3rd party roles vendorized)
* secrets: prod secrets (managed with transcypt)
* assets: served with dj-static (not nginx because I'm lazy)

## development

To create a new dev environment:

* create a new virtualenv
* `pip install -r test_requirements.txt`
* `DJANGO_SETTINGS_MODULE=gchatautorespond.settings_dev python manage.py migrate`

Then:

* run locally: `DJANGO_SETTINGS_MODULE=gchatautorespond.settings_dev python manage.py supervisor`
* run tests: `DJANGO_SETTINGS_MODULE=gchatautorespond.settings_dev ./manage.py test test/`

## production

### for just you 

If you're only hosting for yourself, it's easy to run a bot without the django site:

```
$ pip install -r requirements.txt
$ python gchatautorespond/lib/chatworker/bot.py <email> <access_token> <response> [notify_email]
```

This doesn't handle refreshing the access token, though (handled by `Worker._bot_failed_auth` in the full site).
A nice contribution would be a subclass of AutoRespondBot that's built for this workflow, probably accepting a Credentials filepath and using it during `failed_auth`.

### equivalent to gchat.simon.codes

Get in touch if you want to do this.
The current setup isn't optimized for this, so we'll have to work it out together.
