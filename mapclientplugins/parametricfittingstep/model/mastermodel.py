import os
import json

from PySide import QtCore

from opencmiss.zinc.material import Material

from mapclientplugins.parametricfittingstep.model.fiducialmarkers import FiducialMarkers as FiducialMarkersModel
from mapclientplugins.parametricfittingstep.scene.fiducialmarkers import FiducialMarkers as FiducialMarkersScene
from mapclientplugins.parametricfittingstep.model.imageplane import ImagePlane as ImagePlaneModel
from mapclientplugins.parametricfittingstep.scene.imageplane import ImagePlane as ImagePlaneScene

TIME_LOOP_KEY = 'time_loop'


class MasterModel(QtCore.QObject):

    time_stopped = QtCore.Signal()

    def __init__(self, location, identifier, image_context_data, fitting_point_data):
        super(MasterModel, self).__init__()
        self._location = location
        self._identifier = identifier
        self._filenameStem = os.path.join(self._location, self._identifier)
        self._context = image_context_data.get_context()
        self._image_plane_model = ImagePlaneModel(self)
        self._fiducial_markers_model = FiducialMarkersModel(self)
        self._fiducial_markers_model.set_data(fitting_point_data)
        self._fiducial_markers_model.set_data_to_context()

        self._timekeeper = self._context.getTimekeepermodule().getDefaultTimekeeper()
        self._timer = QtCore.QTimer()
        self._current_time = 0.0
        self._time_value_update = None

        self._frames_per_second = image_context_data.get_frames_per_second()
        self._images_file_name_listing = image_context_data.get_image_file_names()
        self._frame_count = image_context_data.get_frame_count()

        self._region = self._context.getDefaultRegion()
        self._initialise()

        self._image_plane_scene = ImagePlaneScene(self)
        self._image_plane_scene.create_graphics()
        self._image_plane_scene.set_image_material()

        self._fiducial_marker_scene = FiducialMarkersScene(self)
        self._fiducial_marker_scene.create_graphics()

        self._settings = {TIME_LOOP_KEY: False}
        self._make_connections()

    def print_log(self):
        logger = self._context.getLogger()
        for index in range(logger.getNumberOfMessages()):
            print(logger.getMessageTextAtIndex(index))

    def _initialise(self):
        # self._filenameStem = os.path.join(self._location, self._identifier)
        tess = self._context.getTessellationmodule().getDefaultTessellation()
        tess.setRefinementFactors(12)
        # set up standard materials and glyphs so we can use them elsewhere
        self._materialmodule = self._context.getMaterialmodule()
        self._materialmodule.defineStandardMaterials()
        solid_blue = self._materialmodule.createMaterial()
        solid_blue.setName('solid_blue')
        solid_blue.setManaged(True)
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_AMBIENT, [ 0.0, 0.2, 0.6 ])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_DIFFUSE, [ 0.0, 0.7, 1.0 ])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_EMISSION, [ 0.0, 0.0, 0.0 ])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_SPECULAR, [ 0.1, 0.1, 0.1 ])
        solid_blue.setAttributeReal(Material.ATTRIBUTE_SHININESS , 0.2)
        trans_blue = self._materialmodule.createMaterial()
        trans_blue.setName('trans_blue')
        trans_blue.setManaged(True)
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_AMBIENT, [ 0.0, 0.2, 0.6 ])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_DIFFUSE, [ 0.0, 0.7, 1.0 ])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_EMISSION, [ 0.0, 0.0, 0.0 ])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_SPECULAR, [ 0.1, 0.1, 0.1 ])
        trans_blue.setAttributeReal(Material.ATTRIBUTE_ALPHA , 0.3)
        trans_blue.setAttributeReal(Material.ATTRIBUTE_SHININESS , 0.2)
        glyphmodule = self._context.getGlyphmodule()
        glyphmodule.defineStandardGlyphs()

    def _make_connections(self):
        self._timer.timeout.connect(self._time_out)

    def _time_out(self):
        increment = 1000 / self._frames_per_second / 1000
        duration = self._frame_count / self._frames_per_second
        if not self._settings[TIME_LOOP_KEY] and (self._current_time + increment) > duration:
            self._current_time = duration + 1e-08
            self.stop()
            self.time_stopped.emit()
        else:
            self._current_time += increment
        if self._settings[TIME_LOOP_KEY] and self._current_time > duration:
            self._current_time -= duration

        self._timekeeper.setTime(self._current_time)
        self._time_value_update(self._current_time)

    def register_time_value_update_callback(self, time_value_update_callback):
        self._time_value_update = time_value_update_callback

    def get_identifier(self):
        return self._identifier

    def get_timekeeper(self):
        return self._timekeeper

    def get_timekeeper_time(self):
        return self._timekeeper.getTime()

    def set_maximum_time_value(self, maximum_time_value):
        self._timekeeper.setMaximumTime(maximum_time_value)

    def get_scene(self):
        return self._region.getScene()

    def get_context(self):
        return self._context

    def get_image_plane_model(self):
        return self._image_plane_model

    def get_fiducial_markers_model(self):
        return self._fiducial_markers_model

    def get_frames_per_second(self):
        return self._frames_per_second

    def get_frame_count(self):
        return self._frame_count

    def set_time_value(self, time):
        self._current_time = time
        self._timekeeper.setTime(time)

    def set_time_loop(self, state):
        self._settings[TIME_LOOP_KEY] = state

    def is_time_loop(self):
        return self._settings[TIME_LOOP_KEY]

    def play(self):
        self._timer.start(1000/self._frames_per_second)

    def stop(self):
        self._timer.stop()

    def done(self):
        self._save_settings()

    def _get_settings(self):
        settings = self._settings
        settings['image_plane_settings'] = self._image_plane_model.get_settings()
        settings['fiducial_markers'] = self._fiducial_markers_model.get_settings()
        return settings

    def load_settings(self):
        try:
            settings = self._settings
            with open(self._filenameStem + '_settings.json', 'r') as f:
                settings.update(json.loads(f.read()))

            if 'image_plane_settings' not in settings:
                settings.update({'image_plane_settings': self._image_plane_model.get_settings()})
            if 'fiducial_markers' not in settings:
                settings.update({'fiducial_markers': self._fiducial_markers_model.get_settings()})
        except:
            # no settings saved yet, following gets defaults
            settings = self._get_settings()

        self._image_plane_model.set_settings(settings['image_plane_settings'])
        self._fiducial_markers_model.set_settings(settings['fiducial_markers'])

    def _save_settings(self):
        settings = self._get_settings()
        with open(self._filenameStem + '_settings.json', 'w') as f:
            f.write(json.dumps(settings, default=lambda o: o.__dict__, sort_keys=True, indent=4))

    def get_output_model_file_name(self):
        return 'not-a-file'
