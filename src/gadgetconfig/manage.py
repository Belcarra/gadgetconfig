#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python noexpandtab

# gadgetconfig configures and enables a Gadget USB configuration
#

import os
import sys


"""manage.py: ..."""

# __author__  = "Stuart.Lynne@belcarra.com"


class ManageGadget(object):

	def __init__(self, configpath):
		self.configpath = configpath
		self.udcpath = "/sys/class/udc"
		self.device = None
		self.udclist = []
		self.configured_device = ''

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
		self.vprint(verbose, "Gadget UDCS")
		for l in links:
			fpath = "%s/%s" % (self.udcpath, l)
			if os.path.islink(fpath):
				self.udclist.append(l)
				self.vprint(verbose, "  %s -> %s" % (l, os.path.realpath(fpath)))
				device = self.pathread("%s/function" % (fpath))
				if device is not None and len(device) > 0:
					self.device = device[0].rstrip()
					self.vprint(verbose, "  Device definition: %s" % (self.device))
			else:
				self.vprint(verbose, "  %s <UNKNOWN>" % (l))
		self.vprint(verbose, "")
		return self.udclist

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
		if self.device is None:
			print("The Gadget UDC is currently not configured!")
			return

		print("Gadget UDC configured to USB Device %s" % (self.device), file=sys.stderr)
		udcpath = "%s/%s/UDC" % (self.configpath, self.device)
		print("writing to: %s" % (udcpath), file=sys.stderr)
		f = open(udcpath, 'w')
		f.write("\n")
		f.close()

	def enable_current(self, name):
		if self.device is not None:
			print("The Gadget UDC is currently configured!", file=sys.stderr)
			return

		print("Gadget UDC configured to USB Device %s" % (self.device), file=sys.stderr)
		udcpath = "%s/%s/UDC" % (self.configpath, name)
		print("writing to: %s" % (udcpath), file=sys.stderr)
		f = open(udcpath, 'w')
		f.write("%s\n" % (self.udclist[0]))
		f.close()

	def soft_connect(self, flag):
		print("soft_connect: %s" % (['disconnect', 'connect'][flag]), file=sys.stderr)
		if self.device is None:
			print("The Gadget UDC is currently configured!")
			return
		print("udclist: %s" % (self.udclist), file=sys.stderr)
		# udcpath = self.udclist[0]
		f = open("/sys/class/udc/%s/soft_connect" % (self.udclist[0]), 'w')
		f.write("%s\n" % (['disconnect', 'connect'][flag]))
		f.close()
