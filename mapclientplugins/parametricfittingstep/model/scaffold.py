
import numpy as np

from opencmiss.utils.zinc import create_finite_element_field
from opencmiss.zinc.field import Field
from opencmiss.zinc.node import Node
from opencmiss.zinc.streamregion import StreaminformationRegion

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
        self._scaffold_is_time_aware = False
        self._scaffold_fit_parameters = None
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

    def get_default_scaffold_options(self):
        return self._scaffold.getDefaultOptions()

    def get_scaffold_options(self):
        return self._scaffold_options

    def set_scaffold_options(self, options):
        self._scaffold_options = options

        parameters = []
        for option in FIT_OPTIONS:
            parameters.append(self._scaffold_options[option])

        self._scaffold_fit_parameters = parameters

    def get_node_location(self, node_id, index=0):
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
        self._scaffold_fit_parameters = fit_parameters

    def get_fit_parameters(self):
        return self._scaffold_fit_parameters

    def scale(self, options, width, height):
        _scale_width(options, width * 0.8)
        _scale_height(options, height * 0.8)
        self.generate_mesh(options)

    def _undefine_scaffold_nodes(self):
        field_module = self._region.getFieldmodule()

        field_module.beginChange()
        node_set = field_module.findNodesetByName('nodes')
        node_template = node_set.createNodetemplate()
        node_template.undefineField(self._coordinate_field)
        node_iterator = node_set.createNodeiterator()
        node = node_iterator.next()
        while node.isValid():
            node.merge(node_template)
            node = node_iterator.next()

        field_module.endChange()

    def transfer_temp_into_main(self, time):
        node_descriptions = _extract_node_descriptions(self._temp_region)
        if not self._scaffold_is_time_aware:
            self._undefine_scaffold_nodes()
            self._scaffold_is_time_aware = True

        _read_node_descriptions(self._region, node_descriptions, time)

    def generate_temp_mesh(self, fit_options_array=None):

        fit_options = {}
        if fit_options_array is not None:
            for index in range(len(FIT_OPTIONS)):
                fit_options[FIT_OPTIONS[index]] = fit_options_array[index]

        temp_options = self.get_scaffold_options().copy()
        temp_options.update(fit_options)

        self._temp_region = self._parent_region.createRegion()
        self._scaffold.generateMesh(self._temp_region, temp_options)

    def generate_mesh(self, options):
        self._initialise_region()
        field_module = self._region.getFieldmodule()
        field_module.beginChange()
        self._scaffold.generateMesh(self._region, options)
        field_module.defineAllFaces()
        field_module.endChange()

    def perform_rigid_transformation(self, rotation_mx, translation_vec):
        _perform_rigid_transformation(self._region, rotation_mx, translation_vec)

    def perform_rigid_transformation_on_temp(self, rotation_mx, translation_vec):
        _perform_rigid_transformation(self._temp_region, rotation_mx, translation_vec)

    def write(self):
        resources = {}
        stream_information = self._region.createStreaminformationRegion()
        memory_resource = stream_information.createStreamresourceMemory()
        resources['elements'] = memory_resource
        stream_information.setResourceDomainTypes(memory_resource, Field.DOMAIN_TYPE_MESH3D)
        # stream_information.setResourceAttributeReal(memory_resource, StreaminformationRegion.ATTRIBUTE_TIME, time)

        time_values = self._master_model.get_time_sequence()
        for time_value in time_values:
            memory_resource = stream_information.createStreamresourceMemory()
            stream_information.setResourceDomainTypes(memory_resource, Field.DOMAIN_TYPE_NODES)
            stream_information.setResourceAttributeReal(memory_resource, StreaminformationRegion.ATTRIBUTE_TIME, time_value)
            resources[time_value] = memory_resource
        self._region.write(stream_information)

        buffer_contents = {}
        for key in resources:
            buffer_contents[key] = resources[key].getBuffer()[1]

        return buffer_contents


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


def _scale_width(options, width):

    width_options = ['LV outer radius', 'LV free wall thickness', 'LV apex thickness',
                     'RV width', 'RV extra cross radius base', 'Ventricular septum thickness',
                     'Atria base inner major axis length', 'Atria base inner minor axis length',
                     'Atrial septum thickness', 'Atrial base wall thickness',
                     'LV outlet inner diameter', 'LV outlet wall thickness',
                     'RV outlet inner diameter', 'RV outlet wall thickness']
    for option in width_options:
        options[option] *= width


def _scale_height(options, height):

    height_options = ['LV outer height', 'RV inner height', 'RV free wall thickness',
                      'Base height', 'Base thickness', 'Fibrous ring thickness',
                      'Ventricles outlet element length', 'Ventricles outlet spacing']
    for option in height_options:
        options[option] *= height


def _extract_node_descriptions(region):
    stream_information = region.createStreaminformationRegion()
    memory_resource = stream_information.createStreamresourceMemory()
    stream_information.setResourceDomainTypes(memory_resource, Field.DOMAIN_TYPE_NODES)
    region.write(stream_information)
    _, buffer_contents = memory_resource.getBuffer()

    return buffer_contents


def _read_node_descriptions(region, buffer, time):
    stream_information = region.createStreaminformationRegion()
    memory_resource = stream_information.createStreamresourceMemoryBuffer(buffer)
    stream_information.setResourceDomainTypes(memory_resource, Field.DOMAIN_TYPE_NODES)
    stream_information.setResourceAttributeReal(memory_resource, StreaminformationRegion.ATTRIBUTE_TIME, time)

    region.read(stream_information)


def _print_node_location(region):
    node_id = 62
    field_module = region.getFieldmodule()
    node_set = field_module.findNodesetByName('nodes')
    node = node_set.findNodeByIdentifier(node_id)
    field_cache = field_module.createFieldcache()
    field_cache.setNode(node)
    coordinate_field = field_module.findFieldByName('coordinates')
    print(coordinate_field.evaluateReal(field_cache, 3))
