import math

from opencmiss.utils.zinc.general import create_node, AbstractNodeDataObject
from opencmiss.utils.zinc.field import create_field_finite_element

from mapclientplugins.parametricfittingstep.model.base import Base


class NodeCreator(AbstractNodeDataObject):

    def __init__(self, coordinates, time_sequence):
        super(NodeCreator, self).__init__(['coordinates'], time_sequence, ['coordinates'])
        self._coordinates = coordinates

    def coordinates(self):
        return self._coordinates


class FiducialMarkers(Base):

    def __init__(self, master_model):
        super(FiducialMarkers, self).__init__()
        self._master_model = master_model
        self._fiducial_marker_data = None
        self._region = None

        self._initialise()

    def _initialise(self):
        context = self._master_model.get_context()
        default_region = context.getDefaultRegion()
        self._region = default_region.createChild('fiducial')
        self._coordinate_field = create_field_finite_element(self._region)

    def set_data(self, data):
        self._fiducial_marker_data = data

    def get_region(self):
        return self._region

    def get_coordinate_field(self):
        return self._coordinate_field

    def set_data_to_context(self):
        field_module = self._region.getFieldmodule()
        node_set = field_module.findNodesetByName('datapoints')
        field_module.beginChange()
        field_cache = field_module.createFieldcache()
        time_array = self._master_model.get_time_sequence()
        time_array_size = len(time_array)
        for key in self._fiducial_marker_data:
            locations = self._fiducial_marker_data[key]
            location = locations[0]
            node_creator = NodeCreator(location, time_array)
            identifier = create_node(field_module, node_creator, node_set_name='datapoints', time=time_array[0])
            node = node_set.findNodeByIdentifier(identifier)
            field_cache.setNode(node)
            assert time_array_size == len(locations)
            for index in range(1, time_array_size):
                location = locations[index]
                time = time_array[index]
                field_cache.setTime(time)
                self._coordinate_field.assignReal(field_cache, location)

        field_module.endChange()

    def _set_node_location_at_time(self, node, location, time):
        field_module = self._region.getFieldmodule()
        field_module.beginChange()
        field_cache = field_module.createFieldcache()
        field_cache.setTime(time)
        field_cache.setNode(node)
        self._coordinate_field.assignReal(field_cache, location)
        field_module.endChange()

    def get_node_locations(self, index=0):
        locations = []
        for key in self._fiducial_marker_data:
            point_location = self._fiducial_marker_data[key][index]
            locations.append(point_location)

        return locations

    def get_node_location(self, node_label, index=0):
        location = []
        if node_label in self._fiducial_marker_data:
            location = self._fiducial_marker_data[node_label][index]

        return location

    def calculate_extents(self):
        index = 0
        min_x = math.inf
        max_x = -math.inf
        min_y = math.inf
        max_y = -math.inf
        for key in self._fiducial_marker_data:
            point_location = self._fiducial_marker_data[key][index]
            if point_location[0] < min_x:
                min_x = point_location[0]
            if point_location[0] > max_x:
                max_x = point_location[0]
            if point_location[1] < min_y:
                min_y = point_location[1]
            if point_location[1] > max_y:
                max_y = point_location[1]

        return min_x, max_x, min_y, max_y
