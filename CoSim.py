import numpy as np
import jos3
import pandas as pd
import matplotlib.pyplot as plt
#import BerkeleyModel
import sys

""" 
Modification based on heat fluxes from CFD and evaporation from skin
    
"""
## Create human models
Driver=jos3.JOS3(height=1.8,weight=75,age=30,ex_output="all")


# Environmental condition setup according to the simulation
ambTemp = -10 #degC
radTemp = -10 #degC
ambRH = 70 #%

## Constant settings - Global variables
activityLevel = 1.6 # PAR

#Sim settings
dt = 1 #s
try:
    dtCFD = eval(sys.argv[1])
except:
    dtCFD = 0.05 #s


def clothingReq(Ta):
    if Ta <= -20:
        head = 0.
        shirt = 1.5
        pant = 1.5
        shoe = 0.2
        hand = 0.2
        
    elif Ta>-20 and Ta<=-10:
        head = 0.
        shirt = 1.3
        pant = 1.3
        shoe = 0.15
        hand = 0.15
        
    elif Ta > -10 and Ta<=0:
        head = 0.
        shirt = 0.9
        pant = 0.9
        shoe = 0.1
        hand = 0.1
        
    elif Ta>30:
        head = 0.
        shirt = 0.25
        pant = 0.25
        shoe = 0.05
        hand = 0.
    else:
        head = 0.
        shirt = 0.47
        pant = 0.4
        shoe = 0.08
        hand = 0.
    
    icl = [head,shirt,shirt,shirt,shirt*0.2+pant*1,shirt,shirt,hand,shirt,shirt,hand,pant,pant,shoe,pant,pant,shoe]  #clo
    return icl


#Driver settings
Driver.Icl=clothingReq(ambTemp)
Driver.PAR = activityLevel
Driver.posture='sitting'
soakTime = 5 # min

## Don't mess with me ##
sections=['head','face','neck','breathZone','chest','back','pelvis','lUArm',
            'rUArm','lLArm','rLArm','lHand','rHand','lThigh','rThigh','lCalf','rCalf','lFoot','rFoot']

sectionsJOS3 = ['Head', 'Neck', 'Chest', 'Back', 'Pelvis', 'LShoulder', 'LArm',
        'LHand', 'RShoulder', 'RArm', 'RHand', 'LThigh', 'LLeg', 'LFoot',
        'RThigh', 'RLeg', 'RFoot']

corrDictBerkToJOS={'head':'Head',
            'face':'Head',
            'neck':'Neck',
            'breathZone':'Head',
            'chest':'Chest',
            'back':'Back',
            'pelvis':'Pelvis',
            'lUArm':'LShoulder',
            'rUArm':'RShoulder',
            'lLArm':'LArm',
            'rLArm':'RArm',
            'lHand':'LHand',
            'rHand':'RHand',
            'lThigh':'LThigh',
            'rThigh':'RThigh',
            'lCalf':'LLeg',
            'rCalf':'RLeg',
            'lFoot':'LFoot',
            'rFoot':'RFoot'}

corrDictJOSToBerk={'Head':'head',
                   'Neck':'neck',
                   'Chest':'chest',
                   'Back':'back',
                   'Pelvis':'pelvis',
                   'LShoulder':'lUArm',
                   'LArm':'lLArm',
                   'LHand':'lHand',
                   'RShoulder':'rUArm',
                   'RArm':'rLArm',
                   'RHand':'rHand',
                   'LThigh':'lThigh',
                   'LLeg':'lCalf',
                   'LFoot':'lFoot',
                   'RThigh':'rThigh',
                   'RLeg':'rCalf',
                   'RFoot':'rFoot'}

## Function definitions
def InitSolution(model,ambTemp,velocity,radTemp,RH,time):
    """
    Generate initial skin temperature based on soaked conditions
    """
    model.Ta=ambTemp
    model.Va=velocity
    model.Tr=radTemp
    model.RH=RH
    model.simulate(1,time*60)
    model.simulate(1,dt)
    return model

def WriteToCSVForCFD(model,file,new,history):
    """
    Write solution to *.csv file based on the solution
    """
    df = pd.DataFrame(model.dict_results())
    df = df.drop(columns=['ModTime'])
    for col in df.columns:
        df=df.rename(columns={col:col+'(C)'})
    
    df = surfaceTemperatureForCFD(model,df,new)
    
    if new ==1:
        time = [-soakTime*60,0,dt]
        df.insert(loc=0,column='time(s)',value=time)
        df.to_csv(file+'.csv',index=0)
        
    else:
        time = [history['time(s)'].iloc[-1], history['time(s)'].iloc[-1]+dt]
        df.insert(loc=0,column='time(s)',value=time)
        history=history.append(df.iloc[-1])
        history.to_csv(file+'.csv',index=0)
        
def RenameColumnsCFD(case):
    """
    Renames columns from CFD exports
    """
    columnNames = case.columns
    columns=[columnNames[0]]
    for col in columnNames[1:]:
        colTemp = col.find(' Monitor')
        columns.append(col[:colTemp])
    
    columns=pd.Index(columns)
    case.columns=columns
    #case.rename(thCFD,axis='columns',inplace='True')
    
    return case

def surfaceTemperatureForCFD(model,df,new):
    """
    Compute the clothing temperature from skin temperature and heat flux.
    Additionally, compute the vapor flux based on the latent heat flux.
    """
    Tcl = []
    R_clothing = model.Icl*0.155    
    evaporationFlux = []  
    
    for i in range(len(sectionsJOS3)):
        #Q = (df['Tsk'+sectionsJOS3[i]+'(C)'].iloc[-2:]-model.Ta[i])/(R_clothing[i]+R_hc[i])
        Q = (df['SHLsk'+sectionsJOS3[i]+'(C)'].iloc[-2:])
        Tcl.append(df['Tsk'+sectionsJOS3[i]+'(C)'].iloc[-2:]-Q/Driver.BSA[i]*R_clothing[i])

        QEvap = (df['LHLsk'+sectionsJOS3[i]+'(C)'].iloc[-2:])/Driver.BSA[i]        
        evaporationFlux.append(QEvap/2418.7e3)
    for i in range(len(sectionsJOS3)):
        if new==1:
            clothTemp = [Tcl[i].iloc[0],Tcl[i].iloc[0],Tcl[i].iloc[1]]
            vaporationFlux = [evaporationFlux[i].iloc[0],evaporationFlux[i].iloc[0],evaporationFlux[i].iloc[1]]
        else:
            clothTemp = [Tcl[i].iloc[0],Tcl[i].iloc[1]]
            vaporationFlux = [evaporationFlux[i].iloc[0],evaporationFlux[i].iloc[1]]
        df.insert(loc=len(df.columns),column='Tcl'+sectionsJOS3[i]+'(C)',value=clothTemp)
        df.insert(loc=len(df.columns),column='mEvap'+sectionsJOS3[i]+'(kg/m^2-s)',value=vaporationFlux)
        
    return df

    


if __name__=='__main__':
    
    try:
        ## If the files are present, then load the CFD data and body temperature data        
        file=pd.read_csv('monitorData.csv')
        Driver.bodytemp=np.load('bodytempDriver.npy')        
        historyDriver=pd.read_csv('driver.csv')        
        print('Loaded data from CFD')
    except:
        ## If not, initialize the simulation with conditions: (model,Ta,va,Tr,RH,time(min)), save the skin temperature and bodytemp; exit
        print('Setting initial skin temperatures')
        Driver=InitSolution(Driver,ambTemp,0,radTemp,ambRH,soakTime)        
        WriteToCSVForCFD(Driver,'driver',1,None)        
        np.save('bodytempDriver.npy',Driver.bodytemp)        
        sys.exit()

    ## Rename CFD file columns
    file = RenameColumnsCFD(file)
    columns = file.columns

    # Set dictionaries for appropriate sections for air temperature, RH, heatFlux and operating temperatures
    tempLocalDriver = {}
    RHLocalDriver = {}
    heatFluxLocalDriver = {}
    toLocalDriver = {}
    
    if file[columns[0]].iloc[-1]>1.5:
        factor = 2
    else:
        factor = 1
    
    for col in file.columns:
        if col[:18]=='Temp_human.Driver_':
            tempLocalDriver[col[18:]]=file[col].rolling(int(dt/dtCFD)).mean().iloc[-1]-273.15                
        elif col[:16]=='RH_human.Driver_':
            RHLocalDriver[col[16:]]=file[col].rolling(int(dt/dtCFD)).mean().iloc[-1]     
        elif col[:22]=='heatFlux_human.Driver_':
            heatFluxLocalDriver[col[22:]]=file[col].rolling(int(dt/dtCFD)*factor).mean().iloc[-1]
        elif col[:16]=='To_human.Driver_':
            toLocalDriver[col[16:]] = file[col].rolling(int(dt/dtCFD)).mean().iloc[-1]-273.15
        
    ## Create lists of corresponding quantities in the right order
    taDriver = []
    rhDriver = []
    heatFluxDriver = []
    toDriver = []

    for val in sectionsJOS3:
        taDriver.append(tempLocalDriver[corrDictJOSToBerk[val]])
        rhDriver.append(RHLocalDriver[corrDictJOSToBerk[val]])
        heatFluxDriver.append(heatFluxLocalDriver[corrDictJOSToBerk[val]])
        toDriver.append(toLocalDriver[corrDictJOSToBerk[val]])
    
    Tcl=[]
    for i in range(len(sectionsJOS3)):
        Tcl.append(historyDriver['Tcl'+sectionsJOS3[i]+'(C)'].iloc[-1])
    
    ## Update conditions are the next timestep:
    Driver.Ta=taDriver    
    Driver.RH = rhDriver
    Driver._to = np.array(toDriver)
       
    ## Compute the overall thermal resistance between air and the skin
    r_t = abs((np.array(Tcl)-Driver._to)/np.array(heatFluxDriver))+Driver.Icl*0.155
    Driver._rt = r_t

    ## Set the heat transfer coefficient for estimations of evaporative resistance
    Driver._hc = 1/abs((np.array(Tcl)-Driver._to)/np.array(heatFluxDriver)) 

    
    print('Computing new skin temperatures...')
    ## simulate the human
    Driver.simulate(1,dt)    
    print('done')

    ## Write to disc for next iteration    
    print('Updating file...')
    WriteToCSVForCFD(Driver,'driver',0,historyDriver)    
    np.save('bodytempDriver.npy',Driver.bodytemp)
        

