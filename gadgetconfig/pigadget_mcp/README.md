# pigadget_mcp

`pigadget_mcp` exposes selected Raspberry Pi USB gadget operations as MCP tools.
It is intentionally a typed wrapper around the existing `gadgetconfig` CLI, not
a general shell interface.

## Install

Base `gadgetconfig` remains dependency-light. Install MCP support explicitly:

```sh
pip3 install 'gadgetconfig[mcp]'
```

For source-tree testing:

```sh
PYTHONPATH=. PIGADGET_MCP_GADGETCONFIG=./gadgetconfig-runner.py \
  python3 -m gadgetconfig.pigadget_mcp.server --json-status
```

## Run

Use stdio for local MCP clients:

```sh
pigadget-mcp
```

Use streamable HTTP for a Pi node endpoint:

```sh
pigadget-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## Tools

- `gadget.inventory`
- `gadget.status`
- `gadget.add_profile`
- `gadget.enable`
- `gadget.disable`
- `gadget.soft_connect`
- `gadget.soft_disconnect`
- `gadget.configure_profile`
- `gadget.collect_logs`

Profile paths are restricted to approved directories. Override with
`PIGADGET_MCP_PROFILE_DIRS=/etc/gadgetservice:/path/to/definitions`.
