
import numpy as np

from PySide import QtGui

from opencmiss.zinc.status import OK as ZINC_OK
from opencmiss.zinc.node import Node
from opencmiss.zinc.field import Field
from opencmiss.zinchandlers.scenemanipulation import SceneManipulation

from sparc.parametricfitting.rigidfitting import RigidFitting
from sparc.parametricfitting.deformablefitting import DeformableFitting

from mapclientplugins.parametricfittingstep.view.ui_parametricfittingwidget import Ui_ParametricFittingWidget

PLAY_TEXT = 'Play'
STOP_TEXT = 'Stop'


class ParametricFittingWidget(QtGui.QWidget):

    def __init__(self, model, parent=None):
        super(ParametricFittingWidget, self).__init__(parent)
        self._ui = Ui_ParametricFittingWidget()
        self._ui.setupUi(self)
        self._model = model
        self._ui.sceneviewer_widget.set_context(model.get_context())
        self._model.register_time_value_update_callback(self._update_time_value)

        self._done_callback = None
        self._initialise_ui()
        self._setup_handlers()
        self._make_connections()

        self._node_to_fit = {'apex': 46, 'lv1': 68, 'lv2': 79, 'rv1': 111, 'rv2': 117, 'rv3': 63, 'rv4': 74, 'rb': 144,
                             'rb1': 134, 'lb': 157, 'lb1': 150}

        self.fiducial_marker_positions = None

    def _graphics_initialized(self):
        """
        Callback for when SceneviewerWidget is initialised
        Set custom scene from model
        """
        sceneviewer = self._ui.sceneviewer_widget.get_zinc_sceneviewer()
        if sceneviewer is not None:
            self._model.load_settings()
            scene = self._model.get_scene()
            self._ui.sceneviewer_widget.set_scene(scene)
            self._view_all()

    def _make_connections(self):
        self._ui.sceneviewer_widget.graphics_initialized.connect(self._graphics_initialized)
        self._ui.done_button.clicked.connect(self._done_button_clicked)
        self._ui.viewAll_button.clicked.connect(self._view_all)
        self._ui.timeValue_doubleSpinBox.valueChanged.connect(self._time_value_changed)
        self._ui.timePlayStop_pushButton.clicked.connect(self._time_play_stop_clicked)
        self._ui.timeLoop_checkBox.clicked.connect(self._time_loop_clicked)
        self._model.time_stopped.connect(self._time_play_stop_clicked)

    def _setup_handlers(self):
        basic_handler = SceneManipulation()
        self._ui.sceneviewer_widget.register_handler(basic_handler)

    def _initialise_ui(self):
        frame_count = self._model.get_frame_count()
        frames_per_second = self._model.get_frames_per_second()
        duration = frame_count / frames_per_second
        self._model.set_maximum_time_value(duration)
        self._ui.timeValue_doubleSpinBox.setMaximum(duration)
        self._ui.timeValue_doubleSpinBox.setSingleStep(1 / frames_per_second)
        self._ui.timeLoop_checkBox.setChecked(self._model.is_time_loop())

    def get_model(self):
        return self._model

    def register_done_execution(self, done_callback):
        self._done_callback = done_callback

    def _update_ui(self):
        pass

    def _update_time_value(self, value):
        self._ui.timeValue_doubleSpinBox.blockSignals(True)
        self._ui.timeValue_doubleSpinBox.setValue(value)
        self._ui.timeValue_doubleSpinBox.blockSignals(False)

    def _done_button_clicked(self):
        self._ui.dockWidget.setFloating(False)
        self._model.done()
        self._model = None
        self._done_callback()

    def _time_value_changed(self, value):
        self._model.set_time_value(value)

    def _time_play_stop_clicked(self):
        current_text = self._ui.timePlayStop_pushButton.text()
        if current_text == PLAY_TEXT:
            self._ui.timePlayStop_pushButton.setText(STOP_TEXT)
            self._model.play()
        else:
            self._ui.timePlayStop_pushButton.setText(PLAY_TEXT)
            self._model.stop()

    def _time_loop_clicked(self):
        self._model.set_time_loop(self._ui.timeLoop_checkBox.isChecked())

    def _refresh_options(self):
        pass

    def _calculate_rigid_transform(self):
        """
        Performs a rigid transformation of scaffold to fiducial landmarks and updates the view.

        :return:
        """

        print()
        print('Rigid Fitting...')
        print()

        field_module, nodes = self._get_field_module_and_all_nodes()
        node_value_array, coordinates = self._get_node_value_array_and_coordinates(field_module, nodes)
        cache = field_module.createFieldcache()

        if self.fiducial_marker_positions is not None:
            self.fiducial_marker_positions = None
            self.fiducial_marker_positions = np.asarray(self._fiducial_marker_model.getNodeLocation())

        """ computing rigid transformation parameters 1 """
        _, transformation = self._rigid_transform(self.fiducial_marker_positions, node_value_array)
        ridid_scale = transformation.s

        """ scaling 1 """
        scale = field_module.createFieldConstant([ridid_scale, ridid_scale, ridid_scale])
        newCoordinates = field_module.createFieldMultiply(coordinates, scale)
        fieldassignment = coordinates.createFieldassignment(newCoordinates)
        fieldassignment.assign()

        del field_module
        del nodes
        del cache
        del coordinates
        del transformation
        del ridid_scale
        del scale
        del newCoordinates
        del fieldassignment

        """ getting the nodal parameters """
        _, coordinates = self._get_node_value_array_and_coordinates(field_module, nodes)
        cache = field_module.createFieldcache()
        node_set_array = self._get_node_numpy_array(cache, field_module, nodes, coordinates)

        """ computing rigid transformation parameters 2 """
        _, transformation = self._rigid_transform(self.fiducial_marker_positions, node_set_array)
        rigid_rotation, rigid_translation, ridid_scale = transformation.R, transformation.t, transformation.s

        """ finding the new node positions """
        transformed_nodes = np.dot(node_set_array, np.transpose(rigid_rotation)) + np.tile(
            np.transpose(rigid_translation), (node_set_array.shape[0], 1))

        """ scaling 2 """
        scale = field_module.createFieldConstant([ridid_scale, ridid_scale, ridid_scale])
        newCoordinates = field_module.createFieldMultiply(coordinates, scale)
        fieldassignment = coordinates.createFieldassignment(newCoordinates)
        fieldassignment.assign()

        """ setting the nodal parameters """
        self._set_node_params(cache, field_module, nodes, coordinates, transformed_nodes, node_set_array)

    def _calculate_non_rigid_transform(self):
        print()
        print('Non-Rigid Fitting...')
        print()

        if self.fiducial_marker_positions is not None:
            self.fiducial_marker_positions = None
            self.fiducial_marker_positions = np.asarray(self._fiducial_marker_model.getNodeLocation())

        """ getting the nodal parameters """
        field_module, nodes = self._get_field_module_and_all_nodes()
        node_value_array, coordinates = self._get_node_value_array_and_coordinates(field_module, nodes)
        cache = field_module.createFieldcache()
        node_set_array = self._get_node_numpy_array(cache, field_module, nodes, coordinates)

        """ computing non-rigid transformation parameters """
        _, transformation = self._non_rigid_transform(self.fiducial_marker_positions[:, 1:3], node_set_array[:, 1:3])
        transformed_nodes = node_set_array[:, 1:3] + np.dot(transformation.G, transformation.W)

        """ setting the nodal parameters """
        self._set_node_params(cache, field_module, nodes, coordinates, transformed_nodes, node_set_array, rigid=False)

        del field_module
        del nodes
        del cache
        del coordinates
        del transformation

    def _get_node_value_array_and_coordinates(self, field_module, nodes):
        """
        Returns the nodal xyz values of a node set as np array. Also
        returns the coordinate field.

        :param field_module: field_module
        :param nodes: node set
        :return: node values as np array, coordinate field
        """
        reference_nodes_to_fit = self._node_to_fit
        node_value_list = []

        field_module.beginChange()
        coordinate_field = field_module.findFieldByName('coordinates')
        cache = field_module.createFieldcache()
        for n in range(len(reference_nodes_to_fit)):
            id = list(reference_nodes_to_fit.keys())[n]
            node = nodes.findNodeByIdentifier(reference_nodes_to_fit[id])
            cache.setNode(node)
            _, xyz = coordinate_field.getNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, 3)
            node_value_list.append(xyz)
        del cache
        field_module.endChange()
        return np.asarray(node_value_list), coordinate_field

    def _get_field_module_and_all_nodes(self):
        region = self._generator_model.get_region()
        field_module = region.getFieldmodule()
        nodes = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        return field_module, nodes

    """ End of Mahyar's code """

    def _view_all(self):
        """
        Ask sceneviewer to show all of scene.
        """
        if self._ui.sceneviewer_widget.get_zinc_sceneviewer() is not None:
            self._ui.sceneviewer_widget.view_all()


def _get_node_numpy_array(field_cache, field_module, nodes, coordinates):

    field_module.beginChange()
    node_iter = nodes.createNodeiterator()
    node = node_iter.next()
    node_set_list = []
    while node.isValid():
        field_cache.setNode(node)
        _, xyz = coordinates.getNodeParameters(field_cache, -1, Node.VALUE_LABEL_VALUE, 1, 3)  # coordinates
        node_set_list.append(xyz)
        node = node_iter.next()
    field_module.endChange()
    return np.asarray(node_set_list)


def _set_node_params(field_cache, field_module, nodes, coordinates, transformed_nodes, numpy_array, rigid=True):

    field_module.beginChange()
    node_iter = nodes.createNodeiterator()
    node = node_iter.next()

    for n in range(len(transformed_nodes)):
        n_list = transformed_nodes[n].tolist()
        field_cache.setNode(node)
        if not rigid:
            new_n_list = [numpy_array[n][0], n_list[0], n_list[1]]
            result = coordinates.setNodeParameters(field_cache, -1, Node.VALUE_LABEL_VALUE, 1, new_n_list)
        else:
            result = coordinates.setNodeParameters(field_cache, -1, Node.VALUE_LABEL_VALUE, 1, n_list)
        if result == ZINC_OK:
            pass
        else:
            break
        node = node_iter.next()

    field_module.endChange()


def _rigid_transform(landmark, node):
    """

    :param landmark: a numpy array of fiducial landmark points on the image
    :param node: a numpy array selected nodes to compute the transform
    :return: transformed nodes
    """
    fitting = RigidFitting(**{'X': landmark, 'Y': node})
    TY, _ = fitting.fit()

    return TY, fitting


def _non_rigid_transform(landmark, node):
    """

    :param landmark: a numpy array of fiducial landmark points on the image
    :param node: a numpy array selected nodes to compute the transform
    :return: transformed nodes
    """
    fitting = DeformableFitting(**{'X': landmark, 'Y': node})
    TY, _ = fitting.fit()

    return TY, fitting

