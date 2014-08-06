# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
    Useful subroutines that don't fit in any place to particularly for aquilon.
"""

from __future__ import print_function

import errno
import gzip
import json
import logging
import os
import re
import signal
from cStringIO import StringIO
from tempfile import mkstemp

from ipaddr import IPv4Address, AddressValueError

from aquilon.exceptions_ import ArgumentError
from aquilon.config import Config
from aquilon.aqdb.types.mac_address import MACAddress

LOGGER = logging.getLogger(__name__)

yes_re = re.compile(r"^(true|yes|y|1|on|enabled)$", re.I)
no_re = re.compile(r"^(false|no|n|0|off|disabled)$", re.I)
_hex_re = re.compile(r'[0-9a-f]+$')

# Regexp used to check if a value is suitable to be used as an nlist key,
# without escaping.
nlist_key_re = re.compile('^[a-zA-Z_][a-zA-Z0-9_.-]*$')

# Regexp used to check if a value is suitable to be used as a template name
template_name_re = re.compile(r'^[a-zA-Z0-9_.-]+$')


def kill_from_pid_file(pid_file):  # pragma: no cover
    if os.path.isfile(pid_file):
        f = open(pid_file)
        p = f.read()
        f.close()
        pid = int(p)
        print('Killing pid %s' % pid)
        try:
            os.kill(pid, signal.SIGQUIT)
        except OSError as err:
            print('Failed to kill %s: %s' % (pid, err.strerror))


def monkeypatch(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


def validate_nlist_key(label, value):
    if not nlist_key_re.match(value):
        raise ArgumentError("'%s' is not a valid value for %s." %
                            (value, label))


def validate_template_name(label, value):
    if not template_name_re.match(value):
        raise ArgumentError("'%s' is not a valid value for %s." %
                            (value, label))


def force_ipv4(label, value):
    if value is None:
        return None
    if isinstance(value, IPv4Address):
        return value
    try:
        return IPv4Address(value)
    except AddressValueError as e:
        raise ArgumentError("Expected an IPv4 address for %s: %s" % (label, e))


def force_int(label, value):
    """Utility method to force incoming values to int and wrap errors."""
    if value is None:
        return None
    try:
        result = int(value)
    except ValueError:
        raise ArgumentError("Expected an integer for %s." % label)
    return result


def force_float(label, value):
    """Utility method to force incoming values to float and wrap errors."""
    if value is None:
        return None
    try:
        result = float(value)
    except ValueError:
        raise ArgumentError("Expected an floating point number for %s." % label)
    return result


def force_boolean(label, value):
    """Utility method to force incoming values to boolean and wrap errors."""
    if value is None:
        return None
    if yes_re.match(value):
        return True
    if no_re.match(value):
        return False
    raise ArgumentError("Expected a boolean value for %s." % label)


def force_mac(label, value):
    # Allow nullable Mac Addresses, consistent with behavior of IPV4
    if value is None:
        return None

    try:
        return MACAddress(value)
    except ValueError, err:
        raise ArgumentError("Expected a MAC address for %s: %s" % (label, err))


def force_wwn(label, value):
    # See http://standards.ieee.org/develop/regauth/tut/fibre.pdf for a more
    # detailed description for the WWN format. We do not want to be very
    # strict here, to accomodate possibly broken devices out there.
    if not value:
        return None

    # Strip separators if present
    value = str(value).strip().lower().translate(None, ':-')

    if not _hex_re.match(value):
        raise ArgumentError("The value of %s may contain hexadecimal "
                            "characters only." % label)
    if len(value) != 16 and len(value) != 32:
        raise ArgumentError("The value of %s must contain either 16 or 32 "
                            "hexadecimal digits." % label)
    return value


def force_ascii(label, value):
    if value is None:
        return None
    try:
        value = value.decode('ascii')
    except UnicodeDecodeError:
        raise ArgumentError("Only ASCII characters are allowed for %s." % label)
    return value


def force_list(label, value):
    """
    Convert a value containing embedded newlines to a list.

    The function also removes empty lines and lines starting with '#'.
    """
    if value is None:
        return None
    lines = [force_ascii(label, x.strip()) for x in value.splitlines()]
    return [x for x in lines if x and not x.startswith("#")]


def force_json_dict(label, value):
    if value is None:
        return None
    try:
        value = json.loads(value)
    except ValueError as e:
        raise ArgumentError("The json string specified for %s is invalid : %s"
                            % (label, e))
    return value


def first_of(iterable, function):
    """
    Return the first matching element of an iterable

    This function is useful if you already know there is at most one matching
    element.
    """
    for item in iterable:
        if function(item):
            return item
    return None


def remove_dir(dir, logger=LOGGER):
    """Remove a directory.  Could have been implemented as a call to rm -rf."""
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            try:
                thisfile = os.path.join(root, name)
                os.remove(thisfile)
            except OSError as e:
                logger.info("Failed to remove '%s': %s", thisfile, e)
        for name in dirs:
            try:
                thisdir = os.path.join(root, name)
                os.rmdir(thisdir)
            except OSError as e:
                # If this 'directory' is a symlink, the rmdir command
                # will fail.  Try to remove it as a file.  If this
                # fails, report the original error.
                try:
                    os.remove(thisdir)
                except OSError:
                    logger.info("Failed to remove '%s': %s", thisdir, e)
    try:
        os.rmdir(dir)
    except OSError as e:
        logger.info("Failed to remove '%s': %s", dir, e)
    return


def write_file(filename, content, mode=None, compress=None,
               create_directory=False, logger=LOGGER):
    """Atomically write content into the specified filename.

    The content is written into a temp file in the same directory as
    filename, and then swapped into place with rename.  This assumes
    that both the file and the directory can be written to by the
    broker.  The same directory was used instead of a temporary
    directory because atomic swaps are generally only available when
    the source and the target are on the same filesystem.

    If mode is set, change permissions on the file (newly created or
    pre-existing) to the new mode.  If unset and the file exists, the
    current permissions will be kept.  If unset and the file is new,
    the default is 0644.

    This method may raise OSError if any of the OS-related methods
    (creating the temp file, writing to it, correcting permissions,
    swapping into place) fail.  The method will attempt to remove
    the temp file if it had been created.

    If the compress keyword is passed, the content is compressed in
    memory before writing.  The only compression currently supported
    is gzip.

    """
    if compress == 'gzip':
        config = Config()
        buffer = StringIO()
        compress = config.getint('broker', 'gzip_level')
        zipper = gzip.GzipFile(filename, 'wb', compress, buffer)
        zipper.write(content)
        zipper.close()
        content = buffer.getvalue()
    if mode is None:
        try:
            old_mode = os.stat(filename).st_mode
        except OSError:
            old_mode = 0o644
    dirname, basename = os.path.split(filename)

    if not os.path.exists(dirname) and create_directory:
        os.makedirs(dirname)

    fd, fpath = mkstemp(prefix=basename, dir=dirname)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        if mode is None:
            os.chmod(fpath, old_mode)
        else:
            os.chmod(fpath, mode)
        os.rename(fpath, filename)
    finally:
        if os.path.exists(fpath):
            os.remove(fpath)


def remove_file(filename, cleanup_directory=False, logger=LOGGER):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            logger.info("Could not remove file '%s': %s", filename, e)
    if cleanup_directory:
        try:
            os.removedirs(os.path.dirname(filename))
        except OSError:
            pass
