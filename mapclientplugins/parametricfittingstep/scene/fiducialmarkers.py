from cmlibs.zinc.field import Field
from cmlibs.zinc.glyph import Glyph


class FiducialMarkers(object):

    def __init__(self, master_model):
        self._master_model = master_model

    def create_graphics(self):
        fiducial_markers_model = self._master_model.get_fiducial_markers_model()
        coordinate_field = fiducial_markers_model.get_coordinate_field()
        field_module = coordinate_field.getFieldmodule()
        cmiss_number = field_module.findFieldByName('cmiss_number')
        region = fiducial_markers_model.get_region()
        scene = region.getScene()
        scene.beginChange()
        scene.removeAllGraphics()

        material_module = scene.getMaterialmodule()
        gold_material = material_module.findMaterialByName('gold')
        green_material = material_module.findMaterialByName('green')

        points = scene.createGraphicsPoints()
        points.setName('fiducial-points')
        points.setCoordinateField(coordinate_field)
        points.setMaterial(gold_material)
        points.setSelectedMaterial(green_material)
        points.setFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
        attributes = points.getGraphicspointattributes()
        attributes.setGlyphShapeType(Glyph.SHAPE_TYPE_SPHERE)
        attributes.setBaseSize(5.7)
        attributes.setLabelField(cmiss_number)

        # scene.setSelectionField(fiducial_markers_model.get_selection_field())
        scene.endChange()
