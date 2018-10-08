
from mapclientplugins.parametricfittingstep.model.base import Base


class ImagePlane(Base):

    def __init__(self, master_model):
        super(ImagePlane, self).__init__()
        self._master_model = master_model
        self._region = None
        self._scaled_coordinate_field = None
        self._duration_field = None
        self._image_based_material = None

        self._initialise()

    def _initialise(self):
        context = self._master_model.get_context()
        default_region = context.getDefaultRegion()
        self._region = default_region.findChildByName('images')
        field_module = self._region.getFieldmodule()
        self._scaled_coordinate_field = field_module.findFieldByName('scaled_coordinates')
        self._duration_field = field_module.findFieldByName('duration')
        material_module = context.getMaterialmodule()
        self._image_based_material = material_module.findMaterialByName('images')

    def get_coordinate_field(self):
        return self._scaled_coordinate_field

    def get_region(self):
        return self._region

    def get_material(self):
        return self._image_based_material

    def get_duration_field(self):
        return self._duration_field
