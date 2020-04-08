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


def systemctl(service_name):
	#status = os.system('systemctl status '+service_name)
	#return status
	result = subprocess.run(['systemctl', 'status', 'getty@ttyGS0', 'getty@ttyGS1', 'gadget', '--lines', '0'], stdout=subprocess.PIPE)
	return result.stdout


#def handler(signum, frame):
#	print("handler: signum: %s frame: %s" % (signum, frame), file=sys.stderr)


class watch:

	def __init__(self, realudcpath):

		# print('watch')
		#self.i = inotify.adapters.Inotify()
		self.i = inotify.adapters.Inotify(block_duration_s=1)
		self.realudcpath = realudcpath
		self.udcstatepath = "%s/state" % realudcpath

		#i.add_watch('/tmp')
		self.i.add_watch(self.udcstatepath)
		self.i.add_watch('/sys/kernel/config/usb_gadget')

		self.eventFlag = False
		self.events = 0
		self.stopFlag = False

		#with open('/tmp/test_file', 'w'):
		#    pass
		self.x = threading.Thread(target=self.run)

	def run(self):

		# print('watch loop %s' % (self.udcstatepath))
		while not self.stopFlag:
			for event in self.i.event_gen(yield_nones=False, timeout_s=1):
				if self.stopFlag:
					# print('watch exiting', file=sys.stderr)
					return
				#print('.', file=sys.stderr)
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


class Tabs:
	def __init__(self, m, tk, row=0, column=0, columnspan=0):
		#self.tabs = 0
		self.m = m
		self.tk = tk
		self._nextID = 0
		self.tabIDs = {}
		self.nameIDs = {}
		self.textlist = []
		self.texthash = {}
		self.currentID = 0

		self.customFont = tkFont.Font(family='monospace regular', size=9)
		self.frame = Frame(self.tk)
		self.frame.grid(row=5, rowspan=2, column=1, columnspan=9, sticky="nsew")

		self.nb = Notebook(self.frame, width=680, height=520)
		self.nb.bind("<ButtonRelease-1>", self.nb_test)
		self.nb.bind("<<NotebookTabChanged>>", self.nb_test)
		self.nb.pack(expand=1, fill='both')
		self.nb.bind("<Button-3>", self.nbFoo)

		self.tab_names = ["UDC State", "Gadget", "Systemd"]
		for n in self.tab_names:
			self.add_tab(n)

		self.nb_update_tablist()

	def nbFoo(self, event):
		print("nbFoo: %s " % (event), file=sys.stderr)
		self.update()

	def add_tab(self, name):

		id = self._nextID
		# print("add_tab: id: %s name: %s" % (id, name), file=sys.stderr)

		self.tabIDs[id] = name
		self.nameIDs[name] = id
		self._nextID += 1

		newTabFrame = Frame(self.nb)
		text = Text(newTabFrame, font=self.customFont, width=680, height=520)
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
		#showinfo("Success", "It works!")
		#current_tab_id = self.select()

		self.currentID = event.widget.index('current')
		# print("nb_test: event: %s currentID: %s %s" % (event, self.currentID, self.tabIDs[self.currentID]), file=sys.stderr)
		#self.nb_update(self.tabID)
		self.nb_update()

	def nb_update(self):
		s = ''
		if self.currentID == 0:
			s = sysfs(['/sys/devices/platform/soc'], -1,
				include=["*.usb", ["udc"], [], ["soft_connect", "function", "maximum_speed", "state", "uevent"]])

		elif self.currentID == 1:
			s = sysfs(['/sys/kernel/config/usb_gadget/'], 4, 
					pinclude=['*/UDC', '*/idVendor', '*/idProduct', '*/strings/0x409/*'])
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
		# print("tab_test: event: %s" % (event), file=sys.stderr)
		#Imagine the code for selecting the text widget is here.
		return "break"


class Editor:
	def __init__(self, manage=None):

		self.exitFlag = False
		self.tabs = None

		self.button1flag = False
		#self.m = ManageGadget(sys_config_path)
		self.m = manage
		self.gadget_spinbox = None
		# p = self.m.get_realudcpath()
		# print("p: %s" % (p), file=sys.stderr)
		# self.udc_watch = Watch(self.m.get_realudcpath(), self.udc_changed)
		# self.gadget_watch = Watch("/sys/kernel/config/usb_gadget", self.gadget_changed)
		self.nodefstr = '-- no Gadget Definitions --'

	def onevent(self, event):
		print("onevent: %s" % (event))

	def event(self):
		self.tk.event_generate("<<FOO>>", when="now")

	def udc_changed(self, signum, frame):
		# print("*****\nudc_changed: signum: %s frame: %s" % (signum, frame), file=sys.stderr)
		self.tk.event_generate("<<FOO>>", when="now")
		self.udc_watch.close()

	def gadget_changed(self, signum, frame):
		# print("*****\nudc_changed: signum: %s frame: %s" % (signum, frame), file=sys.stderr)
		self.tk.event_generate("<<FOO>>", when="now")
		self.gadget_watch.close()

	def update(self):
		# print("Editor:update", file=sys.stderr)
		# sleep(1)
		self.tabs.nb_update()
		self.gadget_definitions_spinbox()
		self.udc_button_set()
		self.gadget_enable_button_set()
		self.gadget_add_button_set()
		self.gadget_remove_button_set()

	# udc button - attach and detach
	# display current UDC State as label
	def udc_button_set(self):
		# print("udc_button_set: %s" % self.m.query_udc_state(), file=sys.stderr)
		#self.udc_button['text'] = "%s\n%s" % (self.m.query_udc_state(), self.m.query_udc_function())
		if self.m.query_udc_state() == 'configured':
			self.udc_button['text'] = "Configured\n(Click to detach)"
			self.udc_button['bg'] = 'Light Green'
		else:
			gadget = self.m.query_gadget()
			# print("udc_button_set: %s" % self.m.query_gadget(), file=sys.stderr)
			if gadget is None:
				self.udc_button['text'] = "UDC\n(No Gadget Defined)"
				self.udc_button['bg'] = 'Dark Grey'
			else:
				self.udc_button['text'] = "UDC Detached\n(Click to attach)"
				self.udc_button['bg'] = 'Light Blue'

	def udc_button_pressed(self):
		# print("udc_button_pressed: %s" % (self.udc_button['text']), file=sys.stderr)
		self.m.soft_connect(not fnmatch.fnmatch(self.udc_button['text'], 'Configured*'))
		#self.udc_button_set()
		self.update()

	# gadget button - enable and disable
	# display currently Enabled Gadget as label
	def gadget_enable_button_set(self):
		# print("gadget_enable_button_set: %s" % (self.m.query_gadget()), file=sys.stderr)
		gadget = self.m.query_gadget()
		current = self.gadget_spinbox.get().strip()
		if gadget is None:
			if current == self.nodefstr:
				t = "Enable"
				self.gadget_enable_button['bg'] = 'Light Grey'
			else:
				t = "Enable \"%s\"" % (current)
				self.gadget_enable_button['bg'] = 'Light Blue'
		else:
			if current == self.nodefstr:
				t = "Disable" % (current)
				self.gadget_enable_button['bg'] = 'Light Grey'
			elif current != gadget:
				t = "Disable (%s not enabled)" % (current)
				self.gadget_enable_button['bg'] = 'Light Grey'
			else:
				t = "Disable \"%s\"" % (gadget)
				self.gadget_enable_button['bg'] = 'Light Green'
		self.gadget_enable_button['text'] = t

	def gadget_enable_button_pressed(self):
		# print("*****\ngadget_enable_button_pressed: ", file=sys.stderr)
		if self.m.query_gadget() is not None:

			if not self.m.disable_current():
				messagebox.showerror(title="Error", message="Detach UDC from %s first" % (self.m.query_gadget()))
			self.update()
			return

		# print("gadget_enable_button_pressed: gadget selection: %s" % (self.gadget_spinbox.get().strip()), file=sys.stderr)
		self.m.enable_current(self.gadget_spinbox.get().strip())
		#self.gadget_enable_button_set()
		#self.udc_button_set()
		self.update()

	def gadget_add_button_set(self):
		# print("gadget_add_button_set: %s" % (self.m.query_gadget()), file=sys.stderr)
		self.gadget_add_button['bg'] = 'Light Blue'
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

	def gadget_add_button_pressed(self):
		# print("gadget_add_button_pressed:", file=sys.stderr)

		f = filedialog.askopenfilename(
			initialdir="/etc/gadgetservice",
			title="Select Gadget Definition File",
			filetypes=(("json files", "*.json"), ("all files", "*.*")))

		if isinstance(f, tuple):
			return
		if f == '':
			return
		# print("--", file=sys.stderr)
		# print(type(f), file=sys.stderr)
		# print(f, file=sys.stderr)
		# print("--", file=sys.stderr)
		# if f is not None:
		# 	print("gadget_add_button_pressed: file \"%s\"" % (f), file=sys.stderr)
		# else:
		# 	print("gadget_add_button_pressed: file NONE", file=sys.stderr)

		if f is None:
			return

		new_device_name = self.m.check_device_file(f)
		if new_device_name is not None:
			new_device_name = self.get_new_device_name(f)
			if new_device_name is None:
				return
		# print("####\ngadget_add_button_pressed: file: %s %s" % (f, new_device_name), file=sys.stderr)
		try:
			# print("calling add_device_file", file=sys.stderr)
			self.m.add_device_file(f, new_device_name=new_device_name)
		except FileExistsError:
			messagebox.showerror(title="Error", message="Gadget Definition for %s already exists!" % (self.m.check_device_file(f)))
		self.gadget_definitions_spinbox()
		self.notebook()
		self.update()

	def gadget_remove_button_set(self):
		# print("gadget_remove_button_set: %s" % (self.m.query_gadget()), file=sys.stderr)
		current = self.gadget_spinbox.get().strip()
		if current == self.m.query_gadget():
			# print("gadget_remove_button_set: cannot remove enabled gadget", file=sys.stderr)
			self.gadget_remove_button['text'] = "Cannot Remove \"%s\" (disable first)" % (current)
			self.gadget_remove_button['bg'] = 'Light Pink'
		elif current == self.nodefstr:
			self.gadget_remove_button['text'] = "Remove"
			self.gadget_remove_button['bg'] = 'Light Grey'
		else:
			self.gadget_remove_button['text'] = "Remove \"%s\"" % (current)
			self.gadget_remove_button['bg'] = 'Light Blue'

	def gadget_remove_button_pressed(self):
		# print("gadget_remove_button_pressed:", file=sys.stderr)
		if self.gadget_spinbox.get().strip() == self.m.query_gadget():
			messagebox.showerror(title="Error", message="Disable %s first" % (self.m.query_gadget()))
			return
		r = RemoveGadget(self.m.configpath, self.m)
		r.remove_device(self.gadget_spinbox.get().strip())
		self.gadget_definitions_spinbox()
		self.notebook()
		self.update()
		# print("gadget_remove_button_pressed: EXIT", file=sys.stderr)

	# gadget_definitions_spinbox
	# this needs to be created new for each change in the gadgets list
	def gadget_definitions_spinbox(self):
		current = None
		if self.gadget_spinbox is not None:
			current = self.gadget_spinbox.get().strip()
			# print("#####\ngadget_definitions_spinbox: current: %s" % (current), file=sys.stderr)
		else:
			# print("#####\ngadget_definitions_spinbox: NO CURRENT", file=sys.stderr)
			pass

		v = sorted(self.m.query_gadgets(), key=str.casefold, reverse=True)
		lv = v
		# print("gadget_definitions_spinbox: v: %s" % (v), file=sys.stderr)
		if len(v) == 0:
			v.append(self.nodefstr)
		v = [" " + x for x in v]
		self.gadget_spinbox_title = tk.Label(self.tk, text='<-- Select Gadget Device Definition',
				font=tkFont.Font(family='Helvetica', size=8), anchor='ne', justify='left')
		self.gadget_spinbox = ttk.Combobox(self.tk, values=v, height=4, font=tkFont.Font(family='Helvetica', size=10, weight='bold'))

		self.gadget_spinbox_title.grid(row=1, rowspan=1, column=9, columnspan=1, sticky=tk.W, padx=(0, 1), pady=(4, 0))
		self.gadget_spinbox.grid(row=1, rowspan=1, column=2, columnspan=7, sticky=tk.NSEW, padx=(8, 0), pady=(1, 4))

		self.gadget_spinbox.bind("<<ComboboxSelected>>", self.gadget_spinbox_command)
		self.gadget_spinbox.current(0)
		# print("gadget_definitions_spinbox: current: %s v: %s CHECK" % (current, v), file=sys.stderr)
		if current in lv:
			# print("gadget_definitions_spinbox: current: %s UPDATE" % (current), file=sys.stderr)
			self.gadget_spinbox.set(current)

	def gadget_spinbox_command(self, arg):
		# print("gadget_spinbox_command: arg: %s " % (arg), file=sys.stderr)
		self.update()

	def doFoo(self, event):
		print("doFoo: %s " % (event), file=sys.stderr)
		self.update()

	def setExitFlag(self):
		# print("setExitFlag:", file=sys.stderr)
		self.exitFlag = True

	def tk(self):
		self.tk = Tk()
		self.tk.bind("<<FOO>>", self.doFoo)
		self.tk.bind("<Button-1>", self.doFoo)
		self.tk.bind("<Button-3>", self.doFoo)
		self.tk.geometry("700x660")
		self.tk.call('encoding', 'system', 'utf-8')
		self.tk.title("Gadget USB Device Configuration - %s" % (os.uname()[1]))
		self.tk.protocol("WM_DELETE_WINDOW", self.setExitFlag)

		# the spinbox is created and recreated on the fly to respond to the current list of gadgets
		self.gadget_definitions_spinbox()

		self.gadget_enable_button = tk.Button(self.tk, text='', command=self.gadget_enable_button_pressed, width=28, anchor='w')
		self.gadget_remove_button = tk.Button(self.tk, text='', command=self.gadget_remove_button_pressed, width=28, anchor='w')

		self.gadget_add_button = tk.Button(self.tk, text='Add definition', command=self.gadget_add_button_pressed, width=1, anchor='center')
		self.udc_button = tk.Button(self.tk, text='-', command=self.udc_button_pressed, width=14, anchor='center')

		self.udc_button.grid(row=1, rowspan=2, column=1, columnspan=1, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_add_button.grid(row=3, rowspan=1, column=1, columnspan=1, sticky=tk.NSEW, pady=(1, 1))

		self.gadget_enable_button.grid(row=2, rowspan=1, column=2, columnspan=8, sticky=tk.NSEW, pady=(1, 1))
		self.gadget_remove_button.grid(row=3, rowspan=1, column=2, columnspan=8, sticky=tk.NSEW, pady=(1, 1))

		self.udc_button_set()
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

	# gadget_notebook
	# this needs to be created new for each change in the gadgets list
	def notebook(self):
		# print('notebook')
		self.tabs = Tabs(self.m, self.tk, row=4, column=1, columnspan=8)


def main():

	sys_config_path = "/sys/kernel/config/usb_gadget"
	m = ManageGadget(sys_config_path)
	# print('realudcpath: %s' % (m.query_udc_path()))
	w = watch(m.query_udc_path())
	w._start()

	e = Editor(manage=m)
	e.tk()

	while not e.exitFlag:
		e.tk.update()

		try:
			sleep(.1)
		except(KeyboardInterrupt):
			break
		if w.event():
			e.event()

	w.stop()


if __name__ == '__main__':
	main()
