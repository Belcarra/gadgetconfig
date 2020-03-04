#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python noexpandtab

# gadgetconfig configures and enables a Gadget USB configuration
#

import os
import fnmatch

"""gadget.py: ..."""

# __author__  = "Stuart.Lynne@belcarra.com"


class AddGadget(object):

	def __init__(self, configpath, verbose=False):
		self.configpath = configpath
		self.verbose = verbose
		# self.verbose = True

	def vprint(self, s):
		if self.verbose:
			print(s)

	def write_str(self, path, s):
		self.vprint("write_str: %s \"%s\"" % (path, s.strip()))
		try:
			f = open(path, "a")
			f.writelines(s)
			f.close()
		except (PermissionError):
			print("%s %s PERMISSION DENIED" % (path, s.strip()))

	def makedirs(self, lpath):
		self.vprint("makedirs: %s" % (lpath))
		os.makedirs(lpath)

	def symlink(self, src, target):
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
		print("add_attrs: path: %s dict: %s" % (path, dict))
		exclude.append("#*")
		for a in dict:
			if any(fnmatch.fnmatch(a, pattern) for pattern in exclude):
				continue
			if isinstance(dict[a], (int, str)):
				self.write_str("%s/%s" % (path, a), self.hex_or_str(dict[a]))

	# create_device_os_desc
	# Create the Gadget Device os_descs directory, with symlink to
	# configuration.
	def create_device_os_desc(self, path, device_definition):

		try:
			os_descs_dict = device_definition['os_descs']
		except (KeyError):
			return

		# print("create_device_os_descs_dict: %s" % (os_descs_dict))
		if os_descs_dict is None:
			return

		lpath = "%s/os_desc" % (path)
		self.makedirs(lpath)

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

	# create_functions
	# Create the Gadget Device Functions
	def create_functions(self, path, functions_dict):

		# print("create_functions: %s" % (functions_dict))

		functions_path = "%s/functions" % (path)
		exclude = ['#*']
		for function_name in functions_dict:
			if any(fnmatch.fnmatch(function_name, pattern) for pattern in exclude):
				continue

			# print("create_functions: %s %s" % (function_name, functions_dict[function_name]))

			function_dict = functions_dict[function_name]
			function_path = "%s/%s" % (functions_path, function_name)
			self.makedirs(function_path)
			self.add_attrs(function_path, function_dict)

			# os_descs is optional, may not be present
			if 'os_descs' not in function_dict:
				continue
			function_os_descs = function_dict['os_descs']
			for interface in function_os_descs:
				ipath = "%s/os_desc/%s" % (function_path, interface)
				print("create_functions: ipath: %s" % (ipath))

	# create_configs
	# Create the Gadget Device Configurations
	def create_configs(self, path, configs_dict):

		print("create_configs: %s" % (configs_dict))

		configs_path = "%s/configs" % (path)

		for config_name in configs_dict:
			config_dict = configs_dict[config_name]
			print("create_configs: %s" % (config_name))
			print("create_configs: %s" % (config_dict))

			# create directory and add the attributes and strings
			config_path = "%s/%s" % (configs_path, config_name)
			self.makedirs(config_path)
			self.add_attrs(config_path, config_dict)
			self.create_strings(config_path, config_dict['strings'])

			# add the function symlinks
			function_dict = config_dict['functions']
			for f in function_dict:
				print("create_configs: f: %s" % (f))
				function = f['function']
				target = "%s/%s" % (config_path, f['name'])
				src = "%s/functions/%s" % (path, function.replace("_", "."))
				# target = "%s/%s" % (config_path, f)
				self.symlink(src, target)

	# add_device_json
	# Create a Gadget Device definition from saved json configuratiion
	#
	def add_device_json(self, device_definition, device_name=None):
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
