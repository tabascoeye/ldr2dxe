#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# LDR to DXE "deflate"
#
# This tool tries to parse the content of a Blackfin loader format file
# to the original "elf" (also called DXE for blackfin) file.

# DXE header format:
# 4 * 4 Bytes (4 processor words, 32 bit, little endian)
# first word: "Block code" contains the identifier, checksum and flags
# 	[0]:  HDRsign is always 10101101 ==> 0xAD 
#	[1]:  HDRchk is header checksum
#	[2]:  Flag field: FINAL | FIRST | INDIRECT | IGNORE | INIT | CALLBACK | QUICKBOOT | FILL
#	[3]:  UNUSED | UNUSED | SAVE | AUX | DMA CODE
#
# second word: Target address
# third word:  Byte count
# fourth word: Argument

import ctypes
import sys
import struct

c_uint8 = ctypes.c_uint8

class Flags_bits(ctypes.BigEndianStructure): #using big endian here because I'm lazy
    _fields_ = [
            ("final", c_uint8, 1),
            ("first", c_uint8, 1),
            ("indirect", c_uint8, 1),
            ("ignore", c_uint8, 1),
            ("init", c_uint8, 1),
            ("callback", c_uint8, 1),
            ("quickboot", c_uint8, 1),
            ("fill", c_uint8, 1),
        ]

class Flags(ctypes.Union):
    _fields_ = [("b", Flags_bits),
            ("asbyte", c_uint8)]

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print "Usage: ", sys.argv[0], " <input ldr file> <output elf file>"
		exit(1)
	infilename = sys.argv[1]
	outfilename = sys.argv[2]
	infile = open(infilename, "rb") # TODO: try/catch for file open
	# read the first 4 Bytes of the in file in reverse order
	# because LDR is little endian
	header = infile.read(4)[::-1]
	# check if the header has the LDR identifier
	if header[0] != "\xAD":
		print "The infile doesn't look like an LDR file, the Header identifier is not 0xAD"
		exit(1)
	# check the first header flags. Should be "first" AND ("ignore" OR "Final")
	flags = Flags()
	flags.asbyte = ord(header[2])
	if flags.b.first != 1:
		print "The infile doesn't look like an LDR file, the flags in the first Header don't contain the 'first' bit"
		exit(1)
	# check if the Target address of the first block is the default start address (0xFFA00000)
	target = infile.read(4)[::-1] #read it like big endian
	if(target != '\xFF\xA0\x00\x00'):
		print "The infile doesn't look like an LDR file, the target address of the first block is not 0xFFA00000"
		exit(1)
	# check if the byte count of the first block is 0 (should be)
	bytecount = struct.unpack('i', infile.read(4))[0] 
	if(bytecount != 0):
		print "The infile doesn't look like an LDR file, the bytecount of the first block is not 0"
		exit(1)
	# last header part of the first block is the start offset of the next DXE
	nextDXE = struct.unpack('i', infile.read(4))[0]
	print '[working] The infile looks like an LDR file. First Block OK, next DXE is at %X' % nextDXE
	
	# open the outfile
	outfile = open(outfilename, "wb") # TODO: try/catch for file open

	# main parsing loop: 1) check next header 2) parse flags 3) append content to outfile
	i=1
	for header in iter(lambda: infile.read(4)[::-1], ""):
	#header = infile.read(4)[::-1] # remove this line after the above while loop is coded
		target = infile.read(4)[::-1] # TODO: check for each read if EOF and exit with error message "infile ended abruptly"
		bytecount = struct.unpack('i', infile.read(4))[0]
		argument = infile.read(4)
		#check if the header is still a valid LDR header
		if(header[0] != '\xAD'):
			print "The infile doesn't look like an LDR file, one of the Header identifiers is not 0xAD"
			exit(1)
		flags.asbyte = ord(header[2])
		if(flags.b.fill == 1):
			for _ in range(bytecount):
				outfile.write(argument)
		else:
			buffer = infile.read(bytecount)
			outfile.write(buffer)

		print("[written] block {0} with {1} Bytes".format(i, bytecount))
		i=i+1
	outfile.close()
	infile.close()
		
		
