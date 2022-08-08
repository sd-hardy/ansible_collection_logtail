from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import unittest
from unittest import mock
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes

try:
    from ansible_collections.sd_hardy.logtail.plugins.modules import logtail_source_info
    from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_api import LogtailApiClient, LogtailApiError
    from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_source import LogtailSource
    MOCK_PATH = "ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_api.LogtailApiClient"
except ImportError:
    print("ImportError")    

class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


def mocked_exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def mocked_fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class TestLogtailSourceInfoModule(unittest.TestCase):

    def setUp(self):
        self.source = LogtailSource(
            id=123456,
            name='source1',
            platform='ubuntu')
        self.source2 = LogtailSource(
            id=123457,
            name='source2',
            platform='ubuntu')
        self.source3 = LogtailSource(
            id=123458,
            name='newSource',
            platform='mongodb')

        self.mock_module_helper = mock.patch.multiple(
            basic.AnsibleModule,
            exit_json=mocked_exit_json,
            fail_json=mocked_fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
       
        self.patch_get_source = mock.patch(
            MOCK_PATH+'.get_source')
        self.addCleanup(self.patch_get_source.stop)
        self.mocked_get_source = self.patch_get_source.start()

        self.patch_all_sources = mock.patch(
            MOCK_PATH+'.get_all_sources')
        self.addCleanup(self.patch_all_sources.stop)
        self.mocked_all_sources = self.patch_all_sources.start()

    def test_required_args(self):
        set_module_args({})
        with self.assertRaises(AnsibleFailJson) as r:
            logtail_source_info.main()
        self.assertEqual(
            'missing required arguments: token',
            r.exception.args[0]['msg'])

    def test_get_by_id(self):
        self.mocked_get_source.return_value = self.source
        set_module_args({
            'token': 'token',
            'id': self.source.id
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source_info.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(self.source.id)
        self.assertFalse(r.exception.args[0]['changed'])
        self.assertEqual(
            list, type(r.exception.args[0]['sources']))
        self.assertEqual(
            dict, type(r.exception.args[0]['sources'][0]))
        self.assertEqual(
            self.source.id, r.exception.args[0]['sources'][0]['id'])

    def test_get_by_id_not_found(self):
        self.mocked_get_source.return_value=False
        set_module_args({
            'token': 'token',
            'id': self.source.id
        })
        with self.assertRaises(AnsibleFailJson) as r:
            logtail_source_info.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(self.source.id)
        self.assertFalse(r.exception.args[0]['changed'])
        self.assertEqual(
            'No source found with ID %s' % self.source.id,
            r.exception.args[0]['msg'])

    def test_get_by_id_api_exc(self):
        self.mocked_get_source.side_effect = LogtailApiError(
            'Internal Server Error')
        set_module_args({
            'token': 'token',
            'id': self.source.id
        })
        with self.assertRaises(AnsibleFailJson) as r:
            logtail_source_info.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(self.source.id)
        self.assertEqual(
            'Internal Server Error',
            r.exception.args[0]['msg'])

    def test_all_sources_api_exc(self):
        self.mocked_all_sources.side_effect = LogtailApiError(
            'Internal Server Error')
        set_module_args({
            'token': 'token'
        })
        with self.assertRaises(AnsibleFailJson) as r:
            logtail_source_info.main()
        self.mocked_all_sources.assert_called_once()
        self.mocked_all_sources.assert_called_with()
        self.assertEqual(
            'Internal Server Error',
            r.exception.args[0]['msg'])

    def test_all_sources_empty_resp(self):
        self.mocked_all_sources.return_value = False
        set_module_args({'token': 'token'})
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source_info.main()
        self.mocked_all_sources.assert_called_once()
        self.mocked_all_sources.assert_called_with()
        self.assertEqual(
            list, type(r.exception.args[0]['sources']))
        self.assertFalse(r.exception.args[0]['sources'])
        self.assertFalse(r.exception.args[0]['changed'])

    def test_all_sources(self):
        self.mocked_all_sources.return_value = [
            self.source, self.source2]
        set_module_args({'token': 'token'})
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source_info.main()
        self.mocked_all_sources.assert_called_once()
        self.mocked_all_sources.assert_called_with()
        self.assertEqual(
            list, type(r.exception.args[0]['sources']))
        self.assertFalse(r.exception.args[0]['changed'])
        self.assertTrue(r.exception.args[0]['sources'])
        self.assertEqual(
            dict, type(r.exception.args[0]['sources'][0]))
        self.assertEqual(
            dict, type(r.exception.args[0]['sources'][1]))
        self.assertEqual(
            self.source.id, 
            r.exception.args[0]['sources'][0]['id'])
        self.assertEqual(
            self.source2.name, 
            r.exception.args[0]['sources'][1]['name'])

    def test_source_by_name(self):
        self.mocked_all_sources.return_value = [
            self.source, self.source2]
        set_module_args({
            'token': 'token',
            'name': 'source2'
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source_info.main()
        self.mocked_all_sources.assert_called_once()
        self.mocked_all_sources.assert_called_with()
        self.assertEqual(
            list, type(r.exception.args[0]['sources']))
        self.assertFalse(r.exception.args[0]['changed'])
        self.assertTrue(r.exception.args[0]['sources'])
        self.assertEqual(
            dict, type(r.exception.args[0]['sources'][0]))
        self.assertEqual(
            self.source2.name, 
            r.exception.args[0]['sources'][0]['name'])

    def test_source_by_filter(self):
        self.mocked_all_sources.return_value = [
            self.source, self.source2, self.source3]
        set_module_args({
            'token': 'token',
            'filter': {
                'platform': 'mongodb'
            }
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source_info.main()
        self.mocked_all_sources.assert_called_once()
        self.mocked_all_sources.assert_called_with()
        self.assertEqual(
            list, type(r.exception.args[0]['sources']))
        self.assertFalse(r.exception.args[0]['changed'])
        self.assertTrue(r.exception.args[0]['sources'])
