import sys
sys.path.append('C:\\Program Files\\DHI\\2017\\FEFLOW 7.1\\bin64')
import ifm
ifm.forceLicense('demo') #REMOVE THIS LINE FOR BIGGER MODEL RUNS

import ss
import tr
#%% Returns the Model info of the fem sile
def info(fem_path):
    doc = ifm.loadDocument(fem_path)
    print 'Number of nodes: ', doc.getNumberOfNodes()
    print 'Number of elements: ', doc.getNumberOfElements()
    print 'Number of timesteps: ', doc.getTimeSteps()
    print 'Number of layers: ', doc.getNumberOfLayers()
    print 'Number of elements per layer: ', doc.getNumberOfElementsPerLayer()

#%% Runs the Simulator for the fem file
def runSimulator(fem_path):
    doc = ifm.loadDocument(fem_path)
    doc.startSimulator()
    doc.stopSimulator()
    print 'Simulation complete'