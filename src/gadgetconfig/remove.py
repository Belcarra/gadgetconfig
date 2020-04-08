#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python noexpandtab

# ToDo
# 1. unlink osdesc config symlink


# gadgetconfig configures and enables a Gadget USB configuration
#

import os
import fnmatch

"""remove.py: ..."""

# __author__  = "Stuart.Lynne@belcarra.com"


class RemoveGadget(object):

	def __init__(self, configpath, manage):
		self.configpath = configpath
		self.m = manage

	def rmdir(self, path):
		if not os.path.isdir(path):
			print("rmdir: %s NOT A DIR" % (path))
			return
		print("rmdir: %s" % (path))
		os.rmdir(path)

	def unlink(self, path):
		if not os.path.islink(path):
			print("rmdir: %s NOT A SYMLINK" % (path))
			return
		print("unlink: %s" % (path))
		os.unlink(path)

	def listdir(self, path):
		if not os.path.isdir(path):
			print("listdir: %s NOT A DIR" % (path))
			return
		print("listdir: %s" % (path))
		return os.listdir(path)

	def remove_strings(self, path):
		spath = "%s/strings" % path
		if os.path.isdir(spath):
			for l in os.listdir(spath):
				self.rmdir("%s/%s" % (spath, l))

			# Gadget ConfigFS does not allow strings directory to be removed.
			# self.rmdir(spath)

	# remove_device
	#
	# C.f. gadget_configfs.txt - section 7. Cleaning up
	# 0. unlink os_desc symlink
	# For each configuration .../configs/*
	# 1. unlink Functions
	# 2. rmdir strings/<lang>
	# 3. rmdir config
	# Then
	# 4. rmdir functions/*
	# 5. rmdir strings/<lang>
	# 6. rmdir device
	#
	def remove_device(self, configname):

		# sanity checks, verify device is not currently enabled
		#if configname == self.device:
		#	print("The %s Gadget USB Device is currently enabled!" % (configname))
		#	exit(1)
		#if self.query_udc_state() == "not attached":
		#	print("disable_current: UDC not attached!")
		#	return False
		# print("remove_device: %s %s" % (configname, self.m.query_gadget()))
		if configname == self.m.query_gadget():
			print("The %s Gadget USB Device is currently enabled!" % (configname))
			exit(1)

		# sanity checks, verify usb_gadget/configname exists and we have permissions
		device_path = "%s/%s" % (self.configpath, configname)
		try:
			os.stat(device_path, follow_symlinks=False)
		except (FileNotFoundError):
			print("%s FILE NOT FOUND ERROR" % (device_path))
			exit(1)
		except (PermissionError):
			print("%s PERMISSION ERROR" % (device_path))
			exit(1)

		# step 0 - check for osdesc config symlink
		#
		os_desc_path = "%s/os_desc" % (device_path)
		for entry in self.listdir(os_desc_path):
			entry_path = "%s/%s" % (os_desc_path, entry)
			if os.path.islink(entry_path):
				self.unlink(entry_path)

		# iterate across device path configs directory to handle
		# steps #1, #2 and #3 for each configuration
		#
		configs_path = "%s/configs" % (device_path)
		for c in self.listdir(configs_path):
			# print("remove_device: config: %s" % (c))

			# 1.
			config_path = "%s/%s" % (configs_path, c)
			for e in self.listdir(config_path):
				self.unlink("%s/%s" % (config_path, e))
			# 2.
			self.remove_strings(config_path)
			# 3.
			self.rmdir(config_path)

		# iterate across device path / functions so we can
		# perform step #4, rmdir each
		#
		functions_path = "%s/functions" % (device_path)
		for f in self.listdir(functions_path):

			# N.B. mass_storage has sub-functions lun.0...lun.N,
			# lun.1...lun.N must be removed, lun.0 cannot be removed
			sfunctions_path = "%s/%s" % (functions_path, f)
			for d in self.listdir("%s/%s" % (functions_path, f)):
				if d == 'lun.0':
					continue
				if fnmatch.fnmatch(d, "lun.*"):
					self.rmdir("%s/%s" % (sfunctions_path, d))
			# 4.
			self.rmdir("%s/%s" % (functions_path, f))
			# print("AAAA")
		# print("BBBB")

		# Finally for device path, do step #5 remove strings and then step #6 remove the device
		#
		# 5.
		self.remove_strings(device_path)
		# print("CCCC")
		# 6.
		self.rmdir(device_path)
