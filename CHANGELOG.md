# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0]

Major release: multi-broker management, observability, composable skills, blue-green migration,
and security hardening. **61 tools and 16 skills.**

### Added
- **Multi-broker support** — register multiple brokers by alias and switch the active broker at
  runtime (`rabbitmq_broker_select`, `rabbitmq_broker_list_registered_brokers`). See
  [docs/multi-broker.md](docs/multi-broker.md).
- **OAuth broker auth** — `rabbitmq_broker_initialize_connection_with_oauth` connects using an access
  token instead of username/password.
- **HTTP transport with JWT/JWKS Bearer auth** — run as a remote server (`--http`) with token
  validation against a JWKS endpoint, including issuer/audience/scope enforcement, 5-minute JWKS
  caching, and cache-bust-and-retry on key rotation (`src/auth.py`). See
  [docs/authentication.md](docs/authentication.md).
- **Observability tools** — `rabbitmq_broker_get_overview`, `rabbitmq_broker_find_queues_by_threshold`,
  `rabbitmq_broker_get_connection_churn`.
- **16 composable skills** — workflow recipes for migration, dead-letter analysis, topology graphs,
  capacity planning, and policy conflict detection, accessed via `rabbitmq_broker_get_skill`. See
  [docs/skills.md](docs/skills.md).
- **Blue-green migration** — readiness checks, definition export with transforms
  (`strip_cmq_keys`, `convert_classic_to_quorum`, `drop_empty_policies`, `obfuscate_credentials`,
  `exclude_users`, `exclude_permissions`), federation-based draining, and queue rebalancing. See
  [docs/migration.md](docs/migration.md).
- Health-check, cluster/node, policy/shovel, and definition tools.
- Project documentation under [docs/](docs/).

### Changed
- Migrated to **FastMCP 3.x**; `pydantic<2.14`.
- Mutative tools remain gated behind `--allow-mutative-tools` (off by default).

### Security
- Management API requests use protocol-aware TLS verification (`verify=(protocol == "https")`) so
  HTTPS brokers stay verified while plain-HTTP dev brokers work without spurious errors.
- All Management API requests carry connect/read timeouts (`REQUEST_TIMEOUT = (5, 30)`) to prevent a
  stalled broker from hanging the agent.
- Path segments (vhosts, queue/exchange/protocol names) are URL-encoded to prevent injection.

## [2.2.4]

Previous release line. Baseline broker read/CRUD tooling over stdio.
