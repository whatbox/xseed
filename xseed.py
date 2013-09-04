#!/usr/bin/env python

#		Copyright (C) 2010 SuperSnout

#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

#		Modifies .torrent files

from optparse import OptionParser
from bencode import bencode, bdecode
import os, string, random

usage = "usage: %prog [options] filename [filename] ..."
parser = OptionParser(usage=usage)

parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="switch on verbose mode")
parser.add_option("-e", "--edit-in-place", action="store_true", dest="replace", help="overwrite files without prompting")
parser.add_option("-o", "--output", dest="outfile", help="specify output filename. (can not be used if multiple files are given)")
parser.add_option("-d", "--directory", dest="path", help="specify a directory to save output to")
parser.add_option("-a", "--announce", dest="url", help="replace announce-url with the one specified")
parser.add_option("-p", "--private", action="store_true", dest="private", help="make torrent private")
parser.add_option("-n", "--no-cross-seed", action="store_false", dest="cross", default=True, help="do not add a random string to the info dict to ensure unique info hashes")

(options, args) = parser.parse_args()

def random_string(n):
	"""Generate a random string of length n"""
	return ''.join(random.choice(string.letters + string.digits) for i in xrange(n))

def change_announce(dict, url):
	"""Change announce url."""
	dict['announce'] = url
	verbose("announce url changed to '%s'" % url)
	return dict

def make_unique(dict):
	"""Add random string to info dict."""
	dict['info']['unique'] = uniquestr = random_string(32)
	verbose("random string '%s' added to info dict" % uniquestr)
	return dict

def verbose(msg):
	if options.verbose:
		print msg

def read_bencode(stream):
	""" Decode a file to an object."""
	handle = open(stream, "rb")
	dict = bdecode(handle.read())
	if dict:
		verbose("dict read from '%s'" % stream)
	if handle:
		handle.close()
	return dict

def write_bencode(stream, obj):
	""" Encode a given object to a file."""
	handle = open(stream, "wb")
	handle.write(bencode(obj))
	verbose("modified dict written to '%s'" % stream)
	if handle:
		handle.close()

def confirm(prompt=None, resp=False):
	"""prompts for yes or no response from the user. Returns True for yes and
	False for no.

	'resp' should be set to the default value assumed by the caller when
	user simply types ENTER.

	>>> confirm(prompt='Create Directory?', resp=True)
	Create Directory? Y/n: 
	True
	>>> confirm(prompt='Create Directory?', resp=False)
	Create Directory? y/N: 
	False
	>>> confirm(prompt='Create Directory?', resp=False)
	Create Directory? y/N: y
	True

	"""
	
	if prompt is None:
		prompt = 'Confirm'

	if resp:
		prompt = '%s %s/%s: ' % (prompt, 'Y', 'n')
	else:
		prompt = '%s %s/%s: ' % (prompt, 'y', 'N')
		
	while True:
		ans = raw_input(prompt)
		if not ans:
			return resp
		if ans not in ['y', 'Y', 'n', 'N']:
			print 'please enter y or n.'
			continue
		if ans == 'y' or ans == 'Y':
			return True
		if ans == 'n' or ans == 'N':
			return False

# checks for presence of args
if not args:
	parser.error("no file(s) given")
if len(args) > 1 and options.outfile:
	parser.error("output filename specified but multiple files given")

for infile in args:
	dict = read_bencode(infile)
	if options.cross:
		dict = make_unique(dict)
	if options.url:
		dict = change_announce(dict, options.url)
	if options.private:
		dict['info']['private'] = 1
		verbose("private set to 1")
	if options.path and options.outfile:
		stream = options.path + options.outfile
		if not os.path.exists(options.path):
			os.makedirs(options.path)
	elif options.path:
		stream = options.path + infile
		if not os.path.exists(options.path):
			os.makedirs(options.path)
	elif options.outfile:
		stream = options.outfile
	else:
		stream = infile
	if options.replace:
		write_bencode(stream, dict)
	elif os.path.exists(stream) or stream == infile:
		choice = confirm("%s already exists. Overwrite?" % stream, True)
		if choice != True:
			continue
		else:
			write_bencode(stream, dict)
	else:
		write_bencode(stream, dict)
