#%%
## imports dependencies
## creates the EFF List and URL keys from Constants file
## creates the dictionary  needed for engineData
import json,os,re,Constants,copy
import pandas as pd
import numpy as np


with open('../back-end/Engines.txt','r') as inf:
    Engines = eval(inf.read())

EFF_LIST = Constants.effList()

engineInfo = copy.deepcopy(Engines['AllEngines'])
engineSource = copy.deepcopy(Engines['AllEngines'])
engineData = {
    'engineType':engineInfo,
    'tableInfo':engineSource
}

## HELPER FUNCTION to findColumn function
## parameter: ColumnName -> An array that contains the ColumnNames
## returns: Boolean if the column name contains an Effectivity
def findColumn(columnName):
    flag = False
    clnClmName = columnName.replace('-','')
    clmArr = clnClmName.split('_')
    for item in clmArr:
        if item.strip() in EFF_LIST:
            flag = True
    columnInfo = flag
    return columnInfo

## Function
## parameter: df -> the table from CSV
## returns: returns a column name that contains EFF
def getColumn(df):
    for col in df.columns:
        if findColumn(col):
            return col
    return 'Not Found'

## Helper Function to ShapeTable
## parameter: arr -> any array
## returns: The arr with empty cells filled with the last value
def ffill(arr):
    newArr = []
    placeHolder = ''
    for e in arr:
        if e != '':
            placeHolder = e
        newArr.append(placeHolder)
    return newArr

## Function
## parameter: directory -> a string either 'tables' or 'partList'
## returns: List with the file names of either tables or partList
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

## Helper Function
## parameter: s -> any character
## returns: Boolean whether or not a character is an Int or Not
def representsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

## Helper Function
## parameter: item-> the partNumber target, df-> the table of partList
## returns: A dictionary with a usage code and figure number
def itemLookUp(item,df):
    part = df[df['PART NUMBER'] == item]
    if len(part)==0:
        itemDict = {
        'usageCode':'',
        'figNum':''
        }
        return itemDict
    else:
        part = part.iloc[0]
    figNum = part[0]
    if isinstance(figNum,float):
        figNum = ''
    usageCode = part[5]
    if isinstance(usageCode,float):
        usageCode = ''
    itemDict = {
        'usageCode':usageCode,
        'figNum':figNum
    }
    return itemDict

## Function
## parameter: df -> a table csv of an EFF
## returns: df that is normalized
def reshapeTable(df,cl):
    partList = df[cl].to_list()
    partName = []
    partNumbers = []
    for part in partList:
        if part != '':
            if representsInt(part[0]):
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

## Helper Function to dictMaker
## parameter: df -> df from the dictMaker
## returns: a df that has been reshaped
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

## Helper Function to dictMaker
## parameter: df -> df from the dictMaker, keyDict which is tmp dict holder
## returns: reconfigures the dict to show notes
def noteFinder(df,keyDict):
    noteNames = ['note','NOTE']
    for cl in df.columns:
        if cl in noteNames:
            notes = df.groupby('Part Name')[cl].apply(list)
            for key, value in notes.items():
                for idx, val in enumerate(value,0):
                    if val != np.NaN and representsInt(val):
                        name = keyDict[key][idx]['name']
                        keyDict[key][idx]['name'] = name +'('+val+')'
    return keyDict
        
## Function
## parameter: csvFile -> contains the information of the Eff
## returns: a dictionary of the table information
def dictMaker(csvFile):
    path = os.path.join('..\\back-end\\data',csvFile)
    df = dfCleanUp(pd.read_csv(path, na_filter=False))
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    df.fillna(method='ffill', inplace=True)
    df.groupby(['Part Name'])
    partNumbers = df.groupby('Part Name')['Part Number'].apply(list)
    cycles = df.groupby('Part Name')[getColumn(df)].apply(list)
    keyDict=dict()
    for key, value in partNumbers.items():
        partsArr = []
        for idx,val in enumerate(value,0):
            if val.strip()[0]=='(':
                newName = value[idx-1]+val
                partsArr[len(partsArr)-1]['name']=newName
                continue
            currentPart ={
                            'name':val,
                            'partNumber':re.sub(r'\([^)]*\)','',val).strip(),
                            'cycles':cycles[key][idx]
                        }
            partsArr.append(currentPart)
        keyDict.update({re.sub(r'\([^)]*\)','',key):partsArr})
    keyDict = noteFinder(df,keyDict)
    return keyDict

## Function
## parameter: None
## returns: a Dict with keys being engTypes and values being df of partList
def partListGetter():
    partListDict = dict()
    for f in csvFiles('partList'):
        eng = f[f.find('_')+1:f.find('.')]
        path = os.path.join('..\\back-end\\data\\parts','partList_'+eng+'.csv')
        partListDict[eng]=pd.read_csv(path)
    return partListDict

## Function
## paramter: engineData-> dict with engine information
## returns: Nothing, adds to engineData dictionary LLP information
def llpInfoFiller():
    llpParts = {}
    partListDict = partListGetter()
    for engineType in engineData['engineType']:
        for model in engineData['engineType'][engineType]:
            for module in engineData['engineType'][engineType][model]:
                for partName in engineData['engineType'][engineType][model][module]:
                    for part in engineData['engineType'][engineType][model][module][partName]:
                        llpParts[part['partNumber']]=itemLookUp(part['partNumber'],partListDict[engineType])                        
    engineData['llpParts'] = llpParts

## Function
## parameter: engineData,Dict with all info
## returns: Nothing, saves engineData as a file in front-end
def saveToJSON():
    path = os.path.join('..\\front-end','engineData.json')
    with open(path, 'w') as outfile:
        json.dump(engineData, outfile, sort_keys=False, indent=4)

#%%
## MAIN FUNCTION
## Runs through all the csvFiles that are tables and fills engine data with information and saves it to front-end
def main():
    for f in csvFiles('tables'):
        fileDict = dictMaker(f)
        taskTitle = f[:f.find('-')]
        ataCode = f[f.find('-')+1:f.find('_')]
        key ='TKESM'+ ataCode.replace('-','')
        eff = f[f.find('_')+1:f.find('.')]
        effArr = eff.split('_')
        info = {
            'title':taskTitle,
            'key':key,
            'ataCode':ataCode
        }
        print(taskTitle,ataCode)
        for engType in engineInfo:
            for engineModel in engineInfo[engType]:
                if engineModel.replace('/','-') in effArr:
                    engineInfo[engType][engineModel][taskTitle] = fileDict
                    engineSource[engType][engineModel][taskTitle] = info
        
                    
    llpInfoFiller()
    saveToJSON()

#%%
main()

# %%
