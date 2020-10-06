#%%
## imports dependencies
from lxml import etree
from bs4 import BeautifulSoup
import requests,re,os,Constants
import pandas as pd

EFF_LIST = Constants.effList()
URL_KEYS = Constants.urlGen("EM")

##---------------------------------------HELPER FUNCTIONS

## Function
## parameter: a url
## returns: XML, converted from the url
def htmlToXML(URL):
    r = requests.get(URL).text
    cleaner = re.sub('&nbsp;',' ',r)
    cleantext = BeautifulSoup(cleaner,"lxml").text
    begin = cleantext.find('<?xml')
    xml = etree.fromstring(cleantext[begin:])
    return xml  

## Function Helper to CSV Maker
## parameter: pageList -> an xml
## returns: List of columnNames from the xml
def columnNameGen(pageList): 
    columnNames = []
    for header in pageList.iter("THEAD"):
        for clmName in header.iter("TH"):
            if clmName.get("COLSPAN") == None and clmName.text!='&#160;':
                etree.strip_tags(clmName,'P')
                cleanedClm = re.sub('\n','_',clmName.text.strip())
                if cleanedClm != '&#160;' and cleanedClm != '_' and cleanedClm != '':
                    columnNames.append(cleanedClm.strip())
    return columnNames

## Function Helper to CSV Maker
## parameter: columnNames -> list of column Names
## returns: [boolean-> checks if the table contains EFF of AA, eff-> the eff that it contains]
def checkTable(columnNames):
    flag = False
    eff = []
    for clmName in columnNames:
        clnClmName = clmName.replace('-','')
        clmArr = clnClmName.split('_')
        for item in clmArr:
            if item.strip() in EFF_LIST:
                flag = True
                eff.append(item.strip().replace("/","-"))
    tableInfo = [flag,eff]
    return tableInfo

## Function Helper to llpFinder
## parameter: notes-> list of notes, fileTitle-> the title of the file
## returns: nothing, loads to the notes to folder notes
def noteMaker(notes,fileTitle):    
    file1 = open("..\\back-end\\data\\notes\\"+fileTitle+".txt","w")
    for note in notes:
        file1.write(note.text)
        file1.write('\n')
    file1.close

def partListTitle(string):
    begin = string.find("MODEL=")+6
    end = string[begin:].find("&")
    return string[begin:begin+end]
##---------------------------------------EM FUNCTIONS

## Function 
## parameter: tocXML -> xml of LEA ,urlKey -> the base key to use to traverse EM 
## returns: nothing, crawls through EM searching for LLP by title having '- LIFE LIMITS'
def llpFinder(tocXML,urlKey):  
    for element in tocXML.iter("CHILD"):
        elementsRefKey = element.get("REFKEY")
        if elementsRefKey == "LEA_CHAPTER_05_1":
            chptUrl = urlKey.replace("CHANGEHERE",elementsRefKey)
            chptXML = htmlToXML(chptUrl)
            for elem in chptXML.iter("ENTRY"):                
                title = elem.find("TITLE").text
                fileTitle = elem.get("ATACODE")
                isLifeLimits = False
                if title != None:
                    if re.search('- LIFE LIMITS',title) or re.search('-LIFE LIMITS',title):
                        isLifeLimits = True
                if elem.get("TAG")=="TASK" and isLifeLimits:
                    elemsRefKey = elem.get("KEY")
                    llpUrl = urlKey.replace("CHANGEHERE",elemsRefKey)
                    llpFile = htmlToXML(llpUrl)
                    csvFileTitle = title[:title.find('-')]+'-'+fileTitle
                    notes = llpFile.xpath('//NOTE')
                    if notes != None:
                        noteMaker(notes,fileTitle)
                    if partListTitle(urlKey) =='CFM56-5B' and fileTitle[-1]=='N':
                        csvMaker(llpFile,csvFileTitle)
                    elif partListTitle(urlKey) !='CFM56-5B':
                        csvMaker(llpFile,csvFileTitle)

## Function
## paramter: llpFile-> the xml of the llp, csvFileTitle -> from the llpFinder contains the title for csv
## returns: nothing, downloads the csv file to directory back-end\data
def csvMaker(llpFile,csvFileTitle): 
    for table in llpFile.iter("TABLE"):
        columnNames = columnNameGen(table)
        tableInfo = checkTable(columnNames)
        if tableInfo[0]:   
            df = pd.DataFrame(columns = columnNames)
            tableBody = table.find('TBODY')
            for tr in tableBody.iter("TR"): 
                rowData = []
                for td in tr.iter("TD"):           
                    colArr = []
                    col = td.findall("P")
                    for p in col:
                        if p.text != None:
                            colArr.append(p.text.strip())
                    rowData.append(colArr)
                maxLen = max(len(i) for i in rowData) #normalize data since some 
                for arr in rowData:
                    while len(arr)<maxLen:
                        arr.append('')
                for i in range(0,maxLen):
                    row = [ item[i] for item in rowData] #
                    zipObject = zip(columnNames,row)
                    dictObj = dict(zipObject)
                    df = df.append([dictObj],ignore_index=True)
            eff = '_'.join(tableInfo[1])
            csvTitle = csvFileTitle+'_'+eff
            path = os.path.join('..\\back-end\\data',csvTitle)
            df.to_csv(path+'.csv',index=False)             

## MAIN FUNCTION
## parameter: None
## returns: nothing, crawls through EM of Engine downloading tables
def main():
    for urlKey in URL_KEYS:
        key = urlKey.replace("CHANGEHERE","LEA")
        leaXML = htmlToXML(key)
        llpFinder(leaXML,urlKey)

# %%
main()

# %%
