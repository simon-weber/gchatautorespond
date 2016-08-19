from mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, Client

from gchatautorespond.apps.autorespond.models import AutoResponse, GoogleCredential

# todo
# login redirects to index
# auth and oauth callback hit their views? be better to test functionality


def user(i):
    return User.objects.create_user(
        username="user%s" % i,
        password='password',
        email="user%s@example.com" % i,
    )


def post_first_autorespond(client, response, credentials, notifications):
    form_data = {
        'form-TOTAL_FORMS': 1,
        'form-INITIAL_FORMS': 0,
        'form-MIN_NUM_FORMS': 0,
        'form-MAX_NUM_FORMS': 1000,
        'form-0-response': 'autorespond one',
        'form-0-credentials': credentials.id,
        'form-0-email_notifications': 'on',
        'form-0-id': '',
    }

    return client.post('/autorespond/', form_data, follow=True)


class UnauthedTestCase(TestCase):

    def test_auth_required(self):
        for url in ('/autorespond/auth/', '/autorespond/oauth2callback/'):
            res = Client().get(url)
            self.assertEqual(res.status_code, 302)


class AuthedTestCase(TestCase):

    def setUp(self):
        self.user = user(1)
        self.c = Client()
        self.assertTrue(self.c.login(username='user1', password='password'))

    def test_index_no_autoresponds(self):
        self.assertEqual(len(AutoResponse.objects.all()), 0)
        self.assertEqual(self.c.get('/autorespond/').status_code, 200)

    def test_index_with_autoresponds(self):
        AutoResponse.objects.create(
            response='autorespond one', user=self.user,
            credentials=GoogleCredential.objects.create(user=self.user, email=self.user.email))

        AutoResponse.objects.create(
            response='autorespond two', user=self.user,
            credentials=GoogleCredential.objects.create(user=self.user, email='other@example.com'))

        self.assertContains(self.c.get('/autorespond/'), 'autorespond one')
        self.assertContains(self.c.get('/autorespond/'), 'autorespond two')

    @patch('gchatautorespond.apps.autorespond.views.WorkerIPC')
    def test_adding_autorespond(self, _):
        cred = GoogleCredential.objects.create(user=self.user, email=self.user.email)
        self.assertEqual(len(AutoResponse.objects.all()), 0)

        self.assertContains(post_first_autorespond(self.c, 'autorespond one', cred, 'on'), 'autorespond one')

        autoresponds = AutoResponse.objects.all()
        self.assertEqual(len(autoresponds), 1)
        autorespond = autoresponds[0]
        self.assertEqual(autorespond.response, 'autorespond one')
        self.assertEqual(autorespond.user, self.user)
        self.assertEqual(autorespond.credentials, cred)
        self.assertEqual(autorespond.email_notifications, True)

    @patch('gchatautorespond.apps.autorespond.views.WorkerIPC')
    def test_adding_autorespond_for_other_users_credentials_fails(self, _):
        other_cred = GoogleCredential.objects.create(user=user(2), email=self.user.email)
        self.assertEqual(post_first_autorespond(self.c, 'autorespond one', other_cred, 'on').status_code, 400)

        autoresponds = AutoResponse.objects.all()
        self.assertEqual(len(autoresponds), 0)

    @patch('gchatautorespond.apps.autorespond.views.WorkerIPC')
    def test_only_my_autoresponds_show(self, _):
        cred = GoogleCredential.objects.create(user=self.user, email=self.user.email)
        self.assertEqual(len(AutoResponse.objects.all()), 0)

        self.assertContains(post_first_autorespond(self.c, 'autorespond one', cred, 'on'), 'autorespond one')

        other_client = Client()
        other_client.login(username=user(2).username, password='password')
        res = other_client.get('/autorespond/')
        self.assertNotContains(res, 'autorespond one')
        self.assertNotContains(res, self.user.email)
