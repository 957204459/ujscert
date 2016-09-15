from django.db import connection
from ujscert.headquarter.models import Agent, Fingerprint
from django.test import TestCase, Client
from django.test.utils import override_settings


class AuthTestCase(TestCase):
    def setUp(self):
        self.agent = Agent.objects.create(name="Test Agent", description='For test purpose')

    @override_settings(DEBUG=False)
    def test_auth_production(self):
        ping = '/hq/api/ping'

        client = Client()
        response = client.get(ping)
        self.assertEqual(response.status_code, 401)

        response = client.get(ping, HTTP_X_VERIFIED='SUCCESS', HTTP_X_CERT_DN='revoked')
        self.assertEqual(response.status_code, 403)

        response = client.get(ping, HTTP_X_VERIFIED='SUCCESS', HTTP_X_CERT_DN='/CN=%s' % self.agent.uid.hex)
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=True)
    def test_auth_debug(self):
        client = Client()
        response = client.get('/hq/api/ping')
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.agent.delete()


class SearchTestCase(TestCase):
    def setUp(self):
        with connection.cursor() as cur:
            cur.execute('''CREATE EXTENSION zhparser;
                CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);
                ALTER TEXT SEARCH CONFIGURATION chinese ADD MAPPING FOR n,v,a,i,e,l WITH simple;''')

    def test_search(self):
        ssh = {
            "port": 22,
            "raw": "UGiEAgEAAAAKAA==",
            "banner": "SSH-2.0-dropbear_2014.66",
            "cpes": ["a:matt_johnston:dropbear_ssh_server:2014.66", "o:linux:linux_kernel"],
            "info": "protocol 2.0",
            "product": "Dropbear sshd", "version": "2014.66", "os": "Linux", "ip": "192.168.30.1"
        }

        Fingerprint(**ssh).save()
        self.assertEqual(Fingerprint.objects.search('SSH & Linux').count(), 1)
