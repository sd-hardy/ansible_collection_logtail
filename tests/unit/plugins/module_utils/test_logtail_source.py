from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
from unittest import mock

try:
    from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_source import LogtailSource
except ImportError:
    print("ImportError")    

class TestLogtailSourceClass(unittest.TestCase):

    def setUp(self):
        self.source = LogtailSource(
            id=123456,
            name='Source1',
            platform='ubuntu',
            token='token',
            ingest_paused=True,
            autogen_views=True,
            created_at='createdat',
            updated_at='updated_at',
            retention=30,
            table_name='Source1',
            team_id=1111)

    def test_source_requires_update(self):
        update1 = self.source.requires_update(
            'Source1', True, True)
        update2 = self.source.requires_update(None, None, None)
        update3 = self.source.requires_update(
            'Source2', None, None)
        update4 = self.source.requires_update(None, False, None)
        update5 = self.source.requires_update(None, None, False)
        self.assertFalse(update1)
        self.assertFalse(update2)
        self.assertTrue(update3)
        self.assertTrue(update4)
        self.assertTrue(update5)

    def test_source_get_dict(self):
        sourcedict = self.source.get_dict()
        self.assertEqual(dict, type(sourcedict))
        self.assertEqual(sourcedict['id'], self.source.id)
