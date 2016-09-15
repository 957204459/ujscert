import shlex

from OpenSSL import crypto
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse_lazy


def gen_cert(agent_uuid):
    with open(settings.CA_CERT) as f:
        ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())

    with open(settings.CA_KEY) as f:
        ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, f.read(), settings.CA_KEY_PASSPHRASE)

    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    # cert.get_subject().C = "IN"
    # cert.get_subject().ST = "AP"
    # cert.get_subject().L = "127.0.0.1"
    # cert.get_subject().O = 'a'
    # cert.get_subject().OU = hostgroup_uuid.hex
    cert.get_subject().CN = agent_uuid.hex
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(99 * 365 * 24 * 60 * 60)
    cert.set_serial_number(agent_uuid.int)
    cert.set_issuer(ca_cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(ca_key, 'sha1')

    return \
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode(), \
        crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode()


def parse_dn(dn):
    return dict((part.split('=') for part in dn.split('/') if '=' in part))


staff_required = staff_member_required(login_url=reverse_lazy('login'))


def parse_query(query):
    tokens = shlex.split(query)
    dsl = {'search': []}
    key = ''
    for token in tokens:
        if token.endswith(':'):
            key = token[:-1]
        else:
            if ':' in token:
                key, word = token.split(':', 1)
                dsl[key] = word
            elif key:
                dsl[key] = token or ''
            else:
                dsl['search'].append(token)

            key = ''

    if key:
        dsl[key] = ''

    return dsl


