"""This class contains functions for transient use cases
"""
import sys
sys.path.append('C:\\Program Files\\DHI\\2017\\FEFLOW 7.1\\bin64')
import ifm
ifm.forceLicense('demo') #REMOVE THIS LINE FOR BIGGER MODEL RUNS
import numpy as np
import pandas as pd

#%% Read the specified param at the Obs. pts. from a DAC file over specified time steps into a DF
def readDacObsParam(dac, param, ts):
    """Read the specified param at the Obs. pts. from a DAC file over specified time steps into a DF
    """
    doc = ifm.loadDocument(dac)
    supported_params = param=='heads' or param=='temperature' or param=='mass' or param=='moisture' or param=='pressure' or param=='saturation'
    if not supported_params:
        print 'Unsupported param. Retry.'
        sys.exit(1)
    if supported_params:
        nodes = []
        columns = range(0, doc.getNumberOfValidObsPoints())
        for j in range(0, doc.getNumberOfValidObsPoints()): nodes.append(doc.getTypeOfObsId(j))
        columns = ["{}{}{}".format('Obs. ',i, ' at n') for i in columns]
        for j in range(0, len(columns)): columns[j] = columns[j]+str(nodes[j])
        #for j in range(0, len(columns)): obs_name.append(doc.getObsLabel(0)) #Available only in 7.2
    if param == 'heads':
        h, heads, index = [],[],[]
        for i in ts:
            if not doc.loadTimeStep(i):
                print 'Specified time step ', i, 'does not exist in the model ', dac
                break
            doc.loadTimeStep(i)
            for j in range(0, doc.getNumberOfValidObsPoints()):
                h.append(doc.getFlowValueOfObsIdAtCurrentTime(j))
            heads.append(h)
            index.append(i)
            h = []
        heads_df = pd.DataFrame(heads, index=index, columns=columns)
        return heads_df, heads
    if param == 'temperature':
        if doc.getProblemClass() not in [2,3]:
            print 'Model is not of the heat transport type. Param unapplicable.'
            sys.exit(1)
        t, temp, index = [],[],[]
        for i in ts:
            if not doc.loadTimeStep(i):
                print 'Specified time step ', i, 'does not exist in the model ', dac
                break
            doc.loadTimeStep(i)
            for j in range(0, doc.getNumberOfValidObsPoints()):
                t.append(doc.getHeatValueOfObsIdAtCurrentTime(j))
            temp.append(t)
            index.append(i)
            t = []
        temp_df = pd.DataFrame(temp, index=index, columns=columns)
        return temp_df, temp
    if param == 'mass':
        if doc.getProblemClass() not in [1,3]:
            print 'Model is not of the mass transport type. Param unapplicable.'
            sys.exit(1)
        m, mass, index = [],[],[]
        for i in ts:
            if not doc.loadTimeStep(i):
                print 'Specified time step ', i, 'does not exist in the model ', dac
                break
            doc.loadTimeStep(i)
            for j in range(0, doc.getNumberOfValidObsPoints()):
                m.append(doc.getMassValueOfObsIdAtCurrentTime(j))
            mass.append(m)
            index.append(i)
            m = []
        mass_df = pd.DataFrame(mass, index=index, columns=columns)
        return mass_df, mass
    if param == 'moisture':
        if doc.getProblemType() != 1:
            print 'Model is saturated. Param unapplicable.'
            sys.exit(1)
        mo, moisture, index = [],[],[]
        for i in ts:
            if not doc.loadTimeStep(i):
                print 'Specified time step ', i, 'does not exist in the model ', dac
                break
            doc.loadTimeStep(i)
            for j in range(0, doc.getNumberOfValidObsPoints()):
                mo.append(doc.getMoistureContentValueOfObsIdAtCurrentTime(j))
            moisture.append(mo)
            index.append(i)
            mo = []
        moisture_df = pd.DataFrame(moisture, index=index, columns=columns)
        return moisture_df, moisture
    if param == 'pressure':
        p, pressure, index = [],[],[]
        for i in ts:
            if not doc.loadTimeStep(i):
                print 'Specified time step ', i, 'does not exist in the model ', dac
                break
            doc.loadTimeStep(i)
            for j in range(0, doc.getNumberOfValidObsPoints()):
                p.append(doc.getPressureValueOfObsIdAtCurrentTime(j))
            pressure.append(p)
            index.append(i)
            p = []
        pressure_df = pd.DataFrame(pressure, index=index, columns=columns)
        return pressure_df, pressure
    if param == 'saturation':
        if doc.getProblemType() != 1:
            print 'Model is saturated. Param unapplicable.'
            sys.exit(1)
        s, saturation, index = [],[],[]
        for i in ts:
            if not doc.loadTimeStep(i):
                print 'Specified time step ', i, 'does not exist in the model ', dac
                break
            doc.loadTimeStep(i)
            for j in range(0, doc.getNumberOfValidObsPoints()):
                s.append(doc.getSaturationValueOfObsIdAtCurrentTime(j))
            saturation.append(s)
            index.append(i)
            s = []
        saturation_df = pd.DataFrame(saturation, index=index, columns=columns)
        return saturation_df, saturation