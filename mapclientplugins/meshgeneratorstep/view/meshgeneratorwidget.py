"""
Created on Aug 29, 2017

@author: Richard Christie

Last Modigified on Aug 23, 2018 by Mahyar Osanlouy
"""
import types
import sys
import numpy as np

from PySide import QtGui, QtCore
from functools import partial

sys.path.append(
    '/hpc/mosa004/mapclient-plugins/mapclientplugins.meshgeneratorstep/mapclientplugins/meshgeneratorstep/model')
from fiducialmarkermodel import FIDUCIAL_MARKER_LABELS

sys.path.append(
    '/hpc/mosa004/mapclient-plugins/mapclientplugins.meshgeneratorstep/mapclientplugins/meshgeneratorstep/view')
from ui_meshgeneratorwidget import Ui_MeshGeneratorWidget

from opencmiss.utils.maths import vectorops
from opencmiss.zinc.status import OK as ZINC_OK

from scaffoldmaker.utils.zinc_utils import *

sys.path.append(
    '/hpc/mosa004/mapclient-plugins/mapclientplugins.parametricfittingstep/mapclientplugins/parametricfittingstep/core')
import RigidFitting

reload(RigidFitting)
from RigidFitting import RigidFitting
import DeformableFitting

reload(DeformableFitting)
from DeformableFitting import DeformableFitting


# reload(RigidFitting)
# reload(DeformableFitting)
#

class MeshGeneratorWidget(QtGui.QWidget):

    def __init__(self, model, parent=None):
        super(MeshGeneratorWidget, self).__init__(parent)
        self._ui = Ui_MeshGeneratorWidget()
        self._ui.setupUi(self)
        self._model = model
        self._model.registerTimeValueUpdateCallback(self._updateTimeValue)
        self._model.registerFrameIndexUpdateCallback(self._updateFrameIndex)
        self._generator_model = model.getGeneratorModel()
        self._plane_model = model.getPlaneModel()
        self._fiducial_marker_model = model.getFiducialMarkerModel()
        self._ui.sceneviewer_widget.setContext(model.getContext())
        self._ui.sceneviewer_widget.setModel(self._plane_model)
        self._model.registerSceneChangeCallback(self._sceneChanged)
        self._doneCallback = None
        self._populateFiducialMarkersComboBox()
        self._marker_mode_active = False
        self._have_images = False
        self.position = None
        # self._populateAnnotationTree()
        meshTypeNames = self._generator_model.getAllMeshTypeNames()
        for meshTypeName in meshTypeNames:
            self._ui.meshType_comboBox.addItem(meshTypeName)
        self._makeConnections()

        self._node_to_fit = {'apex': 46, 'lv1': 68, 'lv2': 79, 'rv1': 111, 'rv2': 117, 'rv3': 63, 'rv4': 74, 'rb': 144,
                             'rb1': 134, 'lb': 157, 'lb1': 150}

    def _graphicsInitialized(self):
        """
        Callback for when SceneviewerWidget is initialised
        Set custom scene from model
        """
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            self._model.loadSettings()
            self._refreshOptions()
            scene = self._model.getScene()
            self._ui.sceneviewer_widget.setScene(scene)
            # self._ui.sceneviewer_widget.setSelectModeAll()
            sceneviewer.setLookatParametersNonSkew([2.0, -2.0, 1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0])
            sceneviewer.setTransparencyMode(sceneviewer.TRANSPARENCY_MODE_SLOW)
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
        self._ui.meshType_comboBox.currentIndexChanged.connect(self._meshTypeChanged)
        self._ui.deleteElementsRanges_lineEdit.returnPressed.connect(self._deleteElementRangesLineEditChanged)
        self._ui.deleteElementsRanges_lineEdit.editingFinished.connect(self._deleteElementRangesLineEditChanged)
        self._ui.scale_lineEdit.returnPressed.connect(self._scaleLineEditChanged)
        self._ui.scale_lineEdit.editingFinished.connect(self._scaleLineEditChanged)
        self._ui.displayAxes_checkBox.clicked.connect(self._displayAxesClicked)
        self._ui.displayElementNumbers_checkBox.clicked.connect(self._displayElementNumbersClicked)
        self._ui.displayLines_checkBox.clicked.connect(self._displayLinesClicked)
        self._ui.displayNodeDerivatives_checkBox.clicked.connect(self._displayNodeDerivativesClicked)
        self._ui.displayNodeNumbers_checkBox.clicked.connect(self._displayNodeNumbersClicked)
        self._ui.displaySurfaces_checkBox.clicked.connect(self._displaySurfacesClicked)
        self._ui.displaySurfacesExterior_checkBox.clicked.connect(self._displaySurfacesExteriorClicked)
        self._ui.displaySurfacesTranslucent_checkBox.clicked.connect(self._displaySurfacesTranslucentClicked)
        self._ui.displaySurfacesWireframe_checkBox.clicked.connect(self._displaySurfacesWireframeClicked)
        self._ui.displayXiAxes_checkBox.clicked.connect(self._displayXiAxesClicked)
        self._ui.activeModel_comboBox.currentIndexChanged.connect(self._activeModelChanged)
        self._ui.toImage_pushButton.clicked.connect(self._imageButtonClicked)
        self._ui.displayImagePlane_checkBox.clicked.connect(self._displayImagePlaneClicked)
        self._ui.fixImagePlane_checkBox.clicked.connect(self._fixImagePlaneClicked)
        self._ui.timeValue_doubleSpinBox.valueChanged.connect(self._timeValueChanged)
        self._ui.timePlayStop_pushButton.clicked.connect(self._timePlayStopClicked)
        self._ui.frameIndex_spinBox.valueChanged.connect(self._frameIndexValueChanged)
        self._ui.framesPerSecond_spinBox.valueChanged.connect(self._framesPerSecondValueChanged)
        self._ui.timeLoop_checkBox.clicked.connect(self._timeLoopClicked)
        self._ui.displayFiducialMarkers_checkBox.clicked.connect(self._displayFiducialMarkersClicked)
        self._ui.fiducialMarker_comboBox.currentIndexChanged.connect(self._fiducialMarkerChanged)
        self._ui.fiducialMarkerTransform_pushButton_2.clicked.connect(self._calculateRigidTransform)
        self._ui.fiducialMarkerTransform_pushButton_3.clicked.connect(
            self._calculateNonRigidTransform)  # self._ui.treeWidgetAnnotation.itemSelectionChanged.connect(self._annotationSelectionChanged)  # self._ui.treeWidgetAnnotation.itemChanged.connect(self._annotationItemChanged)

    def _fiducialMarkerChanged(self):
        self._fiducial_marker_model.setActiveMarker(self._ui.fiducialMarker_comboBox.currentText())

    def _displayFiducialMarkersClicked(self):
        self._fiducial_marker_model.setDisplayFiducialMarkers(self._ui.displayFiducialMarkers_checkBox.isChecked())

    def _populateFiducialMarkersComboBox(self):
        self._ui.fiducialMarker_comboBox.addItems(FIDUCIAL_MARKER_LABELS)

    def _createFMAItem(self, parent, text, fma_id):
        item = QtGui.QTreeWidgetItem(parent)
        item.setText(0, text)
        item.setData(0, QtCore.Qt.UserRole + 1, fma_id)
        item.setCheckState(0, QtCore.Qt.Unchecked)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsTristate)

        return item

    def _populateAnnotationTree(self):
        tree = self._ui.treeWidgetAnnotation
        tree.clear()
        rsh_item = self._createFMAItem(tree, 'right side of heart', 'FMA_7165')
        self._createFMAItem(rsh_item, 'ventricle', 'FMA_7098')
        self._createFMAItem(rsh_item, 'atrium', 'FMA_7096')
        self._createFMAItem(rsh_item, 'auricle', 'FMA_7218')
        lsh_item = self._createFMAItem(tree, 'left side of heart', 'FMA_7166')
        self._createFMAItem(lsh_item, 'ventricle', 'FMA_7101')
        self._createFMAItem(lsh_item, 'atrium', 'FMA_7097')
        self._createFMAItem(lsh_item, 'auricle', 'FMA_7219')
        apex_item = self._createFMAItem(tree, 'apex of heart', 'FMA_7164')
        vortex_item = self._createFMAItem(tree, 'vortex of heart', 'FMA_84628')

        self._ui.treeWidgetAnnotation.addTopLevelItem(rsh_item)
        self._ui.treeWidgetAnnotation.addTopLevelItem(lsh_item)
        self._ui.treeWidgetAnnotation.addTopLevelItem(apex_item)
        self._ui.treeWidgetAnnotation.addTopLevelItem(vortex_item)

    def getModel(self):
        return self._model

    def registerDoneExecution(self, doneCallback):
        self._doneCallback = doneCallback

    def _updateUi(self):
        if self._have_images:
            frame_count = self._plane_model.getFrameCount()
            self._ui.numFramesValue_label.setText("{0}".format(frame_count))
            self._ui.frameIndex_spinBox.setMaximum(frame_count)
            self._ui.timeValue_doubleSpinBox.setMaximum(frame_count / self._model.getFramesPerSecond())
        else:
            self._generator_model.disableAlignment()
            self._plane_model.disableAlignment()
            self._ui.alignment_groupBox.setVisible(False)
            self._ui.fiducialMarkers_groupBox.setVisible(False)
            self._ui.video_groupBox.setVisible(False)
            self._ui.displayImagePlane_checkBox.setVisible(False)
            self._ui.displayFiducialMarkers_checkBox.setVisible(False)

    def setImageInfo(self, image_info):
        self._plane_model.setImageInfo(image_info)
        self._have_images = image_info is not None
        self._updateUi()

    def _doneButtonClicked(self):
        self._ui.dockWidget.setFloating(False)
        self._model.done()
        self._model = None
        self._doneCallback()

    def _imageButtonClicked(self):
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        normal, up, offset = self._plane_model.getPlaneInfo()
        _, current_lookat_pos = sceneviewer.getLookatPosition()
        _, current_eye_pos = sceneviewer.getEyePosition()
        view_distance = vectorops.magnitude(vectorops.sub(current_eye_pos, current_lookat_pos))
        eye_pos = vectorops.add(vectorops.mult(normal, view_distance), offset)
        lookat_pos = offset
        sceneviewer.setLookatParametersNonSkew(eye_pos, lookat_pos, up)

    def _updateTimeValue(self, value):
        self._ui.timeValue_doubleSpinBox.blockSignals(True)
        frame_count = self._plane_model.getFrameCount()
        max_time_value = frame_count / self._ui.framesPerSecond_spinBox.value()
        if value > max_time_value:
            self._ui.timeValue_doubleSpinBox.setValue(max_time_value)
            self._timePlayStopClicked()
        else:
            self._ui.timeValue_doubleSpinBox.setValue(value)
        self._ui.timeValue_doubleSpinBox.blockSignals(False)

    def _updateFrameIndex(self, value):
        self._ui.frameIndex_spinBox.blockSignals(True)
        self._ui.frameIndex_spinBox.setValue(value)
        self._ui.frameIndex_spinBox.blockSignals(False)

    def _timeValueChanged(self, value):
        self._model.setTimeValue(value)

    def _timeDurationChanged(self, value):
        self._model.setTimeDuration(value)

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

    def _frameIndexValueChanged(self, value):
        self._model.setFrameIndex(value)

    def _framesPerSecondValueChanged(self, value):
        self._model.setFramesPerSecond(value)
        self._ui.timeValue_doubleSpinBox.setMaximum(self._plane_model.getFrameCount() / value)

    def _fixImagePlaneClicked(self):
        self._plane_model.setImagePlaneFixed(self._ui.fixImagePlane_checkBox.isChecked())

    def _displayImagePlaneClicked(self):
        self._plane_model.setImagePlaneVisible(self._ui.displayImagePlane_checkBox.isChecked())

    def _activeModelChanged(self, index):
        if index == 0:
            self._ui.sceneviewer_widget.setModel(self._plane_model)
        else:
            self._ui.sceneviewer_widget.setModel(self._generator_model)

    def _meshTypeChanged(self, index):
        meshTypeName = self._ui.meshType_comboBox.itemText(index)
        self._generator_model.setMeshTypeByName(meshTypeName)
        self._refreshMeshTypeOptions()

    def _meshTypeOptionCheckBoxClicked(self, checkBox):
        self._generator_model.setMeshTypeOption(checkBox.objectName(), checkBox.isChecked())

    def _meshTypeOptionLineEditChanged(self, lineEdit):
        self._generator_model.setMeshTypeOption(lineEdit.objectName(), lineEdit.text())
        finalValue = self._generator_model.getMeshTypeOption(lineEdit.objectName())
        lineEdit.setText(str(finalValue))

    def _refreshMeshTypeOptions(self):
        layout = self._ui.meshTypeOptions_frame.layout()
        # remove all current mesh type widgets
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        optionNames = self._generator_model.getMeshTypeOrderedOptionNames()
        for key in optionNames:
            value = self._generator_model.getMeshTypeOption(key)
            # print('key ', key, ' value ', value)
            if type(value) is bool:
                checkBox = QtGui.QCheckBox(self._ui.meshTypeOptions_frame)
                checkBox.setObjectName(key)
                checkBox.setText(key)
                checkBox.setChecked(value)
                callback = partial(self._meshTypeOptionCheckBoxClicked, checkBox)
                checkBox.clicked.connect(callback)
                layout.addWidget(checkBox)
            else:
                label = QtGui.QLabel(self._ui.meshTypeOptions_frame)
                label.setObjectName(key)
                label.setText(key)
                layout.addWidget(label)
                lineEdit = QtGui.QLineEdit(self._ui.meshTypeOptions_frame)
                lineEdit.setObjectName(key)
                lineEdit.setText(str(value))
                callback = partial(self._meshTypeOptionLineEditChanged, lineEdit)
                lineEdit.returnPressed.connect(callback)
                lineEdit.editingFinished.connect(callback)
                layout.addWidget(lineEdit)

    def _refreshOptions(self):
        self._ui.identifier_label.setText('Identifier:  ' + self._model.getIdentifier())
        self._ui.deleteElementsRanges_lineEdit.setText(self._generator_model.getDeleteElementsRangesText())
        self._ui.scale_lineEdit.setText(self._generator_model.getScaleText())
        self._ui.displayAxes_checkBox.setChecked(self._generator_model.isDisplayAxes())
        self._ui.displayElementNumbers_checkBox.setChecked(self._generator_model.isDisplayElementNumbers())
        self._ui.displayLines_checkBox.setChecked(self._generator_model.isDisplayLines())
        self._ui.displayNodeDerivatives_checkBox.setChecked(self._generator_model.isDisplayNodeDerivatives())
        self._ui.displayNodeNumbers_checkBox.setChecked(self._generator_model.isDisplayNodeNumbers())
        self._ui.displaySurfaces_checkBox.setChecked(self._generator_model.isDisplaySurfaces())
        self._ui.displaySurfacesExterior_checkBox.setChecked(self._generator_model.isDisplaySurfacesExterior())
        self._ui.displaySurfacesTranslucent_checkBox.setChecked(self._generator_model.isDisplaySurfacesTranslucent())
        self._ui.displaySurfacesWireframe_checkBox.setChecked(self._generator_model.isDisplaySurfacesWireframe())
        self._ui.displayXiAxes_checkBox.setChecked(self._generator_model.isDisplayXiAxes())
        self._ui.displayImagePlane_checkBox.setChecked(self._plane_model.isDisplayImagePlane())
        self._ui.displayFiducialMarkers_checkBox.setChecked(self._fiducial_marker_model.isDisplayFiducialMarkers())
        self._ui.fixImagePlane_checkBox.setChecked(self._plane_model.isImagePlaneFixed())
        self._ui.framesPerSecond_spinBox.setValue(self._model.getFramesPerSecond())
        self._ui.timeLoop_checkBox.setChecked(self._model.isTimeLoop())
        index = self._ui.meshType_comboBox.findText(self._generator_model.getMeshTypeName())
        self._ui.meshType_comboBox.blockSignals(True)
        self._ui.meshType_comboBox.setCurrentIndex(index)
        self._ui.meshType_comboBox.blockSignals(False)
        index = self._ui.fiducialMarker_comboBox.findText(self._fiducial_marker_model.getActiveMarker())
        self._ui.fiducialMarker_comboBox.blockSignals(True)
        self._ui.fiducialMarker_comboBox.setCurrentIndex(0 if index == -1 else index)
        self._ui.fiducialMarker_comboBox.blockSignals(False)
        self._refreshMeshTypeOptions()

    def _deleteElementRangesLineEditChanged(self):
        self._generator_model.setDeleteElementsRangesText(self._ui.deleteElementsRanges_lineEdit.text())
        self._ui.deleteElementsRanges_lineEdit.setText(self._generator_model.getDeleteElementsRangesText())

    def _scaleLineEditChanged(self):
        self._generator_model.setScaleText(self._ui.scale_lineEdit.text())
        self._ui.scale_lineEdit.setText(self._generator_model.getScaleText())

    def _displayAxesClicked(self):
        self._generator_model.setDisplayAxes(self._ui.displayAxes_checkBox.isChecked())

    def _displayElementNumbersClicked(self):
        self._generator_model.setDisplayElementNumbers(self._ui.displayElementNumbers_checkBox.isChecked())

    def _displayLinesClicked(self):
        self._generator_model.setDisplayLines(self._ui.displayLines_checkBox.isChecked())
        self._autoPerturbLines()

    def _displayNodeDerivativesClicked(self):
        self._generator_model.setDisplayNodeDerivatives(self._ui.displayNodeDerivatives_checkBox.isChecked())

    def _displayNodeNumbersClicked(self):
        self._generator_model.setDisplayNodeNumbers(self._ui.displayNodeNumbers_checkBox.isChecked())

    def _displaySurfacesClicked(self):
        self._generator_model.setDisplaySurfaces(self._ui.displaySurfaces_checkBox.isChecked())
        self._autoPerturbLines()

    def _displaySurfacesExteriorClicked(self):
        self._generator_model.setDisplaySurfacesExterior(self._ui.displaySurfacesExterior_checkBox.isChecked())

    def _displaySurfacesTranslucentClicked(self):
        self._generator_model.setDisplaySurfacesTranslucent(self._ui.displaySurfacesTranslucent_checkBox.isChecked())
        self._autoPerturbLines()

    def _displaySurfacesWireframeClicked(self):
        self._generator_model.setDisplaySurfacesWireframe(self._ui.displaySurfacesWireframe_checkBox.isChecked())

    def _displayXiAxesClicked(self):
        self._generator_model.setDisplayXiAxes(self._ui.displayXiAxes_checkBox.isChecked())

    def _annotationItemChanged(self, item):
        print(item.text(0))
        print(item.data(0, QtCore.Qt.UserRole + 1))

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

        # fiducial_marker_positions = np.asarray(self._fiducial_marker_model.getNodeLocation())
        fiducial_marker_positions = np.array([# [-0.08378320041032739, 0.060020191975871384, -0.6624821566239206],
            # [0.031569907135766684, 0.007679908312357764, -0.45690192510382405],
            # [0.10025877161353991, -0.021277717915205052, -0.1899708861054778],
            # [-0.39645071642271734, 0.2129401665689472, -0.4968680795311444],
            # [-0.538519453504519, 0.2856339320621082, -0.21160289284989792],
            # [-0.3031422475589496, 0.16863751602454125, -0.45910690793069187],
            # [-0.3141388179601403, 0.1778349211632646, -0.20345438227174692],
            # [-0.45093644663685417, 0.2466547356686979, -0.005754280505576248],
            # [-0.27930466280608646, 0.16388375408230305, -0.020065259452618694],
            # [0.03039541184136718, 0.014243606953794785, -0.06449774186629487],
            # [-0.08027159569963116, 0.06771364158539495, -0.04873733748563988]
        [-0.00185130586563087, 0.02014437569480032, -0.6930864216685104],
        [0.16726735467477938, -0.057467425940428196, -0.4489856949630478],
        [0.15164180124034088, -0.04558319230271746, -0.16321920523491512],
        [0.11913537315196265, -0.028436558536795165, -0.06434276579316178],
        [-0.3981724786424108, 0.21375016245879674, -0.4980550045833302],
        [-0.5178401893040329, 0.275967953790734, -0.1932592096318814],
        [-0.4282651966143486, 0.23619796011707628, 0.02353425298619749],
        [-0.28077328623803677, 0.15808500306750117, -0.44559187130116923],
        [-0.32922047697142653, 0.18548704074526645, -0.17741457658734572],
        [-0.2581494182460182, 0.15390004646864242, -0.0075296953943526646],
        [-0.002717050948245703, 0.030417249846416805, -0.04833619687679752]

        ])

        """ computing rigid transformation parameters 1 """
        _, transformation = self._rigidTransform(fiducial_marker_positions, node_value_array)
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
        _, transformation = self._rigidTransform(fiducial_marker_positions, node_set_array)
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

        # fiducial_marker_positions = np.asarray(self._fiducial_marker_model.getNodeLocation())
        fiducial_marker_positions = np.array([
            # [-0.08378320041032739, 0.060020191975871384, -0.6624821566239206],
            # [0.031569907135766684, 0.007679908312357764, -0.45690192510382405],
            # [0.10025877161353991, -0.021277717915205052, -0.1899708861054778],
            # [-0.39645071642271734, 0.2129401665689472, -0.4968680795311444],
            # [-0.538519453504519, 0.2856339320621082, -0.21160289284989792],
            # [-0.3031422475589496, 0.16863751602454125, -0.45910690793069187],
            # [-0.3141388179601403, 0.1778349211632646, -0.20345438227174692],
            # [-0.45093644663685417, 0.2466547356686979, -0.005754280505576248],
            # [-0.27930466280608646, 0.16388375408230305, -0.020065259452618694],
            # [0.03039541184136718, 0.014243606953794785, -0.06449774186629487],
            # [-0.08027159569963116, 0.06771364158539495, -0.04873733748563988]
            [-0.00185130586563087, 0.02014437569480032, -0.6930864216685104],
            [0.16726735467477938, -0.057467425940428196, -0.4489856949630478],
            [0.15164180124034088, -0.04558319230271746, -0.16321920523491512],
            [0.11913537315196265, -0.028436558536795165, -0.06434276579316178],
            [-0.3981724786424108, 0.21375016245879674, -0.4980550045833302],
            [-0.5178401893040329, 0.275967953790734, -0.1932592096318814],
            [-0.4282651966143486, 0.23619796011707628, 0.02353425298619749],
            [-0.28077328623803677, 0.15808500306750117, -0.44559187130116923],
            [-0.32922047697142653, 0.18548704074526645, -0.17741457658734572],
            [-0.2581494182460182, 0.15390004646864242, -0.0075296953943526646],
            [-0.002717050948245703, 0.030417249846416805, -0.04833619687679752]])

        """ getting the nodal parameters """
        fieldmodule, nodes = self._getFieldmoduleAndAllNodes()
        node_value_array, coordinates = self._getNodeValueArrayAndCoordinates(fieldmodule, nodes)
        cache = fieldmodule.createFieldcache()
        node_set_array = self._getNodeNumpyArray(cache, fieldmodule, nodes, coordinates)

        """ computing non-rigid transformation parameters """
        _, transformation = self._nonRigidTransform(fiducial_marker_positions[:, 1:3], node_set_array[:, 1:3])
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
            #     # _, dx_ds1 = coordinates.getNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS1, 1, 3)  # dx/ds1
            #     # dx1.append(dx_ds1)
            #     # _, dx_ds2 = coordinates.getNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS2, 1, 3)  # dx/ds2
            #     # dx2.append(dx_ds2)
            #     # _, dx_ds3 = coordinates.getNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS3, 1, 3)  # dx/ds3
            #     # dx3.append(dx_ds3)

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

    def _viewAll(self):
        """
        Ask sceneviewer to show all of scene.
        """
        if self._ui.sceneviewer_widget.getSceneviewer() is not None:
            self._ui.sceneviewer_widget.viewAll()

    def keyPressEvent(self, event):
        if event.modifiers() & QtCore.Qt.CTRL and QtGui.QApplication.mouseButtons() == QtCore.Qt.NoButton:
            self._marker_mode_active = True
            self._ui.sceneviewer_widget._model = self._fiducial_marker_model
            self._original_mousePressEvent = self._ui.sceneviewer_widget.mousePressEvent
            self._ui.sceneviewer_widget._calculatePointOnPlane = types.MethodType(_calculatePointOnPlane,
                                                                                  self._ui.sceneviewer_widget)
            self._ui.sceneviewer_widget.mousePressEvent = types.MethodType(mousePressEvent, self._ui.sceneviewer_widget)
            self._model.printLog()

    def keyReleaseEvent(self, event):
        if self._marker_mode_active:
            self._marker_mode_active = False
            self._ui.sceneviewer_widget._model = self._plane_model
            self._ui.sceneviewer_widget._calculatePointOnPlane = None
            self._ui.sceneviewer_widget.mousePressEvent = self._original_mousePressEvent


def mousePressEvent(self, event):
    if self._active_button != QtCore.Qt.NoButton:
        return

    if (event.modifiers() & QtCore.Qt.CTRL) and event.button() == QtCore.Qt.LeftButton:
        point_on_plane = self._calculatePointOnPlane(event.x(), event.y())
        if point_on_plane is not None:
            self._model.setNodeLocation(point_on_plane)


def _calculatePointOnPlane(self, x, y):
    from opencmiss.utils.maths.algorithms import calculateLinePlaneIntersection

    far_plane_point = self.unproject(x, -y, -1.0)
    near_plane_point = self.unproject(x, -y, 1.0)
    plane_point, plane_normal = self._model.getPlaneDescription()
    point_on_plane = calculateLinePlaneIntersection(near_plane_point, far_plane_point, plane_point, plane_normal)

    return point_on_plane
