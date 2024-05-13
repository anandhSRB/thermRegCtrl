#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 17:35:02 2022

@author: anandhr

Employs BerkeleyModel.py to compute comfort and sensation metrics based on UCB-Zhang model.
Use this file as a post processing step. 
 -Include the files monitorData.csv, and driver.csv in the same directory
 -Execute with 'python3 postComfort.py'


"""


import numpy as np
import matplotlib.pyplot as plt
import BerkeleyModel as ucb
import pandas as pd
import os
import matplotlib.ticker as ticker
plt.rcParams.update({'figure.dpi':300})
plt.rcParams.update({'font.size':12})

saveStates = True
colors = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00','#e6ab02','#a65628','#f781bf','#999999']
def RenameColumnsCFD(case):
    
    columnNames = case.columns
    columns=[columnNames[0]]
    for col in columnNames[1:]:
        colTemp = col.find(' Monitor')
        columns.append(col[:colTemp])
    
    columns=pd.Index(columns)
    case.columns=columns
    #case.rename(thCFD,axis='columns',inplace='True')
    return case

def TimeAvg(dF,columnID):
    dT = dF[dF.columns[0]].diff()
    Var = np.sum(dF[columnID]*dT)/dF[dF.columns[0]].iloc[-1]
    return Var
    
def TimeIntegral(dF,columnID):
    dT = dF[dF.columns[0]].diff()
    Var = np.sum(dF[dF.columns[columnID]]*dT)
    return Var

def getComfortDicts():
        
    sections=['head','face','neck','breathZone','chest','back','pelvis','lUArm',
                'rUArm','lLArm','rLArm','lHand','rHand','lThigh','rThigh','lCalf','rCalf','lFoot','rFoot']

    sectionsJOS3 = ['Head', 'Neck', 'Chest', 'Back', 'Pelvis', 'LShoulder', 'LArm',
            'LHand', 'RShoulder', 'RArm', 'RHand', 'LThigh', 'LLeg', 'LFoot',
            'RThigh', 'RLeg', 'RFoot']

    corrDict={'head':'Head',
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
    
    labels = {'head':'Head',
                'face':'Head',
                'neck':'Neck',
                'breathZone':'Head',
                'chest':'Chest',
                'back':'Back',
                'pelvis':'Pelvis',
                'lUArm':'L-Shoulder',
                'rUArm':'R-Shoulder',
                'lLArm':'L-Arm',
                'rLArm':'R-Arm',
                'lHand':'L-Hand',
                'rHand':'R-Hand',
                'lThigh':'L-Thigh',
                'rThigh':'R-Thigh',
                'lCalf':'L-Leg',
                'rCalf':'R-Leg',
                'lFoot':'L-Foot',
                'rFoot':'R-Foot'}
    return sections, sectionsJOS3, corrDict, labels


    
if __name__=='__main__':
        
    ## Import CFD data and human model
    cfd = pd.read_csv('monitorData.csv')
    driver = pd.read_csv('driver.csv')
    

    cfd = RenameColumnsCFD(cfd)
    columnsCFD = cfd.columns
    columnsJOS = driver.columns
    
    ## Inputs for ucb: tempLocal, dTempLocalDt, tempSkinMean, dTempCoreDt
    maxTime = driver['time(s)'].iloc[-1]
    dt = driver['dt(C)'].iloc[-1]
    dtCFD = cfd[columnsCFD[0]].diff().iloc[-1]
    driver = driver.drop(columns = ['Name(C)'])
    driver = driver.drop(columns=['Sex(C)'])
    dDriverDt = driver.diff()    
    
    sections, sectionsJOS3, corrDict, labels = getComfortDicts()    
    
    time = []
    driverOverallComfortHistory=[]    
    driverOverallSensationHistory=[]
    

    driverLocalSensationHistory = pd.DataFrame(columns=sections)
    driverLocalComfortHistory = pd.DataFrame(columns=sections)
    
    for i in range(2,int(maxTime/dt)+2):
        driverSkinMean = driver['TskMean(C)'].iloc[i]    
        driverSkin = {}
        dDriverSkinDt = {}
        dDriverCoreDt = {}

        for j in sections:
            driverSkin[j] = driver['Tsk'+corrDict[j]+'(C)'].iloc[i]
            dDriverSkinDt[j] = dDriverDt['Tsk'+corrDict[j]+'(C)'].iloc[i]/dt
            dDriverCoreDt[j] = dDriverDt['Tcr'+corrDict[j]+'(C)'].iloc[i]/dt
            
        
        DriverComfort = ucb.BerkeleyModel(driverSkin,driverSkinMean,dDriverSkinDt,dDriverCoreDt)

        
        driverOverallComfortHistory.append(DriverComfort.OverallComfort())
        driverOverallSensationHistory.append(DriverComfort.OverallSensation())
        
        driverLocalSensationHistory = pd.concat([driverLocalSensationHistory,pd.DataFrame([DriverComfort.LocalSensation().values()],columns=DriverComfort.LocalSensation().keys())])
        driverLocalComfortHistory = pd.concat([driverLocalComfortHistory,pd.DataFrame([DriverComfort.LocalComfort().values()],columns=DriverComfort.LocalComfort().keys())])
        
        time.append(driver['time(s)'].iloc[i])
    
    T_eq,setPoint = DriverComfort.T_eq()
    meanSkinSetPoint = sum(setPoint.values())/len(setPoint)
    
    ## Plots    
    try:
        os.mkdir('Plots')        
    except Exception:
        pass
    
    try:
        os.mkdir('Exports')
    except:
        pass
    
    if saveStates:
        
        overallComfortTemp = np.array(list(zip(time,driverOverallComfortHistory)))
        df = pd.DataFrame(overallComfortTemp, columns=['time','overallComfort'])
        df.to_csv('Exports/overallComfort.csv',index=0)
        
        overallSensationTemp = np.array(list(zip(time,driverOverallSensationHistory)))
        df = pd.DataFrame(overallSensationTemp, columns=['time','overallSensation'])
        df.to_csv('Exports/overallSensation.csv',index=0)
        
        driverLocalComfortHistory.insert(loc=0,column='time',value=time)
        driverLocalComfortHistory.to_csv('Exports/localComfortHistory.csv',index=0)
        
        driverLocalSensationHistory.insert(loc=0,column='time',value=time)
        driverLocalSensationHistory.to_csv('Exports/localSensationHistory.csv',index=0)
    
    time = np.array(time)
    # Overall Sensation
    fig, ax = plt.subplots(figsize=(5,4))
    ax.plot(time/60,driverOverallSensationHistory,label='Overall sensation',color=colors[0],alpha=0.8)
    ax.plot(time/60,driverOverallComfortHistory,label='Overall comfort',color=colors[1],alpha=0.8)
    ax.set_xlabel('Time (min)')
    ax.set_ylabel('Overall Sensation/Comfort (-)')
    plt.legend()
    plt.axis([None,None,-2,0])
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    plt.savefig('Plots/overallSensation.jpg',bbox_inches='tight')
    
    # Overall Comfort
    plt.figure(figsize=(5,4))
    plt.plot(time/60,driverOverallComfortHistory,label='Driver',color=colors[0],alpha=0.8)    
    plt.xlabel('Time (min)')
    plt.ylabel('Overall Comfort (-)')
    plt.legend()
    plt.savefig('Plots/overallComfort.jpg',bbox_inches='tight')
    
    localPlotSections = ['face','chest','neck','pelvis','rHand','lLArm','rThigh','lCalf','rFoot']
    # Local Sensation
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(time/60,driverLocalSensationHistory[localPlotSections[i]],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel('Local thermal Sensation (-)')
    plt.legend()
    plt.savefig('Plots/driverLocalSensation.jpg',bbox_inches='tight')
    
    
    #Local Comfort
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(time/60,driverLocalComfortHistory[localPlotSections[i]],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel('Driver Local Comfort (-)')
    plt.legend()
    plt.savefig('Plots/driverLocalComfort.jpg',bbox_inches='tight')
            
    
    # HTC
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(cfd[columnsCFD[0]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]/60,cfd['heatFlux_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r' Average heat flux (W/m²)')
    plt.legend()
    plt.savefig('Plots/driverHeatFlux.jpg',bbox_inches='tight')
        
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(cfd[columnsCFD[0]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]/60,cfd['radheatFlux_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r' Average radiation flux (W/m²)')
    #plt.legend()
    plt.savefig('Plots/driverRadHeatFlux.jpg',bbox_inches='tight')
    
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        totalFlux = cfd['heatFlux_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]-cfd['radheatFlux_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]
        plt.plot(cfd[columnsCFD[0]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]/60,totalFlux,label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r' Average convective flux (W/m²)')
    plt.legend()
    plt.savefig('Plots/driverConvHeatFlux.jpg',bbox_inches='tight')
    
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        totalFlux = abs(cfd['heatFlux_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]-cfd['radheatFlux_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)])+abs(cfd['radheatFlux_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)])
        plt.plot(cfd[columnsCFD[0]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]/60,abs(cfd['radheatFlux_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)])/totalFlux*100,label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r' Ratio of radiation to total heat flux (%)')
    plt.legend()
    plt.savefig('Plots/driverRadHeatFluxRatio.jpg',bbox_inches='tight')
    
    # HTC
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(cfd[columnsCFD[0]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]/60,cfd['RH_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r' Average RH (%)')
    plt.legend()
    plt.savefig('Plots/driverRH.jpg',bbox_inches='tight')
    
    # Skin Temperature
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(driver['time(s)'].iloc[1:]/60,driver['Tsk'+corrDict[localPlotSections[i]]+'(C)'].iloc[1:],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r'Skin temperature ($^\circ$C)')
    plt.legend()
    plt.axis([None,None,24,36])
    plt.savefig('Plots/driverSkinTemperature.jpg',bbox_inches='tight')
    
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(driver['time(s)'].iloc[1:]/60,driver['To'+corrDict[localPlotSections[i]]+'(C)'].iloc[1:],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r'Operating temperature ($^\circ$C)')
    plt.legend()
    #plt.axis([None,None,24,36])
    plt.savefig('Plots/driverOperatingTemperature.jpg',bbox_inches='tight')
    
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(driver['time(s)'].iloc[1:]/60,driver['mEvap'+corrDict[localPlotSections[i]]+'(kg/m^2-s)'].iloc[1:],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r'Vapor flux from skin ($(kg/m^2-s)$)')
    plt.legend()
    plt.savefig('Plots/driverEvaporation.jpg',bbox_inches='tight')
    
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(driver['time(s)'].iloc[1:]/60,driver['Tcl'+corrDict[localPlotSections[i]]+'(C)'].iloc[1:],label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r'Clothing temperature ($(^\circ)$C)')
    plt.legend()
    plt.savefig('Plots/driverClothTemp.jpg',bbox_inches='tight')
    
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(cfd[columnsCFD[0]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]/60,cfd['Tr_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]-273.15,label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r'Radiant temperature ($^\circ$C)')
    plt.legend()
    plt.savefig('Plots/driverReferenceTemperature.jpg',bbox_inches='tight')
    
    
    
    plt.figure(figsize=(5,4))
    for i in range(len(localPlotSections)):
        plt.plot(cfd[columnsCFD[0]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]/60,cfd['Temp_human.Driver_'+localPlotSections[i]].iloc[int(dt/dtCFD)-1::int(dt/dtCFD)]-273.15,label=labels[localPlotSections[i]],color=colors[i],alpha=0.8)
    plt.xlabel('Time (min)')
    plt.ylabel(r'Air temperature ($^\circ$C)')
    plt.legend()
    plt.savefig('Plots/driverAirTemperature.jpg',bbox_inches='tight')
    
    # del T| set_pt vs comfort & sensation
    # Overall metrics
    plt.figure(figsize=(5,4))
    plt.scatter(driver['TskMean(C)'].iloc[2:]-meanSkinSetPoint,driverOverallComfortHistory,label='Overall Comfort')
    plt.scatter(driver['TskMean(C)'].iloc[2:]-meanSkinSetPoint,driverOverallSensationHistory,label='Overall Sensation')
    plt.xlabel(r'$T-T_{set}$')
    plt.ylabel('Comfort/Sensation')
    plt.legend()
    plt.savefig('Plots/driverSetPt.jpg',bbox_inches='tight')
       
    
    #Local metrics
    for i in range(len(localPlotSections)):
        plt.figure(figsize=(5,4))
        plt.scatter(driver['Tsk'+corrDict[localPlotSections[i]]+'(C)'].iloc[2:]-setPoint[localPlotSections[i]],driverLocalComfortHistory[localPlotSections[i]],label=labels[localPlotSections[i]]+' Comfort',color=colors[i],alpha=0.8)
        plt.scatter(driver['Tsk'+corrDict[localPlotSections[i]]+'(C)'].iloc[2:]-setPoint[localPlotSections[i]],driverLocalSensationHistory[localPlotSections[i]],label=labels[localPlotSections[i]]+' Sensation',color=colors[i],alpha=0.8,marker='^')
        plt.xlabel(r'$T-T_{set,l}$')
        plt.ylabel('Comfort/Sensation')
        plt.legend()
        plt.savefig('Plots/driver'+corrDict[localPlotSections[i]]+'setPtComp.jpg',bbox_inches='tight')
    
        
    
    
    
    
    
    
