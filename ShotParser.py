#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import xml.etree.ElementTree as ET
from colorama import init as colorInit
from colorama import Fore, Back, Style
import pprint
from ShotgunCom import ShotgunServer
import urllib
import subprocess
import sys
import time
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    FileTransferSpeed, FormatLabel, Percentage, ProgressBar, \
    ReverseBar, RotatingMarker, SimpleProgress, Timer

# set some login credentials for shotgun

shotgun_url = 'https://yourstudio.shotgunstudio.com'
app_name = 'yourAppName'
app_key = 'yourAppKey'

try:
    from settings import *
except ImportError:
    pass

pp = pprint.PrettyPrinter(indent=4)
colorInit(autoreset=True)  # init colorama

# drag and drop input file

XMLFiles = []

for arg in sys.argv:
    XMLFiles.append(arg)

print 'Processing batch file: ' + XMLFiles[1]

try:
    tree = ET.parse(XMLFiles[1])
except Exception, e:
    print 'ERROR: %s' % e
    raw_input('Press a key to exit the program')
    sys.exit()

root = tree.getroot()


# declare a clip Class
class Clip:
    def __init__(self, name, inPoint, outPoint, duration, fileurl):
        self.name = name
        self.inPoint = inPoint
        self.outPoint = outPoint
        self.duration = duration
        self.fileurl = fileurl


# declare a sequence Class

class Sequence:
    def __init__(self,id,duration,ref):
        self.id = id
        self.duration = duration
        self.name = name
        self.reference = ref

def resetColors():
    print Fore.RESET

def generateThumbnail(path, fname, cduration):
    filepath = os.path.dirname(os.path.realpath(__file__)) + '\\thumbs\\' + fname + '.jpg'
    os.system('ffmpeg -loglevel panic -i "%s" -vframes 1 -an -s 400x222 -ss %s %s' % (os.path.abspath(path), cduration / 2 / 24, filepath))
    return filepath

def importShots():

    global shotgun_url #Bad, leaving this for now.
    global app_name
    global app_key
    shotgun = ShotgunServer(shotgun_url, app_name, app_key)
    shotgunConn = shotgun.connect()

    pp.pprint(shotgunConn)

    # shot progress
    widgets = ['Uploading Shots: ', SimpleProgress(), ' ', Bar()]
    pbar = ProgressBar(widgets=widgets, maxval=len(clips)).start()
    i = 0

    for item in clips:
        shot = shotgun.addShot(item, sgSequence, sgScene)
        result = shotgun.uploadThumbnail(shot['id'], item.thumbpath)
        i += 1
        pbar.update(i)

    pbar.finish()
    print 'Finished'

    raw_input('')

def parse():
    track = sequences[seqSelection].reference.find('.//media/video/track')
    take = 1

    for clipitem in track.iter('clipitem'):
        name = sgReel + '_' + sgSequence + '_' + sgScene + '_TK'
        if take < 10:
            name += '0'
        name += str(take)
        duration = int(clipitem.find('./duration').text)
        inPoint = int(clipitem.find('./in').text)
        outPoint = int(clipitem.find('./out').text)
        fileID = clipitem.find('./file').attrib['id']

        # remove the file protocol at the begining
        nodeText = root.findall(".//*[@id='%s']/pathurl" % fileID)[0].text
        url = urllib.unquote(nodeText)
        url = 'Z:' + url.split('Z:')[1]  # NOTE: windows paths only for now.
        clips.append(Clip(name, inPoint, outPoint, duration, url))
        take += 1

def importToShotgun():

    # SET SOME VALUES

    global sgReel
    global sgSequence
    global sgScene
    sgReel = 'EA' + raw_input('Enter REEL (zp): ')
    sgSequence = 'SQ' + raw_input('Enter Sequence (zp): ') + 'X'
    sgScene = 'SC' + raw_input('Enter Sequence (zp): ') + 'X'

    parse()

    # show progress bar
    widgets = ['Generating thumbnails: ', SimpleProgress(), ' ', Bar()]
    pbar = ProgressBar(widgets=widgets, maxval=len(clips)).start()
    i = 0
    for item in clips:
        thumbpath = generateThumbnail(item.fileurl, item.name, item.duration)
        item.thumbpath = thumbpath
        i += 1
        pbar.update(i)

    pbar.finish()
    continueOption = raw_input(Fore.RED
                               + '%s shots were found and will be created under %s, Continue? [y/n]: '
                                % (len(clips), sgReel + '_'
                               + sgSequence + '_' + sgScene))
    if continueOption == 'y' or continueOption == 'Y':
        importShots()
    else:
        sys.exit()


def generateReport():
    parse()
    errorClips = {}

    takeCounter = 1
    for clip in clips:
        if clip.inPoint == 0 or clip.outPoint == clip.duration:
            errorClips['TK' + str(takeCounter)] = clip
        takeCounter += 1

    if len(errorClips) > 0:
        print '\n' + Fore.RED + 'The following clips have either no tail at the end, beginning, or both:\n'

        # get file name

        fileName = os.path.splitext(os.path.basename(XMLFiles[1]))[0]
        for (key, clip) in errorClips.iteritems():
            outPutString = '%s in: %s out: %s duration: %s' % (key, clip.inPoint, clip.outPoint, clip.duration)
            print outPutString
            text_file = open("D:\Trabajos\ShotParser\\results\%s.txt" % fileName, 'a')
            text_file.write('INFO: %s \n' % outPutString)
            text_file.close()
    else:

        print '\n' + Fore.GREEN + 'All clips are OK \n'

    raw_input('Press any key to exit')
    sys.exit()


# get a list of sequences

sequences = []
clips = []

# SET SOME default VALUES

sgReel = 'EA1'
sgSequence = 'TSQ01X'
sgScene = 'TSC01X'

for element in root.iter('sequence'):
    id = element.get('id')
    duration = element.find('./duration').text
    name = element.find('./name').text
    seq = Sequence(id, duration, element)
    sequences.append(seq)

# USER INPUT

choiceCounter = 1
print 'The following sequences were found: \n'

for choice in sequences:
    print Fore.YELLOW + '[%s] %s' % (choiceCounter, choice.name)
    choiceCounter += 1

seqSelection = int(raw_input('\nPlease select one to proceed: ')) - 1

# seqSelection = 1

# ask the user what to do

print '''
What would you like to do?
'''
print '[1] Import shots to Shotgun'
print '[2] Generate missing tail report'
optionsInput = int(raw_input('\nPlease select an option to continue: '))

# optionsInput = 1

if optionsInput == 1:
    importToShotgun()
else:
    generateReport()
