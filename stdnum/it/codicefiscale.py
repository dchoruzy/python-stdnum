# codicefiscale.py - library for Italian fiscal code
#
# This file is based on code from pycodicefiscale, a Python library for
# working with Italian fiscal code numbers officially known as Italy's
# Codice Fiscale.
# https://github.com/baxeico/pycodicefiscale
#
# Copyright (C) 2009-2013 Emanuele Rocca
# Copyright (C) 2014 Augusto Destrero
# Copyright (C) 2014 Arthur de Jong
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

"""Codice Fiscale (Italian tax code for individuals).

The Codice Fiscale is an alphanumeric code of 16 characters used to
identify individuals residing in Italy. The number consists of three
characters derived from the person's last name, three from the person's
first name, five that hold information on the person's gender and birth
date, four that represent the person's place of birth and one check digit.

>>> validate('RCCMNL83S18D969H')
'RCCMNL83S18D969H'
>>> validate('RCCMNL83S18D969')
Traceback (most recent call last):
    ...
InvalidLength: ...
>>> calc_check_digit('RCCMNL83S18D969')
'H'
"""

import re
import datetime

from stdnum.exceptions import *
from stdnum.util import clean


# regular expression for matching fiscal codes
_code_re = re.compile(
    '^[A-Z]{6}'
    '[0-9LMNPQRSTUV]{2}[ABCDEHLMPRST]{1}[0-9LMNPQRSTUV]{2}'
    '[A-Z]{1}[0-9LMNPQRSTUV]{3}[A-Z]{1}$')

# encoding of birth day and year values (usually numeric but some letters
# may be substituted on clashes)
_date_digits = dict((x, n) for n, x in enumerate('0123456789'))
_date_digits.update(dict((x, n) for n, x in enumerate('LMNPQRSTUV')))

# encoding of month values (A = January, etc.)
_month_digits = dict((x, n) for n, x in enumerate('ABCDEHLMPRST'))

# values of characters in even positions for checksum calculation
_even_values = dict((x, n) for n, x in enumerate('0123456789'))
_even_values.update(
    dict((x, n) for n, x in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')))

# values of characters in odd positions for checksum calculation
values = [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8,
          12, 14, 16, 10, 22, 25, 24, 23]
_odd_values = dict((x, values[n]) for n, x in enumerate('0123456789'))
_odd_values.update(
    dict((x, values[n]) for n, x in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')))
del values


def compact(number):
    """Convert the number to the minimal representation. This strips the
    number of any valid separators and removes surrounding whitespace."""
    return clean(number, ' ').strip().upper()


def calc_check_digit(number):
    """Compute the control code for the given number. The passed number
    should be the first 15 characters of a fiscal code."""
    code = sum(_odd_values[x] if n % 2 == 0 else _even_values[x]
               for n, x in enumerate(number))
    return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[code % 26]


def get_birth_date(number, minyear=1920):
    """Get the birth date from the person's fiscal code.

    Only the last two digits of the year are stured in the number. The
    dates will be returned in the range from minyear to minyear + 100.

    >>> get_birth_date('RCCMNL83S18D969H')
    datetime.date(1983, 11, 18)
    >>> get_birth_date('RCCMNL83S18D969H', minyear=1990)
    datetime.date(2083, 11, 18)
    """
    number = compact(number)
    day = (_date_digits[number[9]] * 10 + _date_digits[number[10]]) % 40
    month = _month_digits[number[8]] + 1
    year = _date_digits[number[6]] * 10 + _date_digits[number[7]]
    # find four-digit year
    year += (minyear // 100) * 100
    if year < minyear:
        year += 100
    try:
        return datetime.date(year, month, day)
    except ValueError:
        raise InvalidComponent()


def get_gender(number):
    """Get the gender of the person's fiscal code.

    >>> get_gender('RCCMNL83S18D969H')
    'M'
    >>> get_gender('CNTCHR83T41D969D')
    'F'
    """
    number = compact(number)
    return 'M' if int(number[9:11]) < 32 else 'F'


def validate(number):
    """Checks to see if the given fiscal code is valid. This checks the
    length and whether the check digit is correct."""
    number = compact(number)
    if len(number) != 16:
        raise InvalidLength()
    if not _code_re.match(number):
        raise InvalidFormat()
    if calc_check_digit(number[:-1]) != number[-1]:
        raise InvalidChecksum()
    # check if birth date is valid
    birth_date = get_birth_date(number)
    return number


def is_valid(number):
    """Checks to see if the given fiscal code is valid. This checks the
    length and whether the check digit is correct."""
    try:
        return bool(validate(number))
    except ValidationError:
        return False
