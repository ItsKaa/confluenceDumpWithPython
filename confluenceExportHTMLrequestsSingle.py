# -*- coding: utf-8 -*-
##!/usr/bin/env python3

#import pypandoc # only needed if converting HTML to MD
import requests
import os.path
import json
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup as bs
import sys
import pypandoc
from PIL import Image


apiToken = os.environ["atlassianAPIToken"]
userName = os.environ["atlassianUserEmail"]

try:
    atlassianSite = sys.argv[1]
except IndexError:
    raise SystemExit(f"Usage: <script>.py {sys.argv[1]} <pageID>")
print('Site: ' + atlassianSite)

try:
    pageID = sys.argv[2]
except IndexError:
    raise SystemExit(f"Usage:<script>.py <site> {sys.argv[2]}")
print('Page ID: ' + pageID)

def getBodyExportView(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

def getPageName(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID)
    r_pagetree = requests.get(serverURL, auth=(userName, apiToken))
    return(r_pagetree.json()['id'] + "_" + r_pagetree.json()['title'])

# get page labels
def getPageLabels(argPageID):
    htmlLabels = []
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/api/v2/pages/' + str(argPageID) + '/labels'
    response = requests.get(serverURL, auth=(userName, apiToken),timeout=30).json()
    for l in response['results']:
        htmlLabels.append(l['name'])
    #htmlLabels = ",".join(htmlLabels)
    return(htmlLabels)

myBodyExportView = getBodyExportView(pageID).json()
myBodyExportViewHtml = myBodyExportView['body']['export_view']['value']
myBodyExportViewTitle = myBodyExportView['title']
myBodyExportViewTitle = myBodyExportViewTitle.replace("/","-")
#
# Handling output folder path
#
currentDir = os.getcwd()
scriptDir = os.path.dirname(os.path.abspath(__file__))
try:
    outdir = sys.argv[3]
except IndexError as exc:
    outdir = os.path.join(scriptDir,"output")
    outdir = os.path.join(outdir,str(pageID) + " - " + str(myBodyExportViewTitle))
    print('No output folder supplied, using current path: ' + outdir)
else:
    outdir = os.path.join(outdir,str(pageID) + " - " + str(myBodyExportViewTitle))
#
# Create the output folders, set to match Sphynx structure
#
attachDir = "_images/"
emoticonsDir = "_images/"
stylesDir = "_static/"
outdirAttach = os.path.join(outdir,attachDir)
outdirEmoticons = os.path.join(outdir,emoticonsDir)
outdirStyles = os.path.join(outdir,stylesDir)

if not os.path.exists(outdir):
    os.mkdir(outdir)

if not os.path.exists(outdirAttach):
    os.mkdir(outdirAttach)

if not os.path.exists(outdirEmoticons):
    os.mkdir(outdirEmoticons)

if not os.path.exists(outdirStyles):
    os.mkdir(outdirStyles)

if not os.path.exists(outdirStyles + '/site.css'):
    os.system('cp ' + scriptDir + '/styles/site.css "' + outdirStyles + '"')

def getBodyExportView(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=body.export_view'
    response = requests.get(serverURL, auth=(userName, apiToken))
    return(response)

def getAttachments(argPageID):
    serverURL = 'https://' + atlassianSite + '.atlassian.net/wiki/rest/api/content/' + str(argPageID) + '?expand=children.attachment'
    response = requests.get(serverURL, auth=(userName, apiToken))
    myAttachments = response.json()['children']['attachment']['results']
    for n in myAttachments:
        myTitle = n['title']
        myTitle = myTitle.replace(":","-").replace(" ","_").replace("%20","_")
        myTail = n['_links']['download']
        url = 'https://' + atlassianSite + '.atlassian.net/wiki' + myTail
        requestAttachment = requests.get(url, auth=(userName, apiToken),allow_redirects=True)
        filePath = os.path.join(outdirAttach,myTitle)
        #if (requestAttachment.content.decode("utf-8")).startswith("<!doctype html>"):
        #    filePath = str(filePath) + ".html"
        open(filePath, 'wb').write(requestAttachment.content)
        myAttachmentsList.append(myTitle)
    return(myAttachmentsList)
#
# Define HTML page footer
#
footersHTML = """</body>
</html>"""
#
# Clear all lists (just in case)
#
myAttachments = []
myAttachmentsList = []
myEmbeds = []
myEmbedsExternals = []
myEmoticons = []
myEmoticonsList = []
def dumpHtml(argHTML,argTitle,argPageID):
    soup = bs(argHTML, "html.parser")
    htmlFileName = str(argTitle) + '.html'
    htmlFilePath = os.path.join(outdir,htmlFileName)
    myAttachments = getAttachments(argPageID)
    #
    # dealing with "confluence-embedded-image confluence-external-resource"
    #
    myEmbedsExternals = soup.findAll('img',class_="confluence-embedded-image confluence-external-resource")
    myEmbedsExternalsCounter = 0
    for embedExt in myEmbedsExternals:
        origEmbedExternalPath = embedExt['src']
        origEmbedExternalName = origEmbedExternalPath.rsplit('/',1)[-1].rsplit('?')[0]
        origEmbedExternalName = str(argPageID) + "-" + str(myEmbedsExternalsCounter) + "-" + origEmbedExternalName
        myEmbedExternalPath = os.path.join(outdirAttach,origEmbedExternalName)
        toDownload = requests.get(origEmbedExternalPath, allow_redirects=True)
        myEmbedExternalPath = myEmbedExternalPath.replace(":","-").replace(" ","_").replace("%20","_")
        open(myEmbedExternalPath,'wb').write(toDownload.content)
        print(myEmbedExternalPath)
        embedExt['width'] = "1024px"
        embedExt['height'] = "auto"
        embedExt['onclick'] = "window.open(\"" + myEmbedExternalPath + "\")"
        embedExt['src'] = myEmbedExternalPath
        myEmbedsExternalsCounter = myEmbedsExternalsCounter + 1
    #
    # dealing with "confluence-embedded-image"
    #
    myEmbeds = soup.findAll('img',class_="confluence-embedded-image")
    print(str(len(myEmbeds)) + " embedded images.")
    for embed in myEmbeds:
        origEmbedPath = embed['src']
        origEmbedName = origEmbedPath.rsplit('/',1)[-1].rsplit('?')[0]
        myEmbedName = origEmbedName.replace(":","-").replace(" ","_").replace("%20","_")
        myEmbedPath = attachDir + myEmbedName
        myEmbedPathFull = os.path.join(outdir,myEmbedPath)
        print("Embed path: " + myEmbedPath)
        img = Image.open(myEmbedPathFull)
        if img.width < 600:
            embed['width'] = img.width
        else:
            embed['width'] = 600
        img.close
        embed['height'] = "auto"
        embed['onclick'] = "window.open(\"" + myEmbedPath + "\")"
        embed['src'] = myEmbedPath
    #
    # dealing with "emoticon"
    #
    myEmoticons = soup.findAll('img',class_="emoticon")     # atlassian-check_mark, or
    print(str(len(myEmoticons)) + " emoticons.")
    for emoticon in myEmoticons:
        requestEmoticons = requests.get(emoticon['src'], auth=(userName, apiToken))
        myEmoticonTitle = emoticon['src'].rsplit('/',1)[-1]
        if myEmoticonTitle not in myEmoticonsList:
            myEmoticonsList.append(myEmoticonTitle)
            print("Getting emoticon: " + myEmoticonTitle)
            filePath = os.path.join(outdirEmoticons,myEmoticonTitle)
            open(filePath, 'wb').write(requestEmoticons.content)
        myEmoticonPath = emoticonsDir + myEmoticonTitle
        emoticon['src'] = myEmoticonPath
    #
    # Putting HTML together
    #
    prettyHTML = soup.prettify()
    htmlFile = open(htmlFilePath, 'w')
    htmlFile.write(htmlPageHeader)
    htmlFile.write(prettyHTML)
    htmlFile.write(footersHTML)
    htmlFile.close()
    print("Exported HTML file " + htmlFileName)
    #
    # convert html to rst
    #
    rstFileName = str(argTitle) + '.rst'
    rstFilePath = os.path.join(outdir,rstFileName)
    outputRST = pypandoc.convert_file(str(htmlFilePath), 'rst', format='html',extra_args=['--wrap=none'])
    rstFile = open(rstFilePath, 'w')
    rstFile.write(outputRST)
    rstFile.close()
    print("Exported RST file: " + rstFileName)
#
# Define HTML page header
#
def setPageHeader(argTitle,argURL,argLabels):
    myHeader = """<html>
<head>
<title>""" + argTitle + """</title>
<link rel="stylesheet" href=\"""" + stylesDir + """site.css" type="text/css" />
<meta name="generator" content="confluenceExportHTML" />
<META http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="labels" content=\"""" + str(argLabels) + """\">
</head>
<body>
<h2>""" + argTitle + """</h2>
<p>Original URL: <a href=\"""" + argURL + """\"> """+argTitle+"""</a><hr>"""
    return(myHeader)
#
# Start processing the page to dowload
#
myBodyExportViewName = getPageName(pageID)
print("Page name: " + myBodyExportViewTitle)
myBodyExportViewLabels = getPageLabels(pageID)
myBodyExportViewLabels = ",".join(myBodyExportViewLabels)
myPageURL = str(myBodyExportView['_links']['base']) + str(myBodyExportView['_links']['webui'])
htmlPageHeader = setPageHeader(myBodyExportViewTitle,myPageURL,myBodyExportViewLabels)
dumpHtml(myBodyExportViewHtml,myBodyExportViewTitle,pageID)
