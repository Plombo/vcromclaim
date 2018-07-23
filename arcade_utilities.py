# Functions to split and splice ROMs.



#Utilities

def getAsymmetricPart(fileData, start, length):
    retVal = fileData[ start : (start+length) ]
    assert len(retVal) == length
    return retVal


# e.g. if file data is 4 mb, and lengthInKb = 1024, then index 2 would retrieve the third mb of the region
def getPart(fileData, index, length):
    retVal = fileData[ index*length : index*length + length ]
    assert len(retVal) == length
    return retVal

# E.g. to get the first half of a ROM, call with partIndex = 0, partCount = 2. To get second half, call partIndex 1, partCount = 2.
# fileData = the file data of the region.
# partIndex = the part to retrieve. (0-based index)
# partCount = the total number of parts.
# The size of the returned value will be len(fileData) / partCount.
def getPartByDivision(fileData, partIndex, partCount):
    assert partCount > 0
    assert partIndex >= 0
    assert partIndex < partCount

    partSize = len(fileData) / partCount
    
    retVal = fileData[ partIndex*partSize : partIndex*partSize + partSize ]
    assert len(retVal) == partSize
    return retVal


#stripes = [0] = get byte 0, 4, 8 etc
#stripes = [0,1] = get byte 0,1,4,5,8,9 etc
#stripes = [0,2] = get byte 0,2,4,6,8,10 etc
#stripes = [1,3] = get byte 1,3,5,7,9,11 etc
#stripes = [1,2,3,4] = get all bytes
def getStripes(fileData, stripes):
    retVal = ''
    for i in xrange(0, len(fileData), 4):
        for j in stripes:
            retVal += fileData[i+j]
    return retVal





def pad(fileData, totalLength):
    assert totalLength >= len(fileData)
    return fileData + '\xFF'*(totalLength-len(fileData))


