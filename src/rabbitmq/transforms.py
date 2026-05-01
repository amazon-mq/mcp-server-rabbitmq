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

"""Definition transformations for blue-green migration workflows.

Matches rabbitmqadmin-ng transformation capabilities. Each function takes
a definitions dict (from GET /api/definitions) and returns a modified copy.
"""

import copy

CMQ_KEYS = {
    "ha-mode",
    "ha-params",
    "ha-sync-mode",
    "ha-sync-batch-size",
    "ha-promote-on-shutdown",
    "ha-promote-on-failure",
}


def apply_transforms(definitions: dict, transforms: list[str]) -> dict:
    """Apply a list of named transformations to a definitions dict."""
    defs = copy.deepcopy(definitions)
    dispatch = {
        "strip_cmq_keys": strip_cmq_keys,
        "drop_empty_policies": drop_empty_policies,
        "convert_classic_to_quorum": convert_classic_to_quorum,
        "obfuscate_credentials": obfuscate_credentials,
        "exclude_users": exclude_users,
        "exclude_permissions": exclude_permissions,
    }
    for name in transforms:
        fn = dispatch.get(name)
        if not fn:
            available = ", ".join(dispatch.keys())
            raise ValueError(f"Unknown transform '{name}'. Available: {available}")
        defs = fn(defs)
    return defs


def strip_cmq_keys(definitions: dict) -> dict:
    """Remove classic mirrored queue keys from all policy definitions."""
    for policy in definitions.get("policies", []):
        defn = policy.get("definition", {})
        for key in CMQ_KEYS:
            defn.pop(key, None)
    return definitions


def drop_empty_policies(definitions: dict) -> dict:
    """Remove policies with empty definitions (e.g. after stripping CMQ keys)."""
    definitions["policies"] = [p for p in definitions.get("policies", []) if p.get("definition")]
    return definitions


def convert_classic_to_quorum(definitions: dict) -> dict:
    """Change x-queue-type from classic to quorum in queue arguments."""
    for queue in definitions.get("queues", []):
        args = queue.get("arguments", {})
        if args.get("x-queue-type") == "classic":
            args["x-queue-type"] = "quorum"
            queue["durable"] = True
            # Remove arguments incompatible with quorum queues
            for key in ("x-max-priority",):
                args.pop(key, None)
    return definitions


def obfuscate_credentials(definitions: dict) -> dict:
    """Replace usernames and password hashes with dummy values."""
    for i, user in enumerate(definitions.get("users", [])):
        user["name"] = f"user_{i}"
        user["password_hash"] = "REDACTED"
        if "hashing_algorithm" in user:
            user["hashing_algorithm"] = "rabbit_password_hashing_sha256"
    return definitions


def exclude_users(definitions: dict) -> dict:
    """Remove the users section from definitions."""
    definitions.pop("users", None)
    return definitions


def exclude_permissions(definitions: dict) -> dict:
    """Remove permissions and topic_permissions sections from definitions."""
    definitions.pop("permissions", None)
    definitions.pop("topic_permissions", None)
    return definitions
