from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import unittest
from unittest import mock
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes

try:
    from ansible_collections.sd_hardy.logtail.plugins.modules import logtail_source
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


class TestLogtailSourceModule(unittest.TestCase):

    def setUp(self):
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

        self.patch_remove_source = mock.patch(
            MOCK_PATH+'.remove_source')
        self.addCleanup(self.patch_remove_source.stop)
        self.mocked_remove_source = self.patch_remove_source.start()

        self.patch_update_source = mock.patch(
            MOCK_PATH+'.update_source')
        self.addCleanup(self.patch_update_source.stop)
        self.mocked_update_source = self.patch_update_source.start()

        self.patch_create_source = mock.patch(
            MOCK_PATH+'.create_source')
        self.addCleanup(self.patch_create_source.stop)
        self.mocked_create_source = self.patch_create_source.start()

    def test_required_args(self):
        set_module_args({})
        with self.assertRaises(AnsibleFailJson) as r:
            logtail_source.main()
        self.assertEqual(
            'missing required arguments: token',
            r.exception.args[0]['msg'])

    def test_state_present_no_params(self):
        set_module_args({
            'token': 'token',
            'state': 'present'
        })
        with self.assertRaises(AnsibleFailJson) as r:
            logtail_source.main()
        self.assertEqual(
            'missing required arguments: name, platform',
            r.exception.args[0]['msg'])

    def test_state_present(self):
        source_id = 123456
        source = LogtailSource(id=source_id)
        self.mocked_get_source.return_value=source
        set_module_args({
            'token': 'token',
            'state': 'present',
            'id': source_id
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(source_id)
        self.assertFalse(r.exception.args[0]['changed'])
        self.assertEqual(
            dict,
            type(r.exception.args[0]['source']))
        self.assertEqual(
            'Source present',
            r.exception.args[0]['message'])

    def test_state_absent_missing_id(self):
        set_module_args({
            'token': 'token',
            'state': 'absent'
        })
        with self.assertRaises(AnsibleFailJson) as r:
            logtail_source.main()
        self.assertEqual(
            'missing required arguments: id',
            r.exception.args[0]['msg'])

    def test_state_absent_bad_id(self):
        source_id = 111111
        self.mocked_get_source.return_value=False
        set_module_args({
            'token': 'token',
            'state': 'absent',
            'id': source_id
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(source_id)
        self.assertFalse(r.exception.args[0]['changed'])
        self.assertEqual(
            'Source not found',
            r.exception.args[0]['message'])

    def test_state_absent_api_exc(self):
        source_id = 111112
        self.mocked_get_source.side_effect=LogtailApiError(
            msg="Invalid response from API")
        set_module_args({
            'token': 'token',
            'state': 'absent',
            'id': source_id
        })
        with self.assertRaises(AnsibleFailJson) as r:
            logtail_source.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(source_id)
        self.assertFalse(r.exception.args[0]['changed'])
        self.assertEqual(
            'Invalid response from API',
            r.exception.args[0]['msg'])

    def test_state_absent_checkmode(self):
        source_id = 123456
        source = LogtailSource(id=source_id)
        self.mocked_get_source.return_value=source
        self.mocked_remove_source.return_value=True
        set_module_args({
            'token': 'token',
            'state': 'absent',
            'id': source_id,
            '_ansible_check_mode': True
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(source_id)
        self.mocked_remove_source.assert_not_called()
        self.assertTrue(r.exception.args[0]['changed'])
        self.assertFalse(r.exception.args[0]['source'])

    def test_state_absent(self):
        source_id = 123456
        source = LogtailSource(id=source_id)
        self.mocked_get_source.return_value=source
        self.mocked_remove_source.return_value=True
        set_module_args({
            'token': 'token',
            'state': 'absent',
            'id': source_id
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(source_id)
        self.mocked_remove_source.assert_called_once()
        self.mocked_remove_source.assert_called_with(source_id)
        self.assertTrue(r.exception.args[0]['changed'])
        self.assertEqual(
            dict,
            type(r.exception.args[0]['source']))
        self.assertEqual(
            'Removed source',
            r.exception.args[0]['message'])

    def test_update_checkmode(self):
        source_id = 123456
        source_name = 'updated'
        self.mocked_get_source.return_value = LogtailSource(
            id=source_id,
            name='test')
        set_module_args({
            'token': 'token',
            'state': 'present',
            'name': source_name,
            'id': source_id,
            '_ansible_check_mode': True
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(source_id)
        self.mocked_update_source.assert_not_called()
        self.assertFalse(r.exception.args[0]['source'])
        self.assertTrue(r.exception.args[0]['changed'])

    def test_state_present_update(self):
        source_id = 123456
        source_name = 'updated'
        source_ingest = False
        source_autogen = False
        self.mocked_get_source.return_value = LogtailSource(
            id=source_id,
            name='test',
            ingest_paused=True,
            autogen_views=True)
        self.mocked_update_source.return_value = LogtailSource(
            id=source_id,
            name=source_name,
            ingest_paused=source_ingest,
            autogen_views=source_autogen)
        set_module_args({
            'token': 'token',
            'state': 'present',
            'name': source_name,
            'autogen_views': source_autogen,
            'ingest_paused': source_ingest,
            'id': source_id
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_get_source.assert_called_once()
        self.mocked_get_source.assert_called_with(source_id)
        self.mocked_update_source.assert_called_once()
        self.mocked_update_source.assert_called_with(
            source_id,
            source_name,
            source_autogen,
            source_ingest)
        self.assertEqual(
            dict,
            type(r.exception.args[0]['source']))
        self.assertEqual(
            'Updated source',
            r.exception.args[0]['message'])

    def test_state_present_create_update(self):
        source_id = 654321
        source_name = 'new'
        source_platform = 'ubuntu'
        source_ingest = True
        source_autogen = True
        self.mocked_create_source.return_value = LogtailSource(
            id=source_id,
            name=source_name,
            platform=source_platform)
        self.mocked_update_source.return_value = LogtailSource(
            id=source_id,
            name=source_name,
            ingest_paused=source_ingest,
            autogen_views=source_autogen)
        set_module_args({
            'token': 'token',
            'state': 'present',
            'name': source_name,
            'autogen_views': source_autogen,
            'ingest_paused': source_ingest,
            'platform': source_platform
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_create_source.assert_called_once()
        self.mocked_create_source.assert_called_with(
            source_name,
            source_platform)
        self.mocked_update_source.assert_called_once()
        self.mocked_update_source.assert_called_with(
            source_id,
            source_name,
            source_autogen,
            source_ingest)
        self.assertTrue(r.exception.args[0]['changed'])
        self.assertEqual(
            dict,
            type(r.exception.args[0]['source']))
        self.assertEqual(
            'Created source',
            r.exception.args[0]['message'])

    def test_state_present_create(self):
        source_id = 654321
        source_name = 'created'
        source_platform = 'mongodb'
        self.mocked_create_source.return_value = LogtailSource(
            id=source_id,
            name=source_name,
            platform=source_platform)
        set_module_args({
            'token': 'token',
            'state': 'present',
            'name': source_name,
            'platform': source_platform
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_create_source.assert_called_once()
        self.mocked_create_source.assert_called_with(
            source_name,
            source_platform)
        self.assertTrue(r.exception.args[0]['changed'])
        self.assertEqual(
            dict,
            type(r.exception.args[0]['source']))
        self.assertEqual(
            'Created source',
            r.exception.args[0]['message'])

    def test_create_checkmode(self):
        source_id = 654321
        source_name = 'created'
        source_platform = 'mongodb'
        set_module_args({
            'token': 'token',
            'name': source_name,
            'platform': source_platform,
            '_ansible_check_mode': True
        })
        with self.assertRaises(AnsibleExitJson) as r:
            logtail_source.main()
        self.mocked_create_source.assert_not_called()
        self.assertTrue(r.exception.args[0]['changed'])
        self.assertFalse(r.exception.args[0]['source'])
