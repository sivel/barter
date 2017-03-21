#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2017 Matt Martz
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import print_function

import argparse
import errno
import getpass
import json
import os

__version__ = '1.0.0'


CONF_MAP = {
    'ServerCertPath': 'server.pem',
    'ClientKeyPath': 'key.pem',
    'CaPrivateKeyPath': 'ca-key.pem',
    'ServerKeyPath': 'server-key.pem',
    'ClientCertPath': 'cert.pem',
    'CaCertPath': 'ca.pem',
    'SSHKeyPath': 'id_rsa',
}


def config_serializer(obj):
    try:
        items = obj.items()
    except AttributeError:
        items = enumerate(obj)

    for k, v in items:
        if isinstance(v, (list, dict)):
            obj[k] = config_serializer(v)
        else:
            try:
                if k.lower() in ['username', 'password', 'apikey'] and v:
                    obj[k] = 'omitted'
                elif os.path.isfile(v):
                    with open(v) as f:
                        obj[k] = f.read()
                elif os.path.isdir(v):
                    obj[k] = v.replace(os.path.expanduser('~'), '~')
                else:
                    raise TypeError()
            except TypeError:
                obj[k] = v

    return obj


def config_deserializer(obj, dirname, config):
    try:
        items = obj.items()
    except AttributeError:
        items = enumerate(obj)

    for k, v in items:
        if isinstance(v, (list, dict)):
            obj[k] = config_deserializer(v, dirname, config)
        else:
            try:
                if k == 'Password' and v == 'omitted':
                    obj[k] = getpass.getpass(
                        '%(DriverName)s password: ' % config
                    )
                elif k == 'APIKey' and v == 'omitted':
                    obj[k] = getpass.getpass(
                        '%(DriverName)s API key: ' % config
                    )
                elif k == 'Username' and v == 'omitted':
                    obj[k] = raw_input(
                        '%(DriverName)s username: ' % config
                    )
                elif v and 'path' in k.lower() and not v.startswith('~'):
                    base = CONF_MAP[k]
                    path = os.path.join(dirname, base)
                    with open(path, 'w+') as f:
                        f.write(v)
                    obj[k] = path
                elif v.startswith('~'):
                    obj[k] = os.path.expanduser(v)
                    pass
                else:
                    raise AttributeError()
            except AttributeError:
                obj[k] = v

    return obj


def exporter(args):
    machine = args.machine
    machine_path = os.path.expanduser(
        '~/.docker/machine/machines/%s' % machine
    )
    with open(os.path.join(machine_path, 'config.json')) as f:
        config = json.load(f)

    print(json.dumps(config_serializer(config), indent=4))


def importer(args):
    config_path = os.path.expanduser(args.config)
    with open(config_path) as f:
        config = json.load(f)

    name = config['Name']
    path = os.path.expanduser(
        '~/.docker/machine/machines/%s' % name
    )
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

    out = config_deserializer(config, path, config)
    with open(os.path.join(path, 'config.json'), 'w+') as f:
        json.dump(out, f, indent=4)


def main():
    parser = argparse.ArgumentParser(
        description='Imports and Exports machine configurations from '
                    'docker-machine'
    )
    subparsers = parser.add_subparsers()

    exp_parser = subparsers.add_parser(
        'export',
        help='Export a machine configuration'
    )
    exp_parser.add_argument('machine')
    exp_parser.set_defaults(func=exporter)

    imp_parser = subparsers.add_parser(
        'import',
        help='Import a machine configuration'
    )
    imp_parser.add_argument('config')
    imp_parser.set_defaults(func=importer)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
