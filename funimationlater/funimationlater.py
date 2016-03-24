# -*- coding: utf-8 -*-
from __future__ import absolute_import
from functools import wraps

from funimationlater.error import (UnknowResponse, LoginRequired,
                                   AuthenticationFailed)
from funimationlater.http import HTTPClient, HTTPClientBase
from funimationlater.models import Show

__all__ = ['FunimationLater', 'ShowTypes']


class ShowTypes(object):
    SIMULCAST = 'simulcasts'
    BROADCAST_DUBS = 'broadcast-dubs'
    SEARCH = 'search'
    SHOWS = 'shows'


def require_login(func):
    """Decorator that throws an error when user isn't logged in.

    Args:
        func: The function to wrap
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # args[0] will always be self
        if not args[0].logged_in:
            raise LoginRequired('must be logged in')
        return func(*args, **kwargs)

    return wrapper


class FunimationLater(object):
    host = 'api-funimation.dadcdigital.com'
    base_path = '/xml'
    protocol = 'https'

    def __init__(self, username=None, password=None, http_client=None):
        """
        Args:
            username (str):
            password (str):
            http_client: Must be an instance of HTTPClient
        """
        full_url = '{}://{}{}'.format(self.protocol, self.host, self.base_path)
        if http_client is None:
            self.client = HTTPClient(full_url)
        else:
            # NOTE(Sinap): using assert instead of raise here because we should
            # never use a client that is not a subclass of HTTPClientBase.
            assert issubclass(http_client, HTTPClientBase),\
                'http_client must be a subclass of HTTPClientBase'
            self.client = http_client(full_url)
        self.logged_in = False
        if username and password:
            self.login(username, password)

    def login(self, username, password):
        """Login and set the authentication headers
        Args:
            username (str):
            password (str):
        """
        resp = self.client.post('/auth/login/?',
                                {'username': username, 'password': password})
        if 'error' in resp['authentication']:
            raise AuthenticationFailed('username or password is incorrect')
        # the API returns what headers should be set
        self.client.add_headers(resp['authentication']['parameters']['header'])
        self.logged_in = True

    @require_login
    def get_my_queue(self):
        """Get the list of shows in the current users queue
        Returns:
            list[Show]:
        """
        resp = self.client.get('/myqueue/get-items/?')
        if 'watchlist' in resp:
            return [Show(x['item'], self.client) for x in
                    resp['watchlist']['items']['item']]
        raise UnknowResponse(resp)

    @require_login
    def get_history(self):
        resp = self.client.get('/history/get-items/?')
        if 'watchlist' in resp:
            return [Show(x['item'], self.client) for x in
                    resp['watchlist']['items']['historyitem']]
        raise UnknowResponse(resp)

    @require_login
    def get_shows(self, show_type, limit=20, offset=0):
        """
        Args:
            show_type (str): simulcasts, broadcast-dubs, genre
            offset (int):
            limit (int):

        Returns:
            list([Show]):
        """
        resp = self._get_content(
            id=show_type,
            sort='start_timestamp',
            sort_direction='desc',
            itemThemes='dateAddedShow',
            territory='US',
            role='g',
            offset=offset,
            limit=limit
        )
        return resp

    def search(self, query):
        """Perform a search

        Args:
            query (str): The query string

        Returns:
            list: a list of results
        """
        resp = self._get_content(
            id=ShowTypes.SEARCH,
            sort='start_timestamp',
            sort_direction='desc',
            itemThemes='dateAddedShow',
            q=query
        )
        return resp

    def get_all_shows(self, limit=20, offset=0):
        shows = self.get_shows(ShowTypes.SHOWS, limit, offset)
        if shows is None:
            return []
        else:
            return shows

    def get_simulcasts(self, limit=20, offset=0):
        shows = self.get_shows(ShowTypes.SIMULCAST, limit, offset)
        if shows is None:
            return []
        else:
            return shows

    def _get_content(self, **kwargs):
        resp = self.client.get('/longlist/content/page/', kwargs)['items']
        if isinstance(resp, (tuple, str)):
            return None
        resp = resp['item']
        if isinstance(resp, list):
            return [Show(x, self.client) for x in resp]
        else:
            return [Show(resp, self.client)]

    def __iter__(self):
        offset = 0
        limit = 20
        while True:
            shows = self.get_all_shows(limit=limit, offset=offset)
            for show in shows:
                yield show
            if len(shows) < limit:
                break
            offset += limit
