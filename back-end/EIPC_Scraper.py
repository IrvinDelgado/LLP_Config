##Imports Dependecies
from lxml import etree
from bs4 import BeautifulSoup
import requests,re,os,Constants
import pandas as pd

URL_KEYS = Constants.urlGen("EIPC")

CLM_NAMES = [
    'EIPC FIGURE', 'REVISION DATE', 'ITEM', 'PART NUMBER', 'EFFECTIVE ON', 'USAGE CODE', 'SEE NOTE', 'NOMENCLATURE', 'SUPPLIER CODE',
    'SEE FOR NHA', 'ALT P/N', 'DELETED BY SB NUMBER', 'DELETED BY SB NUMBER - EFFECTIVE ON', 'REPLY BY', 'REPLY BY - EFFECTIVE ON',
    'TOTAL QTY', 'SUPSD BY', 'SUPSD BY - EFFECTIVE ON', 'RWK TO', 'RWK TO - EFFECTIVE ON', 'USE WITH', 'USE WITH FIGURE - ITEM',
    'USE WITH - EFFECTIVE ON', 'REF SB NUMBER', 'REF SB NUMBER - EFFECTIVE ON', 'POST SB NUMBER', 'POST SB - EFFECTIVE ON',
    'POST SB ALT P/N', 'POST SB REPLY BY', 'POST SB REPLY BY - EFFECTIVE ON', 'POST SB SUPSD BY', 'POST SB SUPSD BY - EFFECTIVE ON',
    'POST SB RWK TO', 'POST SB RWK TO - EFFECTIVE ON', 'POST SB RWK FROM', 'POST SB RWK FROM - EFFECTIVE ON', 'POST SB SEE FOR NHA',
    'POST SB SEE FOR NHA - EFFECTIVE ON','POST SB USE WITH PART NUMBER', 'POST SB USE WITH FIGURE - ITEM',
    'POST SB USE WITH PART NUMBER - EFFECTIVE ON', 'UPA'            
]
DF = pd.DataFrame(columns = CLM_NAMES)

## Function
## parameter: a url
## returns: XML, converted from the url
def htmlToXML(URL):
    r = requests.get(URL).text
    cleaner = re.sub('&nbsp;',' ',r)
    cleantext = BeautifulSoup(cleaner,"lxml").text
    cleantext = cleantext.replace('<REVCHG>','')
    cleantext = cleantext.replace('</REVCHG>','')
    begin = cleantext.find('<')
    xml = etree.fromstring(cleantext[begin:])
    return xml

## Helper Function to itemLstInfoGetter
## parameter: parent -> is an xml of an item in EIPC
## returns: Effective on which is what is highlighted in EIPC <? EFFECTIVE A/B>
def getEO(parent):
        for child in parent.getchildren():
            if child.tag is etree.ProcessingInstruction:
                return child.text
        return ''

## Function
## parameter: urlKey -> the url which will crawl through Ch72 of an Engine
## returns: a df of all of the items with their respective information
def itemLstInfoGetter(urlKey):
    df=DF
    chptKey = urlKey.replace("CHANGEHERE","PC72")
    chptXML = htmlToXML(chptKey)
    for key in chptXML.iter("CHILD"):
        url = urlKey.replace('CHANGEHERE',key.get("REFKEY"))
        partList = htmlToXML(url)
        fig = ''
        revDate = ''
        for element in partList.iter("FIGURE"):#Each Element is ITEM Section
            fig = element.get("ATACODE")
            revDate = element.get("REVDATE")    
        for element in partList.iter("ITEM"):#Each Element is ITEM Section
            item = element.get("ITEMNBR")
            partNum = ''
            if element.find(".//PNR") != None:
                partNum = element.find(".//PNR").text
            effOn=''
            if element.find(".//EFFECT") !=None:
                effOn = element.find("EFFECT").get("EFFTEXT")
            usageCode = ''
            if element.find(".//EFFCODE") != None:
                usageCode = element.find(".//EFFCODE").text
            note = ''
            if element.find(".//MSC") != None:
                noteTree = element.find(".//MSC")
                note = f'{noteTree.find("P").text}'
            nomcltr = ''
            if element.find(".//NOM") != None:     
                nomcltrTree = element.find(".//NOM")
                nomcltr = ''.join(nomcltrTree.itertext())
                nomcltr = re.sub('\n',' ',nomcltr)   
            supCode = ''
            if element.find(".//MFR") != None:
                sc = element.findall(".//MFR")
                for s in sc:
                    supCode += s.text+'\n'
            seeNHA = ''
            altPN = ''
            postSBN = ''
            delBySBN = ''
            RefSBN = ''
            if element.find(".//SBNBR") != None and element.find(".//SBNBR").get("SBTYPE") == "POST":
                    sbn = element.findall(".//SBNBR")
                    for s in sbn:
                        if s.get("SBTYPE") == "POST":
                            postSBN += s.text + '\n'
                        if s.get("SBTYPE") == "REF":
                            RefSBN += s.text + '\n'
                        if s.get("SBTYPE") == "DELETED BY":
                            delBySBN += s.text + '\n'
            delBySBNEO = ''  
            replBy = ''
            replByEO = ''
            totQty = ''
            if element.find(".//TQE") != None:
                totQty = element.find(".//TQE").text
            supBy = ''
            supByEO = ''
            rwkTo = ''
            rwkToEO = ''
            useWith = ''       
            useWithFig = ''
            useWithEO = ''
            RefSBNEO = ''
            postSBNEO = ''
            postSBAPN = ''
            postSBRepBy = ''
            postSBRepByEO = ''
            postSBSupBy = ''
            postSBSupByEO = ''
            postSBRwkTo = ''
            postSBRwkToEO = ''
            postSBRwkFrom = ''
            postSBRwkFromEO = ''
            postSBForNHA = ''
            postSBForNHAEO = ''
            postSBUWPart = ''
            postSBUWFig = ''
            postSBUWPartEO = ''
            box = element.xpath('.//ITEMSPEC')[0]
            children = box.getchildren()
            currPost = ''
            isPost = False
            for idx,child in enumerate(children,0):
                if child.tag is etree.ProcessingInstruction:
                    if child.text != '':
                        if children[idx+2].get("SBTYPE")=="POST":
                            postSBNEO += child.text+'\n'
                        elif children[idx+2].get("SBTYPE")=="REF":
                            RefSBNEO += child.text+'\n'
                        elif children[idx+2].get("SBTYPE")=="DELETED BY":
                            delBySBNEO += child.text+'\n'
                if child.tag == 'SBNBR':
                    currPost=''.join(child.itertext()).strip()#Since there might be a REVCHANGE
                    isPost = True
                if child.tag == 'APN':
                    if children[idx-1].tag != children[idx].tag and isPost:
                        postSBAPN += 'POST: '+currPost + '\n'
                    if isPost:
                        postSBAPN += child.text+'\n'
                    else:
                        altPN += child.text+'\n'
                if child.tag == 'REFINT':
                    if children[idx-1].tag != children[idx].tag and isPost:
                        postSBForNHA += 'POST: '+currPost + '\n'
                    if isPost:
                        postSBForNHA += child.text+'\n'
                        postSBForNHAEO += getEO(child)
                    else:
                        seeNHA += child.text+'\n'   
                if child.tag == 'RP':
                    postSBRepByEO += getEO(child)+'\n'
                    if children[idx-1].tag != children[idx].tag and isPost:
                        postSBRepBy += 'POST: '+currPost + '\n'
                    if isPost:
                        postSBRepBy += child.text+'\n'
                        postSBRepByEO += getEO(child)+'\n'
                    else:
                        replBy += child.text+'\n'
                        replByEO += getEO(child)
                if child.tag == 'SD':
                    if children[idx-1].tag != children[idx].tag and isPost:
                        postSBSupBy += 'POST: '+currPost + '\n'
                    if isPost:
                        postSBSupBy += child.text+'\n'
                        postSBSupByEO += getEO(child)+'\n'  
                    else:
                        supBy += child.text+'\n'
                        supByEO += getEO(child)+'\n'
                if child.tag == 'UWP':
                    if children[idx-1].tag != children[idx].tag and isPost:
                        postSBUWPart += 'POST: '+currPost + '\n'
                        postSBUWFig += 'POST: '+currPost + '\n'
                    if isPost:
                        postSBUWPart += child.text.split()[0]+'\n'
                        postSBUWFig += child.text.split()[1]+'\n'
                        postSBUWPartEO =  getEO(child)+'\n'   
                    else:
                        useWith += child.text.split()[0]+'\n'
                        useWithFig += child.text.split()[1]+'\n'
                        useWithEO += getEO(child)+'\n' 
                        
                if child.text == 'RWK FROM':
                    if children[idx-2].tag != children[idx].tag and isPost:
                        postSBRwkFrom += 'POST: '+currPost + '\n'
                    postSBRwkFrom += children[idx+1].text+'\n'
                    postSBRwkFromEO += getEO(child) 
                if child.text == 'RWK TO':  
                    if children[idx-2].tag != children[idx].tag and isPost:
                        postSBRwkTo += 'POST: '+currPost + '\n'
                    if isPost:
                        postSBRwkTo += children[idx+1].text+'\n'
                        postSBRwkToEO += getEO(child)+ '\n'
                    else:
                        rwkTo += children[idx+1].text+'\n'
                        rwkToEO +=getEO(child)+'\n'
            UPA = ''
            if element.find(".//UPA") != None:
                UPA = element.find(".//UPA").text
            
            data = [fig, revDate, item, partNum, effOn, usageCode, note, nomcltr, supCode, seeNHA,
            altPN, delBySBN, delBySBNEO, replBy, replByEO, totQty, supBy, supByEO, rwkTo,
            rwkToEO, useWith, useWithFig, useWithEO, RefSBN, RefSBNEO, postSBN, postSBNEO,
            postSBAPN,postSBRepBy, postSBRepByEO, postSBSupBy, postSBSupByEO, postSBRwkTo,
            postSBRwkToEO, postSBRwkFrom, postSBRwkFromEO, postSBForNHA, postSBForNHAEO,
            postSBUWPart, postSBUWFig, postSBUWPartEO, UPA]       
            zipObject = zip(CLM_NAMES,data)
            dictObj = dict(zipObject)
            df = df.append([dictObj],ignore_index=True)
    return df


## Function
## parameter: string -> urlKey
## returns: The engine model
def partListTitle(string):
    begin = string.find("MODEL=")+6
    end = string[begin:].find("&")
    return string[begin:begin+end]

## MAIN FUNCTION
## Runs through all URL Keys and gets df of each one downloading them
def main():
    for urlKey in URL_KEYS:
        partsInfo = itemLstInfoGetter(urlKey)
        path = os.path.join('..\\back-end\\data\\parts','partList_'+partListTitle(urlKey))
        partsInfo.to_csv(path+'.csv',index=False)

