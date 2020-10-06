#%%
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

# %%
#  
# %%
