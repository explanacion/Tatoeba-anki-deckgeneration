#!/usr/bin/python
# -*- coding: utf8 -*-

import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import re
import sys
import csv
import os
import shutil
import json

#######################################
# basic variables you can change
#######################################

UrlListOfSentences = 'https://tatoeba.org/eng/sentences/search?query=&from=spa&to=und&user=&orphans=no&unapproved=no&has_audio=yes&tags=&list=&native=yes&trans_filter=limit&trans_to=rus&trans_link=direct&trans_user=&trans_orphan=&trans_unapproved=&trans_has_audio=&sort=words&sort_reverse=' # basic url with the list of the sentences (if there are many pages they will be processed page by page)
getAudio = True # True if we grab audio if sentences in a source language have it
getTags = True # True if we copy the tags if they exist
getAutor = True # True if we want to know who is the author (will appear as an extra tag)
srclang = ["spa"] # languages of source sentences (may be 1 or more that will appear on the question field). This should be 2-letter code ISO 639-1  https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
audio3letterslangcodes = ["spa","eng"] # these codes are used in Tatoeba's url when you browse audio by language, e.g. cmn for Chinese in https://tatoeba.org/eng/sentences/with_audio/cmn
targetlang = "rus" # target language code (will be on the answer's fiels)
copymediafilestoankifolder = True # if true you should manually set your anki media folder
#ankimediafolder = "C:\\Users\\atomi\\AppData\\Roaming\\Anki2\\Miles\\collection.media"  # this is "collection.media" folder which is normally located in your documents folder (in Windows)
ankimediafolder = "/home/odexed/.local/share/Anki2/1-й пользователь/collection.media"

########################################
# Here the main code begins
########################################

if os.path.exists('foranki'):
    key = input("'foranki' folder already exists. Press Enter to clean it or close this window")
    if not key:
        shutil.rmtree('foranki')

try:
    os.mkdir('foranki')
except:
    print("The script couldn't create a temporary workdir foranki.")
    sys.exit(1)

cfile = open("foranki/exampledeck.csv", "w")

def procstring(string):
    res = string
    res=res.replace("&#039;","'")
    res=res.replace("&quot;",'"')
    return res

# process the link, open it and grab all we need
def proclink(num):
    taglist = []
    url = 'https://tatoeba.org/eng/sentences/show/' + num

    curaudio = ''
    resp = urllib.request.urlopen(url)
    if resp.getcode() != 200:
        print("Error response for search")
        sys.exit(1)
    html = resp.read().decode('utf-8')

    if getTags:
        tagname=re.findall('class="tagName".+?\>(.+?)\<',html,re.DOTALL)
        for i in tagname:
            taglist.append(i.strip().replace(" ","_"))
    #print(taglist)

    jsonSentence = re.findall('<div ng-cloak flex.+?sentence-and-translations.+?ng-init="vm.init\(\[\]\,(.+?}), \[\{',procstring(html), re.DOTALL)
    targetsentence = ''
    srcsentence = ''

    for jsonItem in jsonSentence:
        #print(jsonItem)
        jsonData = json.loads(jsonItem)
        if getAutor:
            authorname = jsonData['user']['username']
            if len(authorname) > 0:
                taglist.append('by_' + authorname)
            else:
                taglist.append('orphan_sentence')
        mainlang = jsonData['lang']
        if mainlang in srclang:
            srcsentence = jsonData['text']
            for translations in jsonData['translations']:
                for translation in translations:
                    if targetlang == translation['lang'] and 'isDirect' in translation and translation['isDirect']:
                        targetsentence = translation['text']
                        #print(targetsentence)

    if srcsentence=='':
        print("Error while trying to get the source sentence")
        return

    audiourl = 'https://audio.tatoeba.org/sentences/' + mainlang + '/' + num + '.mp3'
    if getAudio:
        if 'audioAvailable' in html:
            # grab audio
            urllib.request.urlretrieve(audiourl,"foranki/" + num + ".mp3")
            curaudio = '[sound:' + num + '.mp3]'


    csv_writer = csv.writer(cfile, delimiter='\t', lineterminator='\n')
    #print(" ".join([srcsentence + curaudio, targetsentence, " ".join(taglist)]))
    csv_writer.writerow([procstring(srcsentence) + curaudio, procstring(targetsentence), " ".join(taglist)])


def mainproc():
    # 1. get the list of sentences from the first page
    global UrlListOfSentences
    UrlListOfSentences=UrlListOfSentences.replace('/page:1', '').replace('?page=1', '').rstrip("/")
    delim = '?'
    if '?' in UrlListOfSentences:
        delim = '&'
    resp = urllib.request.urlopen(UrlListOfSentences + delim + 'page=1')
    if resp.getcode() != 200:
        print("Failed to open " + UrlListOfSentences)
        sys.exit(1)
    html = resp.read().decode('utf-8')
    # how many pages there are in this list
    pagescount = re.findall('page=(\d+?)\D', html)
    if pagescount != []:
        pagescount = max([int(x) for x in pagescount])
    else:
        pagescount = 0 # there is no pagination

    #print(html)
    links = []
    sentences = []

    jsonSentences = re.findall('<div ng-cloak flex.+?sentence-and-translations.+?ng-init="vm.init\(\[\]\,(.+?), \[',procstring(html),re.DOTALL)
    for jsonItem in jsonSentences:
        #print(jsonItem)
        jsonData = json.loads(jsonItem)
        links.append(str(jsonData['id']))
        sentences.append(jsonData['text'])

    resp.close()

    for i in range(len(links)):
        # print links[i] + " " + sentences[i]
        proclink(links[i])

    #print(links)

    prCnt = 1 # this is a progress counter (not really necessary but kind of convenient feature)

    for pagescounter in range(2,pagescount + 1):
        # page=2 ?page=2
        delim = '?'
        if '?' in UrlListOfSentences:
            delim = '&'
        urlloop = UrlListOfSentences.rstrip("/") + delim + "page=" + str(pagescounter)
        print(urlloop)
        resp = urllib.request.urlopen(urlloop)
        if resp.getcode() != 200:
            print("Failed to open " + urlloop)
            sys.exit(1)
        html = resp.read().decode('utf-8')
        # print html
        links = []
        sentences = []

        jsonSentences = re.findall('<div ng-cloak flex.+?sentence-and-translations.+?ng-init="vm.init\(\[\]\,(.+?), \[',
                                   procstring(html), re.DOTALL)
        for jsonItem in jsonSentences:
            # print(jsonItem)
            jsonData = json.loads(jsonItem)
            links.append(str(jsonData['id']))
            sentences.append(jsonData['text'])

        resp.close()
        for i in range(len(links)):
            proclink(links[i])
        prCnt += 1
        curPrcnt = (100.0*prCnt) / pagescount
        #os.system('title ' + str(round(curPrcnt,3)) + '% completed')
        print(str(round(curPrcnt,3)) + '% completed')

    # copy media files to anki media folder
    for root, dirs, files in os.walk('foranki'):
        for f in files:
            filename = os.path.join(root, f)
            if filename.endswith('.mp3'):
                if copymediafilestoankifolder:
                    shutil.copy2(filename,ankimediafolder)

mainproc()
cfile.close()