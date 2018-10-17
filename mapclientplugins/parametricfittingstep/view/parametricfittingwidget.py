
import numpy as np
from scipy.optimize import minimize

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

        self._scaffold_fit_nodes = {'lv_apex': 62, 'rv_apex': 167,
                                    'lv1': 85, 'lv2': 109,
                                    'sept1': 91, 'sept2': 103,
                                    'rv1': 175, 'rv2': 191,
                                    'rb1': 255, 'rb2': 210,
                                    'lb1': 258, 'lb2': 237}
        self._fiducial_fit_nodes = {'lv_apex': 1, 'rv_apex': 5,
                                    'lv1': 6, 'lv2': 7,
                                    'sept1': 8, 'sept2': 9,
                                    'rv1': 10, 'rv2': 11,
                                    'rb1': 12, 'rb2': 2,
                                    'lb1': 3, 'lb2': 4}
        self._applied_rotation_mx = np.matrix('1 0 0; 0 1 0; 0 0 1')
        self._applied_translation_vec = np.matrix('0; 0; 0')

        self._fiducial_marker_positions = None

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
        self._ui.fittingScale_pushButton.clicked.connect(self._perform_scaffold_scale)
        self._ui.fittingFitRigidly_pushButton.clicked.connect(self._do_rigid_fit)
        self._ui.fittingFitNonRigidly_pushButton.clicked.connect(self._do_non_linear_fit)
        self._ui.fittingXAxis_pushButton.clicked.connect(self._rotate_scaffold)
        self._ui.fittingYAxis_pushButton.clicked.connect(self._rotate_scaffold)
        self._ui.fittingZAxis_pushButton.clicked.connect(self._rotate_scaffold)

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

    def _rotate_scaffold(self):
        sender = self.sender()
        scaffold_model = self._model.get_scaffold_model()

        rotation_mx = np.matrix('1 0 0; 0 1 0; 0 0 1')
        if sender == self._ui.fittingXAxis_pushButton:
            rotation_mx = np.matrix('1 0 0; 0 0 -1; 0 1 0')
        elif sender == self._ui.fittingYAxis_pushButton:
            rotation_mx = np.matrix('0 0 1; 0 1 0; -1 0 0')
        elif sender == self._ui.fittingZAxis_pushButton:
            rotation_mx = np.matrix('0 -1 0; 1 0 0; 0 0 1')

        translation_vec = np.matrix('0; 0; 0')
        scaffold_model.perform_rigid_transformation(rotation_mx, translation_vec)

    def _perform_scaffold_scale(self):
        # Can we get the maximum x and y extents and minimum x and y extents.
        # Assumption: The image plane is at z = 0.
        fiducial_markers_model = self._model.get_fiducial_markers_model()
        scaffold_model = self._model.get_scaffold_model()
        min_x, max_x, min_y, max_y = fiducial_markers_model.calculate_extents()
        approximate_width = max_x - min_x
        approximate_height = max_y - min_y
        # Create scaled scaffold to these approximations
        scaffold_model.scale(approximate_width, approximate_height)
        self._model.recreate_scaffold_graphics()

    def _do_rigid_fit(self):
        fiducial_markers_model = self._model.get_fiducial_markers_model()
        scaffold_model = self._model.get_scaffold_model()

        lv_apex_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['lv_apex'])
        rv_lateral_point_1_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['rv1'])
        rv_lateral_point_2_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['rv2'])
        lv_lateral_point_1_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['lv1'])
        lv_lateral_point_2_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['lv2'])
        fiducial_marker_locations = [lv_apex_fiducial_marker,
                                     rv_lateral_point_1_fiducial_marker,
                                     rv_lateral_point_2_fiducial_marker,
                                     lv_lateral_point_1_fiducial_marker,
                                     lv_lateral_point_2_fiducial_marker]

        lv_apex_scaffold = scaffold_model.get_node_location(self._scaffold_fit_nodes['lv_apex'])
        rv_lateral_point_1_scaffold = scaffold_model.get_node_location(self._scaffold_fit_nodes['rv1'])
        rv_lateral_point_2_scaffold = scaffold_model.get_node_location(self._scaffold_fit_nodes['rv2'])
        lv_lateral_point_1_scaffold = scaffold_model.get_node_location(self._scaffold_fit_nodes['lv1'])
        lv_lateral_point_2_scaffold = scaffold_model.get_node_location(self._scaffold_fit_nodes['lv2'])
        scaffold_locations = [lv_apex_scaffold,
                              rv_lateral_point_1_scaffold,
                              rv_lateral_point_2_scaffold,
                              lv_lateral_point_1_scaffold,
                              lv_lateral_point_2_scaffold]

        # Formulate matrices
        source = np.matrix(scaffold_locations)
        target = np.matrix(fiducial_marker_locations)

        rotation_mx, translation_vec = rigid_transform_3d(source.T, target.T)
        scaffold_model.perform_rigid_transformation(rotation_mx, translation_vec)
        self._applied_rotation_mx = rotation_mx
        self._applied_translation_vec = translation_vec

    def _calculate_rigid_transform(self):
        """
        Performs a rigid transformation of scaffold to fiducial landmarks and updates the view.

        :return:
        """
        field_module, nodes = self._get_field_module_and_all_nodes()
        node_value_array, coordinates = self._get_node_value_array_and_coordinates(field_module, nodes)
        cache = field_module.createFieldcache()

        fiducial_markers_model = self._model.get_fiducial_markers_model()
        fiducial_marker_positions = np.asarray(fiducial_markers_model.get_node_locations())

        """ computing rigid transformation parameters 1 """
        _, transformation = _rigid_transform(fiducial_marker_positions, node_value_array)
        rigid_scale = transformation.s

        """ scaling 1 """
        scale = field_module.createFieldConstant([rigid_scale, rigid_scale, rigid_scale])
        new_coordinates = field_module.createFieldMultiply(coordinates, scale)
        field_assignment = coordinates.createFieldassignment(new_coordinates)
        field_assignment.assign()

        # del field_module
        # del nodes
        # del cache
        # del coordinates
        # del transformation
        # del rigid_scale
        # del scale
        # del new_coordinates
        # del field_assignment

        """ getting the nodal parameters """
        _, coordinates = self._get_node_value_array_and_coordinates(field_module, nodes)
        cache = field_module.createFieldcache()
        node_set_array = _get_node_numpy_array(cache, field_module, nodes, coordinates)

        """ computing rigid transformation parameters 2 """
        _, transformation = _rigid_transform(fiducial_marker_positions, node_set_array)
        rigid_rotation, rigid_translation, rigid_scale = transformation.R, transformation.t, transformation.s
        print(rigid_rotation)
        print(rigid_translation)
        print(rigid_scale)
        """ finding the new node positions """
        transformed_nodes = np.dot(node_set_array, np.transpose(rigid_rotation)) + np.tile(
            np.transpose(rigid_translation), (node_set_array.shape[0], 1))

        """ scaling 2 """
        scale = field_module.createFieldConstant([rigid_scale, rigid_scale, rigid_scale])
        new_coordinates = field_module.createFieldMultiply(coordinates, scale)
        field_assignment = coordinates.createFieldassignment(new_coordinates)
        field_assignment.assign()

        """ setting the nodal parameters """
        _set_node_parameters(cache, field_module, nodes, coordinates, transformed_nodes, node_set_array)

    def _do_non_linear_fit(self):
        scaffold_model = self._model.get_scaffold_model()
        fit_parameters = scaffold_model.get_fit_parameters()
        x0 = np.array(fit_parameters)
        result = minimize(self._objective_function, x0, method='nelder-mead', options={'xtol': 1e-6, 'disp': True})

        scaffold_model.set_fit_parameters(result.x)
        scaffold_model.generate_mesh()
        self._do_rigid_fit()
        self._model.recreate_scaffold_graphics()

    def _objective_function(self, parameters):
        fiducial_markers_model = self._model.get_fiducial_markers_model()
        scaffold_model = self._model.get_scaffold_model()
        # print(parameters)
        # Calculate the least squares error for the parameters.
        # Generate a scaffold for the given parameters.
        scaffold_model.generate_temp(parameters)
        scaffold_model.perform_rigid_transformation_on_temp(self._applied_rotation_mx, self._applied_translation_vec)
        # Calculate the difference between the relevant points.
        # Get the coordinates from the scaffold.

        lv_apex_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['lv_apex'])
        rv_lateral_point_1_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['rv1'])
        rv_lateral_point_2_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['rv2'])
        septum_point_1_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['sept1'])
        septum_point_2_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['sept2'])
        lv_lateral_point_1_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['lv1'])
        lv_lateral_point_2_fiducial_marker = fiducial_markers_model.get_node_location(self._fiducial_fit_nodes['lv2'])
        fiducial_marker_locations = [lv_apex_fiducial_marker,
                                     rv_lateral_point_1_fiducial_marker,
                                     rv_lateral_point_2_fiducial_marker,
                                     septum_point_1_fiducial_marker,
                                     septum_point_2_fiducial_marker,
                                     lv_lateral_point_1_fiducial_marker,
                                     lv_lateral_point_2_fiducial_marker]

        lv_apex_scaffold = scaffold_model.get_temp_node_location(self._scaffold_fit_nodes['lv_apex'])
        rv_lateral_point_1_scaffold = scaffold_model.get_temp_node_location(self._scaffold_fit_nodes['rv1'])
        rv_lateral_point_2_scaffold = scaffold_model.get_temp_node_location(self._scaffold_fit_nodes['rv2'])
        septum_point_1_scaffold = scaffold_model.get_temp_node_location(self._scaffold_fit_nodes['sept1'])
        septum_point_2_scaffold = scaffold_model.get_temp_node_location(self._scaffold_fit_nodes['sept2'])
        lv_lateral_point_1_scaffold = scaffold_model.get_temp_node_location(self._scaffold_fit_nodes['lv1'])
        lv_lateral_point_2_scaffold = scaffold_model.get_temp_node_location(self._scaffold_fit_nodes['lv2'])
        scaffold_locations = [lv_apex_scaffold,
                              rv_lateral_point_1_scaffold,
                              rv_lateral_point_2_scaffold,
                              septum_point_1_scaffold,
                              septum_point_2_scaffold,
                              lv_lateral_point_1_scaffold,
                              lv_lateral_point_2_scaffold]

        f_mx = np.matrix(fiducial_marker_locations)
        s_mx = np.matrix(scaffold_locations)

        diff_mx = f_mx - s_mx

        scaffold_model.clear_temp_region()

        sum_squared = np.sum(np.square(diff_mx))
        return sum_squared

    def _calculate_non_rigid_transform(self):
        fiducial_markers_model = self._model.get_fiducial_markers_model()
        fiducial_marker_positions = np.asarray(fiducial_markers_model.get_node_locations())

        """ getting the nodal parameters """
        field_module, nodes = self._get_field_module_and_all_nodes()
        node_value_array, coordinates = self._get_node_value_array_and_coordinates(field_module, nodes)
        cache = field_module.createFieldcache()
        node_set_array = _get_node_numpy_array(cache, field_module, nodes, coordinates)

        """ computing non-rigid transformation parameters """
        _, transformation = _non_rigid_transform(fiducial_marker_positions, node_set_array)
        # _, transformation = _non_rigid_transform(fiducial_marker_positions[:, 1:3], node_set_array[:, 1:3])
        transformed_nodes = node_set_array + np.dot(transformation.G, transformation.W)

        """ setting the nodal parameters """
        _set_node_parameters(cache, field_module, nodes, coordinates, transformed_nodes, node_set_array, rigid=False)

        # del field_module
        # del nodes
        # del cache
        # del coordinates
        # del transformation

    def _get_node_value_array_and_coordinates(self, field_module, nodes):
        """
        Returns the nodal xyz values of a node set as np array. Also
        returns the coordinate field.

        :param field_module: field_module
        :param nodes: node set
        :return: node values as np array, coordinate field
        """
        reference_nodes_to_fit = self._scaffold_fit_nodes
        node_value_list = []

        field_module.beginChange()
        coordinate_field = field_module.findFieldByName('coordinates').castFiniteElement()
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
        scaffold_model = self._model.get_scaffold_model()
        region = scaffold_model.get_region()
        field_module = region.getFieldmodule()
        nodes = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        return field_module, nodes

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


def _set_node_parameters(field_cache, field_module, nodes, coordinates, transformed_nodes, numpy_array, rigid=True):

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


def rigid_transform_3d(A, B):
    assert len(A) == len(B)

    n1 = A.shape[1]  # total points
    n2 = B.shape[1]
    centroid_a = np.mean(A, axis=1)
    centroid_b = np.mean(B, axis=1)

    # centre the points
    AA = A - np.tile(centroid_a, (1, n1))
    BB = B - np.tile(centroid_b, (1, n2))

    # dot is matrix multiplication for array
    H = AA * BB.T

    U, S, Vt = np.linalg.svd(H)

    R = Vt.T * U.T

    # special reflection case
    if np.linalg.det(R) < 0:
        Vt[2, :] *= -1
        R = Vt.T * U.T

    t = -R * centroid_a + centroid_b

    return R, t
