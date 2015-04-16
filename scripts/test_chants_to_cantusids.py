#!/usr/bin/env python3

# Test the "chants_to_cantusids.py" script


from os import path
import subprocess
from xml.etree import ElementTree as ETree


# required files
TEST_SCRIPT = 'chants_to_cantusids.py'
TEST_INPUT = 'test_list_of_chants.xml'
TEST_EXPECTED = 'expected_cantusids.xml'

# expected output file
TEST_ACTUAL = 'list_of_cantusids.xml'


# ensure our files exist
if not (path.exists(TEST_SCRIPT) and path.exists(TEST_INPUT) and path.exists(TEST_EXPECTED)):
    print('Unable to find files required for test!')
    raise SystemExit(1)

# run the test!
print('Testing...')
try:
    return_value = subprocess.call(['python3', TEST_SCRIPT, TEST_INPUT], timeout=30)

# ensure the script worked
except subprocess.TimeoutExpired:
    print('Failure: script took more than 30 seconds.')
    raise SystemExit(1)

if 0 != return_value:
    print('Failure: script returned non-zero.')
    raise SystemExit(1)

if not path.exists(TEST_ACTUAL):
    print('Failure: script did not output to expected path ("{}")'.format(TEST_ACTUAL))
    raise SystemExit(1)

# ensure the script's output is correct
expected = ETree.parse(TEST_EXPECTED).getroot()
actual = ETree.parse(TEST_ACTUAL).getroot()
expected = ETree.tostring(expected, encoding='unicode')
actual = ETree.tostring(actual, encoding='unicode')

if actual != expected:
    print('Output is incorrect.\n\nExpected:\n{}\n\nActual:\n{}'.format(expected, actual))
    raise SystemExit(1)

print('Test passed!')
