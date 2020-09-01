"""FEFLOWPY is an in-house python package developed to handle FeFlow models outside of the FeFlow program with the help of python API functions provided by the FeFlow program

1. Prerequsites:
Install Python 2.7 (other versions are not supported)
Copy the feflowpy folder into the current working directory of Python (i.e. the location of the script where you want to use the module or into the directory from where you want to use it with bash)
Import the package (after performing the above step) simply by running the command "import feflowpy"

2. Currently available functions:
The package has two classes - steady-state, denoted by ss and transient, denoted by tr.
The callable functions are nested in these two classes based on their nature.
However some basic functions are directly situated at the root of the package. (Currently available: 2). They may be called directly as feflowpy.<fn_name>.
*feflowpy.info(<fem_file_path>):
	returns some basic info on the specified fem file (the FeFlow model in effect)
*feflowpy.runSimulator(<fem_file_path>):
	runs the simulator for the specified fem file (the FeFlow model in effect)
The functions are thus called in the following format (once feflowpy has been imported): feflowpy.<ss/tr>.<fn_name>. Example: feflowpy.
*feflowpy.ss.
	+setParamAtBC(<fem_file_path>, bc_type, param, value):
		sets the specified param to the specified value for the specified boundary condition. BC types:\n0 - None\n1 - Dirichlet\n2 - Neumann\n3 - Cauchy\n4 - Single well
		currently supported params: 'head'
	+transferAll(<fem_fileIN_path>, <fem_fileOUT_path>, param):
		copies the values of the specified param from the FeFlow model at fem_fileIN_path to fem_fileOUT_path at all nodes/elements.
		currently supported params: 'conductivity2D', 'conductivity3D', 'heads', 'BC', 'bc', 'porosity', 'recharge', 'transferIN', 'transferOUT'
	+transferSelection(<fem_fileIN_path>, <fem_fileOUT_path>, param,  xml_path):
		copies the values of the specified param from the FeFlow model at fem_fileIN_path to fem_fileOUT_path for all the nodes/elements specified in an xml file.
		currently supported params: 'conductivity2D', 'conductivity3D', 'heads', 'BC', 'bc', 'porosity', 'recharge', 'transferIN', 'transferOUT'
	+transferLayerSlice(<fem_fileIN_path>, <fem_fileOUT_path>, param, layer):
		copies the values of the specified param from the FeFlow model at fem_fileIN_path to fem_fileOUT_path between two specified layers/slices.
		currently supported params: 'conductivity3D', 'heads', 'BC', 'bc', 'porosity', 'recharge', 'transferIN', 'transferOUT'
*feflowpy.tr.
	+readDacObsParam(<dac_file_path>, param, ts):
		reads the values of the specified param from the dac file at dac_file_path for all the observation points and returns a pandas dataframe with the read values.
"""
import sys
sys.path.append('C:\\Program Files\\DHI\\2017\\FEFLOW 7.1\\bin64')
import ifm
#ifm.forceLicense('demo') #REMOVE THIS LINE FOR BIGGER MODEL RUNS

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