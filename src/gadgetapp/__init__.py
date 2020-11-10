#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python noexpandtab
#
# N.B. tkinter appears to be installed by default for full raspbian desktop install (2020-01).
#
# imagetk cannot be installed with pip or pip3
#
# If not available then either synaptic or for Raspbian Preferences -> Add / Remove Software
# search for imagetk and install:
#
# 	python3-pil.imagetk
#
# Or from terminal command line:
#
# 	apt-get install python3-pil.imagetk
#
#

import os
import sys
import argparse

# import fcntl
# import signal

try:
	from tkinter import Frame, Tk, Text, TOP, END, INSERT
	from tkinter.ttk import Notebook
	from tkinter import simpledialog
	from tkinter import filedialog
	from tkinter import messagebox
	from tkinter import ttk
	import tkinter.font as tkFont
	import tkinter as tk
except(ImportError):
	print("ImportError: please install python3-tk package!")
	print("Typically this will be: apt install python3-tk")
	exit(1)

from time import sleep
import fnmatch
from sysfstree import sysfstree
import subprocess
import inotify.adapters
import threading

try:
	# from gadgetconfig.add import AddGadget
	# from gadgetconfig.export import ExportGadget
	from gadgetconfig.manage import ManageGadget
	from gadgetconfig.remove import RemoveGadget
#except ModuleNotFoundError:
except :
	# from add import AddGadget
	# from export import ExportGadget
	from manage import ManageGadget
	from remove import RemoveGadget


def sysfs(paths, maxlevel=-1, pinclude=[], pexclude=[], include=[], exclude=[], bold=[], sort=True):
	# print("_main: bold: %s" % (bold))
	s = ''
	for p in paths:
		try:
			sysfs = sysfstree(p, maxlevel=maxlevel, pinclude=pinclude, pexclude=pexclude, 
					include=include, exclude=exclude, bold=bold, nobold=True, sort=sort)
			for l in sysfs._tree(p, os.listdir(p), "", -1):
				s = s + "%s\n" % (l)
		except(FileNotFoundError):
			pass
	return s

# systemctl
# run systemctl to gather status info
#
def systemctl(service_name):
	result = subprocess.run(['systemctl', 'status', 'getty@ttyGS0', 'getty@ttyGS1', 'gadget', '--lines', '0'], stdout=subprocess.PIPE)
	return result.stdout


# watch
# start a process to watch for changes in /sys, set a flag if anything changes
#
class watch:

	def __init__(self, realudcpath):

		self.i = inotify.adapters.Inotify(block_duration_s=1)
		self.realudcpath = realudcpath
		self.udcstatepath = "%s/state" % realudcpath

		self.i.add_watch(self.udcstatepath)
		self.i.add_watch('/sys/kernel/config/usb_gadget')

		self.eventFlag = False
		self.events = 0
		self.stopFlag = False
		self.spinboxvalues = []

		self.x = threading.Thread(target=self.run)

	def run(self):

		# print('watch loop %s' % (self.udcstatepath))
		while not self.stopFlag:
			for event in self.i.event_gen(yield_nones=False, timeout_s=1):
				if self.stopFlag:
					# print('watch exiting', file=sys.stderr)
					return
				# print('.', file=sys.stderr)
				if event is not None:
					(_, type_names, path, filename) = event
					if path == self.udcstatepath and 'IN_MODIFY' in type_names:
						# print('UDC STATE event', file=sys.stderr)
						self.eventFlag = True
						self.events += 1
						continue
					if filename != '' and ('IN_CREATE' in type_names or 'IN_DELETE' in type_names):
						# print("PATH=%s FILENAME=%s EVENT_TYPES=%s" % (path, filename, type_names))
						self.eventFlag = True
						self.events += 1

		# print('watch loop exit')

	def _start(self):
		self.x.start()

	def event(self):
		eventFlag = self.eventFlag
		self.eventFlag = False
		return eventFlag

	def stop(self):
		self.stopFlag = True

# tabs
# Implement a notebook with tabs to display information of interest in each tab
#
class Tabs:
	def __init__(self, m, tk, row=0, column=0, columnspan=0):
		self.m = m
		self.tk = tk
		self._nextID = 0
		self.tabIDs = {}
		self.nameIDs = {}
		self.textlist = []
		self.texthash = {}
		self.currentID = 0

		self.customFont = tkFont.Font(family='monospace regular', size=8)
		self.frame = Frame(self.tk)
		self.frame.grid(row=5, rowspan=2, column=1, columnspan=10, sticky="nsew")

		self.nb = Notebook(self.frame, width=540, height=520)
		self.nb.bind("<ButtonRelease-1>", self.nb_test)
		self.nb.bind("<<NotebookTabChanged>>", self.nb_test)
		self.nb.pack(expand=1, fill='both')
		self.nb.bind("<Button-3>", self.nbFoo)

		self.tab_names = ["Gadget", "UDC State", "Systemd"]
		for n in self.tab_names:
			self.add_tab(n)

		self.nb_update_tablist()

	def nbFoo(self, event):
		print("nbFoo: %s " % (event), file=sys.stderr)
		self.update(selection=None, msg="nbFoo")

	def add_tab(self, name):

		id = self._nextID

		self.tabIDs[id] = name
		self.nameIDs[name] = id
		self._nextID += 1

		newTabFrame = Frame(self.nb)
		text = Text(newTabFrame, font=self.customFont, width=540, height=520)
		text.pack()
		text.insert(INSERT, "...")
		self.textlist.append(text)
		self.texthash[name] = text
		if id == 0:
			self.nb.add(newTabFrame, compound=TOP)
		else:
			self.nb.add(newTabFrame)
		self.nb.tab(id, text=name)
		newTabFrame.bind("<<NotebookTabChanged>>", self.tab_test)

	def nb_update_tablist(self):
		gadgets = self.m.query_gadgets()
		# print("*************************************************", file=sys.stderr)
		# print("nb_update_tablist: gadgets: %s" % (gadgets), file=sys.stderr)
		# print(self.nb.tabs(), file=sys.stderr)
		# print("nb_update_tablist: nameIDs: %s" % (self.nameIDs), file=sys.stderr)
		# print("nb_update_tablist: tabIDs: %s" % (self.tabIDs), file=sys.stderr)
		# print("---", file=sys.stderr)
		for g in gadgets:
			if g in self.nameIDs:
				# print("nb_update_tablist: %s already in nameIDs" % (g), file=sys.stderr)
				continue
			# print("nb_update_tablist: %s ADD", (g), file=sys.stderr)
			self.add_tab(g)

	def nb_test(self, event=None):
		self.currentID = event.widget.index('current')
		self.nb_update()

	def nb_update(self):
		s = ''
		if self.currentID == 1:
			s = sysfs(['/sys/devices/platform/soc'], -1,
				include=["*.usb", ["udc"], [], ["soft_connect", "function", "maximum_speed", "state", "uevent"]],
				bold=[["*"], ["UDC"]])

		elif self.currentID == 0:
			s = sysfs(['/sys/kernel/config/usb_gadget/'], 4, 
					#pinclude=['*/UDC', '*/idVendor', '*/idProduct', '*/strings/0x409/*', '*/functions/*' ],
					pinclude=['*/functions/*', '*/functions/*/*_addr', '*/id*', '*/UDC',
						'*/strings/*/manufacturer', '*/strings/*/product', '*/strings/*/serial*' 
						'*/configs/*/strings/*/configuration', 
						]
					)
					#pinclude=['*/UDC', '*/idVendor', '*/idProduct', '*/strings/0x409/*'],)
					#pinclude=['*/UDC', '*/idVendor', '*/idProduct', 'strings/0x409/*'])
					#include=[[], ["UDC", "idVendor", "idProduct"], ['strings'], ['0x409'], ['manufacturer']])
		elif self.currentID == 2:
			s = systemctl('gadget')
		else:
			s = sysfs(["/sys/kernel/config/usb_gadget/%s" % (self.tabIDs[self.currentID])], -1, sort=True)

		text = self.textlist[self.currentID]
		text.delete('1.0', END)
		text.insert(INSERT, s)

		#Imagine the code for selecting the text widget is here.
		return "break"

	def tab_test(self, event=None):
		return "break"

# Editor
#
class Editor:
	def __init__(self, manage=None, location=None, auto_serialnumber=True):

		self.exitFlag = False
		self.tabs = None
		self.initialdir="/etc/gadgetservice",

		self.button1flag = False
		#self.m = ManageGadget(sys_config_path)
		self.m = manage
		self.gadget_spinbox = None
		# p = self.m.get_realudcpath()
		# print("p: %s" % (p), file=sys.stderr)
		# self.gadget_watch = Watch("/sys/kernel/config/usb_gadget", self.gadget_changed)
		self.no_def_str = '<empty>'
		self.location = location
		self.auto_serialnumber = auto_serialnumber

	def onevent(self, event):
		print("onevent: %s" % (event))

	def event(self):
		self.tk.event_generate("<<FOO>>", when="now")

	# gadget_definitions_spinbox
	# this needs to be created new for each change in the gadgets list
	def gadget_definitions_spinbox(self, selection=None):

		print("gadget_definitions_spinbox: ------------ selection: %s" % (selection))
		if selection is None:
			if self.gadget_spinbox is not None:
				selection = self.gadget_spinbox.get().strip()
				print("gadget_definitions_spinbox: ------------ selection: %s updated" % (selection))
		
		self.gadget_spinbox = ttk.Combobox(self.tk, state="readonly", 
				values=[self.no_def_str], height=4, postcommand=self.gadget_spinbox_postcommand, width=9,
				font=tkFont.Font(family='Helvetica', size=10, weight='bold'))

		self.gadget_spinbox.grid(             row=1, rowspan=1, column=3, columnspan=3, sticky=tk.NSEW, padx=(8, 0), pady=(1, 4))

		self.gadget_spinbox.bind("<<ComboboxSelected>>", self.gadget_spinbox_command)

		v = sorted(self.m.query_gadgets(), key=str.casefold, reverse=False)
		if len(v) == 0:
			self.gadget_spinbox['values'] = self.no_def_str
			self.gadget_spinbox.current(0)
			print("gadgets_definitions_spinbox: setting values: %s" % (self.no_def_str))
			print("------------")
			return

		self.gadget_spinbox['values'] = v
		print("gadgets_definitions_spinbox: setting values: %s" % (v))

		if selection is None:
			selection = self.m.query_gadget()
			print("gadgets_definitions_spinbox: selection from query %s" % (selection))
		else:
			print("gadgets_definitions_spinbox: selection %s" % (selection))

		if selection in v:
			print("gadget_definitions_spinbox: current: %d" % (v.index(selection)))
			self.gadget_spinbox.current(v.index(selection))
			print("------------")
			return

		print("gadget_definitions_spinbox: selection not found")
		self.gadget_spinbox.current(0)
		print("------------")

		# get list of all gadgets, will include selected


	def gadget_spinbox_command(self, arg):
		selection = self.gadget_spinbox.get().strip()
		current = self.gadget_spinbox.current()
		print("gadget_spinbox_command: arg: %s current: %d selection: %s" % (arg, current, selection), file=sys.stderr)
		self.update(selection=selection, msg="gadget_spinbox_command")
		print("gadget_spinbox_command: current: %d -------------------------------------------" % (current))
		return
		v = self.gadget_spinbox['values']
		#v = self.spinboxvalues
		selection = v[current]


	def gadget_spinbox_postcommand(self):
		selection = self.gadget_spinbox.get().strip()
		current = self.gadget_spinbox.current()
		print("gadget_spinbox_postcommand: current: %d selection: %s" % (current, selection), file=sys.stderr)
		#self.gadget_spinbox_update(None, "POST")

	def gadget_spinbox_update(self, selected, msg):
		return
		self.gadget_spinbox.selection_clear()
		current = self.gadget_spinbox.current()
		print("gadget_spinbox_update: selected: %s current: %d ------------------------------------------- %s" % (selected, current, msg))
		return

		if selected is None:
			selected = self.gadget_spinbox.get()
			print("gadget_spinbox_update: selected: %s GET" % (selected))
		else:
			v = self.gadget_spinbox['values']
			#v = self.spinboxvalues
			current = v[current]


		# get list of all gadgets, will include selected
		#v = sorted(self.m.query_gadgets(), key=str.casefold, reverse=False)
		#if len(v) == 0:
		#	v.append(self.no_def_str)

		#self.gadget_spinbox['values'] = v
		#self.spinboxvalues = v
		#print("gadget_spinbox_update: v: %s" % (v))
		#self.gadget_spinbox.current(0)

		if selected in v:
			print("gadget_spinbox_update: current: %d" % (v.index(selected)))
			self.gadget_spinbox.current(v.index(selected))
		else:
			self.gadget_spinbox.current(current)


	def update(self, selection=None, msg="", event=False):
		print("update: %s" % (msg))
		if not event:
			self.gadget_definitions_spinbox(selection=selection)
		# print("Editor:update", file=sys.stderr)
		# sleep(1)
		self.tabs.nb_update()
		#self.gadget_spinbox_postcommand()
		#self.gadget_spinbox_update(None, "UPDATE")
		#self.udc_status_set()
		self.udc_button_set()
		self.gadget_auto_serialnumber_set()
		self.gadget_enable_button_set()
		self.gadget_add_button_set()
		self.gadget_remove_button_set()

	# udc status - attach and detach
	# display current UDC State as label
	#def udc_status_set(self):
	#	print("=============================================")
	#	print("udc_status_set: %s" % self.m.query_udc_state(), file=sys.stderr)
	#	self.udc_button['text'] = "%s\n%s" % (self.m.query_udc_state(), self.m.query_udc_function())
	#	gadget = self.m.query_gadget()
	#	if self.m.query_udc_state() == 'configured':
	#		self.udc_status['text'] = "%s Configured" % (gadget)
	#		self.udc_status['bg'] = 'Light Green'
	#	else:
	#		gadget = self.m.query_gadget()
	#		# print("statustton_set: %s" % self.m.query_gadget(), file=sys.stderr)
	#		if gadget is None:
	#			self.udc_status['text'] = ""
	#			self.udc_status['bg'] = 'Dark Grey'
	#		else:
	#			self.udc_status['text'] = "%s Detached" % (gadget)
	#			self.udc_status['bg'] = 'Light Blue'
	#
	# udc button - attach and detach
	# display current UDC State as label
	#def udc_button_set(self):
	#	print("=============================================")
	#	print("udc_button_set: %s" % self.m.query_udc_state(), file=sys.stderr)
	#	self.udc_button['text'] = "%s\n%s" % (self.m.query_udc_state(), self.m.query_udc_function())
	#	if self.m.query_udc_state() == 'configured':
	#		self.udc_button['text'] = "Click to detach"
	#		self.udc_button['bg'] = 'Light Green'
	#	else:
	#		gadget = self.m.query_gadget()
	#		# print("udc_button_set: %s" % self.m.query_gadget(), file=sys.stderr)
	#		if gadget is None:
	#			self.udc_button['text'] = ""
	#			self.udc_button['bg'] = 'Dark Grey'
	#		else:
	#			self.udc_button['text'] = "Click to attach"
	#			self.udc_button['bg'] = 'Light Blue'

       	# udc button - attach and detach
        # display current UDC State as label
	def udc_button_set(self):
		print("=============================================")
		print("udc_button_set: %s" % self.m.query_udc_state(), file=sys.stderr)
		#self.udc_button['text'] = "%s\n%s" % (self.m.query_udc_state(), self.m.query_udc_function())
		gadget = self.m.query_gadget()
		state = self.m.query_udc_state()
		if state == 'configured':
			self.udc_button['text'] = "%s\n%s" % (gadget, state)
			self.udc_button['bg'] = 'Light Green'
		else:
			gadget = self.m.query_gadget()
			# print("udc_button_set: %s" % self.m.query_gadget(), file=sys.stderr)
			if gadget is None:
				self.udc_button['text'] = "UDC\n(No Gadget)"
				self.udc_button['bg'] = 'Dark Grey'
			else:
				self.udc_button['text'] = "%s\n%s" % (gadget, state)
				self.udc_button['bg'] = 'Light Blue'




	#def udc_status_pressed(self):
	#	print("udc_status_pressed: %s" % (self.m.query_udc_state()), file=sys.stderr)
	#	#self.m.soft_connect(not fnmatch.fnmatch(self.udc_button['text'], 'Configured*'))
	#	#self.udc_button_set()
	#	#self.m.soft_connect(not fnmatch.fnmatch(self.udc_button['text'], 'Configured*'))
	#	self.m.soft_connect(self.m.query_udc_state() != 'configured')
	#	self.update(selection=None, msg="udc_status_pressed")

	def udc_button_pressed(self):
		print("udc_button_pressed: %s" % (self.m.query_udc_state()), file=sys.stderr)
		#self.m.soft_connect(not fnmatch.fnmatch(self.udc_button['text'], 'Configured*'))
		self.m.soft_connect(self.m.query_udc_state() != 'configured')
		#self.udc_button_set()
		self.update(selection=None, msg="udc_button_pressed")

	# gadget button - enable and disable
	# display currently Enabled Gadget as label
	def gadget_auto_serialnumber_set(self):
		#print("*****\ngadget_auto_serialnumber_set: %s" % (self.auto_serialnumber), file=sys.stderr)
		if self.auto_serialnumber:
			self.gadget_auto_serialnumber['bg'] = 'Light Green'
			self.gadget_auto_serialnumber['text'] = 'auto serialnumber'
		else:
			self.gadget_auto_serialnumber['bg'] = 'Light Grey'
			self.gadget_auto_serialnumber['text'] = 'auto serialnumber'

	# gadget button - enable and disable
	# display currently Enabled Gadget as label
	def gadget_enable_button_set(self):
		print("gadget_enable_button_set: %s" % (self.m.query_gadget()), file=sys.stderr)
		if (self.gadget_spinbox is None):
			return
		gadget = self.m.query_gadget()
		selection = self.gadget_spinbox.get().strip()
		print("enable: selection: %s" % (selection))
		if gadget is None:
			if selection == self.no_def_str:
				#t = "Enable"
				self.gadget_enable_button['text'] = "Enable \"%s\"" % (selection)
				self.gadget_enable_button['bg'] = 'Light Grey'
			else:
				self.gadget_enable_button['text'] = "Enable \"%s\"" % (selection)
				self.gadget_enable_button['bg'] = 'Light Blue'
		else:
			if selection == self.no_def_str:
				#t = "Disable %s" % (selection)
				self.gadget_enable_button['text'] = ""
				self.gadget_enable_button['bg'] = 'Light Grey'
			elif selection != gadget:
				#t = "Disable (%s not enabled)" % (selection)
				self.gadget_enable_button['text'] = ""
				self.gadget_enable_button['bg'] = 'Light Grey'
			else:
				self.gadget_enable_button['text'] = "Disable \"%s\"" % (gadget)
				self.gadget_enable_button['bg'] = 'Light Green'

	def gadget_auto_serialnumber_pressed(self):
		print("*****\nauto_serialnumber_pressed: ", file=sys.stderr)
		self.auto_serialnumber = not self.auto_serialnumber
		self.update(selection=None, msg="gadget_auto_serialnumber_pressed")

	def gadget_enable_button_pressed(self):
		# print("*****\ngadget_enable_button_pressed: ", file=sys.stderr)
		if self.m.query_gadget() is not None:

			if not self.m.disable_current():
				messagebox.showerror(title="Error", message="Detach UDC from %s first" % (self.m.query_gadget()))
			self.update(selection=None, msg="gadget_enable_button_pressed query_gadget NONE")
			return

		# print("gadget_enable_button_pressed: gadget selection: %s" % (self.gadget_spinbox.get().strip()), file=sys.stderr)
		self.m.enable_current(self.gadget_spinbox.get().strip())
		#self.gadget_enable_button_set()
		#self.udc_button_set()
		self.update(selection=None, msg="gadget_enable_button_pressed")

	def gadget_add_button_set(self):
		self.gadget_add_button['bg'] = 'Light Blue'
		self.gadget_ecm_button['bg'] = 'Light Blue'
		self.gadget_eem_button['bg'] = 'Light Blue'
		self.gadget_eth_button['bg'] = 'Light Blue'
		self.gadget_mdlm_button['bg'] = 'Light Blue'
		self.gadget_ncm_button['bg'] = 'Light Blue'
		self.gadget_rndis_button['bg'] = 'Light Blue'
		pass

	def get_new_device_name(self, file):
		# print("get_new_device_name: %s" % (file), file=sys.stderr)
		new_device_name = self.m.check_device_file(file)
		if new_device_name is None:
			return None
		while True:
			new_device_name = simpledialog.askstring("Device Name Exists", "New Device name: ", initialvalue=self.m.check_device_file(file))
			if new_device_name is None:
				return None
			if not self.m.check_device_name(new_device_name):
				return new_device_name


	def add_definition(self, filetypes=None):
		#print("filetypes: %s" % (filetypes))
		f = filedialog.askopenfilename(
			initialdir=self.initialdir,
			title="Select Gadget Definition File",
			#filetypes=(("json files", "rndis*.json"), ("all files", "*.*")))
			filetypes=filetypes)

		if f is None:
			return
		if isinstance(f, tuple):
			return
		if f == '':
			return

		old = sorted(self.m.query_gadgets(), key=str.casefold, reverse=False)

		self.initialdir = os.path.dirname(f)

		new_device_name = self.m.check_device_file(f)
		if new_device_name is not None:
			new_device_name = self.get_new_device_name(f)
			if new_device_name is None:
				return
		#print("####\ngadget_add_button_pressed: file: %s %s" % (f, new_device_name), file=sys.stderr)
		try:
			# print("calling add_device_file", file=sys.stderr)
			self.m.add_device_file(f, new_device_name=new_device_name, auto_serialnumber=self.auto_serialnumber)
		except FileExistsError:
			messagebox.showerror(title="Error", message="Gadget Definition for %s already exists!" % (self.m.check_device_file(f)))

		#self.gadget_definitions_spinbox()

		new = sorted(self.m.query_gadgets(), key=str.casefold, reverse=False)
		added = [item for item in new if item not in old]
		#self.gadget_spinbox_update(added[0], "ADD")
		self.notebook()
		self.update(selection=added[0], msg="add_definition")

	def gadget_add_button_pressed(self):
		filetypes=(
			("all files", "*.*"),
			("eem*", "eem*.json"), 
			("ecm*", "eem*.json"), 
			("ncm*", "eem*.json"), 
			("rndis*", "rndis*.json"),
			("*eem*", "*eem*.json"), 
			("*ecm*", "*eem*.json"), 
			("*ncm*", "*eem*.json"), 
			("*rndis*", "*rndis*.json")
			)
		self.add_definition(filetypes)

	def gadget_ecm_button_pressed(self):
		filetypes=( ("ecm*", "ecm*.json"), ("all files", "*.*"),)
		self.add_definition(filetypes)

	def gadget_eem_button_pressed(self):
		filetypes=( ("eem*", "eem*.json"), ("all files", "*.*"),)
		self.add_definition(filetypes)

	def gadget_eth_button_pressed(self):
		filetypes=( ("eth*", "eth*.json"), ("all files", "*.*"),)
		self.add_definition(filetypes)

	def gadget_mdlm_button_pressed(self):
		filetypes=( ("mdlm*", "mdlm*.json"), ("all files", "*.*"),)
		self.add_definition(filetypes)

	def gadget_ncm_button_pressed(self):
		filetypes=( ("ncm*", "ncm*.json"), ("all files", "*.*"),)
		self.add_definition(filetypes)

	def gadget_rndis_button_pressed(self):
		filetypes=( ("rndis*", "rndis*.json"), ("all files", "*.*"),)
		self.add_definition(filetypes)

	def gadget_remove_button_set(self):
		if (self.gadget_spinbox is None):
			return
		gadget = self.m.query_gadget()
		selection = self.gadget_spinbox.get().strip()
		print("remove: gadget: %s" % (gadget))
		print("remove: selection: %s" % (selection))
		#print("remove: no_def_str: %s" % (self.no_def_str))
		if selection == self.m.query_gadget():
			#self.gadget_remove_button['text'] = "Cannot Remove \"%s\" (disable first)" % (selection)
			self.gadget_remove_button['text'] = ""
			self.gadget_remove_button['bg'] = 'Light Grey'
		elif selection == self.no_def_str:
			self.gadget_remove_button['text'] = "Remove"
			self.gadget_remove_button['bg'] = 'Light Grey'
		else:
			self.gadget_remove_button['text'] = "Remove \"%s\"" % (selection)
			self.gadget_remove_button['bg'] = 'Light Blue'

	def gadget_remove_button_pressed(self):
		if (self.gadget_spinbox is None):
			return
		if self.gadget_spinbox.get().strip() == self.m.query_gadget():
			messagebox.showerror(title="Error", message="Disable %s first" % (self.m.query_gadget()))
			return
		r = RemoveGadget(self.m.configpath, self.m)
		r.remove_device(self.gadget_spinbox.get().strip())
		#self.gadget_spinbox_postcommand()
		#self.gadget_definitions_spinbox()
		#self.gadget_spinbox_update(None, "REMOVE")
		self.notebook()
		self.update(selection=None, msg="gadget_remove_button_pressed")
	def doFoo(self, event):
		print("doFoo: %s " % (event), file=sys.stderr)
		self.update(selection=None, msg="doFoo", event=True)
		#self.udc_button_set()
		return

	def setExitFlag(self):
		# print("setExitFlag:", file=sys.stderr)
		self.exitFlag = True

	def tk(self):
		self.tk = Tk()
		self.tk.bind("<<FOO>>", self.doFoo)
		self.tk.bind("<Button-1>", self.doFoo)
		self.tk.bind("<Button-3>", self.doFoo)
		if self.location:
			self.tk.geometry("550x660" + self.location)
		else:
			self.tk.geometry("550x660")
		self.tk.call('encoding', 'system', 'utf-8')
		self.tk.title("Gadget USB Device Configuration - %s" % (os.uname()[1]))
		self.tk.protocol("WM_DELETE_WINDOW", self.setExitFlag)

		# the spinbox is created and recreated on the fly to respond to the current list of gadgets
		#self.gadget_definitions_spinbox()

		self.gadget_auto_serialnumber = tk.Button(self.tk, text='auto_serialnumber', command=self.gadget_auto_serialnumber_pressed, width=18, anchor='w')

		self.gadget_enable_button = tk.Button(self.tk, text='', command=self.gadget_enable_button_pressed, width=18, anchor='w')
		self.gadget_remove_button = tk.Button(self.tk, text='', command=self.gadget_remove_button_pressed, width=18, anchor='w')


		self.gadget_add_button = tk.Button(self.tk, text='Add definition', command=self.gadget_add_button_pressed, width=18, anchor='center')
		self.gadget_ecm_button = tk.Button(self.tk, text='ECM', command=self.gadget_ecm_button_pressed, width=4, anchor='center')
		self.gadget_eem_button = tk.Button(self.tk, text='EEM', command=self.gadget_eem_button_pressed, width=4, anchor='center')
		self.gadget_eth_button = tk.Button(self.tk, text='ETH', command=self.gadget_eth_button_pressed, width=4, anchor='center')
		self.gadget_mdlm_button = tk.Button(self.tk, text='MDLM', command=self.gadget_mdlm_button_pressed, width=4, anchor='center')
		self.gadget_ncm_button = tk.Button(self.tk, text='NCM', command=self.gadget_ncm_button_pressed, width=4, anchor='center')
		self.gadget_rndis_button = tk.Button(self.tk, text='RNDIS', command=self.gadget_rndis_button_pressed, width=4, anchor='center')

		#self.udc_status = tk.Button(self.tk, text='-', command=self.udc_status_pressed, width=14, anchor='center')
		self.udc_button = tk.Button(self.tk, text='-', command=self.udc_button_pressed, width=14, anchor='center')

		#self.gadget_spinbox_title = tk.Label(self.tk, text='<-- Select Gadget Device Definition',
		#		font=tkFont.Font(family='Helvetica', size=8), anchor='ne', justify='left')

		# row 1
		#self.udc_status.grid(                 row=1, rowspan=1, column=1, columnspan=3, sticky=tk.NSEW, pady=(1, 1))
		#self.gadget_spinbox.grid(             row=1, rowspan=1, column=4, columnspan=4, sticky=tk.NSEW, padx=(8, 0), pady=(1, 4))
		self.udc_button.grid(                 row=1, rowspan=2, column=1, columnspan=2, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_auto_serialnumber.grid(   row=1, rowspan=1, column=6, columnspan=2, sticky=tk.NSEW, pady=(1, 1))

		# row 2
		self.gadget_enable_button.grid(       row=2, rowspan=1, column=3, columnspan=3, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_remove_button.grid(       row=2, rowspan=1, column=6, columnspan=2, sticky=tk.NSEW, pady=(1, 1))

		# row 3
		self.gadget_ecm_button.grid(          row=3, rowspan=1, column=1, columnspan=1, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_eem_button.grid(          row=3, rowspan=1, column=2, columnspan=1, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_eth_button.grid(          row=3, rowspan=1, column=3, columnspan=1, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_mdlm_button.grid(          row=3, rowspan=1, column=4, columnspan=1, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_ncm_button.grid(          row=3, rowspan=1, column=5, columnspan=1, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_rndis_button.grid(        row=3, rowspan=1, column=6, columnspan=1, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_add_button.grid(          row=3, rowspan=1, column=7, columnspan=1, sticky=tk.NSEW, pady=(1, 1))


		#self.udc_status_set()
		self.udc_button_set()
		self.gadget_auto_serialnumber_set()
		self.gadget_enable_button_set()
		self.gadget_add_button_set()
		self.gadget_remove_button_set()


		# help button
		#s elf.help_button = tk.Button(self.tk, text='?', command=self.help_button_pressed, justify=LEFT)
		# self.help_button.grid(row=0, column=8, columnspan=1, sticky=tk.NSEW, pady=(1,6))

		#self.l2 = tk.Label(self.tk, text='Button two')
		#self.l2.grid(row=0, column=1, sticky=tk.W)

		# the Notebook is created and recreated on the fly to respond to the current list of gadgets
		self.notebook()

		self.update(selection=None, msg="tk")

	# gadget_notebook
	# this needs to be created new for each change in the gadgets list
	def notebook(self):
		# print('notebook')
		self.tabs = Tabs(self.m, self.tk, row=4, column=1, columnspan=8)


def main():

	parser = argparse.ArgumentParser(
		usage='%(prog)s [command][options]',
		description="GUI Configure Gadget Device using SysFS and ConfigFS",
		formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=999))

	parser.add_argument("--location", type=str, help="Optional window location +x+y")
	parser.add_argument("--no_auto_serialnumber", action='store_false', help="Disable auto_serialnumber mode")

	args = parser.parse_args()

	print('location: %s' % (args.location))

	sys_config_path = "/sys/kernel/config/usb_gadget"
	#m = ManageGadget(sys_config_path, auto_serialnumber=args.no_auto_serialnumber)
	m = ManageGadget(sys_config_path)

	print('realudcpath: %s' % (m.query_udc_path()))
	w = watch(m.query_udc_path())
	w._start()

	e = Editor(manage=m, location=args.location, auto_serialnumber=args.no_auto_serialnumber)
	e.tk()

	# replacement for tk.mainloop() 
	# This is slightly painful, tk.update() needs to be in main process,
	# but we want to have a separate thread watching for changes in the /sys
	# filesystem. The various approaches for that either also want to live
	# in the main process, or stall. By implementing our own mainloop
	# equivalent we can check the event flag set when something changes
	# in the watched filesystem.
	# 
	while not e.exitFlag:

		# do the tkinter update
		e.tk.update()

		# wait for a short period
		try:
			sleep(.1)

		# exit cleanly on break
		except(KeyboardInterrupt):
			break

		# if flag then call the event handler to update 
		if w.event():
			e.event()

	w.stop()


if __name__ == '__main__':
	main()
