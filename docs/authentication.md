# Authentication

There are **two independent auth layers**. Don't confuse them:

1. **Broker auth** — how the server authenticates *to the RabbitMQ broker*.
2. **Server (transport) auth** — how *MCP clients* authenticate to this server when it runs over HTTP.

## 1. Broker auth

How the server proves identity to RabbitMQ's Management API and AMQP endpoint.

| Method | Tool | Notes |
|--------|------|-------|
| SIMPLE (username/password) | `rabbitmq_broker_initialize_connection` | Basic auth header generated per request |
| OAuth 2.0 (access token) | `rabbitmq_broker_initialize_connection_with_oauth` | Token passed through to the broker |

- TLS is on by default (`use_tls=True`, AMQP port 5671). The Management API client sets certificate
  verification based on protocol: `verify=(protocol == "https")`, so plain-HTTP brokers work in dev
  without spurious verification errors while HTTPS brokers stay verified.
- All Management API requests carry a connect/read timeout (`REQUEST_TIMEOUT = (5, 30)`) so a hung
  broker can't wedge the agent.

## 2. Server (transport) auth — HTTP mode

By default the server speaks MCP over **stdio** (local, no network auth needed). When you run it as a
remote server with `--http`, you can require clients to present a **JWT Bearer token**, validated
against a JWKS endpoint.

### CLI flags

| Flag | Description |
|------|-------------|
| `--http` | Use Streamable HTTP transport instead of stdio |
| `--server-port` | Port to listen on (default: 8888) |
| `--http-auth-jwks-uri` | JWKS URI used to discover signing keys |
| `--http-auth-issuer` | Expected `iss` claim (optional but recommended) |
| `--http-auth-audience` | Expected `aud` claim (optional but recommended) |
| `--http-auth-required-scopes` | Space-separated scopes the token must carry |

### Example

```bash
uv run amq-mcp-server-rabbitmq \
  --http --server-port 8888 \
  --http-auth-jwks-uri https://idp.example.com/.well-known/jwks.json \
  --http-auth-issuer https://idp.example.com/ \
  --http-auth-audience rabbitmq-mcp \
  --http-auth-required-scopes "rabbitmq.read rabbitmq.write"
```

### How verification works

`JWKSBearerVerifier` (`src/auth.py`) validates RS256-signed JWTs:

1. Fetches and **caches the JWKS for 5 minutes** to avoid a network round-trip per request.
2. On a validation failure it **busts the cache once and retries** — this handles IdP key rotation
   gracefully (a token signed with a freshly rotated key won't be rejected just because the cached
   key set is stale).
3. Enforces `iss`, `aud` (string or array), and `required_scopes` when configured.
4. Rejections are logged at DEBUG with the specific reason (issuer mismatch, audience mismatch,
   missing scopes, expired, etc.) to make misconfiguration diagnosable without leaking token
   contents at higher log levels.

Set `FASTMCP_LOG_LEVEL=DEBUG` to see auth-rejection reasons during setup.

## Which do I need?

- Running locally in Claude Desktop over stdio: only **broker auth**.
- Hosting the server for remote/multi-user access: add **server auth** (`--http` + JWKS flags) so
  only authorized callers reach the tools; broker auth still governs what the server can do to
  RabbitMQ.
