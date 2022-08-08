#!/usr/bin/python

# Copyright: (c) 2022, Skyler Hardy <skyler.hardy@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: logtail_source

short_description: Manage Logtail sources.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "2.12.0"

description: A module to manage sources via the Logtail Sources API.

options:
    id:
        description: The ID of the Logtail source to update/delete.
        required: false
        type: int
    name:
        description: The name of the Logtail source.
        required: false
        type: str
    platform:
        description: The Platform for the source. You can only set this during creation.
        required: false
        type: str
        choices:
        - kubernetes
        - docker
        - ruby
        - python
        - javascript
        - node
        - logstash
        - fluentbit
        - fluentd
        - rsyslog
        - syslog-ng
        - http
        - vector
        - heroku
        - ubuntu
        - apache2
        - nginx
        - postgresql
        - mysql
        - mongodb
        - redis
        - cloudflare_worker
        - dokku
    ingest_paused:
        description: Pause log ingesting for this source
        required: false
        type: bool
    autogen_views:
        description:
            - Should Logtail automatically generate Views for this source?
            - This option is only applicable to the ubuntu platform.
        required: false
        type: bool
    token:
        description: Your Logtail API Token.
        required: true
        type: str
    state:
        description: State of the source.
        required: false
        default: present
        type: str
        choices:
        - present
        - absent
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
#extends_documentation_fragment:
#    - sd_hardy.logtail.my_doc_fragment_name
author:
    - Skyler Hardy (https://github.com/sd-hardy)
'''

EXAMPLES = r'''
# Create a new source
- name: Create a logtail source
  sd_hardy.logtail.logtail_source:
    name: Source1
    platform: ubuntu
    token: "{{ logtail_api_token }}"
  register: create

# Print out new source details
- name: Debug register create
  debug:
    var: create

# Retreive the source ID
- name: Get new source ID
  set_fact:
    my_source: create.source

# Update an existing source
- name: Update a source
  sd_hardy.logtail.logtail_source:
    id: "{{ my_source.id }}"
    name: UpdatedSource1
    ingest_paused: true
    autogen_views: false
    token: "{{ logtail_api_token }}"

# Delete a source
- name: Delete a source
  sd_hardy.logtail.logtail_source:
    id: "{{ my_source.id }}"
    token: "{{ logtail_api_token }}"
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message the module generates.
    type: str
    returned: always
    sample: 'Source created'
source:
    description: Dictionary containing the Source.
    returned: On success when state is present
    type: complex
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
    sample: {
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
        }
'''

from ansible.module_utils.basic import AnsibleModule

import json
import time
from json import JSONDecodeError
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible_collections.sd_hardy.logtail.plugins.module_utils.logtail_api import LogtailApiClient, LogtailApiError

def run_module():
    module_args = dict(
        token=dict(type='str', required=True, no_log=True),
        id=dict(type='int', required=False, default=None),
        name=dict(type='str', required=False, default=None),
        autogen_views=dict(type='bool', required=False, default=None),
        ingest_paused=dict(type='bool', required=False, default=None),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        platform=dict(type='str', required=False, choices=[
            'kubernetes', 'docker', 'ruby', 'python', 'javascript', 'node',
            'logstash', 'fluentbit', 'fluentd', 'rsyslog', 'syslog-ng',
            'http', 'vector', 'heroku', 'ubuntu', 'apache2', 'nginx',
            'postgresql', 'mysql', 'mongodb', 'redis', 'cloudflare_worker',
            'dokku'
        ]),
    )

    result = dict(
        changed=False,
        message='',
        source=dict(),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    id = module.params['id']
    name = module.params['name']
    token = module.params['token']
    state = module.params['state']
    platform = module.params['platform']
    ingest = module.params['ingest_paused']
    autogen = module.params['autogen_views']
    lt = LogtailApiClient(token)

    if state == 'absent':
        if id is None:
            return module.fail_json(
                msg="missing required arguments: id",
                **result
            )
        source = None
        try:
            source = lt.get_source(id)
        except LogtailApiError as e:
            return module.fail_json(msg=e.msg, **result)
        if not source:
            result['message'] = "Source not found"
            return module.exit_json(**result)
        else:  # Source was found
            if module.check_mode:
                result['changed'] = True
                return module.exit_json(**result)
            removed = None
            try:
                removed = lt.remove_source(id)
            except LogtailApiError as e:
                return module.fail_json(msg=e.msg, **result)
            if not removed:
                module.fail_json(
                    msg="An error occurred while removing "
                    "source ID %s" % source['id'],
                    **result
                )
            result['changed'] = True
            result['state'] = 'absent'
            result['message'] = "Removed source"
            result['source'] = source.get_dict()
            return module.exit_json(**result)
    if state == 'present':
        if id is not None:
            source = None
            try:
                source = lt.get_source(id)
            except LogtailApiError as e:
                return module.fail_json(msg=e.msg, **result)
            if not source:  # Source not found
                return module.fail_json(
                    msg="No source found with ID %s" % id,
                    **result
                )
            # Source exists
            if not source.requires_update(name, ingest, autogen):
                result['message'] = 'Source present'
                result['source'] = source.get_dict()
                return module.exit_json(**result)
            # Update the source
            if module.check_mode:
                result['changed'] = True
                return module.exit_json(**result)
            updated = None
            try:
                updated = lt.update_source(
                    source.id,
                    name,
                    autogen,
                    ingest)
            except LogtailApiError as e:
                return module.fail_json(msg=e.msg, **result)
            if updated:
                result['changed'] = True
                result['message'] = "Updated source"
                result['source'] = updated.get_dict()
                return module.exit_json(**result)
        if name is None or platform is None:
            return module.fail_json(
                msg="missing required arguments: "
                "name, platform",
                **result
            )
        if module.check_mode:
            result['changed'] = True
            return module.exit_json(**result)
        created = None
        try:
            created = lt.create_source(name, platform)
        except LogtailApiError as e:
            return module.fail_json(msg=e.msg, **result)
        if not created:
            module.fail_json(
                msg="An error occurred while creating "
                "a new source", **result
            )
        else:  # Created source successfully
            result['changed'] = True
            result['message'] = "Created source"
            result['source'] = created.get_dict()
            # Check if we need to set any additional params
            #  after creating the source, such as disable ingest
            if created.requires_update(name, ingest, autogen):
                updated = None
                try:
                    updated = lt.update_source(
                        created.id,
                        name,
                        autogen,
                        ingest)
                except LogtailApiError as e:
                    return module.fail_json(msg=e.msg, **result)
                if updated:
                    result['source'] = updated.get_dict()
            module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
