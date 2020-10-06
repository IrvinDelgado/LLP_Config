#%%
## imports dependencies
## CREATING THE DATAFRAMES
import json,os,re,Constants
import pandas as pd
import numpy as np
from pyutils import get_auth, get_engine, CSpinner

with open('../back-end/Engines.txt','r') as inf:
    Engines = eval(inf.read())

Engine_List = Engines['AllEngines']
EFF_LIST = Constants.effList()

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

def CLEAN_DF(df):
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
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    df = stageDiskCorrector(df)
    df.fillna(method='ffill', inplace=True)
    df.groupby(['Part Name'])
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


## Function
## parameter: file name
## returns: An array with information derived from file name
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
        ## Get File Information
        fileInfo = fileInfoGetter(csvFile)
        ENGINEMODULE = fileInfo[0]
        effArr = fileInfo[3]
        ENGINETYPE = fileInfo[4]

        ## Set up the DF for the file being inspected
        path = os.path.join('..\\back-end\\data',csvFile)
        df = CLEAN_DF(pd.read_csv(path, na_filter=False))

        ## Get a list for each column and prep for unique LLP's
        PARTTITLE = df['Part Name']
        PARTTEXT = df['Part Number']
        cycles = df[getColumn(df)]
        LLP_UNIQUE = set()

        ## Get the pure number since some might be in format ####(String)
        ## This will help in creating a list for the unique LLP's
        for part in PARTTEXT:#Since partNumber is a grouped list
            pureNumber = re.sub(r'\([^)]*\)','',part).strip()
            LLP_UNIQUE.add(pureNumber)

        ## Each file might reference multiple models
        ## Place information of row for each model
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

#%% Prepping Data for SQL Transfer
TABLE_INFO = Table_Info_Filler() 
DF_LIST = Engine_Data_And_Parts_Filler()
ENGINE_DATA = DF_LIST[0]
PARTS_DATA = DF_LIST[1]

TABLE_INFO.drop_duplicates(inplace=True)
ENGINE_DATA.drop_duplicates(inplace=True)
PARTS_DATA.drop_duplicates(inplace=True)

#%% SQL REPLACE DATATABLE WITH NEW DATA
u,p = get_auth('edtdpap1Fun1')
eng = get_engine(u, p, 'EDTDPAP1.aa.com', u)

eng.execute('DELETE FROM *')
TABLE_INFO.to_sql(
    name='BT_LLP_TABLE_INFO',
    con=eng,
    index=False,
    if_exists='append',
    schema='*')

eng.execute('DELETE FROM *')
ENGINE_DATA.to_sql(
    name='BT_LLP_ENGINE_DATA',
    con=eng,
    index=False,
    if_exists='append',
    schema='*')

eng.execute('DELETE FROM *')
PARTS_DATA.to_sql(
    name='BT_LLP_PARTS',
    con=eng,
    index=False,
    if_exists='append',
    schema='*')

eng.dispose()



#%%  
