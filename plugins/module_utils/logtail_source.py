#!/usr/bin/python

#Copyright: (c) 2022, Skyler Hardy <skyler.hardy@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""This module is used by the Logtail Source modules as part of the logtail
ansible collection.

To use this module, include it as part of a custom module as shown below:

  from ansible_collections.sh_hardy.logtail.plugins.module_utils.logtail_source import LogtailSource
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class LogtailSource():

    def __init__(
            self,
            id: int=None,
            name: str=None,
            platform: str=None,
            token: str=None,
            ingest_paused: bool=None,
            autogen_views: bool=None,
            created_at: str=None,
            updated_at: str=None,
            retention: int=None,
            table_name: str=None,
            team_id: int=None):
        self.id = id
        self.name = name
        self.platform = platform
        self.token = token
        self.ingest_paused = ingest_paused
        self.autogen_views = autogen_views
        self.created_at = created_at
        self.updated_at = updated_at
        self.retention = retention
        self.table_name = table_name
        self.team_id = team_id

    def requires_update(self, name, ingest, autogen):
        if name is not None and name != self.name:
            return True
        if ingest is not None and ingest != self.ingest_paused:
            return True
        if autogen is not None and autogen != self.autogen_views:
            return True
        return False

    def get_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'platform': self.platform,
            'token': self.token,
            'ingest_paused': self.ingest_paused,
            'autogen_views': self.autogen_views,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'retention': self.retention,
            'table_name': self.table_name,
            'team_id': self.team_id
        }
