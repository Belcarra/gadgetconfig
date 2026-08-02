#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""MCP tools for the existing gadgetconfig command line interface."""

import argparse
import ast
import glob
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path


DEFAULT_TIMEOUT = int(os.environ.get("PIGADGET_MCP_TIMEOUT", "20"))
GADGETCONFIG_BIN = os.environ.get("PIGADGET_MCP_GADGETCONFIG", "gadgetconfig")
DEFAULT_PROFILE_DIRS = [
	"/etc/gadgetservice",
	"/usr/share/gadgetconfig/definitions",
	str(Path(__file__).resolve().parents[2] / "definitions"),
]


class GadgetError(Exception):
	"""Raised for validation errors before a command is run."""


def _allowed_profile_dirs():
	value = os.environ.get("PIGADGET_MCP_PROFILE_DIRS")
	if value:
		return [Path(p).resolve() for p in value.split(":") if p]
	return [Path(p).resolve() for p in DEFAULT_PROFILE_DIRS]


def _run(argv, timeout=DEFAULT_TIMEOUT):
	try:
		completed = subprocess.run(
			argv,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			universal_newlines=True,
			timeout=timeout,
			check=False,
		)
		return {
			"argv": argv,
			"returncode": completed.returncode,
			"stdout": completed.stdout,
			"stderr": completed.stderr,
			"ok": completed.returncode == 0,
		}
	except FileNotFoundError:
		return {
			"argv": argv,
			"returncode": 127,
			"stdout": "",
			"stderr": "command not found: %s" % argv[0],
			"ok": False,
		}
	except subprocess.TimeoutExpired as exc:
		return {
			"argv": argv,
			"returncode": 124,
			"stdout": exc.stdout or "",
			"stderr": exc.stderr or "command timed out",
			"ok": False,
		}


def _gadgetconfig(args):
	return _run([GADGETCONFIG_BIN] + list(args))


def _parse_suffix(output, prefix):
	for line in output.splitlines():
		line = line.strip()
		if line.startswith(prefix):
			return line[len(prefix):].strip()
	return None


def _parse_list(value):
	if not value:
		return []
	try:
		parsed = ast.literal_eval(value)
		if isinstance(parsed, list):
			return parsed
	except (SyntaxError, ValueError):
		pass
	return [value]


def _query():
	queries = {
		"current": _gadgetconfig(["--query-gadget"]),
		"defined": _gadgetconfig(["--query-gadgets"]),
		"functions": _gadgetconfig(["--query-gadget-functions"]),
		"udc": _gadgetconfig(["--query-udc"]),
	}
	current_text = queries["current"]["stderr"] + queries["current"]["stdout"]
	defined_text = queries["defined"]["stderr"] + queries["defined"]["stdout"]
	functions_text = queries["functions"]["stderr"] + queries["functions"]["stdout"]
	udc_text = queries["udc"]["stderr"] + queries["udc"]["stdout"]
	return {
		"current_gadget": _parse_suffix(current_text, "Currently configured:"),
		"defined_gadgets": _parse_list(_parse_suffix(defined_text, "Currently defined gadgets:")),
		"active_functions": _parse_list(_parse_suffix(functions_text, "UDC Function:")),
		"udc_state": _parse_suffix(udc_text, "UDC State:"),
		"udc_function": _parse_suffix(udc_text, "UDC Function:"),
		"commands": queries,
	}


def _read_text(path):
	try:
		with open(path, "r") as fh:
			return fh.read().strip()
	except (OSError, UnicodeDecodeError):
		return None


def _qmult_values():
	values = {}
	for path in glob.glob("/sys/kernel/config/usb_gadget/*/functions/*/qmult"):
		values[path] = _read_text(path)
	return values


def _usb_interfaces():
	result = _run(["ip", "-brief", "addr", "show"])
	interfaces = []
	for line in result["stdout"].splitlines():
		parts = line.split()
		if not parts:
			continue
		name = parts[0]
		if not re.match(r"^usb[0-9]+$", name):
			continue
		interfaces.append({
			"name": name,
			"state": parts[1] if len(parts) > 1 else "",
			"addresses": parts[2:] if len(parts) > 2 else [],
			"raw": line,
		})
	return {"interfaces": interfaces, "command": result}


def _kernel_log_tail(lines=80):
	result = _run(["dmesg", "--color=never"], timeout=10)
	if result["stdout"]:
		result["stdout"] = "\n".join(result["stdout"].splitlines()[-int(lines):])
	return result


def _proc_arp():
	return _read_text("/proc/net/arp") or ""


def _resolve_profile(profile):
	path = Path(profile)
	candidates = []
	if path.is_absolute():
		candidates.append(path)
	else:
		for directory in _allowed_profile_dirs():
			candidates.append(directory / profile)
			if not profile.endswith(".json"):
				candidates.append(directory / ("%s.json" % profile))

	allowed = _allowed_profile_dirs()
	for candidate in candidates:
		resolved = candidate.resolve()
		if not resolved.is_file():
			continue
		if any(str(resolved).startswith(str(directory) + os.sep) or resolved == directory for directory in allowed):
			return str(resolved)
	raise GadgetError("profile is not in an approved directory or does not exist: %s" % profile)


def _override_args(overrides):
	args = []
	allowed = [
		"idVendor",
		"idProduct",
		"manufacturer",
		"product",
		"serialnumber",
		"dev_addr",
		"host_addr",
		"qmult",
		"name",
	]
	for key in allowed:
		value = overrides.get(key)
		if value is not None:
			args.extend(["--%s" % key, str(value)])
	if overrides.get("auto_serialnumber"):
		args.append("--auto_serialnumber")
	return args


def _select_usb_interface(interfaces):
	if not interfaces:
		return None
	for iface in interfaces:
		if iface.get("state") == "UP":
			return iface["name"]
	for iface in interfaces:
		if "LOWER_UP" in iface.get("raw", ""):
			return iface["name"]
	return interfaces[0]["name"]


def _configure_static_ip(interface, address):
	if not re.match(r"^usb[0-9]+$", interface):
		raise GadgetError("refusing to configure non-usb interface: %s" % interface)
	return [
		_run(["ip", "addr", "flush", "dev", interface]),
		_run(["ip", "addr", "add", address, "dev", interface]),
		_run(["ip", "link", "set", interface, "up"]),
	]


def gadget_inventory():
	"""Return host, gadgetconfig, UDC, profile, and usb interface inventory."""
	query = _query()
	interfaces = _usb_interfaces()
	version = _gadgetconfig(["--version"])
	return {
		"hostname": socket.gethostname(),
		"gadgetconfig_version": (version["stdout"] + version["stderr"]).strip(),
		"profile_dirs": [str(p) for p in _allowed_profile_dirs()],
		"current_gadget": query["current_gadget"],
		"defined_gadgets": query["defined_gadgets"],
		"active_functions": query["active_functions"],
		"udc_state": query["udc_state"],
		"udc_function": query["udc_function"],
		"usb_interfaces": interfaces["interfaces"],
		"diagnostics": {
			"version": version,
			"query": query["commands"],
			"ip": interfaces["command"],
		},
	}


def gadget_status(include_logs=False):
	"""Return current gadget, UDC, qmult, interface, ARP, and optional logs."""
	query = _query()
	interfaces = _usb_interfaces()
	status = {
		"current_gadget": query["current_gadget"],
		"defined_gadgets": query["defined_gadgets"],
		"active_functions": query["active_functions"],
		"udc_state": query["udc_state"],
		"udc_function": query["udc_function"],
		"qmult": _qmult_values(),
		"usb_interfaces": interfaces["interfaces"],
		"selected_usb_interface": _select_usb_interface(interfaces["interfaces"]),
		"arp": _proc_arp(),
		"diagnostics": {
			"query": query["commands"],
			"ip": interfaces["command"],
		},
	}
	if include_logs:
		status["kernel_log_tail"] = _kernel_log_tail()
	return status


def gadget_add_profile(profile, overrides=None):
	"""Add a gadget profile from an approved path or bundled definition."""
	overrides = overrides or {}
	profile_path = _resolve_profile(profile)
	return {
		"profile_path": profile_path,
		"result": _gadgetconfig(["--add", profile_path] + _override_args(overrides)),
	}


def gadget_enable(name):
	"""Enable an already defined gadget."""
	return {"result": _gadgetconfig(["--enable", name]), "status": gadget_status(False)}


def gadget_disable():
	"""Disable the currently enabled gadget."""
	return {"result": _gadgetconfig(["--disable"]), "status": gadget_status(False)}


def gadget_soft_connect():
	"""Attach the configured UDC to the host."""
	return {"result": _gadgetconfig(["--soft-connect"]), "status": gadget_status(False)}


def gadget_soft_disconnect():
	"""Detach the configured UDC from the host."""
	return {"result": _gadgetconfig(["--soft-disconnect"]), "status": gadget_status(False)}


def gadget_configure_profile(profile, name=None, static_ip=None, overrides=None):
	"""Disable current gadget, add/reuse a profile, enable it, and rediscover usbN."""
	overrides = dict(overrides or {})
	if name is not None:
		overrides["name"] = name
	add_result = gadget_add_profile(profile, overrides=overrides)
	enable_name = name
	if enable_name is None:
		query = _query()
		profile_path = Path(add_result["profile_path"])
		candidates = [profile_path.stem] + query["defined_gadgets"]
		enable_name = candidates[0]

	disable_result = _gadgetconfig(["--disable"])
	enable_result = _gadgetconfig(["--enable", enable_name])
	status = gadget_status(False)
	ip_results = []
	if static_ip:
		iface = status["selected_usb_interface"]
		if not iface:
			raise GadgetError("cannot configure static IP; no usbN interface found")
		ip_results = _configure_static_ip(iface, static_ip)
		status = gadget_status(False)
	return {
		"profile": add_result,
		"disable": disable_result,
		"enable": enable_result,
		"static_ip": ip_results,
		"status": status,
	}


def gadget_collect_logs(lines=120):
	"""Collect lightweight diagnostic evidence for a gadget test run."""
	return {
		"status": gadget_status(False),
		"kernel_log_tail": _kernel_log_tail(lines=lines),
	}


def _build_mcp(host, port, log_level):
	try:
		from mcp.server.fastmcp import FastMCP
	except ImportError:
		print("pigadget-mcp requires the optional 'mcp' Python package", file=sys.stderr)
		print("Install it on the Pi with: pip3 install mcp", file=sys.stderr)
		raise

	mcp = FastMCP(
		"pigadget-mcp",
		instructions="Typed Raspberry Pi USB gadget tools backed by gadgetconfig.",
		host=host,
		port=port,
		log_level=log_level,
	)

	mcp.tool(name="gadget.inventory")(gadget_inventory)
	mcp.tool(name="gadget.status")(gadget_status)
	mcp.tool(name="gadget.add_profile")(gadget_add_profile)
	mcp.tool(name="gadget.enable")(gadget_enable)
	mcp.tool(name="gadget.disable")(gadget_disable)
	mcp.tool(name="gadget.soft_connect")(gadget_soft_connect)
	mcp.tool(name="gadget.soft_disconnect")(gadget_soft_disconnect)
	mcp.tool(name="gadget.configure_profile")(gadget_configure_profile)
	mcp.tool(name="gadget.collect_logs")(gadget_collect_logs)
	return mcp


def main():
	parser = argparse.ArgumentParser(description="MCP server for Raspberry Pi gadgetconfig")
	parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
	parser.add_argument("--host", default=os.environ.get("PIGADGET_MCP_HOST", "127.0.0.1"))
	parser.add_argument("--port", type=int, default=int(os.environ.get("PIGADGET_MCP_PORT", "8000")))
	parser.add_argument("--log-level", default=os.environ.get("PIGADGET_MCP_LOG_LEVEL", "INFO"))
	parser.add_argument("--json-status", action="store_true", help="print status JSON and exit")
	args = parser.parse_args()

	if args.json_status:
		print(json.dumps(gadget_status(include_logs=False), indent=2, sort_keys=True))
		return

	mcp = _build_mcp(args.host, args.port, args.log_level)
	mcp.run(transport=args.transport)


if __name__ == "__main__":
	main()
