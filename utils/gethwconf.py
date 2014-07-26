#!/usr/bin/env python
# Copyright (C) 2014 Jurriaan Bremer.
# This file is part of VMCloak - http://www.vmcloak.org/.
# See the file 'docs/LICENSE.txt' for copying permission.

import argparse
import json
import os
import subprocess

DMIDECODE = '/usr/sbin/dmidecode'
LSHW = '/usr/bin/lshw'


def get_dmi(t):
    ret = {}

    try:
        output = subprocess.check_output([DMIDECODE, '-t', '%d' % t])
    except subprocess.CalledProcessError:
        return ret

    for line in output.split('\n'):
        if line.startswith('Handle') and line.count(',') == 2:
            ret['dmi_type'] = int(line.split(',')[1].split(' ')[-1])
            continue

        if ':' not in line:
            continue

        key, value = line.split(':', 1)
        ret[key.strip()] = value.strip()
    return ret


def get_lshw(c):
    try:
        output = subprocess.check_output([LSHW, '-C', c])
    except subprocess.CalledProcessError:
        return

    ret = {}
    for line in output.split('\n'):
        # New disk.
        if '*-disk' in line:
            if ret:
                yield ret

            ret = {}
            continue

        if ':' not in line:
            continue

        key, value = line.split(':', 1)
        ret[key.strip()] = value.strip()

    if ret:
        yield ret


if __name__ == '__main__':
    if os.geteuid():
        print '[!] You will probably want to run this tool as root.'

    parser = argparse.ArgumentParser()
    parser.add_argument('fname', type=str, help='Name of this configuration.')
    parser.add_argument('--dmidecode', type=str, help='Path to dmidecode(8).')
    parser.add_argument('--lshw', type=str, help='Path to lshw(1).')

    args = parser.parse_args()

    if args.dmidecode:
        DMIDECODE = args.dmidecode

    if args.lshw:
        LSHW = args.lshw

    bios = get_dmi(0)
    system = get_dmi(1)
    board = get_dmi(2)
    chassis = get_dmi(3)

    harddisks = []
    for disk in get_lshw('disk'):
        harddisks.append(dict(
            serial='<SERIAL> 14',
            model=disk.get('product'),
            revision=disk.get('version'),
        ))

    d = dict(
        bios=dict(
            vendor=bios.get('Vendor'),
            version=bios.get('Version'),
            release_date=bios.get('Release Date'),
        ),
        system=dict(
            vendor=system.get('Manufacturer'),
            product=system.get('Product Name'),
            version=system.get('Version'),
            serial='<SERIAL> 8',
            sku=system.get('SKU Number'),
            family=system.get('Family'),
            uuid='<UUID>',
        ),
        board=dict(
            board_type=board.get('dmi_type'),
            vendor=board.get('Manufacturer'),
            product=board.get('Product Name'),
            version=board.get('Version'),
            serial='<SERIAL> 10',
            asset=board.get('Asset Tag'),
            location=board.get('Location In Chassis'),
        ),
        chassis=dict(
            chassis_type=chassis.get('dmi_type'),
            vendor=chassis.get('Manufacturer'),
            version=chassis.get('Version'),
            serial='<SERIAL> 8',
            asset=chassis.get('Asset Tag'),
        ),
        harddisk=harddisks,
    )

    f = open(os.path.join('hwconf', '%s.json' % args.fname), 'wb')
    f.write(json.dumps(d, indent=4))