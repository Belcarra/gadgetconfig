#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Set encoding default for python 2.7
# vim: syntax=python expandtab tabstop=4

# sysfstree implements a generator that will recursively iterate a file system, typically /sys, retrieving
# the contents of the files, and displaying the path names them in a fashion similar to the tree(1) command.
#

# e.g. sysfstree /sys/devices/platform/soc/ --include udc
#  [/sys/devices/platform/soc]
#  ┣━[fe980000.usb]
#  ┃   ┣━[udc]
#  ┃   ┃   ┗━[fe980000.usb]
#  ┃   ┃       ┣━device -> /sys/devices/platform/soc/fe980000.usb
#  ┃   ┃       ┣━subsystem -> /sys/class/udc
#  ┃   ┃       ┣━[power]
#  ┃   ┃       ┃   ┣━runtime_suspended_time: 0
#  ┃   ┃       ┃   ┣━autosuspend_delay_ms:
#  ┃   ┃       ┃   ┣━runtime_active_time: 0
#  ┃   ┃       ┃   ┣━control: auto
#  ┃   ┃       ┃   ┗━runtime_status: unsupported
#  ┃   ┃       ┣━current_speed: UNKNOWN
#  ┃   ┃       ┣━is_selfpowered: 0
#

# pigadgetinfo displays info about Gadget USB from the SysFS and ConfigFS.
# The display format is similar to tree(1) with the contents of the files shown.
#
# loosely adapted from FileTreeMaker.py

import os
import sys
import fnmatch
import magic
import struct
from termcolor import colored

"""sysfstree.py: ..."""

# ToDo
# 1. check for null bytes in osdesc and dev/host addr

# __author__  = "Stuart.Lynne@belcarra.com"


class sysfstree(object):

    def __init__(self, root, maxlevel, pinclude=[], pexclude=[], include=None, exclude=None,
            bold=None, ordinary=False, nobold=False, sort=True, followsyms=False):

        self.maxlevel = maxlevel
        self.include = include
        self.exclude = exclude
        self.bold = bold
        self.followsyms = followsyms
        self.ordinary = ordinary
        self.nobold = nobold
        self.root = root
        self.sort = sort

        self.pinclude = [x.split('/') for x in pinclude]
        self.pexclude = [x.split('/') for x in pexclude]

        if len(self.pinclude) > 0 and len(self.include):
            print('sysfstree: pinclude and include mutually exclusive')
            exit(1)
        if len(self.pexclude) > 0 and len(self.exclude):
            print('sysfstree: pexclude and exclude mutually exclusive')
            exit(1)

        #print("sysfstree: pinclude: %s" % (pinclude), file=sys.stderr)
        #print("sysfstree: pinclude: %s" % (self.pinclude), file=sys.stderr)
        #print("sysfstree: pexclude: %s" % (self.pexclude), file=sys.stderr)

        #print("sysfstree: maxlevel: %s include: %s exclude: %s bold: %s root: %s" %
        #   (self.maxlevel, self.include, self.exclude, self.bold, self.root), file=sys.stderr)

    # match_exclude
    # Return False if matches is None or name not in matches
    #
    def match_exclude(self, name, level):

        if len(self.pexclude) > 0:
            return False

        if self.exclude is None:
            return False
        try:
            matches = self.exclude[level]
        except IndexError:
            return False

        print("match_exclude: %s in %s" % (name, matches), file=sys.stderr)
        if len(matches) == 0:
            # print("match_exclude: %s in %s len(matches) == 0" % (name, matches), file=sys.stderr)
            return False
        if type(matches) is list:
            # print("match_exclude: %s in %s list" % (name, matches), file=sys.stderr)
            return any(fnmatch.fnmatch(name, pattern) for pattern in matches)
        if type(matches) is str:
            # print("match_exclude: %s in %s str" % (name, matches), file=sys.stderr)
            return fnmatch.fnmatch(name, matches)
        return False

    # match_include
    # Return True if matches is None or if name in matches
    #
    def match_include(self, name, level):

        if len(self.pinclude) > 0:
            return False

        # print('match_include: %s' % (name), file=sys.stderr)
        if self.include is None:
            return True
        try:
            matches = self.include[level]
        except IndexError:
            return True

        # print("match_include: %s in %s" % (name, matches), file=sys.stderr)
        if len(matches) == 0:
            # print("match_include: len 0")
            return True
        if type(matches) is list:
            # print("match_include: match list")
            return any(fnmatch.fnmatch(name, pattern) for pattern in matches)
        if type(matches) is str:
            # print("match_include: match str")
            return fnmatch.fnmatch(name, matches)
        return True

    # match_pexclude
    # Return False if matches is None or name not in matches
    #
    def match_pexclude(self, path, name, level):

        if len(self.exclude) > 0:
            #print("match_pexclude: self.exclude")
            return False

        # file = path[len(self.root)+1:]
        if self.pexclude is None:
            #print("match_pexclude: no self.pexclude")
            return False

        for match in self.pexclude:
            print("match_pexclude: %s" % (match))
            try:
                print("match_pexclude: %s:%s:%s" % (name, match, match[level]), file=sys.stderr)
                if fnmatch.fnmatch(name, match[level]):
                    #print("match_pexclude: MATCH %s %s" % (name, match), file=sys.stderr)
                    return True
            except (IndexError):
                pass
        return False

    # match_pinclude
    # Return True if matches is None or if name in matches
    #
    def match_pinclude(self, path, name, level):

        if len(self.include) > 0:
            return False

        # file = path[len(self.root)+1:]
        if self.pinclude is None:
            return True

        for match in self.pinclude:
            try:
                #print("match_pinclude: %s:%s:%s" % (name, match, match[level]), file=sys.stderr)
                if fnmatch.fnmatch(name, match[level]):
                    #print("match_pinclude: MATCH %s %s" % (name, match), file=sys.stderr)
                    return True
            except (IndexError):
                pass
        # print("match_pinclude: NO MATCH %s" % (name), file=sys.stderr)
        return False

    def _colored(self, text, color=None, attrs=None):
        if self.nobold:
            return text
        return colored(text, color, attrs=attrs)

    def _color(self, path, level):
        if self.bold is None:
            return path
        try:
            matches = self.bold[level]
        except IndexError:
            matches = None

        # print("_color: %s in %s" % (path, matches), file=sys.stderr)

        if matches is None or len(matches) == 0:
            pass

        elif type(matches) is list:
            # print("color: %s in %s list" % (path, matches), file=sys.stderr)
            if any(fnmatch.fnmatch(path, pattern) for pattern in matches):
                return self._colored(path, 'red', attrs=['bold'])

        elif type(matches) is str:
            # print("color: %s in %s str" % (name, matches), file=sys.stderr)
            if fnmatch.fnmatch(path, matches):
                return self._colored(path, 'red', attrs=['bold'])
        return path

    def pathdescriptors(self, path):
        try:
            # XXX need to stat the file and limit how much
            # we are willing to read
            bdata = []
            with open(path, 'rb') as f:
                byte = f.read(1)
                while byte:
                    bdata.append(struct.unpack('B', byte)[0])
                    byte = f.read(1)

            length = 0
            descriptors = []
            hexstr = ''
            for x in bdata:
                t = "%02x" % (x)
                if length == 0:
                    hexstr = t
                    length = x - 1
                else:
                    length -= 1
                    hexstr += ' ' + t
                if length == 0:
                    length = 0
                    descriptors.append(hexstr)
                    hexstr = ''

            return descriptors

        except Exception:
            return ''

    def pathread(self, path):

        try:
            fstat = os.stat(path)
            #print("fstat: size:%s" % (fstat.st_size), file=sys.stderr)
        except (PermissionError):
            return ''

        # 4096 or 0 byte files should contain info
        #if self.ordinary or fstat.st_size == 4096 or fstat.st_size == 0:
        if self.ordinary or fstat.st_size in [16384, 4096, 0]:
            try:
                f = open(path, "r")
                lines = f.readlines(1000)
                f.close()
                return lines
            except (PermissionError, OSError):
                return ''
            except UnicodeDecodeError:
                print('pathread: [UnicodeDecodeError]', file=sys.stderr)
                pass
            try:
                f = open(path, "rb")
                bytes = f.read(4096)
                f.close
            except (PermissionError, OSError):
                return ''
            #print("bytes: %s" % (type(bytes)), file=sys.stderr)
            #print("bytes: %s" % (bytes), file=sys.stderr)
            return bytes

        # 65553 byte files are USB Descriptors
        if fstat.st_size == 65553:
            return self.pathdescriptors(path)

        # unknown - see if ELF module, this is special case
        # so we can list modules from /lib/.*/modules/
        #
        try:
            filetype = magic.from_file(path)
            if "ELF" in filetype:
                return ["ELF file"]
        except (magic.MagicException, PermissionError):
            return ''
        return '<UNKNOWN>'

    # recurse through the file system displaying information from the files
    # and symlinks found
    #
    def _tree(self, parent_path, file_list, prefix, level):

        if level == -1:
            yield ("[%s]" % (self._colored(parent_path, attrs=['bold'])))
            yield from self._tree(parent_path, file_list, prefix, 0)
            return

        if len(file_list) == 0 or (self.maxlevel != -1 and self.maxlevel <= level):
            return

        if self.sort:
            file_list = sorted(file_list, key=str.casefold)

        # first all of the files and symlinks, skip directories
        for idx, sub_path in enumerate(file_list):

            full_path = os.path.join(parent_path, sub_path)

            # if there is a set of includes for this level ensure that the we match
            # this path
            if not (self.match_pinclude(full_path, sub_path, level) or self.match_include(sub_path, level)):
                # print('%s FILE DID NOT MATCH INCLUDE' % (sub_path), file=sys.stderr)
                continue

            # if there is a set of excludes for this level ensure that the we do not
            # match this path
            if self.match_exclude(sub_path, level) or self.match_pexclude(full_path, sub_path, level):
                # print('%s FILE DID MATCH EXCLUDE' % (sub_path), file=sys.stderr)
                continue

            # set the tree decoration
            # idc = ("┣━━", "┗━━")[idx == len(file_list) - 1]
            idc = ("├──", "└──")[idx == len(file_list) - 1]

            # for symlinks yield the real pathname
            if os.path.islink(full_path) and not self.followsyms:
                yield ("%s%s%s -> %s" % (prefix, idc, self._color(sub_path, level), os.path.realpath(full_path)))
                continue

            # files yield as many lines of data as we read from the file, pathread() does
            # some interpretation so it will recognize ELF files and USB Descriptors
            #
            if not os.path.isfile(full_path):
                continue

            data = self.pathread(full_path)
            first = True
            # test for empty file
            if len(data) == 0:
                yield ("%s%s%s: [NULL]" % (prefix, idc, self._color(sub_path, level)))
                continue

            idc = "├──"
            # special case for non-text data
            if type(data) == bytes:
                line = ''
                count = 0
                total = 0
                for d in data:
                    line += " %02x" % int(d)
                    total += 1
                    count += 1
                    if count < 16 and total < len(data):
                        continue

                    yield ("%s%s%s:%s" % (prefix, idc, self._color(sub_path, level), line))
                    count = 0
                    line = ''
                    if not first:
                        continue
                    # blank sub_path and change idc
                    sub_path = ' ' * (len(sub_path) + 1)
                    idc = "│ "
                    first = False
                continue

            # normal text data
            for d in data:
                yield ("%s%s%s: %s" % (prefix, idc, self._color(sub_path, level), d.rstrip()))
                if not first:
                    continue
                # blank sub_path and change idc
                sub_path = ' ' * (len(sub_path) + 1)
                idc = "│ "
                first = False

        # do directories
        for idx, sub_path in enumerate(file_list):

            full_path = os.path.join(parent_path, sub_path)

            # if there is a set of includes for this level ensure that the we match
            # this path
            if not self.match_pinclude(full_path, sub_path, level) and not self.match_include(sub_path, level):
                # print('%s dir did not match include' % (sub_path), file=sys.stderr)
                continue

            # if there is a set of excludes for this level ensure that the we do not
            # match this path
            if self.match_exclude(sub_path, level) or self.match_pexclude(full_path, sub_path, level):
                # print('%s dir did match exclude' % (sub_path), file=sys.stderr)
                continue

            # set the tree decoration
            # idc = ("┣━━", "┗━━")[idx == len(file_list) - 1]
            idc = ("├──", "└──")[idx == len(file_list) - 1]

            if not self.followsyms and os.path.islink(full_path):
                continue

            # for directories yield the directory name and then yield from recursively
            if os.path.isdir(full_path) or os.path.islink(full_path):

                if os.path.islink(full_path):
                    yield ("%s%s[%s -> %s]" % (prefix, idc, self._color(sub_path, level), os.path.realpath(full_path)))
                    full_path = os.path.realpath(full_path)
                    print("parent_path: %s" % (parent_path))
                    print("full_path: %s" % (full_path))
                else:
                    yield ("%s%s[%s]" % (prefix, idc, self._color(sub_path, level)))

                tmp_prefix = (prefix + "    ", prefix + "│   ")[len(file_list) > 1 and idx != len(file_list) - 1]
                # paths = os.listdir(full_path)
                paths = [d.name for d in sorted(os.scandir(full_path), key=lambda dirent: dirent.inode())]
                yield from self._tree(full_path, paths, tmp_prefix, level + 1)
                # yield from self._tree(full_path, os.listdir(full_path), tmp_prefix, level + 1)


def _main2(paths, maxlevel=-1, pinclude=[], pexclude=[], include=[], exclude=[], bold=[],
        ordinary=False, nobold=False, sort=True, followsyms=False):
    #print("paths: %s" % (paths), file=sys.stderr)
    #print("include: %s" % (include), file=sys.stderr)
    #print("exclude: %s" % (exclude), file=sys.stderr)
    # print("bold: %s" % (bold), file=sys.stderr)
    for p in paths:
        sysfs = sysfstree(p, maxlevel=maxlevel,
                pinclude=pinclude, pexclude=pexclude,
                include=include, exclude=exclude,
                bold=bold, ordinary=ordinary, nobold=nobold, sort=sort, followsyms=followsyms)
        try:
            for l in sysfs._tree(p, os.listdir(p), "", -1):
                print("%s" % (l), file=sys.stdout)
        except PermissionError:
            print("[%s] [PermissionError]" % (p))


def _test(args):
    import doctest
    doctest.testmod()

    _main2(["/sys/kernel/config/usb_gadget"], bold=[[], ['UDC']], sort=False)

    # _ main(["/sys/devices/platform/soc"], include=["*.usb"])
    # _main2(["/sys/devices/platform/soc"], maxlevel=args.maxlevel, include=[["*.usb"]], exclude=[[],
    #   ["usb3", "subsystem", "driver", "power", "gadget", "of_node", "pools", "driver_override", "modalias", "uevent"]])

    # _main2(["/sys/devices/platform/soc"], maxlevel=args.maxlevel, include=[["*.usb"], ["udc"]])

    # _main2(["/sys"], include=[["power"], ["pm_freeze_timeout", "state"]])
    # _main2(["/sys/devices/platform/soc"], include=[["*.usb"], ["usb3"], ["descriptors", "ep_00", "driver"]])

    # _main2(["/sys/kernel/debug/tracing/events/workqueue/workqueue_execute_end"], )

    # (sysname, nodename, release, version, machine) = os.uname()
    # path = "/lib/modules/" + release + "/kernel/drivers/usb/gadget/function/"
    # _main2([path], maxlevel=args.maxlevel, include=["usb_f_*"])


# this is mainly for testing standalone
#
def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Display information about Gadget USB from SysFS and ConfigFS",
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=999))

    parser.add_argument("-T", "--test", help="run tests", action='store_true')
    parser.add_argument("-O", "--ordinary", help="not in /sys", action='store_true')
    parser.add_argument("-P", "--path", nargs='*', help="include (shell pattern match)", default=[])
    parser.add_argument("-I", "--include", nargs='*', help="include (shell pattern match)", default=[])
    parser.add_argument("-E", "--exclude", nargs='*', help="exclude (shell pattern match)", default=[])
    parser.add_argument("--pinclude", nargs='*', help="path include (shell pattern match)", default=[])
    parser.add_argument("--pexclude", nargs='*', help="path exclude (shell pattern match)", default=[])

    parser.add_argument("-B", "--bold", nargs='*', help="bold (shell pattern match)", default=[])
    parser.add_argument("-N", "--nobold", nargs='*', help="bold (shell pattern match)", default=[])

    parser.add_argument("--include_list", type=json.loads, help="json list version of include", default=[])
    parser.add_argument("--exclude_list", type=json.loads, help="json list version of exclude", default=[])
    parser.add_argument("--bold_list", type=json.loads, help="json list version of bold")

    parser.add_argument("--udc", help="/sys/class/udc", action='store_true')
    parser.add_argument("--usb-gadget", "--gadget", help="/sys/kernel/config/usb_gadget", action='store_true')
    parser.add_argument("--usb-gadget-udc", "--gadget-udc", help="/sys/kernel/config/usb_gadget/*/udc", action='store_true')

    parser.add_argument("-m", "--maxlevel", help="max level", type=int, default=-1)
    parser.add_argument("paths", metavar='Path', type=str, nargs=argparse.REMAINDER, help="pathname", default=[])

    args = parser.parse_args()

    print("args: %s" % (args), file=sys.stderr)

    if args.bold and args.bold_list:
        print("--bold and --bold_list are mutually incompatible, use only one", file=sys.stderr)
        exit(1)

    if args.include and args.include_list:
        print("--include and --include_list are mutually incompatible, use only one", file=sys.stderr)
        exit(1)

    if args.exclude and args.exclude_list:
        print("--exclude and --exclude_list are mutually incompatible, use only one", file=sys.stderr)
        exit(1)

    if args.bold:
        args.bold_list = [args.bold]

    if args.include:
        args.include_list = [args.include]

    if args.exclude:
        args.exclude_list = [args.exclude]

    if args.test:
        _test(args)

    if args.udc:
        print("udc")
        for s in os.listdir("/sys/class/udc"):
            # print("udc: s: %s" % (s, ), file=sys.stderr)
            _main2([os.path.realpath("/sys/class/udc/%s" % (s))], maxlevel=args.maxlevel)
        return

    if args.usb_gadget:
        print("usb_gadget")
        _main2(["/sys/kernel/config/usb_gadget"], maxlevel=args.maxlevel)
        return

    if args.usb_gadget_udc:
        print("usb_gadget_udc")
        _main2(["/sys/kernel/config/usb_gadget/"], maxlevel=args.maxlevel,
                include=[[], ["UDC"]],
                bold=[[], ["UDC"]])
        return

    for path in args.path + args.paths:
        _main2([path], maxlevel=args.maxlevel,
                include=args.include_list, exclude=args.exclude_list,
                pinclude=args.pinclude, pexclude=args.pexclude,
                bold=args.bold_list, ordinary=args.ordinary, nobold=args.nobold)


if __name__ == "__main__":
    main()
