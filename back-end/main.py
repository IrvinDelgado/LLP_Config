#%%
from lxml import etree
from bs4 import BeautifulSoup
import requests,re,os
import pandas as pd
import numpy as np
from pyutils import get_auth, get_engine, CSpinner

# EIPC_Scraper
# EM_Scraper
# DATA_Maker


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

## Function
## parameter: string -> urlKey
## returns: The engine model
def partListTitle(string):
    begin = string.find("MODEL=")+6
    end = string[begin:].find("&")
    return string[begin:begin+end]



def effList():
    EFF_LIST=[]
    with open('../back-end/Engines.txt','r') as inf:
        Engines = eval(inf.read())
    for engType in Engines['AllEngines']:
        for engineModel in Engines['AllEngines'][engType]:
            EFF_LIST.append(engineModel)
    return EFF_LIST


#   The parameter could only take the following EM or EIPC
def urlGen(emanual):
    urlArr = []
    with open('../back-end/Engines.txt','r') as inf:
        Engines = eval(inf.read())
    for engType in Engines['Keys'][emanual]:
        urlArr.append(Engines['Keys'][emanual][engType])
    return urlArr

EFF_LIST = effList()

##-----------------------------------------------------------------------  EIPC FUNCTIONS
#%%

URL_KEYS_EIPC = urlGen("EIPC")

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



##-----------------------------------------------------------------EM Scraper
#%%

URL_KEYS_EM = urlGen("EM")

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
## returns: nothing, downloads the csv file to back-end\data
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




#----------------------------------------------------------------------------------------dataMaker
#%%

with open('../back-end/Engines.txt','r') as inf:
    Engines = eval(inf.read())

Engine_List = Engines['AllEngines']

Engine_Data_Clmn_Names = ["ENGINETYPE","ENGINEMODEL","ENGINEMODULE","PARTTITLE","PARTTEXT","PARTCYCLE"]
Table_Info_Clmn_Names = ["ENGINETYPE","ENGINEMODEL","ENGINEMODULE","TABLEKEY","TABLEATACODE","TABLENOTES"]
Parts_Clmn_Names = ["PARTNUMBER","USAGECODE","FIGNUM"]

def partListGetter():
    partListDict = dict()
    for f in csvFiles('partList'):
        eng = f[f.find('_')+1:f.find('.')]
        path = os.path.join('..\\back-end\\data\\parts','partList_'+eng+'.csv')
        partListDict[eng]=pd.read_csv(path)
    return partListDict

def partListGetter():
    partListDict = dict()
    for f in csvFiles('partList'):
        eng = f[f.find('_')+1:f.find('.')]
        path = os.path.join('..\\back-end\\data\\parts','partList_'+eng+'.csv')
        partListDict[eng]=pd.read_csv(path)
    return partListDict

def csvFiles(directory):
    if directory == 'tables':
        fileNames = os.listdir('..\\back-end\\data')
    elif directory == 'partList':
        fileNames = os.listdir('..\\back-end\\data\\parts')
    csvFiles = []
    for fileName in fileNames:
        if '.csv' in fileName:
            csvFiles.append(fileName)
    return csvFiles

def ffill(arr):
    newArr = []
    placeHolder = ''
    for e in arr:
        if e != '':
            placeHolder = e
        newArr.append(placeHolder)
    return newArr

def stageDiskCorrector(df):
    for e in df['Part Name']:
        stages = ['Stage 1','Stage 2','Stage 3','Stage 4']
        if e in stages:
            for stage in stages:
                df.replace(stage, stage + ' Disk', inplace=True)
        df.replace('Disk', np.nan, inplace=True)
    return df

def findEngineType(engineModel):
    for engineType in Engine_List:
        if engineModel.replace('-','/') in Engine_List[engineType]:
            return engineType

def findColumn(columnName):
    flag = False
    clnClmName = columnName.replace('-','')
    clmArr = clnClmName.split('_')
    for item in clmArr:
        if item.strip() in EFF_LIST:
            flag = True
    columnInfo = flag
    return columnInfo

def getColumn(df):
    for col in df.columns:
        if findColumn(col):
            return col
    return 'Not Found'

def representsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def reshapeTable(df,cl):
    partList = df[cl].to_list()
    partName = []
    partNumbers = []
    for part in partList:
        if part != '' and representsInt(part[0]):
            partNumbers.append(part)
            partName.append('')
        else:
            if len(partName) != 0:
                partName.pop()
            if part[0]=='(':
                partWNote = partNumbers[len(partNumbers)-1]
                partNumbers[len(partNumbers)-1] = partWNote + part
                partName.append('')
            else:
                partName.append(part)
    partName.pop()
    columnName = getColumn(df)
    cycles = df[columnName].to_list()
    cycleArr = []
    for cycle in cycles:
        if cycle != '':
            cycleArr.append(cycle)
    return pd.DataFrame({'Part Name':ffill(partName),'Part Number':partNumbers,columnName:cycleArr})

def dfCleanUp(df):
    lastRow = df.iloc[-1].to_list()
    cnt=0
    for cell in lastRow:
        if cell != '':
            cnt+=1
    if cnt <=1:
        df = df.drop(len(df.index)-1)
    clNames = ['Part Name and Number', 'Part Name and Part Number']
    for cl in df.columns:
        if cl in clNames:
            df = reshapeTable(df,cl)
    return df

def itemLookUp(item,df):
    part = df[df['PART NUMBER'] == item]
    if len(part)==0:
        return ['','']
    part = part.iloc[0]
    figNum = part[0]
    usageCode = part[5]
    if isinstance(figNum,float):
        figNum = ''
    if isinstance(usageCode,float):
        usageCode = ''
    return [usageCode,figNum]

def fileInfoGetter(f):
    ENGINEMODULE = f[:f.find('-')]
    TABLEATACODE = f[f.find('-')+1:f.find('_')]
    TABLEKEY ='TKESM'+ TABLEATACODE.replace('-','')
    effString = f[f.find('_')+1:f.find('.')]
    effArr = effString.split('_')
    ENGINETYPE = findEngineType(effArr[0])
    return[ENGINEMODULE,TABLEATACODE,TABLEKEY,effArr,ENGINETYPE]


def Table_Info_Filler():
    Table_Info_DF = pd.DataFrame(columns = Table_Info_Clmn_Names)
    for f in csvFiles('tables'):
        fileInfo = fileInfoGetter(f)
        ENGINEMODULE = fileInfo[0],
        TABLEATACODE = fileInfo[1]
        TABLEKEY = fileInfo[2]
        effArr = fileInfo[3]
        ENGINETYPE = fileInfo[4]
        with open('../back-end/data/notes/'+TABLEATACODE+'.txt','r') as inf:
            TABLENOTES = inf.read()
        for ENGINEMODEL in effArr:
            data = [ENGINETYPE,ENGINEMODEL,ENGINEMODULE,TABLEKEY,TABLEATACODE,TABLENOTES]       
            zipObject = zip(Table_Info_Clmn_Names,data)
            dictObj = dict(zipObject)
            Table_Info_DF = Table_Info_DF.append([dictObj],ignore_index=True)
    return Table_Info_DF


##THIS FUNCTION IS EMBEDDED INTO THE ENGINE_DATA_FILLER()
def Parts_Filler(LLP_SET,ENGINETYPE):
    Parts_DF = pd.DataFrame(columns = Parts_Clmn_Names)
    partListDict = partListGetter()
    for partNumber in LLP_SET:
        itemInfo = itemLookUp(partNumber,partListDict[ENGINETYPE])
        data = [partNumber,itemInfo[0],itemInfo[1]]
        zipObject = zip(Parts_Clmn_Names,data)
        dictObj = dict(zipObject)
        Parts_DF = Parts_DF.append([dictObj],ignore_index=True)
    return Parts_DF

def Engine_Data_And_Parts_Filler():
    Engine_Data_DF = pd.DataFrame(columns = Engine_Data_Clmn_Names)
    Parts_DF_Arr = []
    for csvFile in csvFiles('tables'):
        fileInfo = fileInfoGetter(csvFile)
        ENGINEMODULE = fileInfo[0]
        effArr = fileInfo[3]
        ENGINETYPE = fileInfo[4]
        path = os.path.join('..\\back-end\\data',csvFile)
        df = dfCleanUp(pd.read_csv(path, na_filter=False))
        df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
        df = stageDiskCorrector(df)
        df.fillna(method='ffill', inplace=True)
        df.groupby(['Part Name'])
        PARTTITLE = df['Part Name']
        PARTTEXT = df['Part Number']
        cycles = df[getColumn(df)]
        LLP_UNIQUE = set()
        for part in PARTTEXT:#Since partNumber is a grouped list
            pureNumber = re.sub(r'\([^)]*\)','',part).strip()
            LLP_UNIQUE.add(pureNumber)
        for ENGINEMODEL in effArr:
            for i in range(len(PARTTEXT)):
                data = [ENGINETYPE,ENGINEMODEL,ENGINEMODULE,PARTTITLE[i],PARTTEXT[i],cycles[i]]
                zipObject = zip(Engine_Data_Clmn_Names,data)
                dictObj = dict(zipObject)
                Engine_Data_DF = Engine_Data_DF.append([dictObj],ignore_index=True)
        Parts_DF_Arr.append(Parts_Filler(LLP_UNIQUE,ENGINETYPE))
    Parts_DF = pd.concat(Parts_DF_Arr).drop_duplicates()
    Parts_DF.reset_index(drop=True, inplace=True)
    return [Engine_Data_DF,Parts_DF]

#%%
## 
def EIPC_Scraper():
    for urlKey in URL_KEYS_EIPC:
        partsInfo = itemLstInfoGetter(urlKey)
        path = os.path.join('..\\back-end\\data\\parts','partList_'+partListTitle(urlKey))
        partsInfo.to_csv(path+'.csv',index=False)
##
def EM_Scraper():
    for urlKey in URL_KEYS_EM:
        key = urlKey.replace("CHANGEHERE","LEA")
        leaXML = htmlToXML(key)
        llpFinder(leaXML,urlKey)


#%%
TABLE_INFO = Table_Info_Filler()
DF_LIST = Engine_Data_And_Parts_Filler()
ENGINE_DATA = DF_LIST[0]
PARTS_DATA = DF_LIST[1]

TABLE_INFO.drop_duplicates(inplace=True)
ENGINE_DATA.drop_duplicates(inplace=True)
PARTS_DATA.drop_duplicates(inplace=True)
#%%


#%% SQL REPLACE DATATABLE WITH NEW DATA
u,p = get_auth('')
eng = get_engine(u, p, '', u)

eng.execute('DELETE FROM PROD_TECHOPS_SNBX_DB.BT_LLP_TABLE_INFO')
TABLE_INFO.to_sql(
    name='BT_LLP_TABLE_INFO',
    con=eng,
    index=False,
    if_exists='append',
    schema='PROD_TECHOPS_SNBX_DB')

eng.execute('DELETE FROM PROD_TECHOPS_SNBX_DB.BT_LLP_ENGINE_DATA')
ENGINE_DATA.to_sql(
    name='BT_LLP_ENGINE_DATA',
    con=eng,
    index=False,
    if_exists='append',
    schema='PROD_TECHOPS_SNBX_DB')

eng.execute('DELETE FROM PROD_TECHOPS_SNBX_DB.BT_LLP_PARTS')
PARTS_DATA.to_sql(
    name='BT_LLP_PARTS',
    con=eng,
    index=False,
    if_exists='append',
    schema='PROD_TECHOPS_SNBX_DB')

eng.dispose()



#%%  