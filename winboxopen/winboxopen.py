#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

import os
import re
import sys
import time
import pickle
import getpass
import argparse
import subprocess

__scriptname__ = 'winboxopen'
__version__ = '1.2'
__author__ = 'shmilee'
__configpath__ = '~/.%s.pck' % __scriptname__


class VMinfo(object):

    def __init__(self, name, uuid, ostype, sharepath, sharename, netdrive,
                 user, passwd):
        self.name = name
        self.uuid = uuid
        self.ostype = ostype
        self.sharepath = sharepath  # []
        self.sharename = sharename  # []
        self.netdrive = netdrive   # {}
        self.user = user
        self.__passwd = passwd
        self.host_webcams = tuple(c[0] for c in self.get_info_from_cmd(
            ["VBoxManage", "list", "webcams"], r'^(/dev/.*)') if c)

    @staticmethod
    def get_info_from_cmd(command, pattern, groupdict=False):
        out = subprocess.check_output(command).decode(errors='replace')
        if not isinstance(pattern, re.Pattern):
            pattern = re.compile(pattern)
        res = []
        for line in out.splitlines():
            m = pattern.match(line)
            if not m:
                continue
            if groupdict:
                res.append(m.groupdict())
            else:
                res.append(m.groups())
        return res

    @property
    def cmd_showvminfo(self):
        return ["VBoxManage", "showvminfo", self.name, "--machinereadable"]

    @property
    def config_info(self):
        return dict(
            name=self.name,
            uuid=self.uuid,
            ostype=self.ostype,
            sharepath=self.sharepath,
            sharename=self.sharename,
            netdrive=self.netdrive,
            username=self.user,
            password=self._VMinfo__passwd
        )

    @property
    def vmstate(self):
        k, v = self.get_info_from_cmd(
            self.cmd_showvminfo, r'^(?P<key>VMState)="(?P<val>.*)"$')[0]
        return v

    @property
    def graphicsmode(self):
        '''None; not active -> '0'; active/running -> '50' '''
        kv = self.get_info_from_cmd(
            self.cmd_showvminfo,
            r'^(?P<key>GuestAdditionsFacility_Graphics Mode)=(?P<val>.*)$')
        if kv:
            return kv[0][1].split(',')[0]
        return None

    def start_vm(self):
        if self.vmstate == 'running':
            print("Machine '%s' is running!" % self.name)
        else:
            out = subprocess.check_output(
                ["VBoxManage", "startvm", self.name]).decode()
            print(out)
            if 'successfully started' not in out:
                return
        while self.graphicsmode != '50':
            time.sleep(0.5)
            print("Waiting for Graphics Mode active/running ...", end='\r')
        print()

    def shutdown_vm(self):
        if self.vmstate == 'running':
            print(subprocess.check_output(
                ["VBoxManage", "controlvm", self.name, "acpipowerbutton"]).decode())

    def convert_path(self, path):
        '''Convert host path to guest path'''
        path = os.path.abspath(path)
        for idx in range(len(self.sharepath)):
            if (path.startswith(self.sharepath[idx])
                    and self.sharename[idx] in self.netdrive):
                drive = self.netdrive[self.sharename[idx]]
                guest_path = drive + path.replace(self.sharepath[idx], '')
                win_path = guest_path.replace('/', '\\')
                return win_path
        print("Warnning: cannot convert '%s' to guest(%s) path!"
              % (path, self.name))
        return None

    @property
    def cmd_openpath(self):
        return ["VBoxManage", "guestcontrol", self.name, "run",
                "--exe", "cmd.exe",
                "--username", self.user,
                "--password", self._VMinfo__passwd,
                "--", "cmd", "/c"]

    def open_path(self, path):
        '''Open file by application or attach webcam in guest'''
        if path in self.host_webcams:
            if self.vmstate != 'running':
                self.start_vm()
            if self.vmstate == 'running':
                cmd = ["VBoxManage", "controlvm",
                       self.name, "webcam", "attach", path]
                print("Attaching webcam '%s' to machine '%s': %s ..."
                      % (path, self.name, ' '.join(cmd)))
                proc = subprocess.Popen(
                    cmd, universal_newlines=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                if proc.returncode != 0:
                    print(stderr)
            else:
                print("Error: machine '%s' is not running!" % self.name)
            return
        if not os.path.isfile(path):
            print("Error: '%s' is not a file!" % path)
            return
        win_path = self.convert_path(path)
        if win_path:
            if self.graphicsmode != '50':
                self.start_vm()
            if self.graphicsmode == '50':
                print("Opening file '%s' -> (%s)'%s' ..."
                      % (path, self.name, win_path))
                return subprocess.Popen(
                    self.cmd_openpath + [win_path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                print("Error: machine '%s' Graphics Mode not active!" % self.name)

    @classmethod
    def get_vmlist(cls):
        return cls.get_info_from_cmd(
            ["VBoxManage", "list", "vms"],
            r'^"(?P<name>.*)"\s\{(?P<uuid>.*)\}$')

    @property
    def cmd_netuse(self):
        return ["VBoxManage", "guestcontrol", self.name, "run",
                "--exe", "net.exe",
                "--username", self.user,
                "--password", self._VMinfo__passwd,
                "--", "net/arg0", "use"]

    @classmethod
    def get_init_vminfo(cls, name, uuid):
        '''
        1. find windows guest with sharedfolders
        2. sartvm guest, get network drive, then shutdown guest
        '''
        this = cls(name, uuid, None, [], [], {}, None, None)
        pattern = r'^(?P<key>(?:ostype|SharedFolderNameMachineMapping[\d]+|SharedFolderPathMachineMapping[\d]+))="(?P<val>.*)"$'
        for key, val in cls.get_info_from_cmd(this.cmd_showvminfo, pattern):
            if key == 'ostype':
                if 'Windows' not in val:
                    print("Ignore machine '%s': Not a Windows guest!" % name)
                    return None
                this.ostype = val
            elif key.startswith('SharedFolderPath'):
                this.sharepath.append(val)
            elif key.startswith('SharedFolderName'):
                this.sharename.append(val)
        if not this.sharename or len(this.sharepath) != len(this.sharename):
            print("Ignore machine '%s': No sharedfolder!" % name)
            return None
        this.start_vm()
        if this.vmstate == 'running':
            print("Specify user to logon on machine %s." % name)
            this.user = input('username: ')
            this._VMinfo__passwd = getpass.getpass('password: ')
            pattern = r'\s+(?P<drive>[C-Z]:)\s+\\{2}VBOXSVR\\(?P<sharename>.+?)\s+VirtualBox Shared Folders'
            for drive, sn in cls.get_info_from_cmd(this.cmd_netuse, pattern):
                if sn in this.sharename:
                    this.netdrive[sn] = drive
        for sn, sp in zip(this.sharename, this.sharepath):
            if sn not in this.netdrive:
                print("Warnning: (%s) '%s' not mapped in guest!" % (sn, sp))
        this.shutdown_vm()
        return this

    @classmethod
    def get_vminfo(cls, config_info):
        '''reload vminfo from config_info'''
        return cls(
            config_info['name'],
            config_info['uuid'],
            config_info['ostype'],
            config_info['sharepath'],
            config_info['sharename'],
            config_info['netdrive'],
            config_info['username'],
            config_info['password']
        )


def generate_config(config_path):
    config = dict(default=None, machine={})
    for name, uuid in VMinfo.get_vmlist():
        vm = VMinfo.get_init_vminfo(name, uuid)
        if vm:
            config['machine'][name] = vm.config_info
    if len(config['machine']) == 0:
        print("Warnning: add no guest machine!")
    else:
        config['default'] = list(config['machine'].keys())[0]
    with open(config_path, 'wb') as handle:
        pickle.dump(config, handle, protocol=pickle.HIGHEST_PROTOCOL)


def list_config(config_path):
    with open(config_path, 'rb') as handle:
        c = pickle.load(handle)
        print('Default machine: %s\n' % c['default'])
        for name, info in c['machine'].items():
            print(name.center(24, '-'))
            for k, v in info.items():
                print('%s: %s' % (k, v))
            print()


def set_default_guest(config_path, name):
    with open(config_path, 'rb') as handle:
        c = pickle.load(handle)
    if name in c['machine']:
        c['default'] = name
        with open(config_path, 'wb') as handle:
            pickle.dump(c, handle, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        print("Warnning: machine '%s' not available!" % name)
        print("Please choose from %s." % list(c['machine'].keys()))


def generate_parser():
    parser = argparse.ArgumentParser(
        prog=__scriptname__,
        description=("Open files in a VirtualBox Windows guest from the Linux host, "
                     "if file is a webcam path, just attach it to guest."),
        add_help=False,
    )
    optgrp = parser.add_argument_group('options')
    optgrp.add_argument('-f', '--file', type=str, metavar='path',
                        help='File to open')
    optgrp.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit')
    optgrp.add_argument('-V', '--version', action='store_true',
                        help='Print version and exit')

    subparsers = parser.add_subparsers(title='optional command', dest='cmd')
    subparser_config = subparsers.add_parser(
        name='config',
        description="Config VirtualBox Windows guest's info in %s" % __configpath__,
        add_help=False,
    )
    optgrp = subparser_config.add_argument_group('config options')
    optgrp.add_argument('-g', '--generate', action='store_true',
                        help='Generate new config of guests')
    optgrp.add_argument('-l', '--list', action='store_true',
                        help="List guest's info in config")
    optgrp.add_argument('-s', '--set', type=str, metavar='name',
                        help='Set a default guest')
    optgrp.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit')
    return parser, subparser_config


if __name__ == '__main__':
    parser, subparser_config = generate_parser()
    args = parser.parse_args()
    # print(args)

    config_path = os.path.expanduser(__configpath__)
    if args.cmd == 'config':
        if args.help or not (args.generate or args.list or args.set):
            subparser_config.print_help()
            sys.exit()
        if args.generate:
            generate_config(config_path)
        if args.list:
            list_config(config_path)
        if args.set:
            set_default_guest(config_path, args.set)
        sys.exit()
    else:
        if args.help:
            parser.print_help()
            sys.exit()
        if args.version:
            print("%s v%s" % (__scriptname__, __version__))
            sys.exit()
        if args.file:
            with open(config_path, 'rb') as handle:
                c = pickle.load(handle)
            vm = VMinfo.get_vminfo(c['machine'][c['default']])
            vm.open_path(args.file)
        else:
            parser.print_help()
        sys.exit()
