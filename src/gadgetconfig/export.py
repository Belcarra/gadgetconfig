#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python noexpandtab

# gadgetconfig configures and enables a Gadget USB configuration
#

import os
import collections
from datetime import date
import fnmatch

"""gadget.py: ..."""

# __author__  = "Stuart.Lynne@belcarra.com"


class ExportGadget(object):

	def __init__(self, configpath, verbose=False):
		self.configpath = configpath
		self.verbose = verbose
		self.verbose = True

	def pathread(self, path):

		# print("pathread: %s" % (path))
		try:
			fstat = os.stat(path)
			# print("fstat: size:%s" % (fstat.st_size))
		except (PermissionError):
			print("pathread: %s PERMISSION ERROR" % (path))
			return ''
		except (FileNotFoundError):
			print("pathread: %s NOT FOUND" % (path))
			return ''

		# 4096 or 0 byte files should contain info
		if fstat.st_size == 4096 or fstat.st_size == 0:
			try:
				f = open(path, "r")
				lines = f.readlines(1000)
				f.close()
				return lines
			except (PermissionError, OSError):
				return ''
			except UnicodeDecodeError:
				return '[UnicodeDecodeError]'

		return '<UNKNOWN>'

	def export_attribute_entry(self, path, entry, symlinks=False, exclude=[]):
		if any(fnmatch.fnmatch(entry, pattern) for pattern in exclude):
			return None
		# print("export_attributes: entry %s" % (entry))
		epath = "%s/%s" % (path, entry)
		if symlinks and os.path.islink(epath):
			realpath = os.path.realpath(epath)
			(head, tail) = os.path.split(realpath)
			return tail
		if os.path.isdir(epath) or os.path.islink(epath) or not os.path.isfile(epath):
			return None
		return self.pathread(epath)[0].rstrip('\t\r\n\0')

	def export_attribute(self, path, attributes, entry):
		if entry not in attributes:
			return None
		return self.export_attribute_entry(path, entry)

	def export_attributes(self, path, symlinks=False, exclude=[], idFlag=False, annotation=None):

		attributes = [{}, annotation][annotation is not None]

		# print("export_attributes: annotation %s" % (annotation), file=sys.stderr)
		# print("export_attributes: attributes %s" % (attributes), file=sys.stderr)
		attribute_entries = sorted(os.listdir(path), key=str.casefold)

		idList = ['idVendor', 'idProduct', 'bcdDevice', 'bDeviceClass', 'bDeviceSubClass', 'bDeviceProtocol']
		# print("export_attributes: entries %s" % (attribute_entries), file=sys.stderr)

		if idFlag:
			for entry in idList:
				v = self.export_attribute(path, attribute_entries, entry)
				if v is not None:
					attributes[entry] = v

		for entry in attribute_entries:
			if idFlag and entry in idList:
				continue
			v = self.export_attribute_entry(path, entry, symlinks, exclude)
			if v is not None:
				attributes[entry] = v
		# print("export_attributes: %s" % (attributes), file=sys.stderr)
		# print("", file=sys.stderr)
		return attributes

	def export_strings(self, strings_path, annotation=None):
		strings = [{}, annotation][annotation is not None]
		# print("export_strings: strings_path %s" % (strings_path))
		for lang_name in sorted(os.listdir(strings_path), key=str.casefold):
			# print("export_strings: lang_name %s" % (lang_name))
			string_path = "%s/%s" % (strings_path, lang_name)
			# print("export_strings: string_path %s" % (string_path))
			strings[lang_name] = self.export_attributes(string_path)
		return strings

	def export_device_configs(self, configs_path):
		print("***********************************")
		print("export_device_configs: configs_path: %s" % (configs_path))
		configs = {}
		for config_name in sorted(os.listdir(configs_path), key=str.casefold):
			functions = []
			print("-------")
			print("export_device_configs: config_name: %s" % (config_name))
			config_path = "%s/%s" % (configs_path, config_name)
			config_entries = sorted(os.listdir(config_path), key=str.casefold)
			config = self.export_attributes(config_path, symlinks=True,
					annotation={
						'# Configuration Descriptor': '',
						'# bmAttributes: bit 5 support remote wakeup': '',
						'# bmAttributes: bit 6 self-powered': '',
						'# bmAttributes: bit 7 bus-powered': '',
						'# MaxPower: Power requirements in two-milliampere units, only valid of bit 7 is set': '',
					})
			for entry in config_entries:
				epath = "%s/%s" % (config_path, entry)
				print("export_device_configs: epath: %s" % (epath))
				if os.path.isdir(epath) and not os.path.islink(epath):
					# is a directory
					if entry == 'strings':
						config[entry] = self.export_strings(epath,
								annotation={'# USB Device Configuration Strings': ''})
					continue
				elif os.path.islink(epath):
					# symlink - should not be any at this level
					realpath = os.path.realpath(epath)
					(path, target) = os.path.split(realpath)
					functions.append({'name': entry, 'function': target})
					continue
				elif os.path.isfile(epath):
					# should be regular file
					continue
				else:
					# unknown!
					continue

			config['functions'] = functions
			configs[config_name] = config

		return configs

	def export_function_os_desc(self, os_desc_path):
		# print("")
		# print("export_function_os_desc: os_desc_path: %s" % (os_desc_path))
		os_desc = {}
		os_desc_entries = sorted(os.listdir(os_desc_path), key=str.casefold)
		for entry in os_desc_entries:
			epath = "%s/%s" % (os_desc_path, entry)
			if os.path.isdir(epath) and not os.path.islink(epath) and fnmatch.fnmatch(entry, "interface.*"):
				os_desc[entry] = self.export_attributes(epath)
		return os_desc

	def export_device_functions(self, functions_path, annotation=None):
		# print("")
		# print("export_device_functions: functions_path: %s" % (functions_path))
		functions = [{}, annotation][annotation is not None]
		for function_name in sorted(os.listdir(functions_path), key=str.casefold):
			function_path = "%s/%s" % (functions_path, function_name)
			function_entries = sorted(os.listdir(function_path), key=str.casefold)
			function = self.export_attributes(function_path, exclude=['ifname', 'port_num'])
			for entry in function_entries:
				epath = "%s/%s" % (function_path, entry)
				if os.path.isdir(epath) and not os.path.islink(epath):
					# is a directory
					if entry == 'os_desc':
						function[entry] = self.export_function_os_desc(epath)
					continue
				elif os.path.islink(epath):
					# sysmlink - should not be any at this level
					realpath = os.path.realpath(epath)
					target = os.path.split(realpath)
					function[entry] = target
					continue
				elif os.path.isfile(epath):
					# should be regular file
					continue
				else:
					# unknown!
					continue

			functions[function_name] = function
			pass
		return functions

	def export_device_os_desc(self, os_desc_path):
		# print("export_device_os_desc: os_desc_path: %s" % (os_desc_path))
		os_desc = self.export_attributes(os_desc_path, symlinks=True)
		return os_desc

	def export_devices(self):
		device_paths = sorted(os.listdir(self.configpath), key=str.casefold)
		devices = collections.OrderedDict()
		devices['# Gadget Device Definition File'] = ''
		devices["# %s" % (date.today())] = ''
		for device_name in device_paths:
			device_path = "%s/%s" % (self.configpath, device_name)
			device = self.export_attributes(device_path, exclude=['UDC'], idFlag=True,
					annotation={'# USB Device Descriptor Fields': ''})
			# print("export_device: device_path: %s" % (device_path))
			device_entries = sorted(os.listdir(device_path), key=str.casefold)
			if 'strings' in device_entries:
				epath = "%s/%s" % (device_path, 'strings')
				device['# USB Device Strings'] = ''
				device['strings'] = self.export_strings(epath)
			if 'functions' in device_entries:
				epath = "%s/%s" % (device_path, 'functions')
				device['# Gadget Functions list: see /sys/module/usb_f*,'] = ''
				device['# E.g.: usb_f_acm, usb_f_ecm, usb_f_eem, usb_f_hid, usb_f_mass_storage'] = ''
				device['#       usb_f_midi, usb_f_ncm, usb_f_obex, usb_f_rndis, usb_f_serial'] = ''
				device['# Use: The function name (without prefix) is used with instantion name, e.g. eem.usb0 or acm.GS0'] = ''
				device['functions'] = self.export_device_functions(epath)
			if 'configs' in device_entries:
				epath = "%s/%s" % (device_path, 'configs')
				device['# Gadget Configurations list'] = ''
				device['configs'] = self.export_device_configs(epath)
			for entry in device_entries:
				# print("export_device: device_path: %s entry: %s" % (device_path, entry))
				epath = "%s/%s" % (device_path, entry)
				if os.path.isdir(epath) and not os.path.islink(epath):
					# is a directory
					if entry == 'configs':
						pass
					elif entry == 'functions':
						pass
					elif entry == 'os_desc':
						device['# Microsoft OS Descriptors Support'] = ''
						device['# C.f. https://docs.microsoft.com/en-us/previous-versions/gg463179(v=msdn.10)'] = ''
						device[entry] = self.export_device_os_desc(epath)
					elif entry == 'strings':
						pass
				elif os.path.islink(epath):
					# sysmlink - should not be any at this level
					pass
				# elif os.path.isfile(epath):
					# should be regular file
					pass
				else:
					# unknown!
					pass

			devices[device_name] = device

		return devices
