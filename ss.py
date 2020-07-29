import sys
sys.path.append('C:\\Program Files\\DHI\\2017\\FEFLOW 7.1\\bin64')
import ifm
ifm.forceLicense('demo') #REMOVE THIS LINE FOR BIGGER MODEL RUNS
import numpy as np
from xml.dom import minidom
from collections import Iterable
import pandas as pd

#%% Fetches and returns the Element IDs for a given xml selection
def ElementsInSelection(xml_path):
    xml_file = minidom.parse(xml_path)
    ranges = xml_file.getElementsByTagName('range')
    starts = []
    ends = []
    elem_list = []
    for n in range(len(ranges)):
        starts.append(ranges[n].attributes['start'].value)
        starts = map(int,starts)
        ends.append(ranges[n].attributes['end'].value)
        ends = map(int,ends)
        elem_list.append(range(starts[n],ends[n],1))
    starts = np.array(starts)
    ends = np.array(ends)
    def flatten(node_list):
        for item in node_list:
            if isinstance(item, Iterable) and not isinstance(item, basestring):
                for x in flatten(item):
                    yield x
            else:
                yield item
    elem_list = np.array(list(flatten(elem_list)))
    return elem_list

#%% Fetches and returns the Node IDs for a given xml selection
def NodesInSelection(xml_path):
    xml_file = minidom.parse(xml_path)
    ranges = xml_file.getElementsByTagName('range')
    starts = []
    ends = []
    node_list = []
    for n in range(len(ranges)):
        starts.append(ranges[n].attributes['start'].value)
        starts = map(int,starts)
        ends.append(ranges[n].attributes['end'].value)
        ends = map(int,ends)
        node_list.append(range(starts[n],ends[n],1))
    starts = np.array(starts)
    ends = np.array(ends)
    def flatten(node_list):
        for item in node_list:
            if isinstance(item, Iterable) and not isinstance(item, basestring):
                for x in flatten(item):
                    yield x
            else:
                yield item
    node_list = np.array(list(flatten(node_list)))
    return node_list

#%% Fetches the list of nodes for a specified boundary condition; returns a DF of the locations (nodes/elements) and the value
def setParamAtBC(fem_path, bc_type, param, value):
    doc = ifm.loadDocument(fem_path)
    nn = doc.getNumberOfNodes()
    nodes_list = []
    if param == 'heads':
        for node in range(0,nn):
            if doc.getBcFlowType(node) == bc_type:
                nodes_list.append(node)
        c=0
        for node in nodes_list:
            doc.setResultsFlowHeadValue(node, value)
            c=c+1
        print 'Head value', value, 'set at all specified BC nodes:',c
        val_list= np.zeros(len(nodes_list))
        val_list.fill(value)
        param_df = pd.DataFrame(val_list, index=nodes_list, columns=[param])
        return param_df
    else:
        print 'Unsupported param type or incompatible param type and model. Retry'
        sys.exit(1)

#%% Transfers specific data for between two models
def transferAll(fem_path_in, fem_path_out, param):
    supported_params = param == 'conductivity2D' or param == 'conductivity3D' or param == 'heads' or param == 'BC' or param == 'bc' or param == 'porosity' or param == 'recharge' or param == 'transferIN' or param == 'transferOUT'
    if not supported_params:
        print 'Unsupported param type or incompatible param type and model. Retry.'
        sys.exit(1)
    doc_out = ifm.loadDocument(fem_path_out)
    nlay_out = doc_out.getNumberOfLayers()
    nn_out = doc_out.getNumberOfNodes()
    ne_out = doc_out.getNumberOfElements()
    doc_in = ifm.loadDocument(fem_path_in)
    ne_in = doc_in.getNumberOfElements()
    nn_in = doc_in.getNumberOfNodes()
    nlay_in = doc_in.getNumberOfLayers()
    multi_layer = nlay_in>1 and nlay_out>1
    single_layer = nlay_in==1 and nlay_out==1
    if param == 'conductivity2D':
        if not single_layer:
            print 'Conductivity 2D is not applicable to 3D models. Use conductivity3D instead'
            sys.exit(1)
        if ne_in != ne_out:
            print 'Models are not compatible. Unequal number of elements. Aborting transfer.'
            sys.exit(1)
        cond_in = []
        for e in range(0, ne_in):
            cond_in.append(doc_in.getMatConductivityValue2D(e))
        doc_out = ifm.loadDocument(fem_path_out)
        for e in range(0, ne_out):
            doc_out.setMatConductivityValue2D(e,cond_in[e])
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        elements = range(0,ne_in)
        param_df = pd.DataFrame(cond_in, index=elements, columns=[param])
        return elements, cond_in, param_df
    if param == 'conductivity3D':
        if not multi_layer:
            print 'Conductivity 3D is not applicable to 2D models. Use conductivity2D instead'
            sys.exit(1)
        doc_out = ifm.loadDocument(fem_path_out)
        ne_out = doc_out.getNumberOfElements()
        nlay_out = doc_out.getNumberOfLayers()
        if ne_in != ne_out:
            print 'Models are not compatible. Unequal number of elements. Aborting transfer.'
            sys.exit(1)
        if nlay_in != nlay_out:
            print 'Number of layers for the two specified layers are not equal. Try layer by layer data transfer. Aborting transfer.'
            sys.exit(1)
        cond_x =[]
        cond_y =[]
        cond_z =[]
        for e in range(0,ne_in):
            cond_x.append(doc_in.getMatXConductivityValue3D(e))
            cond_y.append(doc_in.getMatYConductivityValue3D(e))
            cond_z.append(doc_in.getMatZConductivityValue3D(e))
        c = 0
        for e in range(0,ne_out):
            doc_out.setMatXConductivityValue3D(e,cond_x[c])
            doc_out.setMatYConductivityValue3D(e,cond_y[c])
            doc_out.setMatZConductivityValue3D(e,cond_z[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        cond3D_in = []
        elements = range(0,ne_in)
        for i in range(0, len(cond_x)):
            cond3D_in.append([cond_x[i], cond_y[i], cond_z[i]])
        param_df = pd.DataFrame(cond3D_in, index=elements, columns=['kxx','kyy','kzz'])
        return elements, cond3D_in, param_df
    if param == 'heads':
        if nn_in != nn_out:
            print 'Models are not compatible. Unequal number of elements. Aborting transfer.'
            sys.exit(1)
        heads_in = []
        for n in range(0, nn_in):
            heads_in.append(doc_in.getResultsFlowHeadValue(n))
        doc_out = ifm.loadDocument(fem_path_out)
        for n in range(0, nn_out):
            doc_out.setResultsFlowHeadValue(n,heads_in[n])
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        nodes = range(0,nn_in)
        param_df = pd.DataFrame(heads_in, index=nodes, columns=[param])
        return nodes, heads_in, param_df
    if param == 'BC' or param == 'bc':
        if nn_in != nn_out:
            print 'Models are not compatible. Unequal number of elements. Aborting transfer.'
            sys.exit(1)
        bc_in = []
        bc_val_in = []
        if doc_in.getAbsoluteSimulationTime() == 0:
            st_unst = 0
        else:
            st_unst = 1
        for n in range(0, nn_in):
            bc_in.append(doc_in.getBcFlowType(n))
            bc_val_in.append(doc_in.getBcFlowValue(n))
        doc_out = ifm.loadDocument(fem_path_out)
        for n in range(0, nn_out):
            doc_out.setBcFlowTypeAndValueAtCurrentTime(n,bc_in[n],st_unst,bc_val_in[n])
        print 'BC types:\n0 - None\n1 - Dirichlet\n2 - Neumann\n3 - Cauchy\n4 - Single well'
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        nodes = range(0,nn_in)
        bc_df = []
        for i in range(0,len(bc_in)):
            bc_df.append([bc_in[i], bc_val_in[i]])
        param_df = pd.DataFrame(bc_df, index=nodes, columns=['BC type','BC value'])
        return nodes, bc_df, param_df
    if param == 'porosity':
        doc_out = ifm.loadDocument(fem_path_out)
        out_unsat = doc_out.getProblemType()
        doc_in = ifm.loadDocument(fem_path_in)
        in_unsat = doc_in.getProblemType()
        if ne_in != ne_out:
            print 'Models are not compatible. Unequal number of elements. Aborting transfer.'
            sys.exit(1)
        if in_unsat==0 or out_unsat==0:
            print 'Models are not compatible. Porosity can only be assigned to unsaturated problems. Aborting transfer.'
            sys.exit(1)
        porosity_in = []
        for e in range(0, ne_in):
            porosity_in.append(doc_in.getMatUnsatPorosity(e))
        doc_out = ifm.loadDocument(fem_path_out)
        for e in range(0, ne_out):
            doc_out.setMatUnsatPorosity(e,porosity_in[e])
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        elements = range(0,ne_in)
        param_df = pd.DataFrame(porosity_in, index=elements, columns=[param])
        return elements, porosity_in, param_df
    if param == 'recharge':
        if ne_in != ne_out:
            print 'Models are not compatible. Unequal number of elements. Aborting transfer.'
            sys.exit(1)
        recharge_in = []
        for e in range(0, ne_in):
            recharge_in.append(doc_in.getMatFlowRechargeValue(e))
        doc_out = ifm.loadDocument(fem_path_out)
        for e in range(0, ne_out):
            doc_out.setMatFlowRechargeValue(e,recharge_in[e])
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        elements = range(0,ne_in)
        param_df = pd.DataFrame(recharge_in, index=elements, columns=[param])
        return elements, recharge_in, param_df
    if param == 'transferIN':
        if ne_in != ne_out:
            print 'Models are not compatible. Unequal number of elements. Aborting transfer.'
            sys.exit(1)
        transferIN_in = []
        for e in range(0, ne_in):
            transferIN_in.append(doc_in.getMatFlowTransferIn(e))
        doc_out = ifm.loadDocument(fem_path_out)
        for e in range(0, ne_out):
            doc_out.setMatFlowTransferIn(e,transferIN_in[e])
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        elements = range(0,ne_in)
        param_df = pd.DataFrame(transferIN_in, index=elements, columns=[param])
        return elements, transferIN_in, param_df
    if param == 'transferOUT':
        if ne_in != ne_out:
            print 'Models are not compatible. Unequal number of elements. Aborting transfer.'
            sys.exit(1)
        transferOUT_in = []
        for e in range(0, ne_in):
            transferOUT_in.append(doc_in.getMatFlowTransferOut(e))
        doc_out = ifm.loadDocument(fem_path_out)
        for e in range(0, ne_out):
            doc_out.setMatFlowTransferOut(e,transferOUT_in[e])
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        elements = range(0,ne_in)
        param_df = pd.DataFrame(transferOUT_in, index=elements, columns=[param])
        return elements, transferOUT_in, param_df

#%% Transfers specific data between two models for a given node/element (based on param) selection
def transferSelection(fem_path_in, fem_path_out, param,  xml_path):
    supported_params = param == 'conductivity2D' or param == 'conductivity3D' or param == 'heads' or  param == 'BC' or param == 'bc' or param == 'porosity' or param == 'recharge' or param == 'transferIN' or param == 'transferOUT'
    if not supported_params:
        print 'Unsupported param type. Retry.'
        sys.exit(1)
    doc_out = ifm.loadDocument(fem_path_out)
    ne_out = doc_out.getNumberOfElements()
    nn_out = doc_out.getNumberOfNodes()
    nlay_out = doc_out.getNumberOfLayers()
    doc_in = ifm.loadDocument(fem_path_in)
    ne_in = doc_in.getNumberOfElements()
    nn_in = doc_in.getNumberOfNodes()
    nlay_in = doc_in.getNumberOfLayers()
    multi_layer = nlay_in>1 and nlay_out>1
    single_layer = nlay_in==1 and nlay_out==1
    supported_params_elements = ['conductivity2D', 'conductivity3D', 'porosity', 'recharge', 'transferIN','transferOUT']
    supported_params_nodes = ['heads', 'BC', 'bc']
    elements = []
    nodes = []
    if param in supported_params_elements:
        elements = ElementsInSelection(xml_path)
        out_of_bounds = max(elements)>ne_in or max(elements)>ne_out
    if param in supported_params_nodes:
        nodes = NodesInSelection(xml_path)
        out_of_bounds = max(nodes)>nn_in or max(nodes)>nn_out
    if out_of_bounds:
        print 'Selection out of bounds for either the input or output model. Exiting'
        sys.exit(1)
    if param == 'conductivity2D':
        if not single_layer:
            print 'Conductivity 2D is not applicable to 3D models. Use conductivity3D instead'
            sys.exit(1)
        cond_in = []
        for e in elements:
            cond_in.append(doc_in.getMatConductivityValue2D(e))
        if ne_in != ne_out:
            confirmation = 'n'
            confirmation = str(raw_input('Models are not similar. Unequal number of elements. Continue transfer anyways? (y/n):\n'))
            if confirmation == 'y':
                c=0
                doc_out = ifm.loadDocument(fem_path_out)
                for e in elements:
                    doc_out.setMatConductivityValue2D(e,cond_in[c])
                    c=c+1
            elif confirmation == 'n':
                print 'Transfer aborted. Exiting.'
                sys.exit(0)
        else:
            c=0
            doc_out = ifm.loadDocument(fem_path_out)
            for e in elements:
                    doc_out.setMatConductivityValue2D(e,cond_in[c])
                    c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(cond_in, index=elements, columns=[param])
        return elements, cond_in, param_df
    if param == 'conductivity3D':
        if not multi_layer:
            print 'Conductivity 3D is not applicable to 2D models. Use conductivity2D instead'
            sys.exit(1)
        doc_out = ifm.loadDocument(fem_path_out)
        ne_out = doc_out.getNumberOfElements()
        nlay_out = doc_out.getNumberOfLayers()
        e_per_lay_out = doc_out.getNumberOfElementsPerLayer()
        doc_in = ifm.loadDocument(fem_path_in)
        ne_in = doc_in.getNumberOfElements()
        nlay_in = doc_in.getNumberOfLayers()
        e_per_lay_in = doc_in.getNumberOfElementsPerLayer()
        elements = ElementsInSelection(xml_path)
        if max(elements)>ne_in or max(elements)>ne_out:
            print 'Selection out of bounds for either the input or output model. Exiting'
            sys.exit(1)
        confirmation = 'n'
        if ne_in != ne_out:
            confirmation = str(raw_input('Models are not similar. Unequal number of elements. Continue transfer? (y/n):\n'))
        if nlay_in != nlay_out:
            confirmation = str(raw_input('Models are not similar. Unequal number of layers. Continue transfer? (y/n):\n'))
        if e_per_lay_in != e_per_lay_out:
            confirmation = str(raw_input('Models are not similar. Unequal number of layers. Continue transfer? (y/n):\n'))
        same_model = ne_in==ne_out and nlay_in==nlay_out and e_per_lay_in==e_per_lay_out
        if same_model or confirmation=='y':
            cond_x =[]
            cond_y =[]
            cond_z =[]
            for e in elements:
                cond_x.append(doc_in.getMatXConductivityValue3D(e))
                cond_y.append(doc_in.getMatYConductivityValue3D(e))
                cond_z.append(doc_in.getMatZConductivityValue3D(e))
            doc_out = ifm.loadDocument(fem_path_out)
            c = 0
            for e in elements:
                doc_out.setMatXConductivityValue3D(e,cond_x[c])
                doc_out.setMatYConductivityValue3D(e,cond_y[c])
                doc_out.setMatZConductivityValue3D(e,cond_z[c])
                c=c+1
            print 'Transfer complete'
            doc_out.saveDocument(fem_path_out)
            print 'Document saved. Exiting.'
            cond3D_in = []
            for i in range(0, len(cond_x)):
                cond3D_in.append([cond_x[i], cond_y[i], cond_z[i]])
            param_df = pd.DataFrame(cond3D_in, index=elements, columns=['kxx','kyy','kzz'])
            return elements, cond3D_in, param_df
        if not same_model and confirmation=='n':
            print 'Transfer aborted. Exiting.'
            sys.exit(0)
    if param == 'heads':
        heads_in = []
        for n in nodes:
            heads_in.append(doc_in.getResultsFlowHeadValue(n))
        if nn_in != nn_out:
            confirmation = 'n'
            confirmation = str(raw_input('Models are not similar. Unequal number of nodes. Continue transfer anyways? (y/n):\n'))
            if confirmation == 'y':
                c=0
                doc_out = ifm.loadDocument(fem_path_out)
                for n in nodes:
                    doc_out.setResultsFlowHeadValue(n,heads_in[c])
                    c=c+1
            elif confirmation == 'n':
                print 'Transfer aborted. Exiting.'
                sys.exit(0)
        else:
            c=0
            doc_out = ifm.loadDocument(fem_path_out)
            for n in nodes:
                    doc_out.setResultsFlowHeadValue(n,heads_in[c])
                    c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(heads_in, index=nodes, columns=[param])
        return nodes, heads_in, param_df
    if param == 'BC' or param == 'bc':
        if nn_in != nn_out:
            confirmation = 'n'
            confirmation = str(raw_input('Models are not similar. Unequal number of nodes. Continue transfer anyways? (y/n):\n'))
            if confirmation != 'y':
                print 'Aborting transfer. Exiting.'
                sys.exit(0)
        bc_in = []
        bc_val_in = []
        if doc_in.getAbsoluteSimulationTime() == 0:
            st_unst = 0
        else:
            st_unst = 1
        for n in nodes:
            bc_in.append(doc_in.getBcFlowType(n))
            bc_val_in.append(doc_in.getBcFlowValue(n))
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for n in nodes:
            doc_out.setBcFlowTypeAndValueAtCurrentTime(n,bc_in[c],st_unst,bc_val_in[c])
            c=c+1
        print 'BC types:\n0 - None\n1 - Dirichlet\n2 - Neumann\n3 - Cauchy\n4 - Single well'
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        bc_df = []
        for i in range(0,len(bc_in)):
            bc_df.append([bc_in[i], bc_val_in[i]])
        param_df = pd.DataFrame(bc_df, index=nodes, columns=['BC type','BC value'])
        return nodes, bc_df, param_df
    if param == 'porosity':
        doc_out = ifm.loadDocument(fem_path_out)
        out_unsat = doc_out.getProblemType()
        doc_in = ifm.loadDocument(fem_path_in)
        in_unsat = doc_in.getProblemType()
        if ne_in != ne_out:
            confirmation = 'n'
            confirmation = str(raw_input('Models are not similar. Unequal number of nodes. Continue transfer anyways? (y/n):\n'))
            if confirmation != 'y':
                print 'Aborting transfer. Exiting.'
                sys.exit(0)
        if in_unsat==0 or out_unsat==0:
            print 'Models are not compatible. Porosity can only be assigned to unsaturated problems. Aborting transfer.'
            sys.exit(1)
        porosity_in = []
        for e in elements:
            porosity_in.append(doc_in.getMatUnsatPorosity(e))
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for e in elements:
            doc_out.setMatUnsatPorosity(e,porosity_in[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(porosity_in, index=elements, columns=[param])
        return elements, porosity_in, param_df
    if param == 'recharge':

        if ne_in != ne_out:
            confirmation = 'n'
            confirmation = str(raw_input('Models are not similar. Unequal number of nodes. Continue transfer anyways? (y/n):\n'))
            if confirmation != 'y':
                print 'Aborting transfer. Exiting.'
                sys.exit(0)

        recharge_in = []
        for e in elements:
            recharge_in.append(doc_in.getMatFlowRechargeValue(e))
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for e in elements:
            doc_out.setMatFlowRechargeValue(e,recharge_in[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(recharge_in, index=elements, columns=[param])
        return elements, recharge_in, param_df
    if param == 'transferIN':

        if ne_in != ne_out:
            confirmation = 'n'
            confirmation = str(raw_input('Models are not similar. Unequal number of nodes. Continue transfer anyways? (y/n):\n'))
            if confirmation != 'y':
                print 'Aborting transfer. Exiting.'
                sys.exit(0)

        transferIN_in = []
        for e in elements:
            transferIN_in.append(doc_in.getMatFlowTransferIn(e))
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for e in elements:
            doc_out.setMatFlowTransferIn(e,transferIN_in[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(transferIN_in, index=elements, columns=[param])
        return elements, transferIN_in, param_df
    if param == 'transferOUT':

        if ne_in != ne_out:
            confirmation = 'n'
            confirmation = str(raw_input('Models are not similar. Unequal number of nodes. Continue transfer anyways? (y/n):\n'))
            if confirmation != 'y':
                print 'Aborting transfer. Exiting.'
                sys.exit(0)

        transferOUT_in = []
        for e in elements:
            transferOUT_in.append(doc_in.getMatFlowTransferOut(e))
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for e in elements:
            doc_out.setMatFlowTransferOut(e,transferOUT_in[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(transferOUT_in, index=elements, columns=[param])
        return elements, transferOUT_in, param_df
#%% Transfers specific data between two models for a specified layer or slice
def transferLayerSlice(fem_path_in, fem_path_out, param, layer, internalRun=False):
    supported_params = param == 'conductivity3D' or param == 'heads' or param == 'BC' or param == 'bc' or param == 'porosity' or param == 'recharge' or param == 'transferIN' or param == 'transferOUT'
    if not supported_params:
        print 'Unsupported param type. Retry.'
        sys.exit(1)
    doc_out = ifm.loadDocument(fem_path_out)
    nlay_out = doc_out.getNumberOfLayers()
    nsl_out = doc_out.getNumberOfSlices()
    e_per_lay_out = doc_out.getNumberOfElementsPerLayer()
    n_per_sl_out = doc_out.getNumberOfNodesPerSlice()
    doc_in = ifm.loadDocument(fem_path_in)
    nlay_in = doc_in.getNumberOfLayers()
    nsl_in = doc_in.getNumberOfSlices()
    e_per_lay_in = doc_in.getNumberOfElementsPerLayer()
    n_per_sl_in = doc_in.getNumberOfNodesPerSlice()
    multi_layer = nlay_in>1 and nlay_out>1
    if not multi_layer:
        if nlay_in==nlay_out==1:
            print 'Both models are not multi-layered.'
        if nlay_in == 1:
            print 'The input model is not multi-layered.'
        elif nlay_out == 1:
            print 'The output model is not multi-layered.'
        sys.exit(1)
    if param == 'conductivity3D':
        layer_bounds = layer<nlay_in and layer<nlay_out
        if not layer_bounds:
            if not layer<nlay_in:
                print 'Specified layer is out of bounds for the input model'
                sys.exit(1)
            if not layer<nlay_out:
                print 'Specified layer is out of bounds for the output model'
                sys.exit(1)
        e_per_lay_same = e_per_lay_in == e_per_lay_out
        if not e_per_lay_same:
            print 'Number of elements per layer are unequal. Aborting transfer'
            sys.exit(1)
        cond_x =[]
        cond_y =[]
        cond_z =[]
        elements = []
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            cond_x.append(doc_in.getMatXConductivityValue3D(e))
            cond_y.append(doc_in.getMatYConductivityValue3D(e))
            cond_z.append(doc_in.getMatZConductivityValue3D(e))
            elements.append(e)
        c = 0
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            doc_out.setMatXConductivityValue3D(e,cond_x[c])
            doc_out.setMatYConductivityValue3D(e,cond_y[c])
            doc_out.setMatZConductivityValue3D(e,cond_z[c])
            c=c+1
        if internalRun:
            doc_out.saveDocument(fem_path_out)
            return 0
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        cond3D_in = []
        for i in range(0, len(cond_x)):
            cond3D_in.append([cond_x[i], cond_y[i], cond_z[i]])
        param_df = pd.DataFrame(cond3D_in, index=elements, columns=['kxx','kyy','kzz'])
        return elements, cond3D_in, param_df
    if param == 'heads':
        slice_bounds = layer<nsl_in and layer<nsl_out
        if not slice_bounds:
            if not layer<nsl_in:
                print 'Specified slice is out of bounds for the input model'
                sys.exit(1)
            if not layer<nsl_out:
                print 'Specified slice is out of bounds for the output model'
                sys.exit(1)
        n_per_sl_same = n_per_sl_in == n_per_sl_out
        if not n_per_sl_same:
            print 'Number of elements per layer are unequal. Aborting transfer'
            sys.exit(1)
        heads_in = []
        nodes = []
        for n in range(n_per_sl_in*layer,n_per_sl_in*(layer+1)):
            heads_in.append(doc_in.getResultsFlowHeadValue(n))
            nodes.append(n)
        c=0
        doc_out = ifm.loadDocument(fem_path_out)
        for n in range(n_per_sl_out*layer,n_per_sl_out*(layer+1)):
            doc_out.setResultsFlowHeadValue(n,heads_in[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(heads_in, index=nodes, columns=[param])
        return nodes, heads_in, param_df
    if param == 'BC' or param == 'bc':
        slice_bounds = layer<nsl_in and layer<nsl_out
        if not slice_bounds:
            if not layer<nsl_in:
                print 'Specified slice is out of bounds for the input model'
                sys.exit(1)
            if not layer<nsl_out:
                print 'Specified slice is out of bounds for the output model'
                sys.exit(1)
        n_per_sl_same = n_per_sl_in == n_per_sl_out
        if not n_per_sl_same:
            print 'Number of elements per layer are unequal. Aborting transfer'
            sys.exit(1)
        bc_in = []
        bc_val_in = []
        if doc_in.getAbsoluteSimulationTime() == 0:
            st_unst = 0
        else:
            st_unst = 1
        nodes = []
        for n in range(n_per_sl_in*layer,n_per_sl_in*(layer+1)):
            bc_in.append(doc_in.getBcFlowType(n))
            bc_val_in.append(doc_in.getBcFlowValue(n))
            nodes.append(n)
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for n in range(n_per_sl_in*layer,n_per_sl_in*(layer+1)):
            doc_out.setBcFlowTypeAndValueAtCurrentTime(n,bc_in[c],st_unst,bc_val_in[c])
            c=c+1
        print 'BC types:\n0 - None\n1 - Dirichlet\n2 - Neumann\n3 - Cauchy\n4 - Single well'
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        bc_df = []
        for i in range(0,len(bc_in)):
            bc_df.append([bc_in[i], bc_val_in[i]])
        param_df = pd.DataFrame(bc_df, index=nodes, columns=['BC type','BC value'])
        return nodes, bc_df, param_df
    if param == 'porosity':
        doc_out = ifm.loadDocument(fem_path_out)
        out_unsat = doc_out.getProblemType()
        doc_in = ifm.loadDocument(fem_path_in)
        in_unsat = doc_in.getProblemType()
        if in_unsat==0 or out_unsat==0:
            print 'Models are not compatible. Porosity can only be assigned to unsaturated problems. Aborting transfer.'
            sys.exit(1)
        layer_bounds = layer<nlay_in and layer<nlay_out
        if not layer_bounds:
            if not layer<nlay_in:
                print 'Specified layer is out of bounds for the input model'
                sys.exit(1)
            if not layer<nlay_out:
                print 'Specified layer is out of bounds for the output model'
                sys.exit(1)
        e_per_lay_same = e_per_lay_in == e_per_lay_out
        if not e_per_lay_same:
            print 'Number of elements per layer are unequal. Aborting transfer'
            sys.exit(1)
        porosity_in = []
        elements = []
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            porosity_in.append(doc_in.getMatUnsatPorosity(e))
            elements.append(e)
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            doc_out.setMatUnsatPorosity(e,porosity_in[c])
            c=c+1
        print 'Transfer complete'
        param_df = pd.DataFrame(porosity_in, index=elements, columns=[param])
        return elements, porosity_in, param_df
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
    if param == 'recharge':
        layer_bounds = layer<nlay_in and layer<nlay_out
        if not layer_bounds:
            if not layer<nlay_in:
                print 'Specified layer is out of bounds for the input model'
                sys.exit(1)
            if not layer<nlay_out:
                print 'Specified layer is out of bounds for the output model'
                sys.exit(1)
        e_per_lay_same = e_per_lay_in == e_per_lay_out
        if not e_per_lay_same:
            print 'Number of elements per layer are unequal. Aborting transfer'
            sys.exit(1)
        recharge_in = []
        elements = []
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            recharge_in.append(doc_in.getMatFlowRechargeValue(e))
            elements.append(e)
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            doc_out.setMatFlowRechargeValue(e,recharge_in[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(recharge_in, index=elements, columns=[param])
        return elements, recharge_in, param_df
    if param == 'transferIN':
        layer_bounds = layer<nlay_in and layer<nlay_out
        if not layer_bounds:
            if not layer<nlay_in:
                print 'Specified layer is out of bounds for the input model'
                sys.exit(1)
            if not layer<nlay_out:
                print 'Specified layer is out of bounds for the output model'
                sys.exit(1)
        e_per_lay_same = e_per_lay_in == e_per_lay_out
        if not e_per_lay_same:
            print 'Number of elements per layer are unequal. Aborting transfer'
            sys.exit(1)
        transferIN_in = []
        elements = []
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            transferIN_in.append(doc_in.getMatFlowTransferIn(e))
            elements.append(e)
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            doc_out.setMatFlowTransferIn(e,transferIN_in[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(transferIN_in, index=elements, columns=[param])
        return elements, transferIN_in, param_df
    if param == 'transferOUT':
        layer_bounds = layer<nlay_in and layer<nlay_out
        if not layer_bounds:
            if not layer<nlay_in:
                print 'Specified layer is out of bounds for the input model'
                sys.exit(1)
            if not layer<nlay_out:
                print 'Specified layer is out of bounds for the output model'
                sys.exit(1)
        e_per_lay_same = e_per_lay_in == e_per_lay_out
        if not e_per_lay_same:
            print 'Number of elements per layer are unequal. Aborting transfer'
            sys.exit(1)
        transferOUT_in = []
        elements = []
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            transferOUT_in.append(doc_in.getMatFlowTransferOut(e))
            elements.append(e)
        doc_out = ifm.loadDocument(fem_path_out)
        c=0
        for e in range(e_per_lay_in*layer,e_per_lay_in*(layer+1)):
            doc_out.setMatFlowTransferOut(e,transferOUT_in[c])
            c=c+1
        print 'Transfer complete'
        doc_out.saveDocument(fem_path_out)
        print 'Document saved. Exiting.'
        param_df = pd.DataFrame(transferOUT_in, index=elements, columns=[param])
        return elements, transferOUT_in, param_df