#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 17:35:02 2022

@author: anandhr

Class: BerkeleyModel; TestModel using testModel()

Description: Based on the Zhang UCB model [2003].
             T_local_set is based on JOS-3 for local segments.
             
Inputs: tempLocal,tempMean,d(tempLocal)/dt,d(tempCore)/dt

Methods: LocalSensation, OverallSensation, LocalComfort, OverallComfort.
                
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from operator import itemgetter
import random as rand
import time

class BerkeleyModel:
    """
    Class definition    
    """
    def __init__(self,tempLocal,tSkinMean,dTempLocalDt,dTempCoreDt):
        self._tempLocal=tempLocal
        self._tSkinMean=tSkinMean
        self._dTempLocalDt=dTempLocalDt
        self._dTempCoreDt=dTempCoreDt
        
        
       
    def T_eq(self):
        """
        Temperatures to define local set temperatures

        Returns
        -------
        Teq : TYPE
            DESCRIPTION.
        T_local_set : TYPE
            DESCRIPTION.

        """
        Teq = {'body':22.8,
               'head':19.8,
               'face':19.8,
               'chest':21,
               'uBack':21,
               'lUArm':19.5,
               'rUArm':19.5,
               'lLArm':19.5,
               'rLArm':19.5,
               'lHand':22.5,
               'rHand':22.5,
               'lThigh':24.5,
               'rThigh':24.5,
               'lCalf':24.5,
               'rCalf':24.5,
               'lFoot':24.5,
               'rFoot':24.5,
               'lBack':23,
               'seat':23}
        
        T_local_set = {'head':34.94932,
                       'face':34.94932,
                       'neck':34.04004,
                       'breathZone':34.94932,
                       'chest':34.66184,
                       'back':34.5771,
                       'pelvis':35.83006,
                       'lUArm':34.30318,
                       'rUArm':34.30318,
                       'lLArm':33.91815,
                       'rLArm':33.91815,
                       'lHand':34.32792,
                       'rHand':34.32792,
                       'lThigh':34.21247,
                       'rThigh':34.21247,
                       'lCalf':34.01645,
                       'rCalf':34.01645,
                       'lFoot':34.15202,
                       'rFoot':34.15202}
        return Teq,T_local_set
    
    
    
    
    def localStatic(self):
        """
        Local static sensation based on local set temperatures, mean skin temperatures

        Returns
        -------
        localSensationStatic : Local sensation [-4,4]; where -4 is very cold and 4 is very hot

        """
        Teq,tempLocalSet = self.T_eq()
        tempMeanSet = sum(tempLocalSet.values())/len(tempLocalSet)
        sections=tempLocalSet.keys()
        deltaT_Static={}
        for i in sections:
            deltaT_Static[i] = self._tempLocal[i]-tempLocalSet[i]
        C1,K1=self.StaticCoeff(deltaT_Static)
        localSensationStatic={}
        for i in sections:    
            localSensationStatic[i] = 4*(2/(1+np.exp(-C1[i]*(self._tempLocal[i]-tempLocalSet[i])-K1[i]*(self._tempLocal[i]-tempLocalSet[i]-(self._tSkinMean-tempMeanSet))))-1)
        return localSensationStatic
        
    def StaticCoeff(self,deltaT_static):
        """
        Regression coefficients for static sensation

        Parameters
        ----------
        deltaT_static : difference in local temperatures and local set temperature

        Returns
        -------
        C1, K1 

        """
        C1_low = {'head':0.38,
                  'face':0.15,
                  'neck':0.4,
                  'breathZone':0.1,
                  'chest':0.35,
                  'back':0.3,
                  'pelvis':0.2,
                  'lUArm':0.29,
                  'rUArm':0.29,
                  'lLArm':0.3,
                  'rLArm':0.3,
                  'lHand':0.2,
                  'rHand':0.2,
                  'lThigh':0.2,
                  'rThigh':0.2,
                  'lCalf':0.29,
                  'rCalf':0.29,
                  'lFoot':0.25,
                  'rFoot':0.25}
        
        K1_low = {'head':0.18,
                  'face':0.1,
                  'neck':0.15,
                  'breathZone':0.2,
                  'chest':0.1,
                  'back':0.1,
                  'pelvis':0.15,
                  'lUArm':0.1,
                  'rUArm':0.1,
                  'lLArm':0.1,
                  'rLArm':0.1,
                  'lHand':0.15,
                  'rHand':0.15,
                  'lThigh':0.11,
                  'rThigh':0.11,
                  'lCalf':0.1,
                  'rCalf':0.1,
                  'lFoot':0.15,
                  'rFoot':0.15}
        
        C1_high = {'head':1.32,
                  'face':0.7,
                  'neck':1.25,
                  'breathZone':0.6,
                  'chest':0.6,
                  'back':0.7,
                  'pelvis':0.4,
                  'lUArm':0.4,
                  'rUArm':0.4,
                  'lLArm':0.7,
                  'rLArm':0.7,
                  'lHand':0.45,
                  'rHand':0.45,
                  'lThigh':0.29,
                  'rThigh':0.29,
                  'lCalf':0.4,
                  'rCalf':0.4,
                  'lFoot':0.26,
                  'rFoot':0.26}
        
        K1_high = K1_low  
        
        
        C1={}
        K1={}
        for i in deltaT_static.keys():
            if deltaT_static[i]<0:
                C1[i]=C1_low[i]
                K1[i]=K1_low[i]
            else:
                C1[i]=C1_high[i]
                K1[i]=K1_high[i]
                
        return C1,K1
    
    def DynamicSensation(self):
        """
        Dynamic local sensation based on rate of change of temperatures

        Returns
        -------
        dynamicSensation

        """
        A_minus={'head':543,
                  'face':37,
                  'neck':173,
                  'breathZone':68,
                  'chest':39,
                  'back':88,
                  'pelvis':75,
                  'lUArm':156,
                  'rUArm':156,
                  'lLArm':144,
                  'rLArm':144,
                  'lHand':19,
                  'rHand':19,
                  'lThigh':151,
                  'rThigh':151,
                  'lCalf':206,
                  'rCalf':206,
                  'lFoot':109,
                  'rFoot':109}
        B_plus={'head':90,
                  'face':105,
                  'neck':217,
                  'breathZone':741,
                  'chest':136,
                  'back':192,
                  'pelvis':137,
                  'lUArm':167,
                  'rUArm':167,
                  'lLArm':125,
                  'rLArm':125,
                  'lHand':46,
                  'rHand':46,
                  'lThigh':263,
                  'rThigh':263,
                  'lCalf':212,
                  'rCalf':212,
                  'lFoot':162,
                  'rFoot':162}
        C_plus={'head':0,
                  'face':-2289,
                  'neck':0,
                  'breathZone':0,
                  'chest':-2135,
                  'back':-4054,
                  'pelvis':-5053,
                  'lUArm':0,
                  'rUArm':0,
                  'lLArm':0,
                  'rLArm':0,
                  'lHand':0,
                  'rHand':0,
                  'lThigh':0,
                  'rThigh':0,
                  'lCalf':0,
                  'rCalf':0,
                  'lFoot':0,
                  'rFoot':0}
        
        dynamicSensation={}
        for i in self._dTempLocalDt.keys():
            if self._dTempLocalDt[i]<=0:
                dTdtMinus=self._dTempLocalDt[i]
                dTdtPlus=0
            else:
                dTdtMinus=0
                dTdtPlus=self._dTempLocalDt[i]
            dCoreDt = self._dTempCoreDt[i]
                
            dynamicSensation[i]=A_minus[i]*dTdtMinus+B_plus[i]*dTdtPlus+C_plus[i]*dCoreDt
            
        return dynamicSensation
    
    def LocalSensation(self):
        """
        Local sensation as the sum of static and dynamic local sensations constained to [-4,4]

        Returns
        -------
        localSensation 

        """
        localSensationStatic = self.localStatic()
        localSensationDynamic = self.DynamicSensation()
        localSensation={}
        for i in localSensationStatic.keys():
            sensation = localSensationStatic[i]+localSensationDynamic[i]
            if sensation<-4:
                localSensation[i] = -4
            elif sensation>4:
                localSensation[i] = 4
            else:
                localSensation[i] = sensation
        
        return localSensation
        
    def OverallSensation(self): 
        """
        Overall sensation obtained as a weighted sum of local sensations

        Returns
        -------
        overallSensation 

        """
        localSensation=self.LocalSensation()
        meanSensation=np.mean(list(localSensation.values()))
        
        a1={'head':0.13,
            'face':0.15,
            'neck':0.13,
            'breathZone':0.16,
            'chest':0.23,
            'back':0.23,
            'pelvis':0.17,
            'lUArm':0.1,
            'rUArm':0.1,
            'lLArm':0.1,
            'rLArm':0.1,
            'lHand':0.04,
            'rHand':0.04,
            'lThigh':0.13,
            'rThigh':0.13,
            'lCalf':0.13,
            'rCalf':0.13,
            'lFoot':0.09,
            'rFoot':0.09}
        
        a2={'head':0.21,
            'face':0.3,
            'neck':0.23,
            'breathZone':0.19,
            'chest':0.23,
            'back':0.24,
            'pelvis':0.15,
            'lUArm':0.14,
            'rUArm':0.14,
            'lLArm':0.14,
            'rLArm':0.14,
            'lHand':0.04,
            'rHand':0.04,
            'lThigh':0.26,
            'rThigh':0.26,
            'lCalf':0.26,
            'rCalf':0.26,
            'lFoot':0.14,
            'rFoot':0.14}
        
        
        weights={}
        for i in localSensation.keys():
            if (localSensation[i]-meanSensation)<=0:
                a=-a1[i]
                
            else:
                
                a=a2[i]
            weights[i]=a*(localSensation[i]-meanSensation)
        
        overallSensation=0
        for i in weights.keys():
            overallSensation=overallSensation+(weights[i]*localSensation[i])
        overallSensation=overallSensation/(np.sum(list(weights.values())))
        
        return overallSensation
    
    def LocalComfort(self):
        """
        Local comfort

        Returns
        -------
        localComfort : TYPE
            DESCRIPTION.

        """
        overallSensation=self.OverallSensation()
        localSensation=self.LocalSensation()
        
        C31={'head':0,
             'face':-0.11,
             'neck':0,
             'breathZone':0,
             'back':-0.5,
             'chest':-1.07,
             'pelvis':-1,
             'lUArm':-0.43,
             'rUArm':-0.43,
             'lLArm':-1.64,
             'rLArm':-1.64,
             'lHand':-0.8,
             'rHand':-0.8,
             'lThigh':0,
             'rThigh':0,
             'lCalf':-1,
             'rCalf':-1,
             'lFoot':-2.31,
             'rFoot':-2.31}
        
        C32={'head':1.39,
             'face':0.11,
             'neck':0,
             'breathZone':0.62,
             'back':0.59,
             'chest':0,
             'pelvis':0.38,
             'lUArm':0,
             'rUArm':0,
             'lLArm':0.34,
             'rLArm':0.34,
             'lHand':0.8,
             'rHand':0.8,
             'lThigh':0,
             'rThigh':0,
             'lCalf':1.5,
             'rCalf':1.5,
             'lFoot':0.21,
             'rFoot': 0.21 }
        
        C6={'head':1.27,
             'face':2.02,
             'neck':1.96,
             'breathZone':1.95,
             'back':2.22,
             'chest':1.74,
             'pelvis':2.7,
             'lUArm':2.2,
             'rUArm':2.2,
             'lLArm':2.38,
             'rLArm':2.38,
             'lHand':1.99,
             'rHand':1.99,
             'lThigh':1.98,
             'rThigh':1.98,
             'lCalf':1.27,
             'rCalf':1.27,
             'lFoot':1.62,
             'rFoot': 1.62 }
        
        C71={'head':0.28,
             'face':0,
             'neck':0,
             'breathZone':0,
             'back':0.74,
             'chest':0.35,
             'pelvis':0.83,
             'lUArm':0,
             'rUArm':0,
             'lLArm':1.18,
             'rLArm':1.18,
             'lHand':0.48,
             'rHand':0.48,
             'lThigh':0,
             'rThigh':0,
             'lCalf':1.22,
             'rCalf':1.22,
             'lFoot':0.5,
             'rFoot': 0.5 }
        
        C72={'head':0.4,
             'face':0.4,
             'neck':0,
             'breathZone':0.79,
             'back':0,
             'chest':0,
             'pelvis':-0.64,
             'lUArm':0,
             'rUArm':0,
             'lLArm':0.28,
             'rLArm':0.28,
             'lHand':0.48,
             'rHand':0.48,
             'lThigh':0,
             'rThigh':0,
             'lCalf':1.22,
             'rCalf':1.22,
             'lFoot':0.3,
             'rFoot':  0.3}
        
        C8={'head':0.5,
             'face':0.41,
             'neck':-0.19,
             'breathZone':1.1,
             'back':0,
             'chest':0,
             'pelvis':-0.75,
             'lUArm':-0.33,
             'rUArm':-0.33,
             'lLArm':-0.41,
             'rLArm':-0.41,
             'lHand':0,
             'rHand':0,
             'lThigh':0,
             'rThigh':0,
             'lCalf':0.36,
             'rCalf':0.36,
             'lFoot':-0.25,
             'rFoot': -0.25}
        
        n={'head':2,
             'face':2, #1.5
             'neck':1,
             'breathZone':2, # 1.5
             'back':1,
             'chest':2,
             'pelvis':1,
             'lUArm':1,
             'rUArm':1,
             'lLArm':1,
             'rLArm':1,
             'lHand':1,
             'rHand':1,
             'lThigh':1,
             'rThigh':1,
             'lCalf':2, #1.5
             'rCalf':2, #1.5
             'lFoot':2,
             'rFoot': 2 }
        """
        C31={'head':0.35,
             'face':-0.11,
             'neck':0,
             'breathZone':0,
             'back':-0.45,
             'chest':-0.66,
             'pelvis':0.59,
             'lUArm':0.3,
             'rUArm':0.3,
             'lLArm':-0.23,
             'rLArm':-0.23,
             'lHand':-0.8,
             'rHand':-0.8,
             'lThigh':0,
             'rThigh':0,
             'lCalf':-0.2,
             'rCalf':-0.2,
             'lFoot':-0.91,
             'rFoot':-0.91}
        
        C32={'head':0.35,
             'face':0.11,
             'neck':0,
             'breathZone':0.62,
             'back':0.45,
             'chest':0.66,
             'pelvis':0.0,
             'lUArm':0.35,
             'rUArm':0.35,
             'lLArm':0.23,
             'rLArm':0.23,
             'lHand':0.8,
             'rHand':0.8,
             'lThigh':0,
             'rThigh':0,
             'lCalf':0.61,
             'rCalf':0.61,
             'lFoot':0.4,
             'rFoot': 0.4 }
        
        C6={'head':2.17,
             'face':2.02,
             'neck':1.96,
             'breathZone':1.95,
             'back':2.1,
             'chest':2.1,
             'pelvis':2.06,
             'lUArm':2.14,
             'rUArm':2.14,
             'lLArm':2.0,
             'rLArm':2.0,
             'lHand':1.98,
             'rHand':1.98,
             'lThigh':1.98,
             'rThigh':1.98,
             'lCalf':2,
             'rCalf':2,
             'lFoot':2.13,
             'rFoot': 2.13 }
        
        C71={'head':0.28,
             'face':0,
             'neck':0,
             'breathZone':0,
             'back':0.96,
             'chest':1.39,
             'pelvis':0.5,
             'lUArm':0,
             'rUArm':0,
             'lLArm':0,
             'rLArm':0,
             'lHand':0.48,
             'rHand':0.48,
             'lThigh':0,
             'rThigh':0,
             'lCalf':1.67,
             'rCalf':1.67,
             'lFoot':0.5,
             'rFoot': 0.5 }
        
        C72={'head':0.4,
             'face':0.4,
             'neck':0,
             'breathZone':0.79,
             'back':0,
             'chest':0.9,
             'pelvis':0,
             'lUArm':0,
             'rUArm':0,
             'lLArm':1.71,
             'rLArm':1.71,
             'lHand':0.48,
             'rHand':0.48,
             'lThigh':0,
             'rThigh':0,
             'lCalf':0,
             'rCalf':0,
             'lFoot':0.3,
             'rFoot':  0.3}
        
        C8={'head':0.5,
             'face':0.41,
             'neck':-0.19,
             'breathZone':1.1,
             'back':0,
             'chest':0,
             'pelvis':-0.51,
             'lUArm':-0.4,
             'rUArm':-0.4,
             'lLArm':-0.68,
             'rLArm':-0.68,
             'lHand':0,
             'rHand':0,
             'lThigh':0,
             'rThigh':0,
             'lCalf':0,
             'rCalf':0,
             'lFoot':0,
             'rFoot': 0}
        
        n={'head':2,
             'face':1.5,
             'neck':1,
             'breathZone':1.5,
             'back':1,
             'chest':2,
             'pelvis':1,
             'lUArm':1,
             'rUArm':1,
             'lLArm':1,
             'rLArm':1,
             'lHand':1,
             'rHand':1,
             'lThigh':1,
             'rThigh':1,
             'lCalf':1.5,
             'rCalf':1.5,
             'lFoot':2,
             'rFoot': 2 }"""
        
        if overallSensation<=0:
            soMinus=abs(overallSensation)
            soPlus=0
        else:
            soMinus=0
            soPlus=abs(overallSensation)
        
        localComfort={}
        for i in localSensation.keys():
            part1=(-4-(C6[i]+C71[i]*soMinus+C72[i]*soPlus))/(abs(-4+C31[i]*soMinus+C32[i]*soPlus+C8[i]))**n[i]
            part2=(-4-(C6[i]+C71[i]*soMinus+C72[i]*soPlus))/(abs(4+C31[i]*soMinus+C32[i]*soPlus+C8[i]))**n[i]
            part3=(part1-part2)/(np.exp(15*(localSensation[i]+C31[i]*soMinus+C32[i]*soPlus+C8[i]))+1)
            part4=part3+part2
            part5=part4*abs(localSensation[i]+C31[i]*soMinus+C32[i]*soPlus+C8[i])**n[i]+(C6[i]+C71[i]*soMinus+C72[i]*soPlus)
            if part5>4:
                localComfort[i]=4.0
            elif part5<-4:
                localComfort[i]=-4.0
            else:
                localComfort[i]=part5
            
            
        return localComfort        
    
    def OverallComfort(self):
        """
        Overall comfort

        Returns
        -------
        OverallComfort

        """
        localComfort = self.LocalComfort()
        if abs(np.array(list(self._dTempLocalDt.values()))).any()>0.2/3600 or sorted(localComfort.items(), key=itemgetter(1))[1][1]>-2:
            #print(abs(np.array(list(self._dTempLocalDt.values()))))
            lComfort=(sorted(localComfort.items(), key=itemgetter(1))[:2])
            mComfort=max(localComfort.values())
            if all(k in dict(lComfort) for k in ('lHand','rHand')) or all(k in dict(lComfort) for k in ('lFoot','rFoot')):
                lComfort={}
                lComfort=sorted(localComfort.items(), key=itemgetter(1))[0:3:2]
            OverallComfort = (np.mean(list(dict(lComfort).values()))*2+mComfort)/3        
        else:
            lComfort=(sorted(localComfort.items(), key=itemgetter(1))[:2])
            if all(k in dict(lComfort) for k in ('lHand','rHand')) or all(k in dict(lComfort) for k in ('lFoot','rFoot')):
                lComfort={}
                lComfort=(sorted(localComfort.items(), key=itemgetter(1))[0:3:2])
            OverallComfort = np.mean(list(dict(lComfort).values()))
        return OverallComfort
            
    ### Run Model
    def RunModel(self):        
        localSensation=self.LocalSensation()
        localComfort=self.LocalComfort()
        overallSensation=self.OverallSensation()
        overallComfort=self.OverallComfort()
    
        return overallSensation,overallComfort

#%% Main code
def testModel():
        
    start_time = time.time()
    #Inputs
    
    sections=['head','face','neck','breathZone','chest','back','pelvis','lUArm','rUArm','lLArm','rLArm','lHand','rHand','lThigh','rThigh','lCalf','rCalf','lFoot','rFoot']
    tempLocal = {'head':24.6,
                   'face':26,
                   'neck':27,
                   'breathZone':26,
                   'chest':28.5,
                   'back':28.5,
                   'pelvis':28,
                   'lUArm':29,
                   'rUArm':29,
                   'lLArm':29,
                   'rLArm':29,
                   'lHand':24,
                   'rHand':24,
                   'lThigh':28,
                   'rThigh':28,
                   'lCalf':28,
                   'rCalf':28,
                   'lFoot':28,
                   'rFoot':28}
    
    dTempLocalDt = {}
    for i in sections:
        dTempLocalDt[i] = rand.random()*0.00002
    dTempCoreDt = 0
    tSkinMean = 24.6#np.mean(list(tempLocal.values()))
    Driver=BerkeleyModel(tempLocal, tSkinMean, dTempLocalDt, dTempCoreDt)
    #Run
    overallSensation,overallComfort=Driver.RunModel()
    print('Overall Sensation: ',overallSensation)
    print('Overall Comfort: ',overallComfort)
    print("--- %s seconds ---" % (time.time() - start_time))