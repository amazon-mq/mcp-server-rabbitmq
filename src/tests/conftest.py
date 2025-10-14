# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest


@pytest.fixture
def sample_queue_data():
    return [
        {"name": "queue1", "messages": 10, "vhost": "/"},
        {"name": "queue2", "messages": 5, "vhost": "/"},
    ]


@pytest.fixture
def sample_exchange_data():
    return [
        {"name": "exchange1", "type": "direct", "vhost": "/"},
        {"name": "exchange2", "type": "fanout", "vhost": "/"},
    ]


@pytest.fixture
def sample_vhost_data():
    return [{"name": "/"}, {"name": "test-vhost"}]
