
from opencmiss.utils.zinc import create_finite_element_field

from mapclientplugins.parametricfittingstep.model.base import Base


DISPLAY_SURFACES_TRANSLUCENT_KEY = 'display_surface'


class Scaffold(Base):

    def __init__(self, master_model):
        super(Scaffold, self).__init__()
        self._settings[DISPLAY_SURFACES_TRANSLUCENT_KEY] = True
        self._master_model = master_model
        self._region = None
        self._region_name = 'scaffold'
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

    def is_display_surfaces_translucent(self):
        return self._settings[DISPLAY_SURFACES_TRANSLUCENT_KEY]

    def get_coordinate_field(self):
        return self._coordinate_field

    def get_region(self):
        return self._region

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
