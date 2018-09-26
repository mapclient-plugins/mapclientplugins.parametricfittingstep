
import numpy as np

from PySide import QtGui

from opencmiss.zinc.status import OK as ZINC_OK

from mapclientplugins.parametricfittingstep.view.ui_parametricfittingwidget import Ui_ParametricFittingWidget
from sparc.parametricfitting.rigidfitting import RigidFitting
from sparc.parametricfitting.deformablefitting import DeformableFitting


class ParametricFittingWidget(QtGui.QWidget):

    def __init__(self, model, parent=None):
        super(ParametricFittingWidget, self).__init__(parent)
        self._ui = Ui_ParametricFittingWidget()
        self._ui.setupUi(self)
        self._model = model
        self._ui.sceneviewer_widget.setContext(model.getContext())
        self._doneCallback = None
        self._makeConnections()

        self._node_to_fit = {'apex': 46, 'lv1': 68, 'lv2': 79, 'rv1': 111, 'rv2': 117, 'rv3': 63, 'rv4': 74, 'rb': 144,
                             'rb1': 134, 'lb': 157, 'lb1': 150}

        self.fiducial_marker_positions = None

    def _graphicsInitialized(self):
        """
        Callback for when SceneviewerWidget is initialised
        Set custom scene from model
        """
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            self._model.loadSettings()
            scene = self._model.getScene()
            self._ui.sceneviewer_widget.setScene(scene)
            self._autoPerturbLines()
            self._viewAll()

    def _sceneChanged(self):
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            if self._have_images:
                self._plane_model.setSceneviewer(sceneviewer)
            scene = self._model.getScene()
            self._ui.sceneviewer_widget.setScene(scene)
            self._autoPerturbLines()

    def _autoPerturbLines(self):
        """
        Enable scene viewer perturb lines iff solid surfaces are drawn with lines.
        Call whenever lines, surfaces or translucency changes
        """
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            sceneviewer.setPerturbLinesFlag(self._generator_model.needPerturbLines())

    def _makeConnections(self):
        self._ui.sceneviewer_widget.graphicsInitialized.connect(self._graphicsInitialized)
        self._ui.done_button.clicked.connect(self._doneButtonClicked)
        self._ui.viewAll_button.clicked.connect(self._viewAll)
        self._ui.timeValue_doubleSpinBox.valueChanged.connect(self._timeValueChanged)
        self._ui.timePlayStop_pushButton.clicked.connect(self._timePlayStopClicked)
        self._ui.timeLoop_checkBox.clicked.connect(self._timeLoopClicked)

    def getModel(self):
        return self._model

    def registerDoneExecution(self, doneCallback):
        self._doneCallback = doneCallback

    def _updateUi(self):
        pass

    def _doneButtonClicked(self):
        self._ui.dockWidget.setFloating(False)
        self._model.done()
        self._model = None
        self._doneCallback()

    def _timeValueChanged(self, value):
        self._model.setTimeValue(value)

    def _timePlayStopClicked(self):
        play_text = 'Play'
        stop_text = 'Stop'
        current_text = self._ui.timePlayStop_pushButton.text()
        if current_text == play_text:
            self._ui.timePlayStop_pushButton.setText(stop_text)
            self._model.play()
        else:
            self._ui.timePlayStop_pushButton.setText(play_text)
            self._model.stop()

    def _timeLoopClicked(self):
        self._model.setTimeLoop(self._ui.timeLoop_checkBox.isChecked())

    def _refreshOptions(self):
        pass

    def _calculateRigidTransform(self):
        """
        Performs a rigid transformation of scaffold to fiducial landmarks and updates the view.

        :return:
        """

        print
        print('Rigid Fitting...')
        print

        fieldmodule, nodes = self._getFieldmoduleAndAllNodes()
        node_value_array, coordinates = self._getNodeValueArrayAndCoordinates(fieldmodule, nodes)
        cache = fieldmodule.createFieldcache()

        if self.fiducial_marker_positions is not None:
            self.fiducial_marker_positions = None
            self.fiducial_marker_positions = np.asarray(self._fiducial_marker_model.getNodeLocation())

        """ computing rigid transformation parameters 1 """
        _, transformation = self._rigidTransform(self.fiducial_marker_positions, node_value_array)
        ridid_scale = transformation.s

        """ scaling 1 """
        scale = fieldmodule.createFieldConstant([ridid_scale, ridid_scale, ridid_scale])
        newCoordinates = fieldmodule.createFieldMultiply(coordinates, scale)
        fieldassignment = coordinates.createFieldassignment(newCoordinates)
        fieldassignment.assign()

        del fieldmodule
        del nodes
        del cache
        del coordinates
        del transformation
        del ridid_scale
        del scale
        del newCoordinates
        del fieldassignment

        """ getting the nodal parameters """
        fieldmodule, nodes = self._getFieldmoduleAndAllNodes()
        _, coordinates = self._getNodeValueArrayAndCoordinates(fieldmodule, nodes)
        cache = fieldmodule.createFieldcache()
        node_set_array = self._getNodeNumpyArray(cache, fieldmodule, nodes, coordinates)

        """ computing rigid transformation parameters 2 """
        _, transformation = self._rigidTransform(self.fiducial_marker_positions, node_set_array)
        rigid_rotation, rigid_translation, ridid_scale = transformation.R, transformation.t, transformation.s

        """ finding the new node positions """
        transformed_nodes = np.dot(node_set_array, np.transpose(rigid_rotation)) + np.tile(
            np.transpose(rigid_translation), (node_set_array.shape[0], 1))

        """ scaling 2 """
        scale = fieldmodule.createFieldConstant([ridid_scale, ridid_scale, ridid_scale])
        newCoordinates = fieldmodule.createFieldMultiply(coordinates, scale)
        fieldassignment = coordinates.createFieldassignment(newCoordinates)
        fieldassignment.assign()

        """ setting the nodal parameters """
        self._setNodeParams(cache, fieldmodule, nodes, coordinates, transformed_nodes, node_set_array)

    def _calculateNonRigidTransform(self):
        print
        print('Non-Rigid Fitting...')
        print

        if self.fiducial_marker_positions is not None:
            self.fiducial_marker_positions = None
            self.fiducial_marker_positions = np.asarray(self._fiducial_marker_model.getNodeLocation())

        """ getting the nodal parameters """
        fieldmodule, nodes = self._getFieldmoduleAndAllNodes()
        node_value_array, coordinates = self._getNodeValueArrayAndCoordinates(fieldmodule, nodes)
        cache = fieldmodule.createFieldcache()
        node_set_array = self._getNodeNumpyArray(cache, fieldmodule, nodes, coordinates)

        """ computing non-rigid transformation parameters """
        _, transformation = self._nonRigidTransform(self.fiducial_marker_positions[:, 1:3], node_set_array[:, 1:3])
        transformed_nodes = node_set_array[:, 1:3] + np.dot(transformation.G, transformation.W)

        """ setting the nodal parameters """
        self._setNodeParams(cache, fieldmodule, nodes, coordinates, transformed_nodes, node_set_array, rigid=False)

        del fieldmodule
        del nodes
        del cache
        del coordinates
        del transformation

    def _getNodeValueArrayAndCoordinates(self, fm, nds):
        """
        Returns the nodal xyz values of a node set as np array. Also
        returns the coordiate field.

        :param fm: fieldmodule
        :param nds: node set
        :return: node values as np array, coordinate field
        """
        fieldmodule, nodes = fm, nds
        reference_nodes_to_fit = self._node_to_fit
        node_value_list = []

        fieldmodule.beginChange()
        coordinates = getOrCreateCoordinateField(fieldmodule)
        cache = fieldmodule.createFieldcache()
        for n in range(len(reference_nodes_to_fit)):
            id = list(reference_nodes_to_fit.keys())[n]
            node = nodes.findNodeByIdentifier(reference_nodes_to_fit[id])
            cache.setNode(node)
            _, xyz = coordinates.getNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, 3)
            node_value_list.append(xyz)
        del cache
        fieldmodule.endChange()
        return np.asarray(node_value_list), coordinates

    def _getFieldmoduleAndAllNodes(self):
        """

        :return: fieldmodule, node set
        """
        from opencmiss.zinc.field import Field

        region = self._generator_model._region
        fieldmodule = region.getFieldmodule()
        nodes = fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        return fieldmodule, nodes

    def _getNodeNumpyArray(self, c, fm, n, coor):
        cache, fieldmodule, nodes, coordinates = c, fm, n, coor

        fieldmodule.beginChange()
        node_iter = nodes.createNodeiterator()
        node = node_iter.next()
        node_set_list = []
        while node.isValid():
            cache.setNode(node)
            _, xyz = coordinates.getNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, 3)  # coordinates
            node_set_list.append(xyz)
            node = node_iter.next()
        fieldmodule.endChange()
        return np.asarray(node_set_list)

    def _setNodeParams(self, c, fm, n, coor, t_n, narray, rigid=True):
        """

        :param c: cache
        :param fm: fieldmodule
        :param n: nodeset
        :param coor: coordinates
        :param t_n: transformed node - numpy array
        :return:
        """
        cache, fieldmodule, nodes, coordinates, transformed_nodes = c, fm, n, coor, t_n

        fieldmodule.beginChange()
        node_iter = nodes.createNodeiterator()
        node = node_iter.next()

        for n in range(len(transformed_nodes)):
            n_list = transformed_nodes[n].tolist()
            cache.setNode(node)
            if not rigid:
                new_n_list = []
                new_n_list.append(narray[n][0])
                new_n_list.append(n_list[0])
                new_n_list.append(n_list[1])
                result = coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, new_n_list)
            else:
                result = coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, n_list)
            if result == ZINC_OK:
                pass
            else:
                break
            node = node_iter.next()

        fieldmodule.endChange()
        return None

    def _rigidTransform(self, landmark, node):
        """

        :param landmark: a numpy array of fiducial landmark points on the image
        :param node: a numpy array selected nodes to compute the transform
        :return: transformed nodes
        """
        fitting = RigidFitting(**{'X': landmark, 'Y': node})
        TY, _ = fitting.fit()

        return TY, fitting

    def _nonRigidTransform(self, landmark, node):
        """

        :param landmark: a numpy array of fiducial landmark points on the image
        :param node: a numpy array selected nodes to compute the transform
        :return: transformed nodes
        """
        fitting = DeformableFitting(**{'X': landmark, 'Y': node})
        TY, _ = fitting.fit()

        return TY, fitting

    """ End of Mahyar's code """

    def _viewAll(self):
        """
        Ask sceneviewer to show all of scene.
        """
        if self._ui.sceneviewer_widget.getSceneviewer() is not None:
            self._ui.sceneviewer_widget.viewAll()
