from opencmiss.zinc.field import Field
from opencmiss.zinc.graphics import Graphics


class Scaffold(object):

    def __init__(self, master_model):
        self._master_model = master_model

    def create_graphics(self):
        scaffold_model = self._master_model.get_scaffold_model()
        region = scaffold_model.get_region()
        scene = region.getScene()
        material_module = scene.getMaterialmodule()
        coordinate_field = scaffold_model.get_coordinate_field()
        field_module = coordinate_field.getFieldmodule()
        cmiss_number = field_module.findFieldByName('cmiss_number')

        scene.beginChange()
        scene.removeAllGraphics()

        points = scene.createGraphicsPoints()
        points.setName('scaffold-points')
        points.setCoordinateField(coordinate_field)
        points.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
        attributes = points.getGraphicspointattributes()
        attributes.setLabelField(cmiss_number)

        lines = scene.createGraphicsLines()
        lines.setExterior(True)
        lines.setName('scaffold-lines')
        lines.setCoordinateField(coordinate_field)

        surfaces = scene.createGraphicsSurfaces()
        # surfaces.setSubgroupField(self.notHighlighted)
        surfaces.setCoordinateField(coordinate_field)
        surfaces.setRenderPolygonMode(Graphics.RENDER_POLYGON_MODE_SHADED)
        surfaces.setExterior(True)
        surfacesMaterial = material_module.findMaterialByName(
            'trans_blue' if scaffold_model.is_display_surfaces_translucent() else 'solid_blue')
        surfaces.setMaterial(surfacesMaterial)
        surfaces.setName('scaffold-surfaces')

        scene.endChange()
