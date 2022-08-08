#!/usr/bin/python

#Copyright: (c) 2022, Skyler Hardy <skyler.hardy@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""This module is used by the Logtail Source modules as part of the logtail
ansible collection.

To use this module, include it as part of a custom module as shown below:

  from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_api import LogtailApiClient
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from json import JSONDecodeError
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_source import LogtailSource


class LogtailApiError(Exception):
    def __init__(self, msg):
        self.msg = msg


class LogtailApiClient():

    def __init__(self, token):
        self.baseurl = 'https://logtail.com/api'
        self.api_version = 1
        self.api_endpoint = 'sources'
        self.agent = "ansible-logtail (Python-urllib/3.8)"
        self.headers = dict(
            Authorization='Bearer %s' % token
        )

    def _build_url(
            self,
            version=None,
            endpoint=None,
            source=None):
        url = self.baseurl + '/v'
        url += str(version) + '/' if version is not \
            None else str(self.api_version) + '/'
        url += endpoint if endpoint is not None \
            else self.api_endpoint
        if source:
            url += '/' + str(source)
        return url

    def _format_payload(self, source):
        params = list()
        for key, val in vars(source).items():
            if val is not None:
                if key == 'autogen_views':
                    key = 'autogenerate_views'
                if key == 'ingest_paused':
                    key = 'ingesting_paused'
                if isinstance(val, bool):
                    val = str(val).lower()
                params.append('='.join([key, str(val)]))
        return '&'.join(params).encode()

    def _format_source(self, source):
        return LogtailSource(
            id=source['id'],
            name=source['attributes']['name'],
            platform=source['attributes']['platform'],
            token=source['attributes']['token'],
            ingest_paused=source['attributes']['ingesting_paused'],
            autogen_views=source['attributes']['autogenerate_views'],
            created_at=source['attributes']['created_at'],
            updated_at=source['attributes']['updated_at'],
            retention=source['attributes']['retention'],
            table_name=source['attributes']['table_name'],
            team_id=source['attributes']['team_id'])

    def request(self, method='GET', url=None, data=None):
        """ Make a request to the Logtail API """
        if not url:
            url = self._build_url()
        try:
            response = open_url(
                url,
                method=method,
                data=data,
                headers=self.headers,
                http_agent=self.agent
            )
            # Handle empty success repsonse
            if response.status == 204:
                return True
            resp_obj = json.loads(response.read())
            # Catch empty API response
            if 'data' not in resp_obj:
                raise LogtailApiError(
                    "Invalid response from API. Status"
                    "URL: %s code: %i, Response Body: %s"
                    % (url, response.status, response.read())
                )
            return resp_obj
        except HTTPError as error:
            message = error.reason
            # Capture error message from API response
            if 'Content-type' in error.headers and \
                    'application/json' in \
                    error.headers['Content-type'].lower():
                try:
                    resp_body = error.read()
                    resp_obj = json.loads(resp_body)
                    # Return false from 404
                    if error.status == 404:
                        return False
                    if 'errors' in resp_obj:
                        message = resp_obj['errors']
                except JSONDecodeError as err:
                    raise LogtailApiError(
                        "Error decoding response from "
                        "server. Reason: %s. %s %s"
                        % (err.msg, err.doc, err.pos)
                    )
            raise LogtailApiError(
                "Unable to complete API request. "
                "URL: %s, Status code: %i, Reason: %s"
                % (url, error.status, message)
            )
        except JSONDecodeError as err:
            raise LogtailApiError(
                "Error decoding response from server. "
                "Reason: %s. %s %s"
                % (err.msg, err.doc, err.pos)
            )
        except URLError as error:
            raise LogtailApiError(
                "Unable to complete API request. "
                "Reason: %s" % error.reason
            )

    def get_source(self, source_id):
        response = self.request(
            url=self._build_url(source=source_id)
        )
        if response and 'data' in response:
            return self._format_source(response['data'])
        return False

    def update_source(self, source_id, name, autogen, ingest):
        response = self.request(
            method='PATCH',
            url=self._build_url(source=source_id),
            data=self._format_payload(
                LogtailSource(
                    name=name,
                    autogen_views=autogen,
                    ingest_paused=ingest
                )
            )
        )
        if response and 'data' in response:
            return self._format_source(response['data'])
        return False

    def remove_source(self, source_id):
        return self.request(
            method='DELETE',
            url=self._build_url(source=source_id)
        )

    def create_source(self, name, platform):
        response = self.request(
            method='POST',
            data=self._format_payload(LogtailSource(
                name=name,
                platform=platform
            ))
        )
        if response and 'data' in response:
            return self._format_source(response['data'])
        return False

    def get_all_sources(self):
        url = None
        sources = list()
        while True:
            response = self.request(url=url)
            if response and 'data' in response:
                for source in response['data']:
                    sources.append(self._format_source(source).get_dict())
                if response['pagination']['next'] is not None:
                    url = response['pagination']['next']
                else:
                    break
            else: return False
        return sources
