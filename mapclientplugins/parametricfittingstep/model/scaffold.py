
import numpy as np

from opencmiss.utils.zinc import create_finite_element_field
from opencmiss.zinc.field import Field
from opencmiss.zinc.node import Node

from mapclientplugins.parametricfittingstep.model.base import Base


DISPLAY_SURFACES_TRANSLUCENT_KEY = 'display_surface'
FIT_OPTIONS = ['LV outer height', 'Base height', 'LV outer radius', 'RV width']


class Scaffold(Base):

    def __init__(self, master_model):
        super(Scaffold, self).__init__()
        self._settings[DISPLAY_SURFACES_TRANSLUCENT_KEY] = True
        self._master_model = master_model
        self._region = None
        self._region_name = 'scaffold'
        self._temp_region = None
        self._scaffold = None
        self._scaffold_options = None
        self._coordinate_field = None

        self._initialise()

    def _initialise(self):
        context = self._master_model.get_context()
        self._parent_region = context.getDefaultRegion()

    def _initialise_region(self):
        if self._region:
            self._parent_region.removeChild(self._region)
        self._region = self._parent_region.createChild(self._region_name)
        self._coordinate_field = create_finite_element_field(self._region)

    def set_scaffold(self, scaffold):
        self._scaffold = scaffold
        self._scaffold_options = self._scaffold.getDefaultOptions()

    def get_node_location(self, node_id):
        index = 0
        time_values = self._master_model.get_time_sequence()
        return _get_node_location(self._region, time_values, index, node_id)

    def get_temp_node_location(self, node_id):
        index = 0
        time_values = self._master_model.get_time_sequence()
        return _get_node_location(self._temp_region, time_values, index, node_id)

    def get_node_locations(self):
        index = 0
        time_values = self._master_model.get_time_sequence()
        field_module = self._region.getFieldmodule()
        field_module.beginChange()
        cache = field_module.createFieldcache()
        cache.setTime(time_values[index])
        coordinates = field_module.findFieldByName('coordinates')
        node_set = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        node_iterator = node_set.createNodeiterator()
        node = node_iterator.next()

        node_positions = []
        while node.isValid():
            cache.setNode(node)
            _, position = coordinates.evaluateReal(cache, 3)
            node_positions.append(position)
            node = node_iterator.next()

        field_module.endChange()

        return node_positions

    def _set_node_locations(self, locations):
        """
        Assuming that the index + 1 is the node identifier that the location is meant for.

        :param locations: list of coordinates for the nodes
        :return:
        """
        index = 0
        time_values = self._master_model.get_time_sequence()
        field_module = self._region.getFieldmodule()
        field_module.beginChange()
        field_cache = field_module.createFieldcache()
        field_cache.setTime(time_values[index])
        coordinates = field_module.findFieldByName('coordinates').castFiniteElement()
        node_set = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        node_iterator = node_set.createNodeiterator()
        node = node_iterator.next()

        while node.isValid():
            field_cache.setNode(node)
            location_index = node.getIdentifier() - 1
            location = locations[location_index]
            coordinates.setNodeParameters(field_cache, -1, Node.VALUE_LABEL_VALUE, 1, location)
            # coordinates.assignReal(cache, location)
            node = node_iterator.next()

        field_module.endChange()

    def is_display_surfaces_translucent(self):
        return self._settings[DISPLAY_SURFACES_TRANSLUCENT_KEY]

    def get_coordinate_field(self):
        return self._coordinate_field

    def get_region(self):
        return self._region

    def clear_temp_region(self):
        self._temp_region = None

    def set_fit_parameters(self, fit_parameters):
        for index, option in enumerate(FIT_OPTIONS):
            self._scaffold_options[option] = fit_parameters[index]

    def get_fit_parameters(self):

        parameters = []
        for option in FIT_OPTIONS:
            parameters.append(self._scaffold_options[option])

        return parameters

    def _scale_width(self, width):
        width_options = ['LV outer radius', 'LV free wall thickness', 'LV apex thickness',
                         'RV width', 'RV extra cross radius base', 'Ventricular septum thickness',
                         'Atria base inner major axis length', 'Atria base inner minor axis length',
                         'Atrial septum thickness', 'Atrial base wall thickness',
                         'LV outlet inner diameter', 'LV outlet wall thickness',
                         'RV outlet inner diameter', 'RV outlet wall thickness']
        for option in width_options:
            self._scaffold_options[option] *= width

    def _scale_height(self, height):
        height_options = ['LV outer height', 'RV inner height', 'RV free wall thickness',
                          'Base height', 'Base thickness', 'Fibrous ring thickness',
                          'Ventricles outlet element length', 'Ventricles outlet spacing']
        for option in height_options:
            self._scaffold_options[option] *= height

    def scale(self, width, height):
        self._scale_width(width * 0.8)
        self._scale_height(height * 0.8)
        self.generate_mesh()

    def generate_temp(self, fit_options_array):
        fit_options = {}
        for index in range(len(FIT_OPTIONS)):
            fit_options = {FIT_OPTIONS[index]: fit_options_array[index]}

        temp_options = self._scaffold_options.copy()
        temp_options.update(fit_options)

        self._temp_region = self._parent_region.createRegion()
        self._scaffold.generateMesh(self._temp_region, temp_options)

    def generate_mesh(self):
        self._initialise_region()
        # self._scene = self._region.getScene()
        field_module = self._region.getFieldmodule()
        field_module.beginChange()
        self._scaffold.generateMesh(self._region, self._scaffold_options)
        # logger = self._context.getLogger()
        # annotationGroups = self._currentMeshType.generateMesh(self._region, self._scaffold.getDefaultOptions())
        # loggerMessageCount = logger.getNumberOfMessages()
        # if loggerMessageCount > 0:
        #     for i in range(1, loggerMessageCount + 1):
        #         print(logger.getMessageTypeAtIndex(i), logger.getMessageTextAtIndex(i))
        #     logger.removeAllMessages()
        # mesh = self._getMesh()
        # meshDimension = mesh.getDimension()
        # nodes = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        # if len(self._deleteElementRanges) > 0:
        #     deleteElementIdentifiers = []
        #     elementIter = mesh.createElementiterator()
        #     element = elementIter.next()
        #     while element.isValid():
        #         identifier = element.getIdentifier()
        #         for deleteElementRange in self._deleteElementRanges:
        #             if (identifier >= deleteElementRange[0]) and (identifier <= deleteElementRange[1]):
        #                 deleteElementIdentifiers.append(identifier)
        #         element = elementIter.next()
        #     #print('delete elements ', deleteElementIdentifiers)
        #     for identifier in deleteElementIdentifiers:
        #         element = mesh.findElementByIdentifier(identifier)
        #         mesh.destroyElement(element)
        #     del element
        #     # destroy all orphaned nodes
        #     #size1 = nodes.getSize()
        #     nodes.destroyAllNodes()
        #     #size2 = nodes.getSize()
        #     #print('deleted', size1 - size2, 'nodes')
        field_module.defineAllFaces()
        # if annotationGroups is not None:
        #     for annotationGroup in annotationGroups:
        #         annotationGroup.addSubelements()
        # if self._settings['scale'] != '1*1*1':
        #     coordinates = field_module.findFieldByName('coordinates').castFiniteElement()
        #     scale = field_module.createFieldConstant(self._scale)
        #     newCoordinates = field_module.createFieldMultiply(coordinates, scale)
        #     fieldassignment = coordinates.createFieldassignment(newCoordinates)
        #     fieldassignment.assign()
        #     del newCoordinates
        #     del scale
        field_module.endChange()

    def perform_rigid_transformation(self, rotation_mx, translation_vec):
        _perform_rigid_transformation(self._region, rotation_mx, translation_vec)

    def perform_rigid_transformation_on_temp(self, rotation_mx, translation_vec):
        _perform_rigid_transformation(self._temp_region, rotation_mx, translation_vec)


def _perform_rigid_transformation(region, rotation_mx, translation_vec):
    field_module = region.getFieldmodule()
    coordinate_field = field_module.findFieldByName('coordinates')
    field_module.beginChange()
    rotation_mx = rotation_mx.tolist()
    translation_vec = translation_vec.tolist()
    transform_field = field_module.createFieldConstant(
        [rotation_mx[0][0], rotation_mx[0][1], rotation_mx[0][2], translation_vec[0][0],
         rotation_mx[1][0], rotation_mx[1][1], rotation_mx[1][2], translation_vec[1][0],
         rotation_mx[2][0], rotation_mx[2][1], rotation_mx[2][2], translation_vec[2][0],
         0, 0, 0, 1])
    projection_field = field_module.createFieldProjection(coordinate_field, transform_field)
    field_assignment = coordinate_field.createFieldassignment(projection_field)
    field_assignment.assign()
    field_module.endChange()


def _get_node_location(region, time_values, time_index, node_id):
    field_module = region.getFieldmodule()
    field_module.beginChange()

    coordinate_field = field_module.findFieldByName('coordinates')
    field_cache = field_module.createFieldcache()
    node_set = field_module.findNodesetByName('nodes')
    node = node_set.findNodeByIdentifier(node_id)
    field_cache.setNode(node)
    field_cache.setTime(time_values[time_index])
    _, coordinates = coordinate_field.evaluateReal(field_cache, 3)

    field_module.endChange()

    return coordinates
