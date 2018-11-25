from opencmiss.zinc.field import Field
from opencmiss.zinc.graphics import Graphics


class Scaffold(object):

    def __init__(self, master_model):
        self._master_model = master_model

    def _get_scene(self):
        scaffold_model = self._master_model.get_scaffold_model()
        region = scaffold_model.get_region()
        return region.getScene()


    def create_graphics(self):
        scaffold_model = self._master_model.get_scaffold_model()
        scene = self._get_scene()
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

    def write(self):
        scene = self._get_scene()
        stream_information = scene.createStreaminformationScene()
        stream_information.setIOFormat(stream_information.IO_FORMAT_DESCRIPTION)
        memory_resource = stream_information.createStreamresourceMemory()
        scene.write(stream_information)
        _, buffer_contents = memory_resource.getBuffer()

        return buffer_contents

