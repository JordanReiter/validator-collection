# -*- coding: utf-8 -*-

"""
***********************************
tests.test_checkers
***********************************

Tests for :term:`checkers <checker>`.

"""

import decimal
import fractions
import io
import os
import time as time_
import uuid
from datetime import datetime, date, time, tzinfo, timedelta

import pytest

import validator_collection.checkers as checkers

from validator_collection._compat import TimeZone


## CORE

@pytest.mark.parametrize('value, expects', [
    (['test', 123], True),
    ([], True),
    (None, False),
    (None, False),
    ('not-a-list', False),
    (set([1, 2, 3]), True),
    ((1, 2, 3), True),
    (set(), True),
    (tuple(), True),
    (123, False),

    (['test', 123], True),
    ([datetime], True),
    (datetime, False),

    (str, False),
    ([str], True)

])
def test_is_iterable(value, expects):
    result = checkers.is_iterable(value)
    assert result == expects


@pytest.mark.parametrize('args, expects', [
    ([{'key': 'value'}, {'key': 'value'}], True),
    ([{'key': ['list']}, {'key': ['list']}], True),
    ([{'key': {'key': 'value'}}, {'key': {'key': 'value'}}], True),

    ([{'key': 'value'}, {'key': 'value2'}], False),
    ([{'key': ['list']}, {'key': ['else']}], False),
    ([{'key': {'key': 'value'}}, {'key': {'else': 'value'}}], False),
    ([{'key': {'key': 'value'}}, {'else': {'key': 'value'}}], False),

    ([{'key': 'value'}, 123], False)
])
def test_are_dicts_equivalent(args, expects):
    result = checkers.are_dicts_equivalent(*args)
    assert result == expects


@pytest.mark.parametrize('args, expects', [
    (['test', 'test'], True),
    ([['test','test'], ['test','test']], True),
    (['test',123], False),
    (['not-a-list',123], False),
    ([123], True),

    ([{'key': 'value'}, {'key': 'value'}], True),
    ([{'key': ['list']}, {'key': ['list']}], True),
    ([{'key': {'key': 'value'}}, {'key': {'key': 'value'}}], True),

    ([{'key': 'value'}, {'key': 'value2'}], False),
    ([{'key': ['list']}, {'key': ['else']}], False),
    ([{'key': {'key': 'value'}}, {'key': {'else': 'value'}}], False),
    ([{'key': {'key': 'value'}}, {'else': {'key': 'value'}}], False),

    ([{'key': 'value'}, 123], False)
])
def test_are_equivalent(args, expects):
    result = checkers.are_equivalent(*args)
    assert result == expects


@pytest.mark.parametrize('value, check_type, expects', [
    ('test-string', str, True),
    ('test-string', (str, int), True),
    ('test-string', int, False),
    ('test-string', 'str', True),
    ('test-string', ('str', int), True),
    (123, int, True),
    (TimeZone(timedelta(hours = 1)), [int, tzinfo], True),
    (TimeZone(timedelta(hours = 1)), tzinfo, True),
    (TimeZone(timedelta(hours = 1)), str, False)
])
def test_is_type(value, check_type, expects):
    """Test the validators.is_type() function."""
    result = checkers.is_type(value, type_ = check_type)
    assert result is expects


@pytest.mark.parametrize('value, expects', [
    ({ 'key': 'value' }, True),
    ('{"key": "json"}', True),
    (['key', 'value'], False),
    ('[{"key": "json"}]', False),
    ({}, True),
    ({}, True),
    ('not-a-dict', False),
    ('', False),
    (None, False),
])
def test_is_dict(value, expects):
    result = checkers.is_dict(value)
    assert result == expects


@pytest.mark.parametrize('value, expects, minimum_length, maximum_length, whitespace_padding', [
    ('test', True, None, None, False),
    ('', True, None, None, False),
    (None, False, None, None, False),

    ('test', True, 4, None, False),
    ('test', True, 1, None, False),
    ('test', False, 50, None, False),
    ('test', True, 50, None, True),

    ('test', True, None, 5, False),
    ('test', True, None, 4, False),
    ('test', False, None, 3, False),

])
def test_is_string(value, expects, minimum_length, maximum_length, whitespace_padding):
    result = checkers.is_string(value,
                                minimum_length = minimum_length,
                                maximum_length = maximum_length,
                                whitespace_padding = whitespace_padding)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty, minimum_length, maximum_length', [
    (['test', 123], False, False, None, None),
    ([], False, True, None, None),
    (None, True, False, None, None),
    ('not-a-list', True, False, None, None),
    (set([1, 2, 3]), False, False, None, None),
    ((1, 2, 3), False, False, None, None),
    (set(), False, True, None, None),
    ((), False, True, None, None),
    (123, True, False, None, None),

    (['test', 123], False, False, 1, None),
    (['test', 123], False, False, 2, None),
    (['test', 123], False, False, None, 3),
    (['test', 123], False, False, None, 2),
    (['test', 123], True, False, 3, None),
    (['test', 123], True, False, None, 1),

])
def test_is_iterable(value, fails, allow_empty, minimum_length, maximum_length):
    expects = not fails
    result = checkers.is_iterable(value,
                                  minimum_length = minimum_length,
                                  maximum_length = maximum_length)
    assert result == expects


@pytest.mark.parametrize('value, fails, minimum, maximum, expects', [
    (5, False, None, 10, True),
    (5, False, 1, None, True),
    (5, False, 1, 10, True),
    (5, False, 10, None, False),
    (5, False, None, 3, False),
    (5, True, None, None, ValueError)
])
def test_is_between(value, fails, minimum, maximum, expects):
    if not fails:
        result = checkers.is_between(value,
                                     minimum = minimum,
                                     maximum = maximum)
        assert result == expects
    else:
        with pytest.raises(expects):
            result = checkers.is_between(value,
                                         minimum = minimum,
                                         maximum = maximum)


@pytest.mark.parametrize('value, fails, minimum, maximum, expects', [
    ('test', False, None, 10, True),
    ('test', False, 1, None, True),
    ('test', False, 1, 10, True),
    ('test', False, 10, None, False),
    ('test', False, None, 3, False),
    ('test', True, None, None, ValueError),
    (None, True, None, 5, TypeError)
])
def test_has_length(value, fails, minimum, maximum, expects):
    if not fails:
        result = checkers.has_length(value,
                                     minimum = minimum,
                                     maximum = maximum)
        assert result == expects
    else:
        with pytest.raises(expects):
            result = checkers.has_length(value,
                                         minimum = minimum,
                                         maximum = maximum)


@pytest.mark.parametrize('value, fails, allow_empty', [
    (['test', 123], False, False),
    ([], True, False),
    (None, True, False),
    ('', True, False),
    ('not-a-list', False, False),
    (set([1, 2, 3]), False, False),
    ((1, 2, 3), False, False),
    (set(), True, False),
    ((), True, False),
    (123, False, False)
])
def test_is_not_empty(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_not_empty(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty, coerce_value', [
    (['test', 123], True, False, True),
    ([], True, False, False),
    (None, False, False, False),
    ('', True, False, False),
])
def test_is_none(value, fails, allow_empty, coerce_value):
    expects = not fails
    result = checkers.is_none(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('my_variable', False, False),
    ('_my_variable', False, False),
    ('', True, False),
    ('my variable', True, False),
    ('123_variable', True, False),
    ('', True, False),
    ('my variable', True, False),
    ('123_variable', True, False),
    (None, True, False),
    ('', True, False),
    ('my variable', True, False),
    ('123_variable', True, False),
    (None, True, False)
])
def test_is_variable_name(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_variable_name(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    (uuid.uuid4(), False, False),
    ('123e4567-e89b-12d3-a456-426655440000', False, False),
    ('not-a-uuid', True, False),
    ('', True, False),
    (None, True, False),
])
def test_is_uuid(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_uuid(value)
    assert result == expects


## DATE/TIME

@pytest.mark.parametrize('value, fails, allow_empty, minimum, maximum', [
    ('2018-01-01', False, False, None, None),
    ('2018/01/01', False, False, None, None),
    ('01/01/2018', True, False, None, None),
    (date(2018,1,1), False, False, None, None),
    (datetime.utcnow(), False, False, None, None),
    ('1/1/2018', True, False, None, None),
    ('1/1/18', True, False, None, None),
    (None, True, False, None, None),
    ('', True, False, None, None),
    ('1/46/2018', True, False, None, None),
    ('not-a-date', True, False, None, None),
    ('2018-01-01 00:00:00.00000', False, False, None, None),
    ('01/01/2018 00:00:00.00000', True, False, None, None),
    ('2018-01-46', True, False, None, None),
    ('1/46/2018', True, False, None, None),
    ('not-a-date', True, False, None, None),

    ('2018-01-01', False, False, '2017-12-01', None),
    ('2018/01/01', False, False, '2018-01-01', None),
    ('2018-01-01', True, False, '2018-02-01', None),

    ('2018/01/01', False, False, None, '2018-01-31'),
    ('2018/01/01', False, False, None, '2018-01-01'),
    ('2018/01/01', True, False, None, '2017-12-31'),

    (time_.time(), False, False, None, None),
    (datetime.utcnow().time(), True, False, None, None)
])
def test_is_date(value, fails, allow_empty, minimum, maximum):
    expects = not fails
    result = checkers.is_date(value,
                              minimum = minimum,
                              maximum = maximum)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty, minimum, maximum', [
    ('2018-01-01', False, False, None, None),
    ('2018/01/01', False, False, None, None),
    ('01/01/2018', True, False, None, None),
    (date(2018,1,1), False, False, None, None),
    (datetime.utcnow(), False, False, None, None),
    ('1/1/2018', True, False, None, None),
    ('1/1/18', True, False, None, None),
    (None, True, False, None, None),
    ('', True, False, None, None),
    ('1/46/2018', True, False, None, None),
    ('not-a-date', True, False, None, None),
    ('2018-01-01T00:00:00.00000', False, False, None, None),
    ('2018-01-01 00:00:00.00000', False, False, None, None),
    ('01/01/2018 00:00:00.00000', True, False, None, None),
    ('2018-01-46', True, False, None, None),
    ('1/46/2018', True, False, None, None),
    ('not-a-date', True, False, None, None),
    ('2018-01-01T00:00:00', False, False, None, None),

    ('2018-01-01', False, False, '2010-01-01', None),
    ('2018/01/01', False, False, '2018-01-01', None),
    ('2018/01/01', True, False, '2018-02-01', None),

    ('2018-01-01', False, False, None, '2018-02-01'),
    ('2018/01/01', False, False, None, '2018-01-01'),
    ('2018/01/01', True, False, None, '2010-01-01'),

    (time_.time(), False, False, None, None),
    (datetime.utcnow().time(), True, False, None, None),

])
def test_is_datetime(value, fails, allow_empty, minimum, maximum):
    expects = not fails
    result = checkers.is_datetime(value,
                                  minimum = minimum,
                                  maximum = maximum)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty, minimum, maximum', [
    ('2018-01-01', False, False, None, None),
    ('2018/01/01', False, False, None, None),
    ('01/01/2018', True, False, None, None),
    (date(2018,1,1), True, False, None, None),
    (datetime.utcnow(), False, False, None, None),
    ('1/1/2018', True, False, None, None),
    ('1/1/18', True, False, None, None),
    (None, True, False, None, None),
    ('', True, False, None, None),
    ('1/46/2018', True, False, None, None),
    ('not-a-date', True, False, None, None),
    ('2018-01-01T00:00:00.00000', False, False, None, None),
    ('2018-01-01 00:00:00.00000', False, False, None, None),
    ('01/01/2018 00:00:00.00000', True, False, None, None),
    ('2018-01-46', True, False, None, None),
    ('1/46/2018', True, False, None, None),
    ('not-a-date', True, False, None, None),
    ('2018-01-01T00:00:00', False, False, None, None),

    ('2018-01-01', False, False, datetime(year = 2017,
                                          month = 1,
                                          day = 1).time(), None),
    ('2018/01/01', False, False, datetime(year = 2018,
                                          month = 1,
                                          day = 1).time(), None),
    ('2018/01/01', True, False, datetime(year = 2018,
                                         month = 2,
                                         day = 1,
                                         hour = 3).time(), None),

    ('2018-01-01', False, False, None, datetime(year = 2019,
                                                month = 1,
                                                day = 1).time()),
    ('2018/01/01', False, False, None, datetime(year = 2018,
                                                month = 1,
                                                day = 1).time()),
    ('2018/01/01T03:00:00', True, False, None, datetime(year = 2017,
                                                        month = 1,
                                                        day = 1,
                                                        hour = 0).time()),

    (time_.time(), False, False, None, None),
    (datetime.utcnow().time(), False, False, None, None),

])
def test_is_time(value, fails, allow_empty, minimum, maximum):
    expects = not fails
    result = checkers.is_time(value,
                              minimum = minimum,
                              maximum = maximum)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('2018-01-01', False, False),
    ('2018/01/01', False, False),
    ('01/01/2018', True, False),
    (date(2018,1,1), False, False),
    (datetime.utcnow(), False, False),
    ('1/1/2018', True, False),
    ('1/1/18', True, False),
    (None, True, False),
    ('', True, False),
    ('1/46/2018', True, False),
    ('not-a-date', True, False),
    ('2018-01-01T00:00:00.00000', False, False),
    ('2018-01-01 00:00:00.00000', False, False),
    ('01/01/2018 00:00:00.00000', True, False),
    ('2018-01-46', True, False),
    ('1/46/2018', True, False),
    ('not-a-date', True, False),
    ('2018-01-01T00:00:00', False, False),
    ('2018-01-01 00:00:00', False, False),

    (time_.time(), False, False),
    (datetime.utcnow().time(), False, False),

    ('2018-01-01T00:00:00.00000+05:00', False, False),
    ('2018-01-01T00:00:00.00000-05:00', False, False),
    ('2018-01-01T00:00:00.00000-48:00', False, False),
    ('01/01/2018T00:00:00.00000-48:00', True, False),
    ('2018-01-01T00:00:00+01:00', False, False),
    ('2018-01-01T00:00:00+00:00', False, False),
    ('2018-01-01T00:00:00-01:00', False, False),
    ('01/01/2018T00:00:00.00000-48:00', True, False),
    ('2018-01-01T00:00:00+48:00', False, False),

    ('+06:00', False, False),
    ('-06:00', False, False),
    ('+12:00', False, False),
    ('+1:00', False, False),
    ('+48:00', True, False),

])
def test_is_timezone(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_timezone(value)
    assert result == expects


## NUMBERS

@pytest.mark.parametrize('value, fails, allow_empty, minimum, maximum', [
    (1, False, False, None, None),
    (1.5, False, False, None, None),
    (0, False, False, None, None),
    (None, True, False, None, None),
    (decimal.Decimal(1.5), False, False, None, None),
    (fractions.Fraction(1.5), False, False, None, None),

    (1, False, False, -5, None),
    (1, False, False, 1, None),
    (1, True, False, 5, None),

    (5, False, False, None, 10),
    (5, False, False, None, 5),
    (5, True, False, None, 1),

])
def test_is_numeric(value, fails, allow_empty, minimum, maximum):
    expects = not fails
    result = checkers.is_numeric(value,
                                 minimum = minimum,
                                 maximum = maximum)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty, coerce_value, minimum, maximum, expects', [
    (1, False, False, False, None, None, 1),
    (1.5, True, False, False, None, None, 2),
    (1.5, False, False, True, None, None, 2),
    (0, False, False, False, None, None, 0),
    (None, True, False, False, None, None, None),
    (decimal.Decimal(1.5), True, False, False, None, None, 2),
    (decimal.Decimal(1.5), False, False, True, None, None, 2),
    (fractions.Fraction(1.5), True, False, False, None, None, 2),
    (fractions.Fraction(1.5), False, False, True, None, None, 2),

    (1, False, False, False, -5, None, 1),
    (1, False, False, False, 1, None, 1),
    (1, True, False, False, 5, None, None),

    (5, False, False, None, False, 10, 5),
    (5, False, False, None, False, 5, 5),
    (5, True, False, None, False, 1, None),

])
def test_is_integer(value, fails, allow_empty, coerce_value, minimum, maximum, expects):
    expects = not fails
    result = checkers.is_integer(value,
                                 coerce_value = coerce_value,
                                 minimum = minimum,
                                 maximum = maximum)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty, minimum, maximum', [
    (1, False, False, None, None),
    (1.5, False, False, None, None),
    (0, False, False, None, None),
    (None, True, False, None, None),
    (decimal.Decimal(1.5), False, False, None, None),
    (fractions.Fraction(1.5), False, False, None, None),

    (1, False, False, -5, None),
    (1, False, False, 1, None),
    (1, True, False, 5, None),

    (5, False, False, None, 10),
    (5, False, False, None, 5),
    (5, True, False, None, 1),

])
def test_is_float(value, fails, allow_empty, minimum, maximum):
    expects = not fails
    result = checkers.is_float(value,
                               minimum = minimum,
                               maximum = maximum)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty, minimum, maximum', [
    (1, False, False, None, None),
    (1.5, False, False, None, None),
    (0, False, False, None, None),
    (None, True, False, None, None),
    (decimal.Decimal(1.5), False, False, None, None),
    (fractions.Fraction(1.5), False, False, None, None),

    (1, False, False, -5, None),
    (1, False, False, 1, None),
    (1, True, False, 5, None),

    (5, False, False, None, 10),
    (5, False, False, None, 5),
    (5, True, False, None, 1),

])
def test_is_fraction(value, fails, allow_empty, minimum, maximum):
    expects = not fails
    result = checkers.is_fraction(value,
                                  minimum = minimum,
                                  maximum = maximum)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty, minimum, maximum', [
    (1, False, False, None, None),
    (1.5, False, False, None, None),
    (0, False, False, None, None),
    (None, True, False, None, None),
    (decimal.Decimal(1.5), False, False, None, None),
    (fractions.Fraction(1.5), False, False, None, None),

    (1, False, False, -5, None),
    (1, False, False, 1, None),
    (1, True, False, 5, None),

    (5, False, False, None, 10),
    (5, False, False, None, 5),
    (5, True, False, None, 1),

])
def test_is_decimal(value, fails, allow_empty, minimum, maximum):
    expects = not fails
    result = checkers.is_decimal(value,
                                 minimum = minimum,
                                 maximum = maximum)
    assert result == expects


## FILE-RELATED

@pytest.mark.parametrize('value, fails, allow_empty', [
    (io.BytesIO(), False, False),
    ("", True, False),
    (None, True, False),
])
def test_is_bytesIO(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_bytesIO(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    (io.StringIO(), False, False),
    ("", True, False),
    (None, True, False),
])
def test_is_stringIO(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_stringIO(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('/test', False, False),
    ('.', False, False),
    ('./', False, False),
    (os.path.abspath('.'), False, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),
])
def test_is_pathlike(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_pathlike(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('/test', True, False),
    ('.', False, False),
    ('./', False, False),
    (os.path.abspath('.'), False, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),
])
def test_is_on_filesystem(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_on_filesystem(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('/test', True, False),
    (os.path.abspath(__file__), False, False),
    (os.path.abspath('.'), True, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),
])
def test_is_file(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_file(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('/test', True, False),
    (os.path.abspath(__file__), True, False),
    (os.path.abspath('.'), False, False),
    (os.path.dirname(os.path.abspath('.')), False, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),
])
def test_is_directory(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_directory(value)
    assert result == expects


## INTERNET-RELATED

@pytest.mark.parametrize('value, fails, allow_empty', [
    ('test@domain.dev', False, False),
    ('@domain.dev', True, False),
    ('domain.dev', True, False),
    ('not-an-email', True, False),
    ('', True, False),
    (None, True, False),
])
def test_is_email(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_email(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ("http://foo.com/blah_blah", False, False),
    ("http://foo.com/blah_blah/", False, False),
    ("http://foo.com/blah_blah_(wikipedia)", False, False),
    ("http://foo.com/blah_blah_(wikipedia)_(again)", False, False),
    ("http://www.example.com/wpstyle/?p=364", False, False),
    ("https://www.example.com/foo/?bar=baz&inga=42&quux", False, False),
    ("http://✪df.ws/123", False, False),
    ("http://userid:password@example.com:8080", False, False),
    ("http://userid:password@example.com:8080/", False, False),
    ("http://userid@example.com", False, False),
    ("http://userid@example.com/", False, False),
    ("http://userid@example.com:8080", False, False),
    ("http://userid@example.com:8080/", False, False),
    ("http://userid:password@example.com", False, False),
    ("http://userid:password@example.com/", False, False),
    ("http://142.42.1.1/", False, False),
    ("http://142.42.1.1:8080/", False, False),
    ("http://➡.ws/䨹", False, False),
    ("http://⌘.ws", False, False),
    ("http://⌘.ws/", False, False),
    ("http://foo.com/blah_(wikipedia)#cite-1", False, False),
    ("http://foo.com/blah_(wikipedia)_blah#cite-1", False, False),
    ("http://foo.com/unicode_(✪)_in_parens", False, False),
    ("http://foo.com/(something)?after=parens", False, False),
    ("http://☺.damowmow.com/", False, False),
    ("http://code.google.com/events/#&product=browser", False, False),
    ("http://j.mp", False, False),
    ("ftp://foo.bar/baz", False, False),
    ("http://foo.bar/?q=Test%20URL-encoded%20stuff", False, False),
    ("http://مثال.إختبار", False, False),
    ("http://例子.测试", False, False),
    ("http://उदाहरण.परीक्षा", False, False),
    ("http://-.~_!$&'()*+,;=:%40:80%2f::::::@example.com", False, False),
    ("http://1337.net", False, False),
    ("http://a.b-c.de", False, False),
    ("http://a.b--c.de/", False, False),
    ("http://223.255.255.254", False, False),
    ("", True, False),
    (None, True, False),
    ("http://", True, False),
    ("http://.", True, False),
    ("http://..", True, False),
    ("http://../", True, False),
    ("http://?", True, False),
    ("http://??", True, False),
    ("http://??/", True, False),
    ("http://#", True, False),
    ("http://##", True, False),
    ("http://##/", True, False),
    ("http://foo.bar?q=Spaces should be encoded", True, False),
    ("//", True, False),
    ("//a", True, False),
    ("///a", True, False),
    ("///", True, False),
    ("http:///a", True, False),
    ("foo.com", True, False),
    ("rdar://1234", True, False),
    ("h://test", True, False),
    ("http:// shouldfail.com", True, False),
    (":// should fail", True, False),
    ("http://foo.bar/foo(bar)baz quux", True, False),
    ("ftps://foo.bar/", True, False),
    ("http://-error-.invalid/", True, False),
    ("http://-a.b.co", True, False),
    ("http://a.b-.co", True, False),
    ("http://0.0.0.0", True, False),
    ("http://10.1.1.0", True, False),
    ("http://10.1.1.255", True, False),
    ("http://224.1.1.1", True, False),
    ("http://1.1.1.1.1", True, False),
    ("http://123.123.123", True, False),
    ("http://3628126748", True, False),
    ("http://.www.foo.bar/", True, False),
    ("http://www.foo.bar./", True, False),
    ("http://.www.foo.bar./", True, False),
    ("http://10.1.1.1", True, False),
])
def test_is_url(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_url(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('0.0.0.0', False, False),
    ('10.10.10.10', False, False),
    ('192.168.1.1', False, False),
    ('255.255.255.255', False, False),
    ('0.0.0', True, False),
    ('0', True, False),
    ('abc0.0.0.0', True, False),
    ('a.b.c.d', True, False),
    ('275.276.278.279', True, False),
    ('not-a-valid-value', True, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),

    ('::1', False, False),
    ('abcd:ffff:0:0:0:0:41:2', False, False),
    ('abcd:abcd::1:2', False, False),
    ('0:0:0:0:0:ffff:1.2.3.4', False, False),
    ('0:0:0:0:ffff:1.2.3.4', True, False),
    ('::0.0.0.0', False, False),
    ('::10.10.10.10', False, False),
    ('::192.168.1.1', False, False),
    ('::255.255.255.255', False, False),
    ('abcd.0.0.0', True, False),
    ('abcd:123::123:1', False, False),
    ('1:2:3:4:5:6:7:8:9', True, False),
    ('abcd:1abcd', True, False),
    ('::0.0.0', True, False),
    ('abc0.0.0.0', True, False),
    ('a.b.c.d', True, False),
    ('::275.276.278.279', True, False),
    ('not-a-valid-value', True, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),
])
def test_is_ip_address(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_ip_address(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('0.0.0.0', False, False),
    ('10.10.10.10', False, False),
    ('192.168.1.1', False, False),
    ('255.255.255.255', False, False),
    ('0.0.0', True, False),
    ('0', True, False),
    ('abc0.0.0.0', True, False),
    ('a.b.c.d', True, False),
    ('275.276.278.279', True, False),
    ('not-a-valid-value', True, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),
])
def test_is_ipv4(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_ipv4(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('::1', False, False),
    ('abcd:ffff:0:0:0:0:41:2', False, False),
    ('abcd:abcd::1:2', False, False),
    ('0:0:0:0:0:ffff:1.2.3.4', False, False),
    ('0:0:0:0:ffff:1.2.3.4', True, False),
    ('::0.0.0.0', False, False),
    ('::10.10.10.10', False, False),
    ('::192.168.1.1', False, False),
    ('::255.255.255.255', False, False),
    ('abcd.0.0.0', True, False),
    ('abcd:123::123:1', False, False),
    ('1:2:3:4:5:6:7:8:9', True, False),
    ('abcd:1abcd', True, False),
    ('::0.0.0', True, False),
    ('abc0.0.0.0', True, False),
    ('a.b.c.d', True, False),
    ('::275.276.278.279', True, False),
    ('not-a-valid-value', True, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),
])
def test_is_ipv6(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_ipv6(value)
    assert result == expects


@pytest.mark.parametrize('value, fails, allow_empty', [
    ('01:23:45:67:ab:CD', False, False),
    ('C0:8E:80:0E:30:54', False, False),
    ('36:5d:44:50:36:ae', False, False),
    ('6c:ee:1b:41:d9:ea', False, False),
    ('6c:ee:1b:41:d9:ea', False, False),
    ('01-23-45-67-ab-CD', False, False),
    ('C0-8E-80-0E-30-54', False, False),
    ('36-5d-44-50-36-ae', False, False),
    ('6c-ee-1b-41-d9-ea', False, False),
    ('6c-ee-1b-41-d9-ea', False, False),
    ('0.0.0', True, False),
    ('0', True, False),
    ('abc0.0.0.0', True, False),
    ('a.b.c.d', True, False),
    ('275.276.278.279', True, False),
    ('not-a-valid-value', True, False),
    (123, True, False),
    ("", True, False),
    (None, True, False),
])
def test_is_mac_address(value, fails, allow_empty):
    expects = not fails
    result = checkers.is_mac_address(value)
    assert result == expects