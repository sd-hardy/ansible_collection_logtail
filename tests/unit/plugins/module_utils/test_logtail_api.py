from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import io
import json
import unittest
from unittest import mock
from ansible.module_utils import basic
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError

try:
    from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_api import LogtailApiClient, LogtailApiError
    from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_source import LogtailSource
    MOCK_OPENURL_PATH = 'ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_api.open_url'
except ImportError:
    print("ImportError")    

class MockUrllibResponse:
    def __init__(self, status, body, header):
        self.status = status
        self.header = header
        self.body = body

    def read(self):
        return self.body

def mocked_exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def mocked_fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)

def generate_response(
        id='123456',
        name='test',
        platform='ubuntu',
        autogen='true',
        ingest='true',
        paging=False,
        nextpage='null'
    ):
    source = ('{"id":"'+id+'","type":"source",'
        '"attributes":{"team_id":56657,"name":'
        '"'+name+'","platform":"'+platform+'",'
        '"table_name":"test","token":'
        '"bTwMasdasd12NnafAL4At","retention":30,'
        '"ingesting_paused":'+ingest+
        ',"autogenerate_views":'+autogen+
        ',"created_at":"2022-06-10T21:24:46.409Z",'
        '"updated_at":"2022-06-11T21:43:12.740Z"}}')
    pagination = (',"pagination":{"first":null,'
        '"last":null,"next":'+nextpage+',"prev":null}')
    response = '{"data":'
    if paging:
        response += '['+source+']'+pagination
    else:
        response += source
    response += "}"
    return response

def mocked_open_url(*args, **kwargs):
    baseurl = 'https://logtail.com/api/v1'
    headers = {'Content-type': 'Application/json'}
    print('args', args)
    print('kwargs', kwargs)
    url = args[0]
    method = kwargs['method']
    headers = kwargs['headers']
    agents = kwargs['http_agent']
    data = kwargs['data']
    if url == baseurl + '/sources' and method == 'GET':
        page2 = '"'+baseurl+'/sources?page=2\"'
        return MockUrllibResponse(200,
            generate_response(
                paging=True, nextpage=page2), headers)
    if url == baseurl + '/sources?page=2' and method == 'GET':
        return MockUrllibResponse(200, 
            generate_response(paging=True), headers)
    if url == baseurl + '/sources/123456' and method == 'GET':
        return MockUrllibResponse(200, 
            generate_response(), headers)
    if url == baseurl + '/sources' and method == 'POST':
        return MockUrllibResponse(200,
            generate_response(
                name='created',platform='mongodb'), headers)
    if url == baseurl + '/sources/123456' and method == 'PATCH':
        return MockUrllibResponse(200,
            generate_response(name='updated',
                ingest='false',autogen='false'), headers)
    if url == baseurl + '/sources/123456' and method == 'DELETE':
        return MockUrllibResponse(204, '', headers)
    return MockUrllibResponse(500, 'Internal Server Error', None)


class TestLogtailApi(unittest.TestCase):

    def setUp(self):
        self.lt = LogtailApiClient('token')
        self.baseurl = 'https://logtail.com/api/v1'
        self.headers = {
            'Authorization': 'Bearer token'}
        self.agent = 'ansible-logtail (Python-urllib/3.8)'
        self.resp_headers = {'Content-type': 'Application/json'}
        self.source_response = MockUrllibResponse(200, 
            generate_response(),
            self.resp_headers)
        self.mock_module_helper = mock.patch.multiple(
            basic.AnsibleModule,
            exit_json=mocked_exit_json,
            fail_json=mocked_fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
       
        self.patch_open_url = mock.patch(MOCK_OPENURL_PATH)
        self.addCleanup(self.patch_open_url.stop)
        self.mocked = self.patch_open_url.start()

    def test_request_not_found(self):
        self.mocked.side_effect = HTTPError(
            '/sources/none',
            404, 'Resource not found',
            self.resp_headers,
            io.BytesIO(b'{"errors": "No source found"}'))
        response = self.lt.request(
            method='GET',
            url='/sources/none',
            data=None)
        self.assertEqual(response, False)
        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            '/sources/none',
            method='GET',
            data=None,
            headers=self.headers,
            http_agent=self.agent
        )
        
    def test_request_bad_content_type(self):
        with self.assertRaises(LogtailApiError):
            self.mocked.return_value = HTTPError(
                '/bad-content-type',
                200, 'Bad content type',
                {'Content-type': 'unknown'},
                io.BytesIO(b'<html></html>'))
            response = self.lt.request(
                method='GET',
                url='/bad-content-type',
                data=None)
        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            '/bad-content-type',
            method='GET',
            data=None,
            headers=self.headers,
            http_agent=self.agent
        )

    def test_request_decode_error(self):
        with self.assertRaises(LogtailApiError):
            self.mocked.side_effect = HTTPError(
                'https://logtail.com/decode_error',
                404, 'Resource not found',
                self.resp_headers, io.BytesIO(b'"}'))
            response = self.lt.request(
                method='GET',
                url='/decode_error',
                data=None)
        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            '/decode_error',
            method='GET',
            data=None,
            headers=self.headers,
            http_agent=self.agent
        )

    def test_request_nested_decode_error(self):
        with self.assertRaises(LogtailApiError):
            self.mocked.side_effect = HTTPError(
                'https://logtail.com/decode_error',
                404, 'Resource not found',
                self.resp_headers, io.BytesIO(b'"}'))
            response = self.lt.request(
                method='GET',
                url='/nested_decode_error',
                data=None)
        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            '/nested_decode_error',
            method='GET',
            data=None,
            headers=self.headers,
            http_agent=self.agent
        )

    def test_request_url_error(self):
        with self.assertRaises(LogtailApiError):
            self.mocked.side_effect = URLError(
                'Unknown error')
            response = self.lt.request(
                method='GET',
                url='/url_error',
                data=None)
        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            '/url_error',
            method='GET',
            data=None,
            headers=self.headers,
            http_agent=self.agent
        )

    def test_build_url(self):
        url1 = self.lt._build_url()
        self.assertEquals(
            url1,
            'https://logtail.com/api/v1/sources')
        url2 = self.lt._build_url(2, 'endpoint', 12345)
        self.assertEquals(
            url2,
            'https://logtail.com/api/v2/endpoint/12345')
        url3 = self.lt._build_url('3', 'sources', '54321')
        self.assertEquals(
            url3,
            'https://logtail.com/api/v3/sources/54321')

    def test_format_playload(self):
        source = LogtailSource(
            name='source1',
            platform='ubuntu',
            autogen_views=True,
            ingest_paused=True)
        payload = self.lt._format_payload(source)
        self.assertTrue(b'name=source1' in payload)
        self.assertTrue(b'platform=ubuntu' in payload)
        self.assertTrue(b'autogenerate_views=true' in payload)
        self.assertTrue(b'ingesting_paused=true' in payload)

    def test_format_source(self):
        response = json.loads(self.source_response.read())
        source = self.lt._format_source(response['data'])
        self.assertTrue(source.id)
        self.assertTrue(source.name)
        self.assertTrue(source.platform)
        self.assertTrue(source.token)
        self.assertTrue(source.ingest_paused)
        self.assertTrue(source.autogen_views)
        self.assertTrue(source.created_at)
        self.assertTrue(source.updated_at)
        self.assertTrue(source.retention)
        self.assertTrue(source.table_name)
        self.assertTrue(source.team_id)

    def test_get_source(self):
        self.mocked.side_effect=mocked_open_url
        source_id = '123456'
        url = self.baseurl + '/sources/' + source_id
        source = self.lt.get_source(source_id)

        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            url,
            method='GET',
            data=None,
            headers=self.headers,
            http_agent=self.agent
        )
        self.assertEqual(type(source), LogtailSource)
        self.assertEqual(source.id, source_id)

    def test_remove_source(self):
        self.mocked.side_effect=mocked_open_url
        source_id = '123456'
        url = self.baseurl + '/sources/' + source_id
        result = self.lt.remove_source(source_id)
        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            url,
            method='DELETE',
            data=None,
            headers=self.headers,
            http_agent=self.agent
        )
        self.assertEqual(result, True)

    def test_create_source(self):
        self.mocked.side_effect=mocked_open_url
        url = self.baseurl + '/sources'
        source = self.lt.create_source(
            'created', 'mongodb')
        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            url,
            method='POST',
            data=b'name=created&platform=mongodb',
            headers=self.headers,
            http_agent=self.agent
        )
        self.assertEqual(type(source), LogtailSource)
        self.assertEqual(source.name, 'created')
        self.assertEqual(source.platform, 'mongodb')

    def test_create_update(self):
        self.mocked.side_effect=mocked_open_url
        url = self.baseurl + '/sources'
        source = self.lt.create_source(
            'created', 'mongodb')
        self.mocked.assert_called()
        self.mocked.assert_called_with(
            url,
            method='POST',
            data=b'name=created&platform=mongodb',
            headers=self.headers,
            http_agent=self.agent
        )
        self.assertEqual(type(source), LogtailSource)
        self.assertEqual(source.name, 'created')
        self.assertEqual(source.platform, 'mongodb')

    def test_update_source(self):
        self.mocked.side_effect=mocked_open_url
        source_id = '123456'
        url = self.baseurl + '/sources/' + source_id
        source = self.lt.update_source(
            source_id, 'updated', False, False)
        self.mocked.assert_called()
        self.mocked.assert_called_once()
        self.mocked.assert_called_with(
            url,
            method='PATCH',
            data=(
                b'name=updated'
                b'&ingesting_paused=false'
                b'&autogenerate_views=false'),
            headers=self.headers,
            http_agent=self.agent
        )
        self.assertEqual(type(source), LogtailSource)
        self.assertEqual(source.name, 'updated')
        self.assertEqual(source.ingest_paused, False)
        self.assertEqual(source.autogen_views, False)

    def test_get_all_sources(self):
        self.mocked.side_effect=mocked_open_url
        url = self.baseurl + '/sources'
        sources = self.lt.get_all_sources()
        calls = [
            mock.call(
                url,
                method='GET',
                data=None,
                headers=self.headers,
                http_agent=self.agent),
            mock.call(
                url + '?page=2',
                method='GET',
                data=None,
                headers=self.headers,
                http_agent=self.agent)
        ]
        self.mocked.assert_has_calls(calls)    
        self.assertEqual(type(sources), list)
