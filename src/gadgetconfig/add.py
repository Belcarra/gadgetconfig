#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python noexpandtab

# gadgetconfig configures and enables a Gadget USB configuration
#

import os
import sys
import fnmatch

"""gadget.py: ..."""

# __author__  = "Stuart.Lynne@belcarra.com"


class AddGadget(object):

	def __init__(self, configpath, pathname=None, verbose=False, sh=False, enable=False):
		self.configpath = configpath
		self.sh = sh
		self.enable = enable
		self.pathname = pathname
		self.verbose = verbose
		#print("AddGadget: sh: %s" % (sh), file=sys.stderr)
		#print("AddGadget: verbose: %s" % (verbose), file=sys.stderr)
		# self.verbose = True

	def vprint(self, s):
		if self.verbose:
			print(s, file=sys.stderr)

	def echo(self, path, s):
		print("echo \"%s\" > \"%s\"" % (s.strip(), path), file=sys.stdout)

	def echobin(self, path, binarray):
		bytes = [ "\\\\x%02x" % (b) for b in binarray ]
		s = "".join(map(str, bytes))
		print("echo -ne \"%s\" > \"%s\"" % (s, path), file=sys.stdout)

	def write_str(self, path, s):
		self.vprint("write_str: %s \"%s\"" % (path, s.strip()))
		if self.sh:
			self.echo(path, s)
			return
		try:
			f = open(path, "a")
			f.writelines(s)
			f.close()
		except (PermissionError):
			self.vprint("%s %s PERMISSION DENIED" % (path, s.strip()))

	def write_bytes(self, path, bytes):
		self.vprint("write_bytes: %s \"%s\"" % (path, bytes))
		# print("write_bytes: %s \"%s\"" % (path, bytes), file=sys.stderr)
		intarray = [int(b, 0) for b in bytes]
		binarray = bytearray(intarray)
		if self.sh:
			self.echobin(path, binarray)
			return
		# print("write_bytes: %s" % (binarray), file=sys.stderr)
		try:
			f = open(path, "ab")
			f.write(binarray)
			f.close()
		except (PermissionError):
			self.vprint("%s PERMISSION DENIED" % (path))

	def write_8bytes(self, path, s):
		self.vprint("write_bytes: %s \"%s\"" % (path, bytes))
		while len(s) < 8: s += '\0'
		binarray = s.encode()
		if self.sh:
			self.echobin(path, binarray)
			return
		# print("write_8bytes: %s" % (binarray), file=sys.stderr)
		try:
			f = open(path, "ab")
			f.write(binarray)
			f.close()
		except (PermissionError):
			self.vprint("%s PERMISSION DENIED" % (path))

	def makedirs(self, lpath, existsok=False):
		self.vprint("makedirs: %s" % (lpath))
		if self.sh:
			print("mkdir -p \"%s\"" % (lpath), file=sys.stdout)
			return
		try:
			os.makedirs(lpath)
		except (FileExistsError):
			if existsok: return
			self.vprint("makedirs: %s FileExistsError" % (lpath))
			exit(1)

	def symlink(self, src, target):
		if self.sh:
			print("ln -s \"%s\" \"%s\"" % (src, target), file=sys.stdout)
			return
		self.vprint("symlink: %s -> %s" % (target, src))
		os.symlink(src, target)

	def hex_or_str(self, v):
		if isinstance(v, (int)):
			return "0x%02x\n" % v
		else:
			return "%s\n" % v

	# create_strings
	# For each language create a stings/lang directory containing
	# a file for each string descriptor. E.g.
	#
	#   strings/0x409/
	#   strings/0x409/manfacturer
	#   strings/0x409/product
	#
	def create_strings(self, path, string_dicts):
		exclude = ['#*']
		for lang in string_dicts:
			if any(fnmatch.fnmatch(lang, pattern) for pattern in exclude):
				continue
			spath = "%s/strings/%s" % (path, lang)
			self.makedirs(spath)
			string_dict = string_dicts[lang]
			for s in string_dict:
				self.write_str("%s/%s" % (spath, s), "%s\n" % string_dict[s])

	# add_attrs
	# Add misc attributes to a path, convert ints to hex strings,
	# ignoring dictionary entries with values that are not int or str.
	#
	def add_attrs(self, path, dict, exclude=[]):
		#print("add_attrs: path: %s dict: %s" % (path, dict), file=sys.stderr)
		exclude.append("#*")
		for a in dict:
			if any(fnmatch.fnmatch(a, pattern) for pattern in exclude):
				continue
			#print("add_attrs: path: %s %s type: %s" % (path, a, type(dict[a])), file=sys.stderr)
			if isinstance(dict[a], (int, str)):
				self.write_str("%s/%s" % (path, a), self.hex_or_str(dict[a]))

	# create_device_os_desc
	# Create the Gadget Device os_desc directory, with symlink to
	# configuration.
	def create_device_os_desc(self, path, device_definition):

		# print('create_device_os_desc: %s' % (device_definition))
		try:
			os_descs_dict = device_definition['os_desc']
		except (KeyError):
			return

		# print("create_device_os_descs_dict: %s" % (os_descs_dict), file=sys.stderr)
		if os_descs_dict is None:
			return

		if 'use' not in os_descs_dict:
			return

		if os_descs_dict['use'] != "1":
			return

		lpath = "%s/os_desc" % (path)
		self.makedirs(lpath, existsok=True)

		# See if we have separate config_id and config_name, use
		# to compose config name to build src and target paths.
		try:
			config_id = os_descs_dict['config_id']
			config_name = os_descs_dict['config_name']
			config = "%s.%s" % (config_name, config_id)
			src = "/%s/configs/%s" % (path, config)
			target = "%s/%s" % (lpath, config)
			self.symlink(src, target)
		except KeyError:
			pass

		self.add_attrs(lpath, os_descs_dict, exclude=['config_id', 'config_name'])

	# create_subfunctions
	#
	def create_subfunctions(self, subfunction_path, subfunction_dict):
		print("create_subfunctions: %s" % (subfunction_dict), file=sys.stderr)
		self.makedirs(subfunction_path, existsok=True)
		self.add_attrs(subfunction_path, subfunction_dict)

	# create_functions
	# Create the Gadget Device Functions
	def create_functions(self, path, functions_dict):

		# print("create_functions: %s" % (functions_dict), file=sys.stderr)

		functions_path = "%s/functions" % (path)
		exclude = ['#*']
		for function_name in functions_dict:
			if any(fnmatch.fnmatch(function_name, pattern) for pattern in exclude):
				continue

			function_path = "%s/%s" % (functions_path, function_name)
			function_dict = functions_dict[function_name]

			self.makedirs(function_path)
			self.add_attrs(function_path, function_dict)

			# mass storage has sub lun.0...lun.N directories
			for l in function_dict:
				if not fnmatch.fnmatch(l, 'lun.*'): continue
				# print("****\ncreate_functions: %s" % (l), file=sys.stderr)
				self.create_subfunctions("%s/%s" % (function_path, l), function_dict[l])

			# os_desc is optional, may not be present
			if 'os_desc' in function_dict:
				function_os_descs = function_dict['os_desc']
				for interface in function_os_descs:
					interface_ids = function_os_descs[interface]
					ipath = "%s/os_desc/%s" % (function_path, interface)
					# print("create_functions: ipath: %s" % (ipath), file=sys.stderr)
					# print("create_functions: %s" % (interface_ids), file=sys.stderr)

					self.makedirs("%s/os_desc" % (function_path), existsok=True)
					self.makedirs(ipath, existsok=True)
					for id in ['compatible_id', 'sub_compatible_id']:
						self.write_8bytes("%s/%s" % (ipath, id), interface_ids[id])

			# report_descs is optional, typical hid only
			if 'report_desc' in function_dict:
				rpath = "%s/report_desc" % (function_path)
				self.write_bytes(rpath, function_dict['report_desc'])

	# create_configs
	# Create the Gadget Device Configurations
	def create_configs(self, path, configs_dict):

		# print("create_configs: %s" % (configs_dict), file=sys.stderr)

		configs_path = "%s/configs" % (path)

		for config_name in configs_dict:
			config_dict = configs_dict[config_name]
			# print("create_configs: %s" % (config_name), file=sys.stderr)
			# print("create_configs: %s" % (config_dict), file=sys.stderr)

			# create directory and add the attributes and strings
			config_path = "%s/%s" % (configs_path, config_name)
			self.makedirs(config_path)
			self.add_attrs(config_path, config_dict)
			self.create_strings(config_path, config_dict['strings'])

			# add the function symlinks
			function_dict = config_dict['functions']
			for f in function_dict:
				# print("create_configs: f: %s" % (f), file=sys.stderr)
				function = f['function']
				target = "%s/%s" % (config_path, f['name'])
				# src = "%s/functions/%s" % (path, function.replace("_", "."))
				src = "%s/functions/%s" % (path, function)
				# target = "%s/%s" % (config_path, f)
				self.symlink(src, target)

	# add_device_json
	# Create a Gadget Device definition from saved json configuratiion
	#
	def add_device_json(self, device_definition, device_name=None):

		if self.sh:
			print("#!/bin/sh", file=sys.stdout)
			print("# Created from %s\n" % (self.pathname), file=sys.stdout)

		print("add_device_json", file=sys.stderr)
		device_path = "%s/%s" % (self.configpath, device_name)
		self.makedirs(device_path)

		# handle device attributes, anything at the top level that is a string
		# or int, not a dict
		self.add_attrs(device_path, device_definition)

		# add the strings, functions, configs and os_desc
		#
		self.create_strings(device_path, device_definition['strings'])
		self.create_functions(device_path, device_definition['functions'])
		self.create_configs(device_path, device_definition['configs'])
		self.create_device_os_desc(device_path, device_definition)

		if self.sh and self.enable:
			print("\nbasename /sys/class/udc/* > %s/UDC" % (device_path))

