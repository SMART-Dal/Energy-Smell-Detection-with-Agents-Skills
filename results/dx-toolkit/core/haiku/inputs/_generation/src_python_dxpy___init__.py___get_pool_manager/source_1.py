import os
import ssl
import dxpy
from dxpy import _get_pool_manager

# Create dummy certificate files under WORKDIR (they are only stored as paths by urllib3)
_CA_FILE = WORKDIR / "ca.pem"
_CERT_FILE = WORKDIR / "cert.pem"
_KEY_FILE = WORKDIR / "key.pem"
_CA_FILE.write_text("-----BEGIN CERTIFICATE-----\nDUMMY\n-----END CERTIFICATE-----\n")
_CERT_FILE.write_text("-----BEGIN CERTIFICATE-----\nDUMMY\n-----END CERTIFICATE-----\n")
_KEY_FILE.write_text("-----BEGIN PRIVATE KEY-----\nDUMMY\n-----END PRIVATE KEY-----\n")

_SSL_CONTEXT = ssl.create_default_context()

_ENV_KEYS = ('DX_USE_OS_CA_BUNDLE', 'DX_CA_CERT',
             'http_proxy', 'HTTP_PROXY', 'https_proxy', 'HTTPS_PROXY')

def _clear_env():
    for k in _ENV_KEYS:
        os.environ.pop(k, None)

def _set_env(**kwargs):
    _clear_env()
    for k, v in kwargs.items():
        os.environ[k] = v

def _reset_pool():
    dxpy._pool_manager = None

def _make_args(verify, cert_file, key_file, ssl_context, env=None):
    if env is None:
        _clear_env()
    else:
        _set_env(**env)
    _reset_pool()
    return (verify, cert_file, key_file, ssl_context)

def checks():
    return [
        ("default",        lambda: _make_args(None, None, None, None)),
        ("noverify-env",   lambda: _make_args(None, None, None, None,
                                              env={'DX_CA_CERT': 'NOVERIFY'})),
        ("odd-verify",     lambda: _make_args([], None, None, None)),
    ]

def cases():
    return [
        ("verify-false",   lambda: _make_args(False, None, None, None)),
        ("verify-path",    lambda: _make_args(str(_CA_FILE), None, None, None)),
        ("cert-file",      lambda: _make_args(None, str(_CERT_FILE), str(_KEY_FILE), None)),
        ("ssl-context",    lambda: _make_args(None, None, None, _SSL_CONTEXT,
                                              env={'DX_CA_CERT': str(_CA_FILE)})),
        ("dx-ca-noverify", lambda: _make_args(None, None, None, None,
                                              env={'DX_CA_CERT': 'NOVERIFY'})),
        ("proxy-auth",     lambda: _make_args(None, None, None, None,
                                              env={'DX_CA_CERT': str(_CA_FILE),
                                                   'http_proxy': 'http://user:pass@proxy.example.com:8080'})),
        ("proxy-noauth",   lambda: _make_args(False, None, None, None,
                                              env={'https_proxy': 'https://proxy.example.com:3128'})),
        ("cached-os-ca",   lambda: _make_args(None, None, None, None,
                                              env={'DX_USE_OS_CA_BUNDLE': '1',
                                                   'http_proxy': 'http://proxy.example.com:8080'})),
    ]
