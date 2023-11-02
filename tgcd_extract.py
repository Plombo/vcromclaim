#!/usr/bin/env python3

import os.path, struct, zlib
from io import BytesIO, StringIO
from configurationfile import getConfiguration 


#TODO: audio clearly runs to slow in Mednafen (may cause secondary issues, like music/sound starting at the wrong positions)
#   Exported audio files are 48khz. Maybe Mednafen probably plays this in 44khz (the CD-A frequency).
#   Can be worked-around by using any tool to convert the OGG files to CD-A or any other format that Mednafen can support
#   and updating the Cue sheet accordingly.
#TODO: Extracted super air zonk freeze on BIOS screen in Mednafen, a raw disk dump (2352 bytes/sector) of the same game plays fine.
#   Maybe there is a problem with the CD-ROM overhead (VC emulator ignores it or recreates the headers/footers differntly than Mednafen?)



def extract_tgcd(u8InputFile, outputFolder):

    # The data tracks = bin files are extracted as is, but padded or truncated to the length specified in HCD file.
    # cue file instructs emulator to read files as MODE1/2048.
    
    # Missing bin files (mentioned in HCD file but not existing) have replacment null-filled
    # ".dummy" files of the size specified in the HCD file.

    # Audio files are in OGG format and copied as is.
    
    # Missing audio files are replaced by null-filled ".dummy" files of the size specified in the HCD file. 


    hcdFileName = getHcdFileName(extractFile(u8InputFile, "config.ini"))
    hcdFileContent = extractFile(u8InputFile, hcdFileName)
    assert hcdFileContent is not None

    cueFileContent = StringIO()

    #saveFile(hcdFileContent, "debug.hcd", outputFolder)
    #saveFile(extractFile(u8InputFile, "config.ini"), "debug.ini", outputFolder)

    for trackDescription in getTrackDescriptionsFromHcdFile(hcdFileContent):



        # It is normal that the file mentioned in HCD file does not exist.
        # First track is often an audio track with a voice asking the user to stop playing the disc in a CD player.
        # One of the last tracks is often a copy of the first data track.

        if trackDescription.dataTrack:

            if fileExists(u8InputFile, trackDescription.fileName):
                data = decompressBinaryFile(extractFile(u8InputFile,trackDescription.fileName))
                fileName = trackDescription.fileName
            else:
                data = BytesIO()
                fileName = getWithOtherFileExtension(trackDescription.fileName, "dummy")
            saveFile(getLengthCorrectedData(data, 2048, trackDescription.sectorCount), fileName, outputFolder)
            cueFileContent.write(createCueDirective(trackDescription, fileName))

        else: #Audio track

            if fileExists(u8InputFile, trackDescription.fileName):
                saveFile(extractFile(u8InputFile,trackDescription.fileName), trackDescription.fileName, outputFolder)
                cueFileContent.write(createCueDirective(trackDescription, trackDescription.fileName))
            else:
                dummyFileName = getWithOtherFileExtension(trackDescription.fileName, "dummy")
                saveFile(getLengthCorrectedData(BytesIO(), 2352, trackDescription.sectorCount), dummyFileName, outputFolder)
                cueFileContent.write(createDummyAudioCueDirective(trackDescription, dummyFileName))


    saveFile(cueFileContent, getWithOtherFileExtension(hcdFileName, "cue"), outputFolder)

    saveFile(extractFile(u8InputFile, "syscard3P.pce"), "syscard3P.pce", outputFolder)
    



def fileExists(u8InputFile, fileName):
    return u8InputFile.hasfile(fileName)

def extractFile(u8InputFile, fileName):
    return u8InputFile.getfile(fileName)

def getHcdFileName(configFileContent):
    romname = getConfiguration(configFileContent, "ROM")
    if romname:
        return romname
    else:
        raise ValueError

def getTrackDescriptionsFromHcdFile(hcdFileContentBytesIO):
    #convert BytesIO to stringIO
    hcdBytes = hcdFileContentBytesIO.read()
    # Convert to a "unicode" object
    text_obj = hcdBytes.decode('ascii')
    hcdFileContentStringIO = StringIO(text_obj)

    hcdFileContentStringIO.seek(0)
    returnArray = []
    counter = 1
    previousEndSector = 0
    for line in hcdFileContentStringIO:
        trackDescription = TrackDescription(line, counter, previousEndSector)
        returnArray.append(trackDescription)
        previousEndSector = trackDescription.endSector
        counter += 1
    assert len(returnArray) > 0
    return returnArray

def decompressBinaryFile(compressedBinaryFileContent):
    #Based on qwikrazor87's decomp.py!

    compressedBinaryFileContent.seek(0)
    entries = struct.unpack('<I', compressedBinaryFileContent.read(4))[0]

    decompressed = BytesIO()

    for i in range(entries):
        compressedBinaryFileContent.seek((i * 8) + 4)
        offset = struct.unpack('<I', compressedBinaryFileContent.read(4))[0]
        size = struct.unpack('<I', compressedBinaryFileContent.read(4))[0]
        compressedBinaryFileContent.seek(offset)
        decompressed.write(zlib.decompress(compressedBinaryFileContent.read(size)))

    return decompressed


def getWithOtherFileExtension(path, newFileExtension):
    return os.path.splitext(path)[0] + "." + newFileExtension


def saveFile(fileContent, fileName, outputFolder):
    folderPath = os.path.join(outputFolder)
    filePath = os.path.join(outputFolder, fileName)

    if not os.path.lexists(folderPath):
        os.makedirs(folderPath)

    if isinstance(fileContent, str) or isinstance(fileContent, StringIO):
        mode = 'w'
    else:
        mode = 'wb'
    
    outputFile = open(filePath, mode)
    fileContent.seek(0)
    outputFile.write(fileContent.read())
    fileContent.seek(0)
    outputFile.close()
        
def createCueDirective(trackDescription, replacementFileName):
    directive  = "FILE \"" + replacementFileName + "\" " + ("BINARY" if trackDescription.dataTrack else "OGG") + "\r"
    directive += "  TRACK " + ('%02d' % trackDescription.trackNumber) + " " + ("MODE1/2048" if trackDescription.dataTrack else "AUDIO") + "\r"
    directive += "    PREGAP " + getTimeFromSectorIndex(trackDescription.pregap) + "\r"
    directive += "    INDEX 01 " + getTimeFromSectorIndex(0) + "\r"
    return directive

def createDummyAudioCueDirective(trackDescription, replacementFileName):
    directive  = "FILE \"" + replacementFileName + "\" BINARY\r"
    directive += "  TRACK " + ('%02d' % trackDescription.trackNumber) + " AUDIO\r"
    directive += "    PREGAP " + getTimeFromSectorIndex(trackDescription.pregap) + "\r"
    directive += "    INDEX 01 " + getTimeFromSectorIndex(0) + "\r"
    return directive


def getTimeFromSectorIndex(sectorIndex):
    sectors = sectorIndex % 75
    seconds = int(((sectorIndex - sectors) / 75)) % 60
    minutes = int((sectorIndex - seconds * 75 - sectors) / (60*75))

    return ('%02d' % minutes) + ":" + ('%02d' % seconds) + ":" + ('%02d' % sectors)

#cuts the file if it is longer than specified (assuming the extra length is just padding).
#adds null padding if the file is shorter than specified
def getLengthCorrectedData(data, sectorSize, sectorCount):
    targetSize = sectorSize * sectorCount
    data.seek(0, os.SEEK_END)
    actualSize = data.tell()
    
    #pad if needed
    if actualSize < targetSize:
        data.write(b'\x00'*(targetSize-actualSize))
        return data
    elif actualSize > targetSize:
        newData = StringIO()
        data.seek(0)
        newData.write(data.read(targetSize))
        return newData
    else:
        return data



    


class TrackDescription(object):
    def __init__(self, hcdLine, trackNumber, previousEndSector):
        splitLine = hcdLine.split(",")

        assert trackNumber >= 0
        assert trackNumber <= 99
        self.trackNumber = trackNumber
        
        assert len(splitLine[2]) > 0
        self.fileName = splitLine[2]

        normalizedTrackType = splitLine[1].strip()
        assert normalizedTrackType == "audio" or normalizedTrackType == "code"
        self.dataTrack = normalizedTrackType == "code" # True = data, False = audiotrack

        # start sectors seems to be offset by 150 sectors
        self.startSector = int(splitLine[3]) - 150
        assert (self.startSector >= 0)

        self.sectorCount = int(splitLine[4])
        assert (self.sectorCount >= 0)

        self.endSector = self.startSector + self.sectorCount #NON-INCLUSIVE
        assert (self.endSector >= self.startSector)

        # Calculate the pregap.
        # In Cue/Bin, each track starts immediatelly after the next track.
        # In HCD, the start sector of each track is specified.
        # We calculate pregap for the ISO to start the new track at the correct sector.

        # Sometimes this track is positioned before the last track's start+length.
        # I've only seen it once, track 3 on Castlevania: RoB is about 15 frames (0,1 or 0,2 sec) too long.
        # It is probably a bug on that game.
        #if (self.startSector - previousEndSector < 0):
        #    print("Warning: Start sector less than previous end sector.")
        #    print(self.trackNumber)
        #    print(self.fileName)
        #    print(self.startSector)
        #    print(self.sectorCount)
        #    print(previousEndSector)

        self.pregap = max(0, self.startSector - previousEndSector)
        assert (self.pregap) >= 0
