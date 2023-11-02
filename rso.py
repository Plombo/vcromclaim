#!/usr/bin/env python3

# Utilities to extract stuff from RSO files.
# RSO files are like SO files in Linux or DLL files in Windows, so they contain mostly code but sometimes other binary data.
# In some VC Arcade games, some RSO files contain the system specific emulation code, as well as the emulated ROMs.

# Invaluable source: https://github.com/sepalani/librso/blob/master/rvl/rso.py

# The actual binary data is in the "Sections".
# The externals table lists different offset within different sections to make available to use by other code. (including ROMs)
# The internals table is a bit unknown.

# Unless otherwise mentioned, all "offset" is relative to the beginning of the file.
# It seems that all offsets are aligned to 4 bytes, there is null padding between file portions with odd lenghts.
# Unless otherwise mentioned, each value is 4 bytes

#HEADER:

#Info
#headerValues[0] = Next RSO Entry
#headerValues[1] = Previous RSO Entry
#headerValues[2] = Section Count
#headerValues[3] = Section Table Offset
#headerValues[4] = Name Offset
#headerValues[5] = Name Size
#headerValues[6] = Version
#headerValues[7] = BSS Section Size

#SectionInfo
#headerValues[8] = 4x1 byte values - Has Prolog, Has Epilog, Has Unresolved, Has BSS
#headerValues[9] = Prolog Offset
#headerValues[10] = Epilog Offset
#headerValues[11] = Unresolved Offset

#RelocationTables:
#headerValues[12] = Internals Relocation Table Offset
#headerValues[13] = Internals Relocation Table Size
#headerValues[14] = Externals Relocation Table Offset
#headerValues[15] = Externals Relocation Table Size

#Exports:
#headerValues[16] = Exports Offset
#headerValues[17] = Exports Size
#headerValues[18] = Exports Name Offset

#Imports
#headerValues[19] = Imports Offset
#headerValues[20] = Imports Size
#headerValues[21] = Imports Name Offset

#end of header, the rest of the file is different portions, whose positions is given in the header, or in other tables.

#SECTION TABLE:
#Starts at position "Section Table Offset" in header
#For each section (0 - section count-1):
    # Section offset
    # Section length, in bytes
#Some sections have both 0 offset and 0 length. Ignoring them.
#Some sections have both 0 offset but a positive length. Not sure what this means. Ignoring them.

#SECTION:
#Starts at the position and has the length determined by the values in the section table.
#The content is the actual binary data. Most often Wii binary code, but sometimes ROM content.

#NAME:
#The name of the entire library.
#Starts at the position and has the length specified in header.

#EXPORTS TABLE:
#Contains the list of export points in the different sections.
#Starts at position "Exports Offset" in header. The size in bytes is specified in header. The number of entries is the size in bytes / 16.
#For each entry:
    #Name offset (offset of the name in the Exports Name table, relative to the start of the export name table)
    #Data Offset (relative to section start, i.e. 0=first byte in the section)
    #Section index (0-section count-1)
    #??? (large value, not referenced elsewhere in the file)

#EXPORT NAMES:
#Starts at position "Exports Name Offset" in header. Size is not specified anywhere.
#Contains a number of nullterminated names without any alignment.
#The position of a name is specified in the exports table.

#EXTERNALS RELOCATION TABLE
#Starts point and Size specified at "Externals Relocation Table Offset" and "Size" in header.
#Not sure what this is.

#IMPORTS TABLE, IMPORT NAMES, INTERNALS RELOCATION TABLE:
#Similar to EXTERNALS counterparts.


import struct

class rso(object):
    def __init__(self, inputFile):
        self.file = inputFile

    def getExport(self, name, dataLength):
        self.file.seek(0)
        headerValues = struct.unpack(">22I", self.file.read(22*4))

        exportTableOffset = headerValues[16]
        exportTableLength = headerValues[17]
        exportNamesOffset = headerValues[18]

        for exportTableEntryPosition in range(0, exportTableLength, 4*4):

            self.file.seek(exportTableOffset + exportTableEntryPosition)
            exportTableEntry = struct.unpack(">4I", self.file.read(4*4))
            
            namePosition = exportTableEntry[0]
            dataPosition = exportTableEntry[1]
            sectionIndex = exportTableEntry[2]

            nameCandidate = self.readNullTerminatedString(exportNamesOffset + namePosition)

            if name == nameCandidate:

                sectionTableEntry = self.getSectionTableEntry(sectionIndex)

                sectionOffset = sectionTableEntry[0]
                sectionLength = sectionTableEntry[1]

                assert dataPosition + dataLength <= sectionLength

                self.file.seek(sectionOffset + dataPosition)
                
                data = self.file.read(dataLength)

                assert len(data) == dataLength
                return data

    def getSectionTableEntry(self, sectionIndex):
        self.file.seek(0)
        headerValues = struct.unpack(">22I", self.file.read(22*4))

        sectionTableOffset = headerValues[3]
        sectionCount = headerValues[2]

        assert sectionIndex < sectionCount

        self.file.seek(sectionTableOffset + sectionIndex*2*4)
        return struct.unpack(">2I", self.file.read(2*4))


    def getAllExports(self):
        self.file.seek(0)
        headerValues = struct.unpack(">22I", self.file.read(22*4))

        exportTableOffset = headerValues[16]
        exportTableLength = headerValues[17]
        exportNamesOffset = headerValues[18]

        exports = []

        for exportTableEntryOffset in range(0, exportTableLength, 4*4):

            self.file.seek(exportTableOffset + exportTableEntryOffset)
            exportTableEntry = struct.unpack(">4I", self.file.read(4*4))
            
            nameOffset = exportTableEntry[0]

            name = self.readNullTerminatedString(exportNamesOffset + nameOffset)

            exports.append(name)

        return exports

    def readNullTerminatedString(self, startOffset):
        self.file.seek(startOffset)
        ba = bytearray()
        while True:
            b = self.file.read(1)
            
            if b[0] == 0:
                return ba.decode('ascii')
            else:
                ba.extend(b)


        
















