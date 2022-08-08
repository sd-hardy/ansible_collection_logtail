# Copyright: (c) 2022, Skyler Hardy <skyler.hardy@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: logtail_source_info

short_description: Pulls Logtail source data from the logtail API

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "2.12.0"

description: Pull Logtail Source data from the logtail API.

options:
    id:
        description: Pull A logtail source via name
        required: false
        type: int
    name:
        description: Pull a logtail source by name
        required: false
        type: str
    filter:
        description: Pull logtail sources by key-value filter
        required: false
        type: dict
    token:
        description: Your Logtail API Token.
        required: true
        type: str
#extends_documentation_fragment:
#    - sd_hardy.logtail.my_doc_fragment_name
author:
    - Skyler Hardy (https://github.com/sd-hardy)
'''

EXAMPLES = r'''
- name: return all sources
  sd_hardy.logtail.logtail_source_info:
    token: "{{ logtail_token }}"

- name: return a single source by id
  sd_hardy.logtail.logtail_source_info:
    token: "{{ logtail_token }}"
    id: 123456

- name: return sources with name
  sd_hardy.logtail.logtail_source_info:
    token: "{{ logtail_token }}"
    name: 'source1'

- name: return sources by key-value filter
  sd_hardy.logtail.logtail_source_info:
    token: "{{ logtail_token }}"
    filter: {
      'platform': 'mongo'
    }
'''

RETURN = r'''
sources:
    description: List containing the Source(s) dictionary.
    returned: On success when state is present
    type: list
    elements: dict
    contains:
        id:
            description: The Source ID.
            type: str
            sample: 123456
        name:
            description: The Source Name.
            type: str
            sample: "MySource"
        platform:
            description: The Source platform.
            type: str
            sample: "ubuntu"
        token:
            description: The Source token.
            type: str
            sample: "zzzTMvasdj25kznafAL4At"
        ingest_paused:
            description: If log ingesting is paused.
            type: bool
            sample: true
        autogen_views:
            description: If default views are generated.
            type: bool
            sample: true
        team_id:
            description: The team to send alerts.
            type: int
            sample: 1234
        table_name:
            description: The table name for the source.
            type: str
            sample: "mysource"
        created_at:
            description: Timestamp when created
            type: str
            sample: "2022-06-10T21:24:46.409Z"
        updated_at:
            description: Timestamp when updated
            type: str
            sample: "2022-06-10T21:24:46.409Z"
        retention:
            description: Log retention period in days
            type: int
            sample: 30
    sample: [
        {
          "id": "123456",
          "name": "testSource",
          "platform": "ubuntu",
          "retention": 30,
          "table_name": "testsource",
          "autogen_views": true,  
          "ingest_paused": false,  
          "team_id": 12345,
          "token": "token",
          "created_at": "2022-06-27T19:45:17.078Z",  
          "updated_at": "2022-07-01T10:56:05.177Z"
        },
        {
          "id": "123457",
          "name": "testSource2",
          "platform": "ubuntu",
          "retention": 30,
          "table_name": "testsource2",
          "autogen_views": true,  
          "ingest_paused": false,  
          "team_id": 12345,
          "token": "token",
          "created_at": "2022-06-27T19:45:17.078Z",  
          "updated_at": "2022-07-01T10:56:05.177Z"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_api import LogtailApiClient, LogtailApiError
from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_source import LogtailSource

def match_source(filter, source):
    for key,val in filter.items():
        if val in source[key].lower():
            return True
    return False

def run_module():
    module_args = dict(
        token=dict(type='str', required=True, no_log=True),
        filter=dict(type='dict', required=False, default=None),
        name=dict(type='str', required=False, default=None),
        id=dict(type='int', required=False, default=None),
    )

    result = dict(
        changed=False,
        sources=list(),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    token = module.params['token']
    filter = module.params['filter']
    name = module.params['name']
    id = module.params['id']
    lt = LogtailApiClient(token)

    if id is not None:
        source = None
        try:
            source = lt.get_source(id)
        except LogtailApiError as e:
            return module.fail_json(msg=e.msg, **result)
        if not source:  # Source not found
            return module.fail_json(
                msg="No source found with ID %s" % id,
                ** result)
        result['sources'].append(source.get_dict())
    else:
        sources = None
        try:
            sources = lt.get_all_sources()
        except LogtailApiError as e:
            return module.fail_json(msg=e.msg, **result)
        if sources:
            for source in sources:
                if name is None and filter is None:
                    result['sources'].append(source)
                elif name is not None and name == source['name']:
                    result['sources'].append(source)
                elif filter is not None:
                    if match_source(filter, source):
                        result['sources'].append(source)
    return module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
