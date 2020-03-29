#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python noexpandtab

# ToDo
# 1. export config_id and config_name in osdesc

# gadgetconfig configures and enables a Gadget USB configuration
#
# N.B. annotations are supported by adding comments attributes:
#
# E.g.
#	device['# Gadget Functions list: see /sys/module/usb_f*,'] = ''
#	device['# E.g.: usb_f_acm, usb_f_ecm, usb_f_eem, usb_f_hid, usb_f_mass_storage'] = ''
#	device['#       usb_f_midi, usb_f_ncm, usb_f_obex, usb_f_rndis, usb_f_serial'] = ''
#	device['# Use: The function name (without prefix) is used with instantion name, e.g. eem.usb0 or acm.GS0'] = ''
#	device['functions'] = self.export_device_functions(epath)
#
# These will be translated on output to a comment in the JSON file
#
#        },
#        # Gadget Functions list: see /sys/module/usb_f*,
#        # E.g.: usb_f_acm, usb_f_ecm, usb_f_eem, usb_f_hid, usb_f_mass_storage
#        #       usb_f_midi, usb_f_ncm, usb_f_obex, usb_f_rndis, usb_f_serial
#        # Use: The function name (without prefix) is used with instantion name, e.g. eem.usb0 or acm.GS0
#        "functions": {
#
# And removed before input via the add command.
#

import os
import sys
import collections
import fnmatch
import re

"""gadget.py: ..."""

# __author__  = "Stuart.Lynne@belcarra.com"


class ExportGadget(object):

	def __init__(self, configpath, verbose=False):
		self.configpath = configpath
		self.verbose = verbose
		self.verbose = True
		# device['# E.g.: usb_f_acm, usb_f_ecm, usb_f_eem, usb_f_hid, usb_f_mass_storage'] = ''
		# device['#       usb_f_midi, usb_f_ncm, usb_f_obex, usb_f_rndis, usb_f_serial'] = ''
		self.interfaces = {'acm': 2, 'ecm': 2, 'eem': 1, 'ncm': 2, 'hid': 1, 'mass_storage': 1, 'rndis': 1, 'serial': 2}

	def pathread(self, path):

		# print("pathread: %s" % (path), file=sys.stderr)
		try:
			fstat = os.stat(path)
			# print("fstat: size:%s" % (fstat.st_size), file=sys.stderr)
		except (PermissionError):
			print("pathread: %s PERMISSION ERROR" % (path), file=sys.stderr)
			return ''
		except (FileNotFoundError):
			print("pathread: %s NOT FOUND" % (path), file=sys.stderr)
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
				print('pathread: [UnicodeDecodeError]', file=sys.stderr)

			try:
				f = open(path, "rb")
				bytes = f.read(4096)
				f.close
			except (PermissionError, OSError):
				return ''
			# print("bytes: %s" % (type(bytes)), file=sys.stderr)
			# print("bytes: %s" % (bytes), file=sys.stderr)
			return bytes

		return None

	def export_attribute_entry(self, path, entry, symlinks=False, exclude=[]):
		if any(fnmatch.fnmatch(entry, pattern) for pattern in exclude):
			return None
		print("export_attributes: entry %s" % (entry), file=sys.stderr)
		epath = "%s/%s" % (path, entry)
		if symlinks and os.path.islink(epath):
			realpath = os.path.realpath(epath)
			(head, tail) = os.path.split(realpath)
			return tail
		if os.path.isdir(epath) or os.path.islink(epath) or not os.path.isfile(epath):
			return None
		data = self.pathread(epath)
		if isinstance(data, bytes):
			a = []
			for b in data:
				a.append("0x%02x" % (b))
			print("export_attribute_entry: b: %s" % (a), file=sys.stderr)
			return a
		print("data: %s" % (data), file=sys.stderr)
		if data is None or len(data) == 0:
			return
		return data[0].rstrip('\t\r\n\0')

	def export_attribute(self, path, attributes, entry):
		if entry not in attributes:
			return None
		return self.export_attribute_entry(path, entry)

	def export_attributes(self, path, symlinks=False, exclude=[], idFlag=False, annotation=None):

		attributes = [{}, annotation][annotation is not None]

		# print("export_attributes: annotation %s" % (annotation), file=sys.stderr)
		# print("export_attributes: attributes %s" % (attributes), file=sys.stderr)

		#attribute_entries = sorted(os.listdir(path), key=str.casefold)

		attribute_entries = [d.name for d in sorted(os.scandir(path), key=lambda dirent: dirent.inode())]
		#print("export_attributes: entries %s" % (attribute_entries), file=sys.stderr)

		idList = ['idVendor', 'idProduct', 'bcdDevice', 'bDeviceClass', 'bDeviceSubClass', 'bDeviceProtocol']

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

	def export_device_configs(self, configs_path, idVendor, idProduct):
		# print("***********************************", file=sys.stderr)
		# print("export_device_configs: configs_path: %s" % (configs_path), file=sys.stderr)
		configs = {}
		for config_name in sorted(os.listdir(configs_path), key=str.casefold):

			# we need to iterate across the config directory twice, first to get
			# the sorted attributes and symlink targets. Then a second time
			# to get the symlink creation times so we can generate the
			# functions list in the order they were created in. This appears
			# to work reliably.
			#
			function_map = {}
			functions = []
			# print("export_device_configs: config_name: %s" % (config_name), file=sys.stderr)
			config_path = "%s/%s" % (configs_path, config_name)
			config_entries = sorted(os.listdir(config_path), key=str.casefold)
			config = self.export_attributes(config_path, symlinks=False,
					annotation={
						'# Configuration Descriptor': '',
						'# bmAttributes: bit 5 support remote wakeup': '',
						'# bmAttributes: bit 6 self-powered': '',
						'# bmAttributes: bit 7 bus-powered': '',
						'# MaxPower: Power requirements in two-milliampere units, only valid of bit 7 is set': '',
					})
			for entry in config_entries:
				epath = "%s/%s" % (config_path, entry)
				# print("export_device_configs: epath: %s" % (epath), file=sys.stderr)
				if os.path.isdir(epath) and not os.path.islink(epath):
					# is a directory
					if entry == 'strings':
						config[entry] = self.export_strings(epath,
								annotation={'# USB Device Configuration Strings': ''})
					continue
				elif os.path.islink(epath):
					# get the realpath and save it, os.listdir can't sort by inode
					realpath = os.path.realpath(epath)
					(path, target) = os.path.split(realpath)
					function_map[entry] = target
					continue
				elif os.path.isfile(epath):
					# should be regular file
					continue
				else:
					# unknown!
					continue

			# config_entries = sorted(os.listdir(config_path), key=str.casefold)
			config_dirents = sorted(os.scandir(config_path), key=lambda dirent: dirent.inode())
			print("************\nexport_device_configs: config_entries %s" % (config_entries), file=sys.stderr)
			num = 0
			interface = 0
			valid = True
			idVendor = re.sub(r'0x(.*)', r'\1', idVendor)
			idProduct = re.sub(r'0x(.*)', r'\1', idProduct)
			print("****\nexport_device_configs: len(config_dirents) %s" % (len(config_dirents)), file=sys.stderr)
			symlinks = 0
			for dirent in config_dirents:
				if dirent.is_symlink(): symlinks += 1
			for dirent in config_dirents:
				if dirent.is_symlink():
					print("export_device_configs: name: %s" % (dirent.name), file=sys.stderr)
					if symlinks > 1:
						a = "# Host Match USB\\VID_%s&PID_%s&MI_%02d" % (idVendor.upper(), idProduct.upper(), interface)
					else:
						a = "# Host Match USB\\VID_%s&PID_%s" % (idVendor.upper(), idProduct.upper())
					functions.append({a: '', 'name': dirent.name, 'function': function_map[dirent.name]})
					# (f,n) = dirent.name.split('.')
					(f, n) = function_map[dirent.name].split('.')
					if valid and f in self.interfaces:
						interface += self.interfaces[f]
					else:
						valid = False
					num += 1

			config['# This determines the order in the Configuration descriptor'] = ''

			config['functions'] = functions
			configs[config_name] = config

		return configs

	def export_function_os_desc(self, os_desc_path):
		# print("", file=sys.stderr)
		# print("export_function_os_desc: os_desc_path: %s" % (os_desc_path), file=sys.stderr)
		os_desc = {}
		os_desc_entries = sorted(os.listdir(os_desc_path), key=str.casefold)
		for entry in os_desc_entries:
			epath = "%s/%s" % (os_desc_path, entry)
			if os.path.isdir(epath) and not os.path.islink(epath) and fnmatch.fnmatch(entry, "interface.*"):
				os_desc[entry] = self.export_attributes(epath)
		return os_desc

	def export_device_functions(self, functions_path, annotation=None):
		# print("", file=sys.stderr)
		# print("export_device_functions: functions_path: %s" % (functions_path), file=sys.stderr)
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
					if fnmatch.fnmatch(entry, 'lun.*'):
						print("export_device_functions: %s" % (entry), file=sys.stderr)
						function[entry] = self.export_attributes(epath)
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

		return functions

	def export_device_os_desc(self, os_desc_path):
		print("export_device_os_desc: os_desc_path: %s" % (os_desc_path), file=sys.stderr)
		os_desc = self.export_attributes(os_desc_path, symlinks=False)
		print("export_device_os_desc: os_desc: %s" % (os_desc), file=sys.stderr)

		for e in os.listdir(os_desc_path):
			if not os.path.islink("%s/%s" % (os_desc_path, e)):
				print("export_device_os_desc: e: %s NOT" % (e), file=sys.stderr)
				continue
			print("export_device_os_desc: e: %s" % (e), file=sys.stderr)

			config_name, config_id = e.split(".")
			os_desc['config_name'] = config_name
			os_desc['config_id'] = config_id
			print("export_device_os_desc: config_name: %s config_id: %s" % (config_name, config_id), file=sys.stderr)

		return os_desc

	def export_devices(self, annotations=True):
		device_paths = sorted(os.listdir(self.configpath), key=str.casefold)
		devices = collections.OrderedDict()
		for device_name in device_paths:
			device_path = "%s/%s" % (self.configpath, device_name)
			device = self.export_attributes(device_path, exclude=['UDC'], idFlag=True,
					annotation={'# USB Device Descriptor Fields': ''})
			print("export_device: device: %s" % (device), file=sys.stderr)
			# print("export_device: device_path: %s" % (device_path), file=sys.stderr)
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
				device['configs'] = self.export_device_configs(epath, device['idVendor'], device['idProduct'])
			for entry in device_entries:
				# print("export_device: device_path: %s entry: %s" % (device_path, entry), file=sys.stderr)
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
