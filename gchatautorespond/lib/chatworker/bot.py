import datetime
import logging
import ssl
import sys

from django.core.mail import EmailMessage
from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream import resolver, cert

from gchatautorespond.lib import report_ga_event_async


class GChatBot(ClientXMPP):
    """A Bot that connects to Google Chat over ssl."""

    def __init__(self, email, token, **kwargs):
        """
        Args:
            email (unicode): the email to login as, including domain.
              Custom domains are supported.
            token (string): a `googletalk` scoped oauth2 access token
        """

        if '@' not in email:
            raise ValueError('email must be a full email')

        super(GChatBot, self).__init__(email + '/chatbot', token)

        self.email = email

        # TODO it'd be nice if the sleekxmpp logs had the context of the email as well.
        # It looks like this could be done with a filter + threadlocal variable, since
        # process(block=False) starts a new thread.
        self.logger = logging.getLogger("%s.%s.%s" % (__name__, id(self), email.encode('utf-8')))
        self.logger.info("bot initialized (%s)", id(self))

        self.use_ipv6 = False
        self.auto_reconnect = True

        self.add_event_handler('session_start', self.session_start)
        self.add_event_handler('ssl_invalid_cert', self.ssl_invalid_cert)

    def connect(self):
        self.credentials['api_key'] = self.jid
        self.credentials['access_token'] = self.password
        super(GChatBot, self).connect(('talk.google.com', 5222))

    def session_start(self, event):
        self.send_presence()
        self.get_roster()

        # Most get_*/set_* methods from plugins use Iq stanzas, which
        # can generate IqError and IqTimeout exceptions. Example code:
        #
        # try:
        #     self.get_roster()
        # except IqError as err:
        #     logging.error('There was an error getting the roster')
        #     logging.error(err.iq['error']['condition'])
        #     self.disconnect()
        # except IqTimeout:
        #     logging.error('Server is taking too long to respond')
        #     self.disconnect()

    def ssl_invalid_cert(self, raw_cert):
        self._verify_gtalk_cert(raw_cert)

    def _verify_gtalk_cert(self, raw_cert):
        hosts = resolver.get_SRV(self.boundjid.server, 5222,
                                 self.dns_service,
                                 resolver=resolver.default_resolver())
        it_is_google = False
        for host, _ in hosts:
            if host.lower().find('google.com') > -1:
                it_is_google = True

        if it_is_google:
            try:
                if cert.verify('talk.google.com', ssl.PEM_cert_to_DER_cert(raw_cert)):
                    self.logger.info('google cert found for %s',
                                     self.boundjid.server)
                    return
            except cert.CertificateError:
                pass

        self.logger.error("invalid cert received for %s",
                          self.boundjid.server)

        # We should probably disconnect, but custom domains (eg simonmweber.com) trigger false positives here.
        # self.disconnect()


class AutoRespondBot(GChatBot):
    """A GChatBot that responds to incoming messages with a set response.

    This works for all sender/receiver combinations ({gchat, hangouts} x {gchat, hangouts}).

    Hangouts messages are sent over a Google-internal xmpp bridge.
    They can mostly be treated normally, with two exceptions:

      * Hangouts senders have weird jids and don't reveal their email. This isn't
        a huge problem because we get their full name through the roster.
      * the body of Hangouts invites is never seen. This might be a bug? Or just something
        Google didn't want to build an extension for? Either way, this situation
        usually resolves itself, since we'll respond to the first message in the new conversation.

    There is a way to respond to chat invites, but it seems to be more trouble than it's worth.
    It involves listening for:
      * a roster subscription request from a Hangouts jid
      * later, a resource under that jid coming online
    """

    def __init__(self, email, token, response, notify_email, response_throttle=datetime.timedelta(seconds=60)):
        """
        Args:
            email (string): see GChatBot.
            token (string): see GChatBot.
            response (string): the message to respond with.
            notify_email (string): if not None, an email will be sent for each response.
            response_throttle (datetime.timedelta): no more than one response will be sent during this interval.
        """

        self.response = response
        self.notify_email = notify_email
        self.response_throttle = response_throttle

        self.last_reply_datetime = {}  # {jid: datetime.datetime}

        super(AutoRespondBot, self).__init__(email, token)

        self.add_event_handler('message', self.message)

        # uncomment this to respond to chat invites.
        # self.add_event_handler('roster_subscription_request',
        #                        self.roster_subscription_request)
        # self.add_event_handler('presence_available', self.presence_available)

        self.hangouts_jids_seen = set()

    def message(self, msg):
        """Respond to Hangouts/gchat normal messages."""

        if msg['type'] in ('chat', 'normal') and not self._throttled(msg['from']):
            jid = msg['from']
            body = msg.get('body')
            self.logger.info("responding to %s via message. message %r", jid, msg)
            msg.reply(self.response).send()
            self._sent_reply(jid, body)

    def roster_subscription_request(self, presence):
        """Watch for Hangouts bridge chat invites and add them to `hangouts_jids_seen`."""

        from_jid = presence['from']

        if from_jid.domain == 'public.talk.google.com':
            # Hangouts users get these goofy jids.
            # Replying to them doesn't seem to work, but replying to resources under it will.
            # So, we store the bare jid, with a weird name thing stripped out, then
            # wait for a resource to become active.
            if '--' in from_jid.user:
                waiting_jid = from_jid.bare.partition('--')[-1]
            else:
                waiting_jid = from_jid.bare

            self.logger.info("saw hangouts jid %s. message %r", from_jid, presence)
            self.hangouts_jids_seen.add(waiting_jid)

    def presence_available(self, presence):
        """Watch for Hangouts bridge jids coming online and respond to any in `hangouts_jids_seen`."""

        from_jid = presence['from']
        if from_jid.bare in self.hangouts_jids_seen and from_jid.resource:
            self.hangouts_jids_seen.remove(from_jid.bare)
            if not self._throttled(from_jid):
                # Message type is important; omitting it will silently discard the message.
                self.logger.info("responding to %s via presence. message %r", from_jid, presence)
                self.send_message(mto=from_jid, mbody=self.response, mtype='chat')
                self._sent_reply(from_jid)

    def _sent_reply(self, jid, message=None):
        """Perform any bookkeeping needed after a response is sent.

        Args:
            jid: the jid that was responded to.
            message (string): the message received. None if unknown.
        """

        self.last_reply_datetime[jid] = datetime.datetime.now()

        report_ga_event_async(self.email, category='message', action='receive')

        if self.notify_email is not None:
            from_identifier = jid.jid
            from_nick = self.client_roster[jid.jid]['name']
            if from_nick:
                from_identifier = "%s (%s)" % (from_nick, jid.jid)

            body_paragraphs = ["gchat.simon.codes just responded to a message from %s." % from_identifier]

            if message is not None:
                body_paragraphs.append("The message we received was \"%s\"." % message.encode('utf-8'))
            else:
                body_paragraphs.append("Due to a bug on Google's end, we didn't receive a message body.")

            body_paragraphs.append("We replied with your autoresponse \"%s\"." % self.response.encode('utf-8'))

            body_paragraphs.append("If any of this is unexpected or strange, email simon@simonmweber.com for support.")

            email = EmailMessage(
                subject='gchat.simon.codes sent an autoresponse',
                to=[self.notify_email],
                body='\n\n'.join(body_paragraphs),
                reply_to=['noreply@gchat.simon.codes'],
            )
            email.send(fail_silently=True)
            self.logger.info("sent an email notification to %r", self.notify_email)

    def _throttled(self, jid):
        """Return True if we're currently throttled and should not send a message."""

        throttled = False
        if jid in self.last_reply_datetime:
            throttled = (datetime.datetime.now() - self.last_reply_datetime[jid]) < self.response_throttle

        if throttled:
            self.logger.info("bot is throttled")

        return throttled


if __name__ == '__main__':
    xmpp = AutoRespondBot(*sys.argv[1:])
    xmpp.connect()
    xmpp.process()
