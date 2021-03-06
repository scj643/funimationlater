# -*- coding: utf-8 -*-
import unittest
import urllib2
from StringIO import StringIO
from urllib import urlencode

import mock

import funimationlater.http as http
from funimationlater.response_handler import NullHandler


class TestHTTPClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = 'https://foo.bar'

    def test_get_request(self):
        with mock.patch('funimationlater.http.urllib2.urlopen') as urlopen:
            client = http.HTTPClient(self.host, NullHandler)
            header = {'Foo': 'bar'}
            client.add_headers(header)
            client.get('/')
            self.assertTrue(urlopen.called)
            request = urlopen.call_args[0][0]
            self.assertIsInstance(request, urllib2.Request)
            self.assertDictContainsSubset(header, request.headers)

    def test_get_request_with_query_string(self):
        with mock.patch('funimationlater.http.urllib2.urlopen') as urlopen:
            uri = '/foobar'
            qry = {'foo': 'bar'}
            client = http.HTTPClient(self.host, NullHandler)
            client.get(uri, qry)
            self.assertTrue(urlopen.called)
            request = urlopen.call_args[0][0]
            self.assertIsInstance(request, urllib2.Request)
            self.assertEqual(request._Request__original,
                             '{}{}?{}'.format(self.host, uri, urlencode(qry)))

    def test_post_request(self):
        with mock.patch('funimationlater.http.urllib2.urlopen') as urlopen:
            client = http.HTTPClient(self.host, NullHandler)
            expected_payload = {'foo': 'bar'}
            header = {'Foo': 'bar'}
            client.add_headers(header)
            client.post('/', expected_payload)
            self.assertTrue(urlopen.called)
            request = urlopen.call_args[0][0]
            actual_payload = urlopen.call_args[0][1]
            self.assertEqual(urlencode(expected_payload), actual_payload)
            self.assertIsInstance(request, urllib2.Request)
            self.assertDictContainsSubset(header, request.headers)

    def test_add_headers(self):
        client = http.HTTPClient(self.host)
        header = {'Foo': 'Bar'}
        client.add_headers(header)
        self.assertDictContainsSubset(header, client.headers)

    def test_add_bad_headers(self):
        client = http.HTTPClient(self.host)
        header = 'foo=bar'
        self.assertRaises(TypeError, client.add_headers, header)

    def test_build_url_correctly(self):
        with mock.patch('funimationlater.http.urllib2.urlopen') as urlopen:
            uri = 'foobar'
            client = http.HTTPClient(self.host, NullHandler)
            client.get(uri)
            self.assertTrue(urlopen.called)
            request = urlopen.call_args[0][0]
            self.assertIsInstance(request, urllib2.Request)
            self.assertEqual(request.get_full_url(),
                             '{}/{}'.format(self.host, uri))

    def test_xml_response_handling(self):
        with mock.patch('funimationlater.http.urllib2.urlopen') as urlopen:
            uri = '/foobar'
            expected = {'foo': {'bar': {'#text': 'fiz', '@bang': 'foo'}}}
            urlopen.return_value = StringIO(
                '<foo><bar bang="foo">fiz</bar></foo>')
            client = http.HTTPClient(self.host)
            actual = dict(client.get(uri))
            self.assertTrue(urlopen.called)
            request = urlopen.call_args[0][0]
            self.assertIsInstance(request, urllib2.Request)
            self.assertIsInstance(actual, dict)
            self.assertEqual(actual, expected)
