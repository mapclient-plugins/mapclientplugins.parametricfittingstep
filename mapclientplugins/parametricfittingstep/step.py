
"""
MAP Client Plugin Step
"""
import json

from PySide2 import QtGui, QtWidgets

from scaffoldmaker.scaffolds import Scaffolds

from mapclient.mountpoints.workflowstep import WorkflowStepMountPoint
from mapclientplugins.parametricfittingstep.configuredialog import ConfigureDialog
from mapclientplugins.parametricfittingstep.model.mastermodel import MasterModel
from mapclientplugins.parametricfittingstep.view.parametricfittingwidget import ParametricFittingWidget


# Options for '3D Heart Ventricles with Base 2'
# options = {'Number of elements around LV free wall': 5,
#            'Number of elements around ventricular septum': 7,
#            'Number of elements up LV apex': 1,
#            'Number of elements up ventricular septum': 4,
#            'LV outer height': 0.95,
#            'LV outer radius': 0.5,
#            'LV free wall thickness': 0.12,
#            'LV apex thickness': 0.06,
#            'RV inner height': 0.8,
#            'RV arc around degrees': 200.0,
#            'RV free wall thickness': 0.04,
#            'RV width': 0.4,
#            'RV extra cross radius base': 0.1,
#            'Ventricular septum thickness': 0.1,
#            'Ventricular septum base radial displacement': 0.15,
#            'Use cross derivatives': False,
#            'Refine': False,
#            'Refine number of elements surface': 4,
#            'Refine number of elements through LV wall': 1,
#            'Refine number of elements through RV wall': 1,
#            'Number of elements around atria': 8,
#            'Atria base inner major axis length': 0.55,
#            'Atria base inner minor axis length': 0.42,
#            'Atria major axis rotation degrees': 40.0,
#            'Atrial septum thickness': 0.06,
#            'Atrial base wall thickness': 0.05,
#            'Atrial base slope degrees': 30.0,
#            'Base height': 0.12,
#            'Base thickness': 0.06,
#            'Fibrous ring thickness': 0.01,
#            'LV outlet inner diameter': 0.3,
#            'LV outlet wall thickness': 0.025,
#            'RV outlet inner diameter': 0.27,
#            'RV outlet wall thickness': 0.025,
#            'Ventricles outlet element length': 0.1,
#            'Ventricles outlet incline degrees': 15.0,
#            'Ventricles outlet spacing': 0.04}

class ParametricFittingStep(WorkflowStepMountPoint):
    """
    Skeleton step which is intended to be a helpful starting point
    for new steps.
    """

    def __init__(self, location):
        super(ParametricFittingStep, self).__init__('Parametric Fitting', location)
        self._configured = False # A step cannot be executed until it has been configured.
        self._category = 'Fitting'
        # Add any other initialisation code here:
        # self._icon =  QtGui.QImage(':/parametricfitting/images/model-viewer.png')
        # Ports:
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#provides',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#mesh_description'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#image_context_data'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#time_labelled_fiducial_marker_locations'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#scaffold_description'))
        # Port data:
        self._portData0 = None # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location
        self._image_context_data = None
        self._time_labelled_nodal_locations = None
        self._scaffold_description = '3D Heart Ventricles with Base 2'
        # Config:
        self._config = {'identifier': '', 'AutoDone': False}
        self._model = None
        self._view = None

    def execute(self):
        """
        Kick off the execution of the step, in this case an interactive dialog.
        User invokes the _doneExecution() method when finished, via pushbutton.
        """
        sc = Scaffolds()
        active_mesh = None
        for mesh_type in sc.getMeshTypes():
            if mesh_type.getName() == '3D Heart Ventricles with Base 2':
                active_mesh = mesh_type

        self._model = MasterModel(self._location, self._config['identifier'],
                                  self._image_context_data, self._time_labelled_nodal_locations,
                                  active_mesh)
        self._view = ParametricFittingWidget(self._model)
        # self._view.setWindowFlags(QtCore.Qt.Widget)
        self._view.register_done_execution(self._myDoneExecution)
        self._setCurrentWidget(self._view)

    def _myDoneExecution(self):
        self._portData0 = self._model.get_scaffold_description()
        self._model.done()
        self._view = None
        self._model = None
        self._doneExecution()

    def getPortData(self, index):
        """
        Add your code here that will return the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        provides port for this step then the index can be ignored.

        :param index: Index of the port to return.
        """
        return self._portData0 # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location

    def setPortData(self, index, data):
        if index == 1:
            self._image_context_data = data
        elif index == 2:
            self._time_labelled_nodal_locations = data
        elif index == 3:
            print('index is three@@@@@@'
            )

    def configure(self):
        """
        This function will be called when the configure icon on the step is
        clicked.  It is appropriate to display a configuration dialog at this
        time.  If the conditions for the configuration of this step are complete
        then set:
            self._configured = True
        """
        dlg = ConfigureDialog(QtWidgets.QApplication.activeWindow().currentWidget())
        dlg.identifierOccursCount = self._identifierOccursCount
        dlg.setConfig(self._config)
        dlg.validate()
        dlg.setModal(True)

        if dlg.exec_():
            self._config = dlg.getConfig()

        self._configured = dlg.validate()
        self._configuredObserver()

    def getIdentifier(self):
        """
        The identifier is a string that must be unique within a workflow.
        """
        return self._config['identifier']

    def setIdentifier(self, identifier):
        """
        The framework will set the identifier for this step when it is loaded.
        """
        self._config['identifier'] = identifier

    def serialize(self):
        """
        Add code to serialize this step to string.  This method should
        implement the opposite of 'deserialize'.
        """
        return json.dumps(self._config, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def deserialize(self, string):
        """
        Add code to deserialize this step from string.  This method should
        implement the opposite of 'serialize'.

        :param string: JSON representation of the configuration in a string.
        """
        self._config.update(json.loads(string))

        d = ConfigureDialog()
        d.identifierOccursCount = self._identifierOccursCount
        d.setConfig(self._config)
        self._configured = d.validate()


