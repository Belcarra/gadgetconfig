#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python noexpandtab

# gadgetconfig configures and enables a Gadget USB configuration
#

import io
import os
import sys
import commentjson

try:
	from gadgetconfig.add import AddGadget
except ModuleNotFoundError:
	from add import AddGadget

"""manage.py: ..."""

# __author__  = "Stuart.Lynne@belcarra.com"


class ManageGadget(object):

	def __init__(self, configpath, test=False):
		self.configpath = configpath
		self.udcpath = "/sys/class/udc"
		self.device = None
		self.udclist = []
		self.test = test
		self.configured_device = ''

		self.checkfs(verbose=True)
		self.find_udcs(verbose=True)
		self.check_current(verbose=True)

	def pathread(self, path):

		# print("pathread: %s" % (path), file=sys.stderr)
		try:
			fstat = os.stat(path)
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
				return '[UnicodeDecodeError]'

		return '<UNKNOWN>'

	def vprint(self, verbose, s):
		if verbose:
			print(s, file=sys.stderr)

	# checkfs will verify that the usb_gadget configfs is available
	#
	def checkfs(self, verbose=False):
		try:
			if not os.path.isdir(self.configpath):
				self.vprint(verbose, "%s: not a directory" % (self.configpath))
				return False
			if os.path.islink(self.configpath):
				self.vprint(verbose, "%s: is a symlink to %s" % (self.configpath, os.path.realpath(self.configpath)))
				return False
			return True
		except PermissionError:
			self.vprint(verbose, "Cannot read: %s PermissionError" % (self.configpath))
		except NameError:
			self.vprint(verbose, "Cannot read: %s NameError" % (self.configpath))
		return False

	# def detach(self):
	#
	def find_udcs(self, verbose=False):
		links = os.listdir(self.udcpath)
		self.udclist = []
		#self.vprint(verbose, "Gadget UDCS %s" % (self.udcpath))
		#self.vprint(verbose, "Gadget UDCS %s" % (links))
		for l in links:
			fpath = "%s/%s" % (self.udcpath, l)
			if os.path.islink(fpath):
				self.udclist.append(l)
				self.realudcpath = os.path.realpath(fpath)
				self.vprint(verbose, "  %s -> %s" % (l, self.realudcpath))
				device = self.pathread("%s/function" % (fpath))
				if device is not None and len(device) > 0:
					self.device = device[0].rstrip()
					self.vprint(verbose, "  Device definition: %s" % (self.device))
			else:
				self.vprint(verbose, "  %s <UNKNOWN>" % (l))
		self.vprint(verbose, "")
		return self.udclist

	def _query_gadget(self, all=False):
		gadgets = []
		dirs = os.listdir(self.configpath)
		self.vprint(True, "Current Gadget configurations")
		if len(dirs) == 0:
			return gadgets
		for d in dirs:
			if all:
				gadgets.append(d)
				continue
			udc = self.pathread(("%s/%s/UDC" % (self.configpath, d)))
			#self.vprint(True, "UDC: %s %d %d" % (udc, len(udc), len(udc[0])))
			if len(udc) == 1 and len(udc[0]) > 1:
				return [d]
		return gadgets

	def query_gadget(self):
		dirs = os.listdir(self.configpath)
		for d in dirs:
			udc = self.pathread(("%s/%s/UDC" % (self.configpath, d)))
			#self.vprint(True, "UDC: %s %d %d" % (udc, len(udc), len(udc[0])))
			if len(udc) == 1 and len(udc[0]) > 1:
				return d
		return 'GADGET NOT CONFIGURED'

	def query_gadgets(self):
		gadgets = []
		dirs = os.listdir(self.configpath)
		self.vprint(True, "Current Gadget configurations")
		if len(dirs) == 0:
			return gadgets
		for d in dirs:
			gadgets.append(d)
		return sorted(gadgets, key=str.casefold)
		#return gadgets

	def query_udc_function(self):
		#if self.device is None:
		#	return "GADGET NOT CONFIGURED"
		function_path = "%s/function" % (self.realudcpath)
		function = self.pathread(function_path)
		#print("query_udc_function: %s" % (function))
		#print("query_udc_function: %d" % (len(function)))
		if len(function) == 0:
			return "NO FUNCTION"
		else:
			return function[0].rstrip()

		#self.vprint(True, "state: %s" % (state))
		# udcpath = self.udclist[0]
		#f = open("/sys/class/udc/%s/soft_connect" % (self.udclist[0]), 'w')
		#f.write("%s\n" % (['disconnect', 'connect'][flag]))
		#f.close()

		return

	def query_udc_state(self):
		#if self.device is None:
		#	return "GADGET NOT CONFIGURED"
		state_path = "%s/state" % (self.realudcpath)
		state = self.pathread(state_path)
		return state[0].rstrip()
		#self.vprint(True, "state: %s" % (state))
		# udcpath = self.udclist[0]
		#f = open("/sys/class/udc/%s/soft_connect" % (self.udclist[0]), 'w')
		#f.write("%s\n" % (['disconnect', 'connect'][flag]))
		#f.close()

		return

	def check_current(self, verbose=False):
		dirs = os.listdir(self.configpath)
		self.vprint(verbose, "Current Gadget configurations")
		if len(dirs) == 0:
			self.vprint(verbose, "<NONE>")

		# print("check_current: %s" % (self.configpath))
		# print("check_current: dirs: %s" % (dirs))
		for d in dirs:
			udc = self.pathread(("%s/%s/UDC" % (self.configpath, d)))
			# print("udc: type: %s len: %s" % (type(udc),len(udc)))
			if len(udc) == 1 and len(udc[0]) > 1:
				# print("udc: type: %s len: %s" % (type(udc[0]),len(udc[0])))
				self.vprint(verbose, "  %s UDC -> %s" % (d, udc[0].rstrip()))
				self.configured_device = d
			else:
				self.vprint(verbose, "  %s Not Configured" % (d))
		self.vprint(verbose, "")

	def disable_current(self):
		#if self.device is None:
		#	print("UDC not configured!")
		#	return
		#print("disable_current: %s" % (self.query_udc_state()))
		if self.query_udc_state() != "not attached":
			print("disable_current: UDC attached!")
			return False

		print("Gadget UDC configured to USB Device %s" % (self.query_gadget()), file=sys.stderr)
		udcpath = "%s/%s/UDC" % (self.configpath, self.query_gadget())
		print("writing to: %s" % (udcpath), file=sys.stderr)
		f = open(udcpath, 'w')
		f.write("\n")
		f.close()
		return True

	def enable_current(self, name):
		#if self.device is not None:
		#	print("UDC not configured!", file=sys.stderr)
		#	return

		print("Gadget UDC configured to USB Device %s" % (self.query_gadget()), file=sys.stderr)
		udcpath = "%s/%s/UDC" % (self.configpath, name)
		print("writing to: %s" % (udcpath), file=sys.stderr)
		f = open(udcpath, 'w')
		f.write("%s\n" % (self.udclist[0]))
		f.close()

	def soft_connect(self, flag):
		print("soft_connect: %s" % (['disconnect', 'connect'][flag]), file=sys.stderr)
		print("soft_connect: udc_state: %s" % (self.query_udc_state()), file=sys.stderr)
		if flag and not self.query_udc_state() == "not attached":
			print("UDC attached!")
			return
		if not flag and self.query_udc_state() == "not attached":
			print("UDC not attached!")
			return
		print("udclist: %s" % (self.udclist), file=sys.stderr)
		f = open("/sys/class/udc/%s/soft_connect" % (self.udclist[0]), 'w')
		f.write("%s\n" % (['disconnect', 'connect'][flag]))
		f.close()

	def get_udcpath(self):
		return self.udcpath

	def get_realudcpath(self):
		return self.realudcpath

	def get_udcdir(self):
		return "/sys/class/udc/%s" % (self.udclist[0])

	# get_device_name
	def get_device_name(self, pathname, device_name=None, args=None):
		with io.open(pathname) as f:
			device_definitions = commentjson.load(f)
			names = []
			for device_name in device_definitions:
				names.append(device_name)
		return names

	# check_device_file
	def check_device_file(self, pathname, device_name=None, args=None):
		print("check_device_file: device_name %s" % (device_name))
		with io.open(pathname) as f:
			device_definitions = commentjson.load(f)
			for device_name in device_definitions:
				if device_name in self.query_gadgets():
					print("check_device_file: %s already defined" % (device_name))
					return device_name
		return None

	# check_device_name
	def check_device_name(self, device_name):
		return device_name in self.query_gadgets()

	def replace(self, data, match, repl):
		if isinstance(data, (dict, list)):
			for k, v in (data.items() if isinstance(data, dict) else enumerate(data)):
				if k == match:
					data[k] = repl
				self.replace(v, match, repl)

	def add_device_file(self, pathname, new_device_name=None, args=None):
		print("*****\nadd_device_file: path: %s new_device_name: %s" % (pathname, new_device_name))
		a = AddGadget(self.configpath)
		with io.open(pathname) as f:
			device_definitions = commentjson.load(f)
			for definition_name in device_definitions:
				device_definition = device_definitions[definition_name]
				if new_device_name is not None:
					device_name = new_device_name
				else:
					device_name = definition_name
				print('device_name: %s' % (device_name))
				if device_name in self.query_gadgets():
					print("add_device_file: %s already defined" % (device_name))
					continue

				if args is not None:
					if args.idVendor: self.replace(device_definition, 'idVendor', args.idVendor)
					if args.idProduct: self.replace(device_definition, 'idProduct', args.idProduct)
					if args.manufacturer: self.replace(device_definition, 'manufacturer', args.manufacturer)
					if args.product: self.replace(device_definition, 'product', args.product)
					if args.serialnumber: self.replace(device_definition, 'serialnumber', args.serialnumber)
					if args.dev_addr: self.replace(device_definition, 'dev_addr', args.dev_addr)
					if args.host_addr: self.replace(device_definition, 'host_addr', args.host_addr)

				a.add_device_json(device_definition, device_name=device_name)

