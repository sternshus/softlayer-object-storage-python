"""
    Transport Methods

    See COPYING for license information
"""
from socket import timeout

import sys
import re
if sys.version_info.major == 2:
    from urllib2 import Request, urlopen
    from urlparse import urlparse
    from httplib import HTTPConnection, HTTPSConnection
else:
    from urllib.request import Request, urlopen
    from urllib.parse import urlparse
    from http.client import HTTPConnection, HTTPSConnection

from object_storage.errors import ResponseError, NotFound
from object_storage import consts


class Response(object):
    def __init__(self):
        self.status_code = 0
        self.version = 0
        self.phrase = self.verb = None
        self.headers = {}
        self.content = None

    def raise_for_status(self):
        if self.status_code == 404:
            raise NotFound(self.status_code, "Not Found")
        if (self.status_code >= 300) and (self.status_code < 400):
            raise ResponseError(self.status_code,
                                '%s Redirection' % self.status_code)
        elif (self.status_code >= 400) and (self.status_code < 500):
            raise ResponseError(self.status_code,
                                '%s Client Error' % self.status_code)
        elif (self.status_code >= 500) and (self.status_code < 600):
            raise ResponseError(self.status_code,
                                '%s Server Error' % self.status_code)


class BaseAuthenticatedConnection:
    def _authenticate(self):
        """ Do authentication and set token and storage_url """
        self.auth_headers = self.auth.auth_headers
        self.token = self.auth.auth_token
        self.storage_url = self.auth.storage_url

    def get_headers(self):
        """ Get default headers for this connection """
        return dict([('User-Agent', consts.USER_AGENT)] + list(self.auth_headers.items()))

    def chunk_upload(self, method, url, size=None, headers=None):
        """ Returns new ChunkedConnection """
        headers = headers or {}
        headers.update(self.get_headers())
        return ChunkedUploadConnection(self, method, url, size=size,
                                       headers=headers)

    def chunk_download(self, url, chunk_size=10 * 1024):
        """ Returns new ChunkedConnection """
        headers = self.get_headers()
        req = Request(url)
        for k, v in headers.items():
            req.add_header(k, v)
        r = urlopen(req)
        while True:
            buff = r.read(chunk_size)
            if not buff:
                break
            yield buff


class BaseAuthentication(object):
    """
        Base Authentication class. To be inherited if you want to create
        a new Authentication method. authenticate() should be overwritten.
    """
    def __init__(self, auth_url=None,
                 protocol='https',
                 datacenter='dal05',
                 network='public'):
        self.auth_url = auth_url
        self.protocol = protocol or 'https'
        self.datacenter = datacenter or 'dal05'
        self.network = network or 'public'

        self.use_default_storage_url = True
        if not auth_url:
            self.use_default_storage_url = False
            dc_endpoints = consts.ENDPOINTS.get(self.datacenter)

            if not dc_endpoints:
                dc_endpoints = consts.dc_endpoints(self.datacenter)

            self.auth_url = dc_endpoints.get(self.network) \
                                        .get(self.protocol)

        self.storage_url = None
        self.auth_token = None
        self.authenticated = False

    def get_storage_url(self, storage_urls):
        if self.use_default_storage_url:
            return storage_urls[storage_urls['default']]
        if self.network in storage_urls:
            return storage_urls[self.network]
        return None

    @property
    def auth_headers(self):
        return {'X-Auth-Token': 'AUTH_TOKEN'}

    def authenticate(self):
        """
            Called when the client wants to authenticate. self.storage_url and
            self.auth_token needs to be set.
        """
        self.storage_url = 'STORAGE_URL'
        self.auth_token = 'AUTH_TOKEN'
        self.authenticated = True


class ChunkedUploadConnection:
    """
        Chunked Connection class.
        send_chunk() will send more data.
        finish() will end the request.
    """
    def __init__(self, conn, method, url, size=None, headers=None):
        self.conn = conn
        self.method = method
        self.req = None
        self._chunked_encoding = True
        headers = headers or {}

        if size is None:
            headers['Transfer-Encoding'] = 'chunked'
        else:
            self._chunked_encoding = False
            headers['Content-Length'] = str(size)

        if 'ETag' in headers:
            del headers['ETag']

        scheme, netloc, path, params, query, fragment = urlparse(url)
        match = re.match('([a-zA-Z0-9\-\.]+):?([0-9]{2,5})?', netloc)

        if match:
            (host, port) = match.groups()
        else:
            ValueError('Invalid URL')

        if not port:
            if scheme == 'https':
                port = 443
            else:
                port = 80

        port = int(port)

        if scheme == 'https':
            self.req = HTTPSConnection(host, port)
        else:
            self.req = HTTPConnection(host, port)
        try:
            self.req.putrequest('PUT', path)
            for key, value in headers.items():
                self.req.putheader(key, value)
            self.req.endheaders()
        except Exception as e:
            raise ResponseError(0, 'Disconnected: %s' % e)

    def send(self, chunk):
        """ Sends a chunk of data. """
        try:
            if self._chunked_encoding:
                self.req.send("%X\r\n" % len(chunk))
                self.req.send(chunk)
                self.req.send("\r\n")
            else:
                self.req.send(chunk)
        except timeout as err:
            raise err
        except:
            raise ResponseError(0, 'Disconnected')

    def finish(self):
        """ Finished the request out and receives a response. """
        try:
            if self._chunked_encoding:
                self.req.send("0\r\n\r\n")
        except timeout as err:
            raise err
        except:
            raise ResponseError(0, 'Disconnected')

        res = self.req.getresponse()
        content = res.read()

        r = Response()
        r.status_code = res.status
        r.version = res.version
        r.headers = dict([(k.lower(), v) for k,v in res.getheaders()])
        r.content = content
        r.raise_for_status()
        return r


class ChunkedDownloadConnection:
    def __init__(self, conn, method, url, headers=None):
        self.conn = conn
        self.method = method
        self.url = url
        self.req = None
        self.headers = headers or {}
