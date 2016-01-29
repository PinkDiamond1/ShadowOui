import math
import os
import sys

import numpy
from PyQt4 import QtGui
from PyQt4.QtGui import QPalette, QColor, QFont, QDialog, QWidget

from matplotlib import cm
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

import orangecanvas.resources as resources

from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerIn, ShadowPreProcessorData, \
    ShadowOpticalElement, ShadowBeam, ShadowFile
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPhysics, ShadowPreProcessor
from orangecontrib.shadow.widgets.gui import ow_generic_element

shadow_oe_to_copy = None

class GraphicalOptions:
    is_empty = False
    is_curved = False
    is_mirror=False
    is_screen_slit=False
    is_crystal=False
    is_grating=False
    is_spheric= False
    is_ellipsoidal=False
    is_toroidal=False
    is_paraboloid=False
    is_hyperboloid=False
    is_cone=False
    is_codling_slit=False
    is_polynomial=False
    is_conic_coefficients=False
    is_refractor=False

    def __init__(self,
                 is_empty = False,
                 is_curved=False,
                 is_mirror=False,
                 is_crystal=False,
                 is_grating=False,
                 is_screen_slit=False,
                 is_spheric=False,
                 is_ellipsoidal=False,
                 is_toroidal=False,
                 is_paraboloid=False,
                 is_hyperboloid=False,
                 is_cone=False,
                 is_codling_slit=False,
                 is_polynomial=False,
                 is_conic_coefficients=False,
                 is_refractor=False):
        self.is_empty = is_empty
        self.is_curved = is_curved
        self.is_mirror=is_mirror
        self.is_crystal=is_crystal
        self.is_grating=is_grating
        self.is_screen_slit=is_screen_slit
        self.is_spheric=is_spheric
        self.is_ellipsoidal=is_ellipsoidal
        self.is_toroidal=is_toroidal
        self.is_paraboloid=is_paraboloid
        self.is_hyperboloid=is_hyperboloid
        self.is_cone=is_cone
        self.is_codling_slit=is_codling_slit
        self.is_polynomial=is_polynomial
        self.is_conic_coefficients=is_conic_coefficients
        self.is_refractor=is_refractor

class OpticalElement(ow_generic_element.GenericElement):

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("PreProcessor Data #1", ShadowPreProcessorData, "setPreProcessorData"),
              ("PreProcessor Data #2", ShadowPreProcessorData, "setPreProcessorData")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"},
               {"name":"Trigger",
                "type": ShadowTriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"}]

    input_beam = None

    NONE_SPECIFIED = "NONE SPECIFIED"

    ONE_ROW_HEIGHT = 65
    TWO_ROW_HEIGHT = 110
    THREE_ROW_HEIGHT = 170

    INNER_BOX_WIDTH_L3=322
    INNER_BOX_WIDTH_L2=335
    INNER_BOX_WIDTH_L1=358
    INNER_BOX_WIDTH_L0=375

    graphical_options=None

    source_plane_distance = Setting(10.0)
    image_plane_distance = Setting(20.0)

    angles_respect_to = Setting(0.0)

    incidence_angle_deg = Setting(88.0)
    incidence_angle_mrad = Setting(0.0)
    reflection_angle_deg = Setting(88.0)
    reflection_angle_mrad = Setting(0.0)
    mirror_orientation_angle = Setting(0)

    ##########################################
    # BASIC SETTING
    ##########################################

    conic_coefficient_0 = Setting(0.0)
    conic_coefficient_1 = Setting(0.0)
    conic_coefficient_2 = Setting(0.0)
    conic_coefficient_3 = Setting(0.0)
    conic_coefficient_4 = Setting(0.0)
    conic_coefficient_5 = Setting(0.0)
    conic_coefficient_6 = Setting(0.0)
    conic_coefficient_7 = Setting(0.0)
    conic_coefficient_8 = Setting(0.0)
    conic_coefficient_9 = Setting(0.0)

    surface_shape_parameters = Setting(0)
    spherical_radius = Setting(0.0)

    torus_major_radius = Setting(0.0)
    torus_minor_radius = Setting(0.0)
    toroidal_mirror_pole_location=Setting(0.0)

    ellipse_hyperbola_semi_major_axis=Setting(0.0)
    ellipse_hyperbola_semi_minor_axis=Setting(0.0)
    angle_of_majax_and_pole=Setting(0.0)

    paraboloid_parameter=Setting(0.0)
    focus_location=Setting(0.0)

    focii_and_continuation_plane = Setting(0)

    object_side_focal_distance = Setting(0.0)
    image_side_focal_distance = Setting(0.0)
    incidence_angle_respect_to_normal = Setting(0.0)

    surface_curvature = Setting(0)
    is_cylinder = Setting(1)
    cylinder_orientation = Setting(0.0)
    reflectivity_type = Setting(0)
    source_of_reflectivity = Setting(0)
    file_prerefl = Setting("reflec.dat")
    alpha = Setting(0.0)
    gamma = Setting(0.0)
    file_prerefl_m = Setting("reflec.dat")
    m_layer_tickness = Setting(0.0)

    is_infinite = Setting(0)
    mirror_shape = Setting(0)
    dim_x_plus = Setting(0.0)
    dim_x_minus = Setting(0.0)
    dim_y_plus = Setting(0.0)
    dim_y_minus = Setting(0.0)

    diffraction_geometry = Setting(0)
    diffraction_calculation = Setting(0)
    file_diffraction_profile = Setting("diffraction_profile.dat")
    file_crystal_parameters = Setting("reflec.dat")
    crystal_auto_setting = Setting(0)
    units_in_use = Setting(0)
    photon_energy = Setting(5.0)
    photon_wavelength = Setting(5000.0)

    mosaic_crystal = Setting(0)
    angle_spread_FWHM = Setting(0.0)
    thickness = Setting(0.0)
    seed_for_mosaic = Setting(1626261131)

    johansson_geometry = Setting(0)
    johansson_radius = Setting(0.0)

    asymmetric_cut = Setting(0)
    planes_angle = Setting(0.0)
    below_onto_bragg_planes = Setting(-1)

    grating_diffraction_order = Setting(-1.0)
    grating_auto_setting = Setting(0)
    grating_units_in_use = Setting(0)
    grating_photon_energy = Setting(5.0)
    grating_photon_wavelength = Setting(5000.0)

    grating_ruling_type = Setting(0)
    grating_ruling_density = Setting(12000.0)

    grating_holo_left_distance = Setting(300.0)
    grating_holo_left_incidence_angle = Setting(-20.0)
    grating_holo_left_azimuth_from_y = Setting(0.0)
    grating_holo_right_distance = Setting(300.0)
    grating_holo_right_incidence_angle = Setting(-20.0)
    grating_holo_right_azimuth_from_y = Setting(0.0)
    grating_holo_pattern_type = Setting(0)
    grating_holo_source_type = Setting(0)
    grating_holo_cylindrical_source = Setting(0)
    grating_holo_recording_wavelength = Setting(4879.86)

    grating_groove_pole_distance = Setting(0.0)
    grating_groove_pole_azimuth_from_y = Setting(0.0)
    grating_coma_correction_factor = Setting(0.0)

    grating_poly_coeff_1 = Setting(0.0)
    grating_poly_coeff_2 = Setting(0.0)
    grating_poly_coeff_3 = Setting(0.0)
    grating_poly_coeff_4 = Setting(0.0)
    grating_poly_signed_absolute = Setting(0)

    grating_mount_type = Setting(0)

    grating_hunter_blaze_angle = Setting(0.0)
    grating_hunter_grating_selected = Setting(0)
    grating_hunter_monochromator_length = Setting(0.0)
    grating_hunter_distance_between_beams = Setting(0.0)


    optical_constants_refraction_index = Setting(0)
    fresnel_zone_plate = Setting(0)
    refractive_index_in_object_medium = Setting(0.0)
    attenuation_in_object_medium = Setting(0.0)
    file_prerefl_for_object_medium = Setting("NONE SPECIFIED")
    refractive_index_in_image_medium = Setting(0.0)
    attenuation_in_image_medium = Setting(0.0)
    file_prerefl_for_image_medium = Setting("NONE SPECIFIED")

    ##########################################
    # ADVANCED SETTING
    ##########################################

    modified_surface = Setting(0)

    # surface error
    ms_type_of_defect = Setting(0)
    ms_defect_file_name = Setting(NONE_SPECIFIED)
    ms_ripple_wavel_x = Setting(0.0)
    ms_ripple_wavel_y = Setting(0.0)
    ms_ripple_ampli_x = Setting(0.0)
    ms_ripple_ampli_y = Setting(0.0)
    ms_ripple_phase_x = Setting(0.0)
    ms_ripple_phase_y = Setting(0.0)

    # faceted surface
    ms_file_facet_descr = Setting(NONE_SPECIFIED)
    ms_lattice_type = Setting(0)
    ms_orientation = Setting(0)
    ms_intercept_to_use = Setting(0)
    ms_facet_width_x = Setting(10.0)
    ms_facet_phase_x = Setting(0.0)
    ms_dead_width_x_minus = Setting(0.0)
    ms_dead_width_x_plus = Setting(0.0)
    ms_facet_width_y = Setting(10.0)
    ms_facet_phase_y = Setting(0.0)
    ms_dead_width_y_minus = Setting(0.0)
    ms_dead_width_y_plus = Setting(0.0)

    # surface roughness
    ms_file_surf_roughness = Setting(NONE_SPECIFIED)
    ms_roughness_rms_x = Setting(0.0)
    ms_roughness_rms_y = Setting(0.0)

    # kumakhov lens
    ms_specify_rz2 = Setting(0)
    ms_file_with_parameters_rz = Setting(NONE_SPECIFIED)
    ms_file_with_parameters_rz2 = Setting(NONE_SPECIFIED)
    ms_save_intercept_bounces = Setting(0)

    # segmented mirror
    ms_number_of_segments_x = Setting(1)
    ms_number_of_segments_y = Setting(1)
    ms_length_of_segments_x = Setting(0.0)
    ms_length_of_segments_y = Setting(0.0)
    ms_file_orientations = Setting(NONE_SPECIFIED)
    ms_file_polynomial = Setting(NONE_SPECIFIED)

    #####

    mirror_movement = Setting(0)

    mm_mirror_offset_x = Setting(0.0)
    mm_mirror_rotation_x = Setting(0.0)
    mm_mirror_offset_y = Setting(0.0)
    mm_mirror_rotation_y = Setting(0.0)
    mm_mirror_offset_z = Setting(0.0)
    mm_mirror_rotation_z = Setting(0.0)

    #####

    source_movement = Setting(0)
    sm_angle_of_incidence = Setting(0.0)
    sm_distance_from_mirror = Setting(0.0)
    sm_z_rotation = Setting(0.0)
    sm_offset_x_mirr_ref_frame = Setting(0.0)
    sm_offset_y_mirr_ref_frame = Setting(0.0)
    sm_offset_z_mirr_ref_frame = Setting(0.0)
    sm_offset_x_source_ref_frame = Setting(0.0)
    sm_offset_y_source_ref_frame = Setting(0.0)
    sm_offset_z_source_ref_frame = Setting(0.0)
    sm_rotation_around_x = Setting(0.0)
    sm_rotation_around_y = Setting(0.0)
    sm_rotation_around_z = Setting(0.0)

    #####

    file_to_write_out = Setting(3)
    write_out_inc_ref_angles = Setting(0)

    ##########################################
    # DCM UTILITY
    ##########################################

    vertical_quote = Setting(0.0)
    total_distance = Setting(0.0)
    twotheta_bragg = Setting(0.0)

    d_1 = 0.0
    d_2 = 0.0

    image_path = resources.package_dirname("orangecontrib.shadow.widgets.gui") + "/misc/distances.png"

    ##########################################
    # SCREEN/SLIT SETTING
    ##########################################

    aperturing = Setting(0)
    open_slit_solid_stop = Setting(0)
    aperture_shape = Setting(0)
    slit_width_xaxis = Setting(0.0)
    slit_height_zaxis = Setting(0.0)
    slit_center_xaxis = Setting(0.0)
    slit_center_zaxis = Setting(0.0)
    external_file_with_coordinate=Setting(NONE_SPECIFIED)
    absorption = Setting(0)
    thickness = Setting(0.0)
    opt_const_file_name = Setting(NONE_SPECIFIED)

    want_main_area=1

    def __init__(self, graphical_options = GraphicalOptions()):
        super().__init__()

        self.runaction = widget.OWAction("Copy O.E. Parameters", self)
        self.runaction.triggered.connect(self.copy_oe_parameters)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Paste O.E. Parameters", self)
        self.runaction.triggered.connect(self.paste_oe_parameters)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Run Shadow/Trace", self)
        self.runaction.triggered.connect(self.traceOpticalElement)
        self.addAction(self.runaction)

        self.graphical_options = graphical_options

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow/Trace", callback=self.traceOpticalElement)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_pos = oasysgui.createTabPage(tabs_setting, "Position")

        upper_box = oasysgui.widgetBox(tab_pos, "Optical Element Orientation", addSpace=True, orientation="vertical")

        self.le_source_plane_distance = oasysgui.lineEdit(upper_box, self, "source_plane_distance", "Source Plane Distance", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_image_plane_distance  = oasysgui.lineEdit(upper_box, self, "image_plane_distance", "Image Plane Distance", labelWidth=260, valueType=float, orientation="horizontal")

        # graph tab
        if not self.graphical_options.is_empty:
            tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_adv = oasysgui.createTabPage(tabs_setting, "Advanced Setting")

        ##########################################
        ##########################################
        # ADVANCED SETTINGS
        ##########################################
        ##########################################

        tabs_advanced_setting = gui.tabWidget(tab_adv)

        if not (self.graphical_options.is_empty or graphical_options.is_screen_slit):
            tab_adv_mod_surf = oasysgui.createTabPage(tabs_advanced_setting, "Modified Surface")
        tab_adv_mir_mov = oasysgui.createTabPage(tabs_advanced_setting, "O.E. Movement")
        tab_adv_sou_mov = oasysgui.createTabPage(tabs_advanced_setting, "Source Movement")
        tab_adv_misc = oasysgui.createTabPage(tabs_advanced_setting, "Output Files")


        ##########################################
        #
        # TAB 2.2 - Mirror Movement
        #
        ##########################################

        mir_mov_box = oasysgui.widgetBox(tab_adv_mir_mov, "O.E. Movement Parameters", addSpace=False, orientation="vertical", height=230)

        gui.comboBox(mir_mov_box, self, "mirror_movement", label="O.E. Movement", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_MirrorMovement, sendSelectedValue=False, orientation="horizontal")

        gui.separator(mir_mov_box, height=10)

        self.mir_mov_box_1 = oasysgui.widgetBox(mir_mov_box, "", addSpace=False, orientation="vertical")

        self.le_mm_mirror_offset_x = oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_x", "O.E. Offset X", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_x", "O.E. Rotation X [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_mm_mirror_offset_y = oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_y", "O.E. Offset Y", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_y", "O.E. Rotation Y [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_mm_mirror_offset_z = oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_z", "O.E. Offset Z", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_z", "O.E. Rotation Z [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_MirrorMovement()

       ##########################################
        #
        # TAB 2.3 - Source Movement
        #
        ##########################################

        sou_mov_box = oasysgui.widgetBox(tab_adv_sou_mov, "Source Movement Parameters", addSpace=False, orientation="vertical", height=400)

        gui.comboBox(sou_mov_box, self, "source_movement", label="Source Movement", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_SourceMovement, sendSelectedValue=False, orientation="horizontal")

        gui.separator(sou_mov_box, height=10)

        self.sou_mov_box_1 = oasysgui.widgetBox(sou_mov_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_angle_of_incidence", "Angle of Incidence [deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_distance_from_mirror = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_distance_from_mirror", "Distance from O.E.", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_z_rotation", "Z-rotation [deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_x_mirr_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_mirr_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_y_mirr_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_mirr_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_z_mirr_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_mirr_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_x_source_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_source_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_y_source_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_source_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_z_source_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_source_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_x", "rotation [CCW, deg] around X", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_y", "rotation [CCW, deg] around Y", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_z", "rotation [CCW, deg] around Z", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_SourceMovement()

        ##########################################
        #
        # TAB 2.4 - Other
        #
        ##########################################

        adv_other_box = oasysgui.widgetBox(tab_adv_misc, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=150,
                     items=["All", "Mirror", "Image", "None", "Debug (All + start.xx/end.xx)"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_Footprint)

        gui.comboBox(adv_other_box, self, "write_out_inc_ref_angles", label="Write out Incident/Reflected angles [angle.xx]", labelWidth=300,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")

        self.set_Footprint()


        if self.graphical_options.is_screen_slit:
            box_aperturing = oasysgui.widgetBox(tab_bas, "Screen/Slit Shape", addSpace=True, orientation="vertical", height=240)

            gui.comboBox(box_aperturing, self, "aperturing", label="Aperturing", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_Aperturing, sendSelectedValue=False, orientation="horizontal")

            gui.separator(box_aperturing, width=self.INNER_BOX_WIDTH_L0)

            self.box_aperturing_shape = oasysgui.widgetBox(box_aperturing, "", addSpace=False, orientation="vertical")

            gui.comboBox(self.box_aperturing_shape, self, "open_slit_solid_stop", label="Open slit/Solid stop", labelWidth=260,
                         items=["aperture/slit", "obstruction/stop"],
                         sendSelectedValue=False, orientation="horizontal")

            gui.comboBox(self.box_aperturing_shape, self, "aperture_shape", label="Aperture shape", labelWidth=260,
                         items=["Rectangular", "Ellipse", "External"],
                         callback=self.set_ApertureShape, sendSelectedValue=False, orientation="horizontal")


            self.box_aperturing_shape_1 = oasysgui.widgetBox(self.box_aperturing_shape, "", addSpace=False, orientation="horizontal")


            self.le_external_file_with_coordinate = oasysgui.lineEdit(self.box_aperturing_shape_1, self, "external_file_with_coordinate", "External file with coordinate", labelWidth=185, valueType=str, orientation="horizontal")

            pushButton = gui.button(self.box_aperturing_shape_1, self, "...")
            pushButton.clicked.connect(self.selectExternalFileWithCoordinate)

            self.box_aperturing_shape_2 = oasysgui.widgetBox(self.box_aperturing_shape, "", addSpace=False, orientation="vertical")

            self.le_slit_width_xaxis  = oasysgui.lineEdit(self.box_aperturing_shape_2, self, "slit_width_xaxis", "Slit width/x-axis", labelWidth=260, valueType=float, orientation="horizontal")
            self.le_slit_height_zaxis = oasysgui.lineEdit(self.box_aperturing_shape_2, self, "slit_height_zaxis", "Slit height/z-axis", labelWidth=260, valueType=float, orientation="horizontal")
            self.le_slit_center_xaxis = oasysgui.lineEdit(self.box_aperturing_shape_2, self, "slit_center_xaxis", "Slit center/x-axis", labelWidth=260, valueType=float, orientation="horizontal")
            self.le_slit_center_zaxis = oasysgui.lineEdit(self.box_aperturing_shape_2, self, "slit_center_zaxis", "Slit center/z-axis", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_Aperturing()

            box_absorption = oasysgui.widgetBox(tab_bas, "Absorption Parameters", addSpace=True, orientation="vertical", height=130)

            gui.comboBox(box_absorption, self, "absorption", label="Absorption", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_Absorption, sendSelectedValue=False, orientation="horizontal")

            gui.separator(box_absorption, width=self.INNER_BOX_WIDTH_L0)

            self.box_absorption_1 = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")
            self.box_absorption_1_empty = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")

            self.le_thickness = oasysgui.lineEdit(self.box_absorption_1, self, "thickness", "Thickness", labelWidth=300, valueType=float, orientation="horizontal")

            file_box = oasysgui.widgetBox(self.box_absorption_1, "", addSpace=True, orientation="horizontal", height=25)

            self.le_opt_const_file_name = oasysgui.lineEdit(file_box, self, "opt_const_file_name", "Opt. const. file name", labelWidth=130, valueType=str, orientation="horizontal")

            pushButton = gui.button(file_box, self, "...")
            pushButton.clicked.connect(self.selectOptConstFileName)

            self.set_Absorption()
        else:
            gui.comboBox(upper_box, self, "angles_respect_to", label="Angles in [deg] indicated with respect to the", labelWidth=260,
                         items=["Normal", "Surface"],
                         callback=self.set_AnglesRespectTo,
                         sendSelectedValue=False, orientation="horizontal")

            self.incidence_angle_deg_le = oasysgui.lineEdit(upper_box, self, "incidence_angle_deg", "--", labelWidth=300, callback=self.calculate_incidence_angle_mrad, valueType=float, orientation="horizontal")
            self.incidence_angle_rad_le = oasysgui.lineEdit(upper_box, self, "incidence_angle_mrad", "Incident Angle with respect to the surface [mrad]", labelWidth=300, callback=self.calculate_incidence_angle_deg, valueType=float, orientation="horizontal")
            self.reflection_angle_deg_le = oasysgui.lineEdit(upper_box, self, "reflection_angle_deg", "--", labelWidth=300, callback=self.calculate_reflection_angle_mrad, valueType=float, orientation="horizontal")
            self.reflection_angle_rad_le = oasysgui.lineEdit(upper_box, self, "reflection_angle_mrad", "Reflection Angle with respect to the surface [mrad]", labelWidth=300, callback=self.calculate_reflection_angle_deg, valueType=float, orientation="horizontal")

            self.set_AnglesRespectTo()

            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            if self.graphical_options.is_mirror:
                self.reflection_angle_deg_le.setEnabled(False)
                self.reflection_angle_rad_le.setEnabled(False)

            gui.comboBox(upper_box, self, "mirror_orientation_angle", label="O.E. Orientation Angle [deg]", labelWidth=390,
                         items=[0, 90, 180, 270],
                         valueType=float,
                         sendSelectedValue=False, orientation="horizontal")

            if not self.graphical_options.is_empty:
                if self.graphical_options.is_crystal:
                    tab_dcm = oasysgui.createTabPage(tabs_setting, "D.C.M. Utility")

                tabs_basic_setting = gui.tabWidget(tab_bas)

                if self.graphical_options.is_curved: tab_bas_shape = oasysgui.createTabPage(tabs_basic_setting, "Surface Shape")
                if self.graphical_options.is_mirror: tab_bas_refl = oasysgui.createTabPage(tabs_basic_setting, "Reflectivity")
                elif self.graphical_options.is_crystal: tab_bas_crystal = oasysgui.createTabPage(tabs_basic_setting, "Crystal")
                elif self.graphical_options.is_grating: tab_bas_grating = oasysgui.createTabPage(tabs_basic_setting, "Grating")
                elif self.graphical_options.is_refractor: tab_bas_refractor = oasysgui.createTabPage(tabs_basic_setting, "Refractor")
                tab_bas_dim = oasysgui.createTabPage(tabs_basic_setting, "Dimensions")

                ##########################################
                #
                # TAB 1.1 - SURFACE SHAPE
                #
                ##########################################


                if self.graphical_options.is_curved:
                    surface_box = oasysgui.widgetBox(tab_bas_shape, "Surface Shape Parameter", addSpace=False, orientation="vertical")

                    if self.graphical_options.is_conic_coefficients:
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_0", "c[1]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_1", "c[2]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_2", "c[3]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_3", "c[4]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_4", "c[5]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_5", "c[6]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_6", "c[7]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_7", "c[8]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_8", "c[9]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_9", "c[10]", labelWidth=260, valueType=float, orientation="horizontal")
                    else:
                        gui.comboBox(surface_box, self, "surface_shape_parameters", label="Type", items=["internal/calculated", "external/user_defined"], labelWidth=240,
                                     callback=self.set_IntExt_Parameters, sendSelectedValue=False, orientation="horizontal")

                        self.surface_box_ext = oasysgui.widgetBox(surface_box, "", addSpace=True, orientation="vertical", height=150)
                        gui.separator(self.surface_box_ext)

                        if self.graphical_options.is_spheric:
                            self.le_spherical_radius = oasysgui.lineEdit(self.surface_box_ext, self, "spherical_radius", "Spherical Radius", labelWidth=260, valueType=float, orientation="horizontal")
                        elif self.graphical_options.is_toroidal:
                            self.le_torus_major_radius = oasysgui.lineEdit(self.surface_box_ext, self, "torus_major_radius", "Torus Major Radius", labelWidth=260, valueType=float, orientation="horizontal")
                            self.le_torus_minor_radius = oasysgui.lineEdit(self.surface_box_ext, self, "torus_minor_radius", "Torus Minor Radius", labelWidth=260, valueType=float, orientation="horizontal")
                        elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                            self.le_ellipse_hyperbola_semi_major_axis = oasysgui.lineEdit(self.surface_box_ext, self, "ellipse_hyperbola_semi_major_axis", "Ellipse/Hyperbola semi-major Axis",  labelWidth=260, valueType=float, orientation="horizontal")
                            self.le_ellipse_hyperbola_semi_minor_axis = oasysgui.lineEdit(self.surface_box_ext, self, "ellipse_hyperbola_semi_minor_axis", "Ellipse/Hyperbola semi-minor Axis", labelWidth=260, valueType=float, orientation="horizontal")
                            oasysgui.lineEdit(self.surface_box_ext, self, "angle_of_majax_and_pole", "Angle of MajAx and Pole [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
                        elif self.graphical_options.is_paraboloid:
                            self.le_paraboloid_parameter = oasysgui.lineEdit(self.surface_box_ext, self, "paraboloid_parameter", "Paraboloid parameter", labelWidth=260, valueType=float, orientation="horizontal")

                        self.surface_box_int = oasysgui.widgetBox(surface_box, "", addSpace=True, orientation="vertical", height=150)

                        gui.comboBox(self.surface_box_int, self, "focii_and_continuation_plane", label="Focii and Continuation Plane", labelWidth=280,
                                     items=["Coincident", "Different"], callback=self.set_FociiCont_Parameters, sendSelectedValue=False, orientation="horizontal")

                        self.surface_box_int_2 = oasysgui.widgetBox(self.surface_box_int, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)
                        self.surface_box_int_2_empty = oasysgui.widgetBox(self.surface_box_int, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)

                        self.w_object_side_focal_distance = oasysgui.lineEdit(self.surface_box_int_2, self, "object_side_focal_distance", "Object Side_Focal Distance", labelWidth=260, valueType=float, orientation="horizontal")
                        self.w_image_side_focal_distance = oasysgui.lineEdit(self.surface_box_int_2, self, "image_side_focal_distance", "Image Side_Focal Distance", labelWidth=260, valueType=float, orientation="horizontal")
                        self.w_incidence_angle_respect_to_normal = oasysgui.lineEdit(self.surface_box_int_2, self, "incidence_angle_respect_to_normal", "Incidence Angle Respect to Normal [deg]", labelWidth=260, valueType=float, orientation="horizontal")

                        if self.graphical_options.is_paraboloid:
                            gui.comboBox(self.surface_box_int, self, "focus_location", label="Focus location", labelWidth=280, items=["Image", "Source"], sendSelectedValue=False, orientation="horizontal")

                        self.set_IntExt_Parameters()

                        if self.graphical_options.is_toroidal:
                            surface_box_thorus = oasysgui.widgetBox(surface_box, "", addSpace=True, orientation="vertical")

                            gui.comboBox(surface_box_thorus, self, "toroidal_mirror_pole_location", label="Torus pole location", labelWidth=145,
                                         items=["lower/outer (concave/concave)",
                                                "lower/inner (concave/convex)",
                                                "upper/inner (convex/concave)",
                                                "upper/outer (convex/convex)"],
                                         sendSelectedValue=False, orientation="horizontal")

                        if not self.graphical_options.is_toroidal:
                            surface_box_2 = oasysgui.widgetBox(tab_bas_shape, "Cylinder Parameter", addSpace=True, orientation="vertical", height=125)

                            gui.comboBox(surface_box_2, self, "surface_curvature", label="Surface Curvature", items=["Concave", "Convex"], labelWidth=280, sendSelectedValue=False, orientation="horizontal")
                            gui.comboBox(surface_box_2, self, "is_cylinder", label="Cylindrical", items=["No", "Yes"],  labelWidth=350, callback=self.set_isCyl_Parameters, sendSelectedValue=False, orientation="horizontal")

                            self.surface_box_cyl = oasysgui.widgetBox(surface_box_2, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)
                            self.surface_box_cyl_empty = oasysgui.widgetBox(surface_box_2, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)

                            gui.comboBox(self.surface_box_cyl, self, "cylinder_orientation", label="Cylinder Orientation (deg) [CCW from X axis]", labelWidth=350,
                                         items=[0, 90],
                                         valueType=float,
                                         sendSelectedValue=False, orientation="horizontal")

                            self.set_isCyl_Parameters()

                ##########################################
                #
                # TAB 1.2 - REFLECTIVITY/CRYSTAL
                #
                ##########################################

                if self.graphical_options.is_mirror:
                    refl_box = oasysgui.widgetBox(tab_bas_refl, "Reflectivity Parameter", addSpace=False, orientation="vertical", height=190)

                    gui.comboBox(refl_box, self, "reflectivity_type", label="Reflectivity", labelWidth=150,
                                 items=["Not considered", "Full Polarization dependence", "No Polarization dependence (scalar)"],
                                 callback=self.set_Refl_Parameters, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(refl_box, width=self.INNER_BOX_WIDTH_L2, height=10)

                    self.refl_box_pol = oasysgui.widgetBox(refl_box, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)
                    self.refl_box_pol_empty = oasysgui.widgetBox(refl_box, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)

                    gui.comboBox(self.refl_box_pol, self, "source_of_reflectivity", label="Source of Reflectivity", labelWidth=150,
                                 items=["file generated by PREREFL", "electric susceptibility", "file generated by pre_mlayer"],
                                 callback=self.set_ReflSource_Parameters, sendSelectedValue=False, orientation="horizontal")

                    self.refl_box_pol_1 = oasysgui.widgetBox(self.refl_box_pol, "", addSpace=True, orientation="vertical")

                    gui.separator(self.refl_box_pol_1, width=self.INNER_BOX_WIDTH_L1)

                    file_box = oasysgui.widgetBox(self.refl_box_pol_1, "", addSpace=True, orientation="horizontal", height=25)

                    self.le_file_prerefl = oasysgui.lineEdit(file_box, self, "file_prerefl", "File Name", labelWidth=100, valueType=str, orientation="horizontal")

                    pushButton = gui.button(file_box, self, "...")
                    pushButton.clicked.connect(self.selectFilePrerefl)

                    self.refl_box_pol_2 = gui.widgetBox(self.refl_box_pol, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.refl_box_pol_2, self, "alpha", "Alpha [epsilon=(1-alpha)+i gamma]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.refl_box_pol_2, self, "gamma", "Gamma [epsilon=(1-alpha)+i gamma]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.refl_box_pol_3 = gui.widgetBox(self.refl_box_pol, "", addSpace=True, orientation="vertical")

                    file_box = oasysgui.widgetBox(self.refl_box_pol_3, "", addSpace=True, orientation="horizontal", height=25)

                    self.le_file_prerefl_m = oasysgui.lineEdit(file_box, self, "file_prerefl_m", "File Name", labelWidth=100, valueType=str, orientation="horizontal")

                    pushButton = gui.button(file_box, self, "...")
                    pushButton.clicked.connect(self.selectFilePrereflM)

                    gui.comboBox(self.refl_box_pol_3, self, "m_layer_tickness", label="Mlayer thickness vary as cosine", labelWidth=350,
                                 items=["No", "Yes"],
                                 sendSelectedValue=False, orientation="horizontal")

                    self.set_Refl_Parameters()
                elif self.graphical_options.is_crystal:

                    dcm_box = oasysgui.widgetBox(tab_dcm, "Optical Parameters", addSpace=True, orientation="vertical")

                    figure_box = oasysgui.widgetBox(dcm_box, "", addSpace=True, orientation="horizontal")

                    label = QtGui.QLabel("")
                    label.setPixmap(QtGui.QPixmap(self.image_path))

                    figure_box.layout().addWidget(label)

                    self.le_vertical_quote = oasysgui.lineEdit(dcm_box, self, "vertical_quote", "H (Vertical Distance)", labelWidth=260, valueType=float, orientation="horizontal", callback=self.calculate_dcm_distances)
                    self.le_total_distance = oasysgui.lineEdit(dcm_box, self, "total_distance", "D (First Crystal to Next O.E.)", labelWidth=260, valueType=float, orientation="horizontal", callback=self.calculate_dcm_distances)

                    dcm_box_1 = oasysgui.widgetBox(dcm_box, "", addSpace=True, orientation="horizontal")
                    oasysgui.lineEdit(dcm_box_1, self, "twotheta_bragg", "Bragg Angle [deg]",
                                       labelWidth=190, valueType=float, orientation="horizontal", callback=self.calculate_dcm_distances)

                    dcm_button1 = gui.button(dcm_box_1, self, "from O.E.")
                    dcm_button1.clicked.connect(self.grab_dcm_value_from_oe)

                    gui.separator(dcm_box_1)

                    dcm_box_2 = oasysgui.widgetBox(dcm_box, "", addSpace=True, orientation="horizontal")

                    self.le_d_1 = oasysgui.lineEdit(dcm_box_2, self, "d_1", "d_1", labelWidth=100, valueType=float, orientation="horizontal")
                    self.le_d_1.setReadOnly(True)
                    font = QtGui.QFont(self.le_d_1.font())
                    font.setBold(True)
                    self.le_d_1.setFont(font)
                    palette = QtGui.QPalette(self.le_d_1.palette()) # make a copy of the palette
                    palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
                    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
                    self.le_d_1.setPalette(palette)

                    dcm_button2_1 = gui.button(dcm_box_2, self, "set as S.P.")
                    dcm_button2_1.clicked.connect(self.set_d1_as_source_plane)

                    dcm_button2_2 = gui.button(dcm_box_2, self, "set as I.P.")
                    dcm_button2_2.clicked.connect(self.set_d1_as_image_plane)

                    dcm_box_3 = oasysgui.widgetBox(dcm_box, "", addSpace=True, orientation="horizontal")

                    self.le_d_2 = oasysgui.lineEdit(dcm_box_3, self, "d_2", "d_2", labelWidth=100, valueType=float, orientation="horizontal")
                    self.le_d_2.setReadOnly(True)
                    font = QtGui.QFont(self.le_d_2.font())
                    font.setBold(True)
                    self.le_d_2.setFont(font)
                    palette = QtGui.QPalette(self.le_d_2.palette()) # make a copy of the palette
                    palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
                    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
                    self.le_d_2.setPalette(palette)

                    dcm_button3_1 = gui.button(dcm_box_3, self, "set as S.P.")
                    dcm_button3_1.clicked.connect(self.set_d2_as_source_plane)

                    dcm_button3_2 = gui.button(dcm_box_3, self, "set as I.P.")
                    dcm_button3_2.clicked.connect(self.set_d2_as_image_plane)

                    self.grab_dcm_value_from_oe()
                    self.calculate_dcm_distances()

                    ####################################

                    tabs_crystal_setting = gui.tabWidget(tab_bas_crystal)

                    self.tab_cryst_1 = oasysgui.createTabPage(tabs_crystal_setting, "Diffraction Settings")
                    self.tab_cryst_2 = oasysgui.createTabPage(tabs_crystal_setting, "Geometric Setting")

                    crystal_box = oasysgui.widgetBox(self.tab_cryst_1, "Diffraction Parameters", addSpace=True,
                                                      orientation="vertical", height=240)

                    gui.comboBox(crystal_box, self, "diffraction_geometry", label="Diffraction Geometry", labelWidth=250,
                                 items=["Bragg", "Laue"],
                                 sendSelectedValue=False, orientation="horizontal")

                    gui.comboBox(crystal_box, self, "diffraction_calculation", label="Diffraction Profile", labelWidth=250,
                                 items=["Calculated", "User Defined"],
                                 sendSelectedValue=False, orientation="horizontal",
                                 callback=self.set_DiffractionCalculation)

                    gui.separator(crystal_box, height=10)

                    self.crystal_box_1 = oasysgui.widgetBox(crystal_box, "", addSpace=True, orientation="vertical",
                                                             height=150)


                    file_box = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=True, orientation="horizontal", height=30)

                    self.le_file_crystal_parameters = oasysgui.lineEdit(file_box, self, "file_crystal_parameters", "File with crystal\nparameters",
                                       labelWidth=150, valueType=str, orientation="horizontal")

                    pushButton = gui.button(file_box, self, "...")
                    pushButton.clicked.connect(self.selectFileCrystalParameters)

                    gui.comboBox(self.crystal_box_1, self, "crystal_auto_setting", label="Auto setting", labelWidth=350,
                                 items=["No", "Yes"],
                                 callback=self.set_Autosetting, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(self.crystal_box_1, height=10)

                    self.autosetting_box = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=True,
                                                               orientation="vertical")
                    self.autosetting_box_empty = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=True,
                                                                     orientation="vertical")

                    self.autosetting_box_units = oasysgui.widgetBox(self.autosetting_box, "", addSpace=True, orientation="vertical")

                    gui.comboBox(self.autosetting_box_units, self, "units_in_use", label="Units in use", labelWidth=260,
                                 items=["eV", "Angstroms"],
                                 callback=self.set_UnitsInUse, sendSelectedValue=False, orientation="horizontal")

                    self.autosetting_box_units_1 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.autosetting_box_units_1, self, "photon_energy", "Set photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.autosetting_box_units_2 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.autosetting_box_units_2, self, "photon_wavelength", "Set wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.crystal_box_2 = oasysgui.widgetBox(crystal_box, "", addSpace=True, orientation="horizontal",
                                                             height=150)

                    self.le_file_diffraction_profile = oasysgui.lineEdit(self.crystal_box_2, self, "file_diffraction_profile",
                                       "File with Diffraction\nProfile (XOP format)", labelWidth=150, valueType=str,
                                       orientation="horizontal")

                    pushButton = gui.button(self.crystal_box_2, self, "...")
                    pushButton.clicked.connect(self.selectFileDiffractionProfile)

                    self.set_DiffractionCalculation()

                    mosaic_box = oasysgui.widgetBox(self.tab_cryst_2, "Geometric Parameters", addSpace=True,
                                                     orientation="vertical", height=350)

                    gui.comboBox(mosaic_box, self, "mosaic_crystal", label="Mosaic Crystal", labelWidth=355,
                                 items=["No", "Yes"],
                                 callback=self.set_Mosaic, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(mosaic_box, height=10)

                    self.mosaic_box_1 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")

                    self.asymmetric_cut_box = oasysgui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=110)

                    gui.comboBox(self.asymmetric_cut_box, self, "asymmetric_cut", label="Asymmetric cut", labelWidth=355,
                                 items=["No", "Yes"],
                                 callback=self.set_AsymmetricCut, sendSelectedValue=False, orientation="horizontal")

                    self.asymmetric_cut_box_1 = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")
                    self.asymmetric_cut_box_1_empty = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.asymmetric_cut_box_1, self, "planes_angle", "Planes angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.asymmetric_cut_box_1, self, "below_onto_bragg_planes", "Below[-1]/onto[1] bragg planes",  labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_thickness_1 = oasysgui.lineEdit(self.asymmetric_cut_box_1, self, "thickness", "Thickness", valueType=float, labelWidth=260, orientation="horizontal")

                    gui.separator(self.mosaic_box_1)

                    self.johansson_box = oasysgui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=100)

                    gui.comboBox(self.johansson_box, self, "johansson_geometry", label="Johansson Geometry", labelWidth=355,
                                 items=["No", "Yes"],
                                 callback=self.set_JohanssonGeometry, sendSelectedValue=False, orientation="horizontal")

                    self.johansson_box_1 = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")
                    self.johansson_box_1_empty = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")

                    self.le_johansson_radius = oasysgui.lineEdit(self.johansson_box_1, self, "johansson_radius", "Johansson radius", labelWidth=260, valueType=float, orientation="horizontal")

                    self.mosaic_box_2 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.mosaic_box_2, self, "angle_spread_FWHM", "Angle spread FWHM [deg]",  labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_thickness_2 = oasysgui.lineEdit(self.mosaic_box_2, self, "thickness", "Thickness", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.mosaic_box_2, self, "seed_for_mosaic", "Seed for mosaic [>10^5]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.set_Mosaic()
                elif self.graphical_options.is_grating:
                    tabs_grating_setting = gui.tabWidget(tab_bas_grating)

                    tab_grating_2 = oasysgui.createTabPage(tabs_grating_setting, "Ruling Setting")
                    tab_grating_1 = oasysgui.createTabPage(tabs_grating_setting, "Diffraction Settings")

                    grating_box = oasysgui.widgetBox(tab_grating_1, "Diffraction Parameters", addSpace=True, orientation="vertical", height=380)

                    oasysgui.lineEdit(grating_box, self, "grating_diffraction_order", "Diffraction Order", labelWidth=260, valueType=float, orientation="horizontal")

                    gui.comboBox(grating_box, self, "grating_auto_setting", label="Auto setting", labelWidth=350,
                                 items=["No", "Yes"],
                                 callback=self.set_GratingAutosetting, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(grating_box, height=10)

                    self.grating_autosetting_box = oasysgui.widgetBox(grating_box, "", addSpace=True, orientation="vertical")
                    self.grating_autosetting_box_empty = oasysgui.widgetBox(grating_box, "", addSpace=True, orientation="vertical")

                    self.grating_autosetting_box_units = oasysgui.widgetBox(self.grating_autosetting_box, "", addSpace=True, orientation="vertical")

                    gui.comboBox(self.grating_autosetting_box_units, self, "grating_units_in_use", label="Units in use", labelWidth=260,
                                 items=["eV", "Angstroms"],
                                 callback=self.set_GratingUnitsInUse, sendSelectedValue=False, orientation="horizontal")

                    self.grating_autosetting_box_units_1 = oasysgui.widgetBox(self.grating_autosetting_box_units, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.grating_autosetting_box_units_1, self, "grating_photon_energy", "Set photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.grating_autosetting_box_units_2 = oasysgui.widgetBox(self.grating_autosetting_box_units, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.grating_autosetting_box_units_2, self, "grating_photon_wavelength", "Set wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.grating_mount_box = oasysgui.widgetBox(grating_box, "", addSpace=True, orientation="vertical")

                    gui.comboBox(self.grating_mount_box, self, "grating_mount_type", label="Mount Type", labelWidth=250,
                                 items=["TGM/Seya", "ERG", "Constant Incidence Angle", "Costant Diffraction Angle", "Hunter"],
                                 callback=self.set_GratingMountType, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(self.grating_mount_box)

                    self.grating_mount_box_1 = oasysgui.widgetBox(self.grating_mount_box, "", addSpace=True, orientation="vertical")

                    oasysgui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_blaze_angle", "Blaze angle [deg]", labelWidth=250, valueType=float, orientation="horizontal")
                    gui.comboBox(self.grating_mount_box_1, self, "grating_hunter_grating_selected", label="Grating selected", labelWidth=250,
                                 items=["First", "Second"], sendSelectedValue=False, orientation="horizontal")
                    self.le_grating_hunter_monochromator_length = oasysgui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_monochromator_length", "Monochromator Length", labelWidth=250, valueType=float, orientation="horizontal")
                    self.le_grating_hunter_distance_between_beams = oasysgui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_distance_between_beams", "Distance between beams", labelWidth=250, valueType=float, orientation="horizontal")

                    self.set_GratingAutosetting()

                    ################

                    ruling_box = oasysgui.widgetBox(tab_grating_2, "Ruling Parameters", addSpace=True, orientation="vertical", height=380)

                    gui.comboBox(ruling_box, self, "grating_ruling_type", label="Ruling Type", labelWidth=150,
                                 items=["Constant on X-Y Plane", "Constant on Mirror Surface", "Holographic", "Fan Type", "Polynomial Line Density"],
                                 callback=self.set_GratingRulingType, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(ruling_box)

                    self.ruling_box_1 = oasysgui.widgetBox(ruling_box, "", addSpace=True, orientation="horizontal")

                    self.ruling_density_label = gui.widgetLabel(self.ruling_box_1, "Ruling Density at origin", labelWidth=260)
                    oasysgui.lineEdit(self.ruling_box_1, self, "grating_ruling_density", "", labelWidth=1, valueType=float, orientation="horizontal")

                    self.ruling_box_2 = oasysgui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                    self.le_grating_holo_left_distance = oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_left_distance", "\"Left\" distance", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_left_incidence_angle", "\"Left\" incidence angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_left_azimuth_from_y", "\"Left\" azimuth from +Y (CCW) [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_grating_holo_right_distance = oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_right_distance", "\"Right\" distance", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_right_incidence_angle", "\"Right\" incidence angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_right_azimuth_from_y", "\"Right\" azimuth from +Y (CCW) [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    gui.comboBox(self.ruling_box_2, self, "grating_holo_pattern_type", label="Pattern Type", labelWidth=185,
                                 items=["Spherical/Spherical", "Plane/Spherical", "Spherical/Plane", "Plane/Plane"], sendSelectedValue=False, orientation="horizontal")
                    gui.comboBox(self.ruling_box_2, self, "grating_holo_source_type", label="Source Type", labelWidth=250,
                                 items=["Real/Real", "Real/Virtual", "Virtual/Real", "Real/Real"], sendSelectedValue=False, orientation="horizontal")
                    gui.comboBox(self.ruling_box_2, self, "grating_holo_cylindrical_source", label="Cylindrical Source", labelWidth=250,
                                 items=["Spherical/Spherical", "Cylindrical/Spherical", "Spherical/Cylindrical", "Cylindrical/Cylindrical"], sendSelectedValue=False, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_recording_wavelength", "Recording wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.ruling_box_3 = oasysgui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                    self.le_grating_groove_pole_distance = oasysgui.lineEdit(self.ruling_box_3, self, "grating_groove_pole_distance", "Groove pole distance", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_3, self, "grating_groove_pole_azimuth_from_y", "Groove pole azimuth from +Y (CCW) [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_3, self, "grating_coma_correction_factor", "Coma correction factor", labelWidth=260, valueType=float, orientation="horizontal")

                    self.ruling_box_4 = oasysgui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                    self.le_grating_poly_coeff_1 = oasysgui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_1", "Polyn. Line Density coeff.: 1st", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_grating_poly_coeff_2 = oasysgui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_2", "Polyn. Line Density coeff.: 2nd", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_grating_poly_coeff_3 = oasysgui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_3", "Polyn. Line Density coeff.: 3rd", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_grating_poly_coeff_4 = oasysgui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_4", "Polyn. Line Density coeff.: 4th", labelWidth=260, valueType=float, orientation="horizontal")
                    gui.comboBox(self.ruling_box_4, self, "grating_poly_signed_absolute", label="Line density absolute/signed from the origin", labelWidth=265,
                                 items=["Absolute", "Signed"], sendSelectedValue=False, orientation="horizontal")

                    self.set_GratingRulingType()

                elif self.graphical_options.is_refractor:
                    refractor_box = oasysgui.widgetBox(tab_bas_refractor, "Optical Constants - Refractive Index", addSpace=False, orientation="vertical", height=320)

                    gui.comboBox(refractor_box, self, "fresnel_zone_plate", label="Fresnel Zone Plate", labelWidth=260,
                                 items=["No", "Yes"],
                                 sendSelectedValue=False, orientation="horizontal")

                    gui.comboBox(refractor_box, self, "optical_constants_refraction_index", label="optical constants\n/refraction index", labelWidth=120,
                                 items=["constant in both media",
                                        "from prerefl in OBJECT media",
                                        "from prerefl in IMAGE media",
                                        "from prerefl in both media"],
                                 callback=self.set_RefrectorOpticalConstants, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(refractor_box, height=10)
                    self.refractor_object_box_1 = oasysgui.widgetBox(refractor_box, "OBJECT side", addSpace=False, orientation="vertical", height=100)
                    oasysgui.lineEdit(self.refractor_object_box_1, self, "refractive_index_in_object_medium", "refractive index in object medium", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_attenuation_in_object_medium = oasysgui.lineEdit(self.refractor_object_box_1, self, "attenuation_in_object_medium", "attenuation in object medium", labelWidth=260, valueType=float, orientation="horizontal")

                    self.refractor_object_box_2 = oasysgui.widgetBox(refractor_box, "OBJECT side", addSpace=False, orientation="horizontal", height=100)
                    self.le_file_prerefl_for_object_medium = oasysgui.lineEdit(self.refractor_object_box_2, self, "file_prerefl_for_object_medium",
                                                                                "file prerefl for\nobject medium", labelWidth=120, valueType=str, orientation="horizontal")

                    pushButton = gui.button(self.refractor_object_box_2, self, "...")
                    pushButton.clicked.connect(self.selectPrereflObjectFileName)

                    self.refractor_image_box_1 = oasysgui.widgetBox(refractor_box, "IMAGE side", addSpace=False, orientation="vertical", height=100)
                    oasysgui.lineEdit(self.refractor_image_box_1, self, "refractive_index_in_image_medium", "refractive index in image medium", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_attenuation_in_image_medium = oasysgui.lineEdit(self.refractor_image_box_1, self, "attenuation_in_image_medium", "attenuation in image medium", labelWidth=260, valueType=float, orientation="horizontal")

                    self.refractor_image_box_2 = oasysgui.widgetBox(refractor_box, "IMAGE side", addSpace=False, orientation="horizontal", height=100)
                    self.le_file_prerefl_for_image_medium = oasysgui.lineEdit(self.refractor_image_box_2, self, "file_prerefl_for_image_medium",
                                                                               "file prerefl for\nimage medium", labelWidth=120, valueType=str, orientation="horizontal")

                    pushButton = gui.button(self.refractor_image_box_2, self, "...")
                    pushButton.clicked.connect(self.selectPrereflImageFileName)

                    self.set_RefrectorOpticalConstants()

                ##########################################
                #
                # TAB 1.3 - DIMENSIONS
                #
                ##########################################

                dimension_box = oasysgui.widgetBox(tab_bas_dim, "Dimensions", addSpace=False, orientation="vertical", height=210)

                gui.comboBox(dimension_box, self, "is_infinite", label="Limits Check",
                             items=["Infinite o.e. dimensions", "Finite o.e. dimensions"],
                             callback=self.set_Dim_Parameters, sendSelectedValue=False, orientation="horizontal")

                gui.separator(dimension_box, width=self.INNER_BOX_WIDTH_L2, height=10)

                self.dimdet_box = oasysgui.widgetBox(dimension_box, "", addSpace=False, orientation="vertical")
                self.dimdet_box_empty = oasysgui.widgetBox(dimension_box, "", addSpace=False, orientation="vertical")

                gui.comboBox(self.dimdet_box, self, "mirror_shape", label="Shape selected", labelWidth=260,
                             items=["Rectangular", "Full ellipse", "Ellipse with hole"],
                             sendSelectedValue=False, orientation="horizontal")

                self.le_dim_x_plus  = oasysgui.lineEdit(self.dimdet_box, self, "dim_x_plus", "X(+) Half Width / Int Maj Ax", labelWidth=260, valueType=float, orientation="horizontal")
                self.le_dim_x_minus = oasysgui.lineEdit(self.dimdet_box, self, "dim_x_minus", "X(-) Half Width / Int Maj Ax", labelWidth=260, valueType=float, orientation="horizontal")
                self.le_dim_y_plus  = oasysgui.lineEdit(self.dimdet_box, self, "dim_y_plus", "Y(+) Half Width / Int Min Ax", labelWidth=260, valueType=float, orientation="horizontal")
                self.le_dim_y_minus = oasysgui.lineEdit(self.dimdet_box, self, "dim_y_minus", "Y(-) Half Width / Int Min Ax", labelWidth=260, valueType=float, orientation="horizontal")

                self.set_Dim_Parameters()


                ##########################################
                #
                # TAB 2.1 - Modified Surface
                #
                ##########################################

                mod_surf_box = oasysgui.widgetBox(tab_adv_mod_surf, "Modified Surface Parameters", addSpace=False, orientation="vertical", height=390)

                gui.comboBox(mod_surf_box, self, "modified_surface", label="Modification Type", labelWidth=260,
                             items=["None", "Surface Error", "Faceted Surface", "Surface Roughness", "Kumakhov Lens", "Segmented Mirror"],
                             callback=self.set_ModifiedSurface, sendSelectedValue=False, orientation="horizontal")

                gui.separator(mod_surf_box, height=10)

                # SURFACE ERROR

                self.surface_error_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

                type_of_defect_box = oasysgui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="vertical")

                gui.comboBox(type_of_defect_box, self, "ms_type_of_defect", label="Type of Defect", labelWidth=260,
                             items=["sinusoidal", "gaussian", "external spline"],
                             callback=self.set_TypeOfDefect, sendSelectedValue=False, orientation="horizontal")

                self.mod_surf_err_box_1 = oasysgui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="horizontal")

                self.le_ms_defect_file_name = oasysgui.lineEdit(self.mod_surf_err_box_1, self, "ms_defect_file_name", "File name", labelWidth=80, valueType=str, orientation="horizontal")

                pushButton = gui.button(self.mod_surf_err_box_1, self, "...")
                pushButton.clicked.connect(self.selectDefectFileName)
                pushButton = gui.button(self.mod_surf_err_box_1, self, "View")
                pushButton.clicked.connect(self.viewDefectFileName)

                self.mod_surf_err_box_2 = oasysgui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="vertical")

                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_wavel_x", "Ripple Wavel. X", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_wavel_y", "Ripple Wavel. Y", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_ampli_x", "Ripple Ampli. X", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_ampli_y", "Ripple Ampli. Y", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_phase_x", "Ripple Phase X", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_phase_y", "Ripple Phase Y", labelWidth=260, valueType=float, orientation="horizontal")

                # FACETED SURFACE

                self.faceted_surface_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

                file_box = oasysgui.widgetBox(self.faceted_surface_box, "", addSpace=True, orientation="horizontal", height=25)

                self.le_ms_file_facet_descr = oasysgui.lineEdit(file_box, self, "ms_file_facet_descr", "File w/ facet descr.", labelWidth=125, valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFileFacetDescr)

                gui.comboBox(self.faceted_surface_box, self, "ms_lattice_type", label="Lattice Type", labelWidth=260,
                             items=["rectangle", "hexagonal"], sendSelectedValue=False, orientation="horizontal")

                gui.comboBox(self.faceted_surface_box, self, "ms_orientation", label="Orientation", labelWidth=260,
                             items=["y-axis", "other"], sendSelectedValue=False, orientation="horizontal")

                gui.comboBox(self.faceted_surface_box, self, "ms_intercept_to_use", label="Intercept to use", labelWidth=260,
                             items=["2nd first", "2nd closest", "closest", "farthest"], sendSelectedValue=False, orientation="horizontal")


                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_facet_width_x", "Facet width (in X)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_facet_phase_x", "Facet phase in X (0-360)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_x_minus", "Dead width (abs, for -X)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_x_plus", "Dead width (abs, for +X)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_facet_width_y", "Facet width (in Y)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_facet_phase_y", "Facet phase in Y (0-360)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_y_minus", "Dead width (abs, for -Y)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_y_plus", "Dead width (abs, for +Y)", labelWidth=260, valueType=float, orientation="horizontal")

                # SURFACE ROUGHNESS

                self.surface_roughness_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")


                file_box = oasysgui.widgetBox(self.surface_roughness_box, "", addSpace=True, orientation="horizontal", height=25)

                self.le_ms_file_surf_roughness = oasysgui.lineEdit(file_box, self, "ms_file_surf_roughness", "Surf. Rough. File w/ PSD fn", valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFileSurfRoughness)

                oasysgui.lineEdit(self.surface_roughness_box, self, "ms_roughness_rms_y", "Roughness RMS in Y (Å)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.surface_roughness_box, self, "ms_roughness_rms_x", "Roughness RMS in X (Å)", labelWidth=260, valueType=float, orientation="horizontal")

                # KUMAKHOV LENS

                self.kumakhov_lens_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

                gui.comboBox(self.kumakhov_lens_box, self, "ms_specify_rz2", label="Specify r(z)^2", labelWidth=350,
                             items=["No", "Yes"], callback=self.set_SpecifyRz2, sendSelectedValue=False, orientation="horizontal")

                self.kumakhov_lens_box_1 =  oasysgui.widgetBox(self.kumakhov_lens_box, box="", addSpace=False, orientation="vertical")
                self.kumakhov_lens_box_2 =  oasysgui.widgetBox(self.kumakhov_lens_box, box="", addSpace=False, orientation="vertical")

                file_box = oasysgui.widgetBox(self.kumakhov_lens_box_1, "", addSpace=True, orientation="horizontal", height=25)

                self.le_ms_file_with_parameters_rz = oasysgui.lineEdit(file_box, self, "ms_file_with_parameters_rz", "File with parameters (r(z))", labelWidth=185, valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFileWithParametersRz)

                file_box = oasysgui.widgetBox(self.kumakhov_lens_box_2, "", addSpace=True, orientation="horizontal", height=25)

                self.le_ms_file_with_parameters_rz2 = oasysgui.lineEdit(file_box, self, "ms_file_with_parameters_rz2", "File with parameters (r(z)^2)", labelWidth=185, valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFileWithParametersRz2)

                gui.comboBox(self.kumakhov_lens_box, self, "ms_save_intercept_bounces", label="Save intercept and bounces", labelWidth=350,
                             items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

                # SEGMENTED MIRROR

                self.segmented_mirror_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

                oasysgui.lineEdit(self.segmented_mirror_box, self, "ms_number_of_segments_x", "Number of segments (X)", labelWidth=260, valueType=int, orientation="horizontal")
                oasysgui.lineEdit(self.segmented_mirror_box, self, "ms_length_of_segments_x", "Length of segments (X)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.segmented_mirror_box, self, "ms_number_of_segments_y", "Number of segments (Y)", labelWidth=260, valueType=int, orientation="horizontal")
                oasysgui.lineEdit(self.segmented_mirror_box, self, "ms_length_of_segments_y", "Length of segments (Y)", labelWidth=260, valueType=float, orientation="horizontal")


                file_box = oasysgui.widgetBox(self.segmented_mirror_box, "", addSpace=True, orientation="horizontal", height=25)

                self.le_ms_file_orientations = oasysgui.lineEdit(file_box, self, "ms_file_orientations", "File w/ orientations", labelWidth=155, valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFileOrientations)

                file_box = oasysgui.widgetBox(self.segmented_mirror_box, "", addSpace=True, orientation="horizontal", height=25)

                self.le_ms_file_polynomial = oasysgui.lineEdit(file_box, self, "ms_file_polynomial", "File w/ polynomial", labelWidth=155, valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFilePolynomial)

                self.set_ModifiedSurface()


    def after_change_workspace_units(self):
        label = self.le_source_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_image_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

        if self.graphical_options.is_screen_slit:
            label = self.le_slit_width_xaxis.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_slit_height_zaxis.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_slit_center_xaxis.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_slit_center_zaxis.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_thickness.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")


        else:
            if self.graphical_options.is_curved:
                if not self.graphical_options.is_conic_coefficients:
                    if self.graphical_options.is_spheric:
                        label = self.le_spherical_radius.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                    elif self.graphical_options.is_toroidal:
                        label = self.le_torus_major_radius.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_torus_minor_radius.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                    elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                        label = self.le_ellipse_hyperbola_semi_major_axis.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_ellipse_hyperbola_semi_minor_axis.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                    elif self.graphical_options.is_paraboloid:
                        label = self.le_paraboloid_parameter.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")

                    label = self.w_object_side_focal_distance.parent().layout().itemAt(0).widget()
                    label.setText(label.text() + " [" + self.workspace_units_label + "]")
                    label = self.w_image_side_focal_distance.parent().layout().itemAt(0).widget()
                    label.setText(label.text() + " [" + self.workspace_units_label + "]")

            if self.graphical_options.is_crystal:
                label = self.le_johansson_radius.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_vertical_quote.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_total_distance.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_d_1.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_d_2.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_thickness_1.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_thickness_2.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")

            elif self.graphical_options.is_grating:
                label = self.le_grating_hunter_monochromator_length.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_grating_hunter_distance_between_beams.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                self.ruling_density_label.setText(self.ruling_density_label.text() + "  [Lines/" + self.workspace_units_label + "]")
                label = self.le_grating_poly_coeff_1.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [Lines." + self.workspace_units_label + "-2]")
                label = self.le_grating_poly_coeff_2.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [Lines." + self.workspace_units_label + "-3]")
                label = self.le_grating_poly_coeff_3.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [Lines." + self.workspace_units_label + "-4]")
                label = self.le_grating_poly_coeff_4.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [Lines." + self.workspace_units_label + "-5]")

                label = self.le_grating_holo_left_distance.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_grating_holo_right_distance.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_grating_groove_pole_distance.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
            elif self.graphical_options.is_refractor:
                label = self.le_attenuation_in_object_medium.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "-1]")
                label = self.le_attenuation_in_image_medium.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "-1]")

            if not self.graphical_options.is_empty:
                # DIMENSIONS
                label = self.le_dim_x_plus.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_dim_x_minus.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_dim_y_plus.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_dim_y_minus.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")

        # ADVANCED SETTINGS
        # MIRROR MOVEMENTS
        label = self.le_mm_mirror_offset_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_mm_mirror_offset_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_mm_mirror_offset_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        # SOURCE MOVEMENTS
        label = self.le_sm_distance_from_mirror.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_sm_offset_x_mirr_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset X [" + self.workspace_units_label + "] in O.E. reference frame")
        label = self.le_sm_offset_y_mirr_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset Y [" + self.workspace_units_label + "] in O.E. reference frame")
        label = self.le_sm_offset_z_mirr_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset Z [" + self.workspace_units_label + "] in O.E. reference frame")
        label = self.le_sm_offset_x_source_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset X [" + self.workspace_units_label + "] in SOURCE reference frame")
        label = self.le_sm_offset_y_source_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset Y [" + self.workspace_units_label + "] in SOURCE reference frame")
        label = self.le_sm_offset_z_source_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset Z [" + self.workspace_units_label + "] in SOURCE reference frame")


    def set_Footprint(self):
        if self.file_to_write_out == 0 or self.file_to_write_out == 1 or self.file_to_write_out == 4:
            self.enableFootprint(not self.graphical_options.is_screen_slit)
        else:
            self.enableFootprint(False)

    def callResetSettings(self):
        super().callResetSettings()
        self.setupUI()

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def set_AnglesRespectTo(self):
        label_1 = self.incidence_angle_deg_le.parent().layout().itemAt(0).widget()
        label_2 = self.reflection_angle_deg_le.parent().layout().itemAt(0).widget()

        if self.angles_respect_to == 0:
            label_1.setText("Incident Angle with respect to the normal [deg]")
            label_2.setText("Reflection Angle with respect to the normal [deg]")
        else:
            label_1.setText("Incident Angle with respect to the surface [deg]")
            label_2.setText("Reflection Angle with respect to the surface [deg]")

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()

    # TAB 1.1

    def set_IntExt_Parameters(self):
        self.surface_box_int.setVisible(self.surface_shape_parameters == 0)
        self.surface_box_ext.setVisible(self.surface_shape_parameters == 1)
        if self.surface_shape_parameters == 0: self.set_FociiCont_Parameters()

    def set_FociiCont_Parameters(self):
        self.surface_box_int_2.setVisible(self.focii_and_continuation_plane == 1)
        self.surface_box_int_2_empty.setVisible(self.focii_and_continuation_plane == 0)

    def set_isCyl_Parameters(self):
        self.surface_box_cyl.setVisible(self.is_cylinder == 1)
        self.surface_box_cyl_empty.setVisible(self.is_cylinder == 0)

    # TAB 1.2

    def set_Refl_Parameters(self):
        self.refl_box_pol.setVisible(self.reflectivity_type != 0)
        self.refl_box_pol_empty.setVisible(self.reflectivity_type == 0)
        if self.reflectivity_type != 0: self.set_ReflSource_Parameters()

    def set_ReflSource_Parameters(self):
        self.refl_box_pol_1.setVisible(self.source_of_reflectivity == 0)
        self.refl_box_pol_2.setVisible(self.source_of_reflectivity == 1)
        self.refl_box_pol_3.setVisible(self.source_of_reflectivity == 2)

    def set_Autosetting(self):
        self.autosetting_box_empty.setVisible(self.crystal_auto_setting == 0)
        self.autosetting_box.setVisible(self.crystal_auto_setting == 1)

        if self.crystal_auto_setting == 0:
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.incidence_angle_deg_le.setEnabled(False)
            self.incidence_angle_rad_le.setEnabled(False)
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)
            self.set_UnitsInUse()

    def set_DiffractionCalculation(self):
        self.tab_cryst_2.setEnabled(self.diffraction_calculation == 0)

        self.crystal_box_1.setVisible(self.diffraction_calculation == 0)
        self.crystal_box_2.setVisible(self.diffraction_calculation == 1)

        if (self.diffraction_calculation == 1):
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.set_Autosetting()


    def set_UnitsInUse(self):
        self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
        self.autosetting_box_units_2.setVisible(self.units_in_use == 1)

    def set_Mosaic(self):
        self.mosaic_box_1.setVisible(self.mosaic_crystal == 0)
        self.mosaic_box_2.setVisible(self.mosaic_crystal == 1)

        if self.mosaic_crystal == 0:
            self.set_AsymmetricCut()
            self.set_JohanssonGeometry()

    def set_AsymmetricCut(self):
        self.asymmetric_cut_box_1.setVisible(self.asymmetric_cut == 1)
        self.asymmetric_cut_box_1_empty.setVisible(self.asymmetric_cut == 0)

    def set_JohanssonGeometry(self):
        self.johansson_box_1.setVisible(self.johansson_geometry == 1)
        self.johansson_box_1_empty.setVisible(self.johansson_geometry == 0)

    def set_GratingAutosetting(self):
        self.grating_autosetting_box_empty.setVisible(self.grating_auto_setting == 0)
        self.grating_autosetting_box.setVisible(self.grating_auto_setting == 1)
        self.grating_mount_box.setVisible(self.grating_auto_setting == 1)

        if self.grating_auto_setting == 1:
            self.set_GratingUnitsInUse()
            self.set_GratingMountType()

    def set_GratingUnitsInUse(self):
        self.grating_autosetting_box_units_1.setVisible(self.grating_units_in_use == 0)
        self.grating_autosetting_box_units_2.setVisible(self.grating_units_in_use == 1)

    def set_GratingRulingType(self):
        self.ruling_box_1.setVisible(self.grating_ruling_type != 2)
        self.ruling_box_2.setVisible(self.grating_ruling_type == 2)
        self.ruling_box_3.setVisible(self.grating_ruling_type == 3)
        self.ruling_box_4.setVisible(self.grating_ruling_type == 4)

        if (self.grating_ruling_type == 0 or self.grating_ruling_type == 1):
            self.ruling_density_label.setText("Ruling Density at origin")
        elif (self.grating_ruling_type == 3):
            self.ruling_density_label.setText("Ruling Density at center")
        elif (self.grating_ruling_type == 4):
            self.ruling_density_label.setText("Polyn. Line Density coeff.: 0th")

        if hasattr(self, "workspace_units_label"):
            self.ruling_density_label.setText(self.ruling_density_label.text() + "  [Lines/" + self.workspace_units_label + "]")

    def set_GratingMountType(self):
        self.grating_mount_box_1.setVisible(self.grating_mount_type == 4)

    def set_RefrectorOpticalConstants(self):
        self.refractor_object_box_1.setVisible(self.optical_constants_refraction_index == 0 or self.optical_constants_refraction_index == 2)
        self.refractor_object_box_2.setVisible(self.optical_constants_refraction_index == 1 or self.optical_constants_refraction_index == 3)
        self.refractor_image_box_1.setVisible(self.optical_constants_refraction_index == 0 or self.optical_constants_refraction_index == 1)
        self.refractor_image_box_2.setVisible(self.optical_constants_refraction_index == 2 or self.optical_constants_refraction_index == 3)

    # TAB 1.3

    def set_Dim_Parameters(self):
        self.dimdet_box.setVisible(self.is_infinite == 1)
        self.dimdet_box_empty.setVisible(self.is_infinite == 0)

    # TAB 2

    def set_SourceMovement(self):
        self.sou_mov_box_1.setVisible(self.source_movement == 1)

    def set_MirrorMovement(self):
        self.mir_mov_box_1.setVisible(self.mirror_movement == 1)

    def set_TypeOfDefect(self):
        self.mod_surf_err_box_1.setVisible(self.ms_type_of_defect != 0)
        self.mod_surf_err_box_2.setVisible(self.ms_type_of_defect == 0)

    def set_ModifiedSurface(self):
        self.surface_error_box.setVisible(self.modified_surface == 1)
        self.faceted_surface_box.setVisible(self.modified_surface == 2)
        self.surface_roughness_box.setVisible(self.modified_surface == 3)
        self.kumakhov_lens_box.setVisible(self.modified_surface == 4)
        self.segmented_mirror_box.setVisible(self.modified_surface == 5)
        if self.modified_surface == 1: self.set_TypeOfDefect()
        if self.modified_surface == 4: self.set_SpecifyRz2()

    def set_SpecifyRz2(self):
        self.kumakhov_lens_box_1.setVisible(self.ms_specify_rz2 == 0)
        self.kumakhov_lens_box_2.setVisible(self.ms_specify_rz2 == 1)


    def set_ApertureShape(self):
        self.box_aperturing_shape_1.setVisible(self.aperture_shape == 2)
        self.box_aperturing_shape_2.setVisible(self.aperture_shape != 2)

    def set_Aperturing(self):
            self.box_aperturing_shape.setVisible(self.aperturing == 1)

            if self.aperturing == 1: self.set_ApertureShape()

    def set_Absorption(self):
        self.box_absorption_1_empty.setVisible(self.absorption == 0)
        self.box_absorption_1.setVisible(self.absorption == 1)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def selectExternalFileWithCoordinate(self):
        self.le_external_file_with_coordinate.setText(oasysgui.selectFileFromDialog(self, self.external_file_with_coordinate, "Open External File With Coordinate"))

    def selectOptConstFileName(self):
        self.le_opt_const_file_name.setText(oasysgui.selectFileFromDialog(self, self.opt_const_file_name, "Open Opt. Const. File"))

    def selectFilePrerefl(self):
        self.le_file_prerefl.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl, "Select File Prerefl", file_extension_filter="Data Files (*.dat)"))

    def selectFilePrereflM(self):
        self.le_file_prerefl_m.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl_m, "Select File Premlayer", file_extension_filter="Data Files (*.dat)"))

    def selectFileCrystalParameters(self):
        self.le_file_crystal_parameters.setText(oasysgui.selectFileFromDialog(self, self.file_crystal_parameters, "Select File With Crystal Parameters"))

    def selectFileDiffractionProfile(self):
        self.le_file_diffraction_profile.setText(oasysgui.selectFileFromDialog(self, self.file_diffraction_profile, "Select File With User Defined Diffraction Profile"))

    def selectDefectFileName(self):
        self.le_ms_defect_file_name.setText(oasysgui.selectFileFromDialog(self, self.ms_defect_file_name, "Select Defect File Name", file_extension_filter="Data Files (*.dat *.sha)"))

    class ShowDefectFileDialog(QDialog):

        def __init__(self, parent=None, filename=""):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Defect File - Surface Error Profile')
            layout = QtGui.QVBoxLayout(self)

            figure = Figure(figsize=(100, 100))
            figure.patch.set_facecolor('white')

            axis = figure.add_subplot(111, projection='3d')

            axis.set_xlabel("X [" + parent.workspace_units_label + "]")
            axis.set_ylabel("Y [" + parent.workspace_units_label + "]")
            axis.set_zlabel("Z [" + parent.workspace_units_label + "]")

            figure_canvas = FigureCanvasQTAgg(figure)
            figure_canvas.setFixedWidth(500)
            figure_canvas.setFixedHeight(450)

            x_coords, y_coords, z_values = ShadowPreProcessor.read_surface_error_file(filename)

            x_to_plot, y_to_plot = numpy.meshgrid(x_coords, y_coords)

            axis.plot_surface(x_to_plot, y_to_plot, z_values.T,
                              rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            figure_canvas.draw()

            bbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)

            bbox.accepted.connect(self.accept)
            layout.addWidget(figure_canvas)
            layout.addWidget(bbox)

    def viewDefectFileName(self):
        try:
            dialog = OpticalElement.ShowDefectFileDialog(parent=self, filename=self.ms_defect_file_name)
            dialog.show()
        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception), QtGui.QMessageBox.Ok)


    def selectFileFacetDescr(self):
        self.le_ms_file_facet_descr.setText(oasysgui.selectFileFromDialog(self, self.ms_file_facet_descr, "Select File with Facet Description"))

    def selectFileSurfRoughness(self):
        self.le_ms_file_surf_roughness.setText(oasysgui.selectFileFromDialog(self, self.ms_file_surf_roughness, "Select Surface Roughness File with PSD fn"))

    def selectFileWithParametersRz(self):
        self.le_ms_file_with_parameters_rz.setText(oasysgui.selectFileFromDialog(self, self.ms_file_with_parameters_rz, "Select File with parameters (r(z))"))

    def selectFileWithParametersRz2(self):
        self.le_ms_file_with_parameters_rz2.setText(oasysgui.selectFileFromDialog(self, self.ms_file_with_parameters_rz2, "Select File with parameters (r(z)^2)"))

    def selectFileOrientations(self):
        self.le_ms_file_orientations.setText(oasysgui.selectFileFromDialog(self, self.ms_file_orientations, "Select File with Orientations"))

    def selectFilePolynomial(self):
        self.le_ms_file_polynomial.setText(oasysgui.selectFileFromDialog(self, self.ms_file_polynomial, "Select File with Polynomial"))

    def selectPrereflObjectFileName(self):
        self.le_file_prerefl_for_object_medium.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl_for_object_medium, "Select File Prerefl for Object Medium"))

    def selectPrereflImageFileName(self):
        self.le_file_prerefl_for_image_medium.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl_for_image_medium, "Select File Prerefl for Image Medium"))

    def calculate_incidence_angle_mrad(self):
        if self.angles_respect_to == 0:
            self.incidence_angle_mrad = round(math.radians(90-self.incidence_angle_deg)*1000, 2)
        else:
            self.incidence_angle_mrad = round(math.radians(self.incidence_angle_deg)*1000, 2)

        if self.graphical_options.is_mirror:
            self.reflection_angle_deg = self.incidence_angle_deg
            self.reflection_angle_mrad = self.incidence_angle_mrad

    def calculate_reflection_angle_mrad(self):
        if self.angles_respect_to == 0:
            self.reflection_angle_mrad = round(math.radians(90-self.reflection_angle_deg)*1000, 2)
        else:
            self.reflection_angle_mrad = round(math.radians(self.reflection_angle_deg)*1000, 2)

    def calculate_incidence_angle_deg(self):
        if self.angles_respect_to == 0:
            self.incidence_angle_deg = round(math.degrees(0.5*math.pi-(self.incidence_angle_mrad/1000)), 3)
        else:
            self.incidence_angle_deg = round(math.degrees(self.incidence_angle_mrad/1000), 3)

        if self.graphical_options.is_mirror:
            self.reflection_angle_deg = self.incidence_angle_deg
            self.reflection_angle_mrad = self.incidence_angle_mrad

    def calculate_reflection_angle_deg(self):
        if self.angles_respect_to == 0:
            self.reflection_angle_deg = round(math.degrees(0.5*math.pi-(self.reflection_angle_mrad/1000)), 3)
        else:
            self.reflection_angle_deg = round(math.degrees(self.reflection_angle_mrad/1000), 3)

    def grab_dcm_value_from_oe(self):
        self.twotheta_bragg = self.incidence_angle_deg
        self.calculate_dcm_distances()

    def set_d1_as_source_plane(self):
        self.source_plane_distance = self.d_1

    def set_d1_as_image_plane(self):
        self.image_plane_distance = self.d_1

    def set_d2_as_source_plane(self):
        self.source_plane_distance = self.d_2

    def set_d2_as_image_plane(self):
        self.image_plane_distance = self.d_2

    def calculate_dcm_distances(self):
        if self.twotheta_bragg >= 45.0:
            twotheta = numpy.radians(2*(90-self.twotheta_bragg))

            self.d_1 = round(self.vertical_quote/numpy.sin(twotheta), 3)
            self.d_2 = round(self.total_distance - self.vertical_quote/numpy.tan(twotheta), 3)
        else:
            self.d_1 = numpy.nan
            self.d_2 = numpy.nan

    def populateFields(self, shadow_oe = ShadowOpticalElement.create_empty_oe()):
        shadow_oe._oe.DUMMY = self.workspace_units_to_cm # Issue #3 : Global User's Unit

        if self.graphical_options.is_screen_slit:
            shadow_oe._oe.T_SOURCE     = self.source_plane_distance
            shadow_oe._oe.T_IMAGE      = self.image_plane_distance
            shadow_oe._oe.T_INCIDENCE  = 0.0
            shadow_oe._oe.T_REFLECTION = 180.0
            shadow_oe._oe.ALPHA        = 0.0

            if self.mirror_movement == 1:
                 shadow_oe._oe.F_MOVE=1
                 shadow_oe._oe.OFFX=self.mm_mirror_offset_x
                 shadow_oe._oe.OFFY=self.mm_mirror_offset_y
                 shadow_oe._oe.OFFZ=self.mm_mirror_offset_z
                 shadow_oe._oe.X_ROT=self.mm_mirror_rotation_x
                 shadow_oe._oe.Y_ROT=self.mm_mirror_rotation_y
                 shadow_oe._oe.Z_ROT=self.mm_mirror_rotation_z

            if self.source_movement == 1:
                 shadow_oe._oe.FSTAT=1
                 shadow_oe._oe.RTHETA=self.sm_angle_of_incidence
                 shadow_oe._oe.RDSOUR=self.sm_distance_from_mirror
                 shadow_oe._oe.ALPHA_S=self.sm_z_rotation
                 shadow_oe._oe.OFF_SOUX=self.sm_offset_x_mirr_ref_frame
                 shadow_oe._oe.OFF_SOUY=self.sm_offset_y_mirr_ref_frame
                 shadow_oe._oe.OFF_SOUZ=self.sm_offset_z_mirr_ref_frame
                 shadow_oe._oe.X_SOUR=self.sm_offset_x_source_ref_frame
                 shadow_oe._oe.Y_SOUR=self.sm_offset_y_source_ref_frame
                 shadow_oe._oe.Z_SOUR=self.sm_offset_z_source_ref_frame
                 shadow_oe._oe.X_SOUR_ROT=self.sm_rotation_around_x
                 shadow_oe._oe.Y_SOUR_ROT=self.sm_rotation_around_y
                 shadow_oe._oe.Z_SOUR_ROT=self.sm_rotation_around_z
        elif self.graphical_options.is_empty:
            shadow_oe._oe.T_SOURCE     = self.source_plane_distance
            shadow_oe._oe.T_IMAGE      = self.image_plane_distance
            shadow_oe._oe.T_INCIDENCE  = self.incidence_angle_deg
            shadow_oe._oe.T_REFLECTION = self.reflection_angle_deg
            shadow_oe._oe.ALPHA        = 90*self.mirror_orientation_angle

            if self.mirror_movement == 1:
                 shadow_oe._oe.F_MOVE=1
                 shadow_oe._oe.OFFX=self.mm_mirror_offset_x
                 shadow_oe._oe.OFFY=self.mm_mirror_offset_y
                 shadow_oe._oe.OFFZ=self.mm_mirror_offset_z
                 shadow_oe._oe.X_ROT=self.mm_mirror_rotation_x
                 shadow_oe._oe.Y_ROT=self.mm_mirror_rotation_y
                 shadow_oe._oe.Z_ROT=self.mm_mirror_rotation_z

            if self.source_movement == 1:
                 shadow_oe._oe.FSTAT=1
                 shadow_oe._oe.RTHETA=self.sm_angle_of_incidence
                 shadow_oe._oe.RDSOUR=self.sm_distance_from_mirror
                 shadow_oe._oe.ALPHA_S=self.sm_z_rotation
                 shadow_oe._oe.OFF_SOUX=self.sm_offset_x_mirr_ref_frame
                 shadow_oe._oe.OFF_SOUY=self.sm_offset_y_mirr_ref_frame
                 shadow_oe._oe.OFF_SOUZ=self.sm_offset_z_mirr_ref_frame
                 shadow_oe._oe.X_SOUR=self.sm_offset_x_source_ref_frame
                 shadow_oe._oe.Y_SOUR=self.sm_offset_y_source_ref_frame
                 shadow_oe._oe.Z_SOUR=self.sm_offset_z_source_ref_frame
                 shadow_oe._oe.X_SOUR_ROT=self.sm_rotation_around_x
                 shadow_oe._oe.Y_SOUR_ROT=self.sm_rotation_around_y
                 shadow_oe._oe.Z_SOUR_ROT=self.sm_rotation_around_z
        else:
            shadow_oe._oe.T_SOURCE     = self.source_plane_distance
            shadow_oe._oe.T_IMAGE      = self.image_plane_distance

            if self.angles_respect_to == 0:
                shadow_oe._oe.T_INCIDENCE  = self.incidence_angle_deg
                shadow_oe._oe.T_REFLECTION = self.reflection_angle_deg
            else:
                shadow_oe._oe.T_INCIDENCE  = 90-self.incidence_angle_deg
                shadow_oe._oe.T_REFLECTION = 90-self.reflection_angle_deg

            shadow_oe._oe.ALPHA        = 90*self.mirror_orientation_angle

            #####################################
            # BASIC SETTING
            #####################################

            if self.graphical_options.is_curved:
                if self.graphical_options.is_toroidal:
                   shadow_oe._oe.FCYL = 0
                elif self.is_cylinder==1:
                   shadow_oe._oe.FCYL = 1
                   shadow_oe._oe.CIL_ANG=90*self.cylinder_orientation
                else:
                   shadow_oe._oe.FCYL = 0

                if self.graphical_options.is_conic_coefficients:
                    conic_coefficients = [self.conic_coefficient_0,
                                          self.conic_coefficient_1,
                                          self.conic_coefficient_2,
                                          self.conic_coefficient_3,
                                          self.conic_coefficient_4,
                                          self.conic_coefficient_5,
                                          self.conic_coefficient_6,
                                          self.conic_coefficient_7,
                                          self.conic_coefficient_8,
                                          self.conic_coefficient_9]

                    shadow_oe._oe.F_EXT = 1
                    shadow_oe._oe.CCC[:] = conic_coefficients[:]
                else:
                    if self.surface_shape_parameters == 0:
                       if (self.is_cylinder==1 and self.cylinder_orientation==1):
                           if self.graphical_options.is_spheric:
                               shadow_oe._oe.F_EXT=1

                               #IMPLEMENTATION OF THE AUTOMATIC CALCULATION OF THE SAGITTAL FOCUSING FOR SPHERICAL CYLINDERS
                               # RADIUS = (2 F1 F2 sin (theta)) /( F1+F2)
                               if self.focii_and_continuation_plane == 0:
                                  self.spherical_radius = ((2*self.source_plane_distance*self.image_plane_distance)/(self.source_plane_distance+self.image_plane_distance))*math.sin(self.reflection_angle_mrad)
                               else:
                                  self.spherical_radius = ((2*self.object_side_focal_distance*self.image_side_focal_distance)/(self.object_side_focal_distance+self.image_side_focal_distance))*math.sin(round(math.radians(90-self.incidence_angle_respect_to_normal), 2))

                               shadow_oe._oe.RMIRR = self.spherical_radius
                       else:
                           shadow_oe._oe.F_EXT = 0

                           if self.focii_and_continuation_plane == 0:
                              shadow_oe._oe.F_DEFAULT=1
                           else:
                              shadow_oe._oe.F_DEFAULT=0
                              shadow_oe._oe.SSOUR = self.object_side_focal_distance
                              shadow_oe._oe.SIMAG = self.image_side_focal_distance
                              shadow_oe._oe.THETA = self.incidence_angle_respect_to_normal

                           if self.graphical_options.is_paraboloid: shadow_oe._oe.F_SIDE=self.focus_location
                    else:
                       shadow_oe._oe.F_EXT=1
                       if self.graphical_options.is_spheric:
                           shadow_oe._oe.RMIRR = self.spherical_radius
                       elif self.graphical_options.is_toroidal:
                           shadow_oe._oe.R_MAJ=self.torus_major_radius
                           shadow_oe._oe.R_MIN=self.torus_minor_radius
                       elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                           shadow_oe._oe.AXMAJ=self.ellipse_hyperbola_semi_major_axis
                           shadow_oe._oe.AXMIN=self.ellipse_hyperbola_semi_minor_axis
                           shadow_oe._oe.ELL_THE=self.angle_of_majax_and_pole
                       elif self.graphical_options.is_paraboloid:
                           shadow_oe._oe.PARAM=self.paraboloid_parameter

                    if self.graphical_options.is_toroidal:
                        shadow_oe._oe.F_TORUS=self.toroidal_mirror_pole_location
                    else:
                        if self.surface_curvature == 0:
                           shadow_oe._oe.F_CONVEX=0
                        else:
                           shadow_oe._oe.F_CONVEX=1
            else:
               shadow_oe._oe.FCYL = 0

            if self.graphical_options.is_mirror:
                if self.reflectivity_type == 0:
                   shadow_oe._oe.F_REFLEC = 0
                elif self.reflectivity_type == 1:
                    if self.source_of_reflectivity == 0:
                        shadow_oe._oe.F_REFLEC = 1
                        shadow_oe._oe.F_REFL = 0
                        shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_prerefl), 'utf-8')
                        shadow_oe._oe.ALFA = 0.0
                        shadow_oe._oe.GAMMA = 0.0
                        shadow_oe._oe.F_THICK = 0
                    elif self.source_of_reflectivity == 1:
                        shadow_oe._oe.F_REFLEC = 1
                        shadow_oe._oe.F_REFL = 1
                        shadow_oe._oe.FILE_REFL = 'GAAS.SHA'
                        shadow_oe._oe.ALFA = self.alpha
                        shadow_oe._oe.GAMMA = self.gamma
                        shadow_oe._oe.F_THICK = 0
                    elif self.source_of_reflectivity == 2:
                        shadow_oe._oe.F_REFLEC = 1
                        shadow_oe._oe.F_REFL = 2
                        shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_prerefl_m), 'utf-8')
                        shadow_oe._oe.ALFA = 0.0
                        shadow_oe._oe.GAMMA = 0.0
                        shadow_oe._oe.F_THICK = self.m_layer_tickness
                elif self.reflectivity_type == 2:
                    if self.source_of_reflectivity == 0:
                        shadow_oe._oe.F_REFLEC = 2
                        shadow_oe._oe.F_REFL = 0
                        shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_prerefl), 'utf-8')
                        shadow_oe._oe.ALFA = 0.0
                        shadow_oe._oe.GAMMA = 0.0
                        shadow_oe._oe.F_THICK = 0
                    elif self.source_of_reflectivity == 1:
                        shadow_oe._oe.F_REFLEC = 2
                        shadow_oe._oe.F_REFL = 1
                        shadow_oe._oe.FILE_REFL = 'GAAS.SHA'
                        shadow_oe._oe.ALFA = self.alpha
                        shadow_oe._oe.GAMMA = self.gamma
                        shadow_oe._oe.F_THICK = 0
                    elif self.source_of_reflectivity == 2:
                        shadow_oe._oe.F_REFLEC = 2
                        shadow_oe._oe.F_REFL = 2
                        shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_prerefl_m), 'utf-8')
                        shadow_oe._oe.ALFA = 0.0
                        shadow_oe._oe.GAMMA = 0.0
                        shadow_oe._oe.F_THICK = self.m_layer_tickness
            elif self.graphical_options.is_crystal:
                shadow_oe._oe.F_REFLEC = 0

                if self.diffraction_calculation == 1:
                    shadow_oe._oe.F_CRYSTAL = 0  # user defined profile -> simulated as mirror with no reflectivity
                else:
                    shadow_oe._oe.F_CRYSTAL = 1
                    shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_crystal_parameters), 'utf-8')
                    shadow_oe._oe.F_REFLECT = 0
                    shadow_oe._oe.F_BRAGG_A = 0
                    shadow_oe._oe.A_BRAGG = 0.0
                    shadow_oe._oe.F_REFRACT = 0

                    shadow_oe._oe.F_REFRAC = self.diffraction_geometry

                    if self.crystal_auto_setting == 0:
                        shadow_oe._oe.F_CENTRAL = 0
                    else:
                        shadow_oe._oe.F_CENTRAL = 1
                        shadow_oe._oe.F_PHOT_CENT = self.units_in_use
                        shadow_oe._oe.PHOT_CENT = self.photon_energy
                        shadow_oe._oe.R_LAMBDA = self.photon_wavelength

                    if self.mosaic_crystal == 1:
                        shadow_oe._oe.F_MOSAIC = 1
                        shadow_oe._oe.MOSAIC_SEED = self.seed_for_mosaic
                        shadow_oe._oe.SPREAD_MOS = self.angle_spread_FWHM
                        shadow_oe._oe.THICKNESS = self.thickness
                    else:
                        if self.asymmetric_cut == 1:
                            shadow_oe._oe.F_BRAGG_A = 1
                            shadow_oe._oe.A_BRAGG = self.planes_angle
                            shadow_oe._oe.ORDER = self.below_onto_bragg_planes
                            shadow_oe._oe.THICKNESS = self.thickness
                        if self.johansson_geometry == 1:
                            shadow_oe._oe.F_JOHANSSON = 1
                            shadow_oe._oe.F_EXT = 1
                            shadow_oe._oe.R_JOHANSSON = self.johansson_radius
            elif self.graphical_options.is_grating:
                shadow_oe._oe.F_REFLEC = 0

                if self.grating_ruling_type == 0 or self.grating_ruling_type == 1:
                    shadow_oe._oe.F_GRATING = 1
                    shadow_oe._oe.F_RULING = self.grating_ruling_type
                    shadow_oe._oe.RULING = self.grating_ruling_density
                elif self.grating_ruling_type == 2:
                    shadow_oe._oe.F_GRATING = 1
                    shadow_oe._oe.F_RULING = 2
                    shadow_oe._oe.HOLO_R1  = self.grating_holo_left_distance
                    shadow_oe._oe.HOLO_R2  = self.grating_holo_right_distance
                    shadow_oe._oe.HOLO_DEL = self.grating_holo_left_incidence_angle
                    shadow_oe._oe.HOLO_GAM = self.grating_holo_right_incidence_angle
                    shadow_oe._oe.HOLO_W   = self.grating_holo_recording_wavelength
                    shadow_oe._oe.HOLO_RT1 = self.grating_holo_left_azimuth_from_y
                    shadow_oe._oe.HOLO_RT2 = self.grating_holo_right_azimuth_from_y
                    shadow_oe._oe.F_PW = self.grating_holo_pattern_type
                    shadow_oe._oe.F_PW_C = self.grating_holo_cylindrical_source
                    shadow_oe._oe.F_VIRTUAL = self.grating_holo_source_type
                elif self.grating_ruling_type == 3:
                    shadow_oe._oe.F_GRATING = 1
                    shadow_oe._oe.F_RULING = 3
                    shadow_oe._oe.AZIM_FAN = self.grating_groove_pole_azimuth_from_y
                    shadow_oe._oe.DIST_FAN = self.grating_groove_pole_distance
                    shadow_oe._oe.COMA_FAC = self.grating_coma_correction_factor
                elif self.grating_ruling_type == 4:
                    shadow_oe._oe.F_GRATING = 1
                    shadow_oe._oe.F_RULING = 5
                    shadow_oe._oe.F_RUL_ABS = self.grating_poly_signed_absolute
                    shadow_oe._oe.RULING = self.grating_ruling_density
                    shadow_oe._oe.RUL_A1 = self.grating_poly_coeff_1
                    shadow_oe._oe.RUL_A2 = self.grating_poly_coeff_2
                    shadow_oe._oe.RUL_A3 = self.grating_poly_coeff_3
                    shadow_oe._oe.RUL_A4 = self.grating_poly_coeff_4
                if self.grating_auto_setting == 0:
                    shadow_oe._oe.F_CENTRAL=0
                else:
                    shadow_oe._oe.F_CENTRAL = 1
                    shadow_oe._oe.F_PHOT_CENT = self.grating_units_in_use
                    shadow_oe._oe.PHOT_CENT = self.grating_photon_energy
                    shadow_oe._oe.R_LAMBDA = self.grating_photon_wavelength
                    shadow_oe._oe.F_MONO = self.grating_mount_type

                    if self.grating_mount_type != 4:
                        shadow_oe._oe.F_HUNT = 1
                        shadow_oe._oe.HUNT_H = 0.0
                        shadow_oe._oe.HUNT_L = 0.0
                        shadow_oe._oe.BLAZE = 0.0
                    else:
                        shadow_oe._oe.F_HUNT = self.grating_hunter_grating_selected+1
                        shadow_oe._oe.HUNT_H = self.grating_hunter_distance_between_beams
                        shadow_oe._oe.HUNT_L = self.grating_hunter_monochromator_length
                        shadow_oe._oe.BLAZE = self.grating_hunter_blaze_angle
            elif self.graphical_options.is_refractor:
                shadow_oe._oe.F_R_IND =  self.optical_constants_refraction_index

                shadow_oe._oe.FZP = self.fresnel_zone_plate

                if self.fresnel_zone_plate == 1:
                    shadow_oe._oe.F_GRATING = 1

                if self.optical_constants_refraction_index == 0:
                    shadow_oe._oe.R_IND_OBJ = self.refractive_index_in_object_medium
                    shadow_oe._oe.R_ATTENUATION_OBJ = self.attenuation_in_object_medium
                    shadow_oe._oe.R_IND_IMA =self.refractive_index_in_image_medium
                    shadow_oe._oe.R_ATTENUATION_IMA = self.attenuation_in_image_medium
                elif self.optical_constants_refraction_index == 1:
                    shadow_oe._oe.FILE_R_IND_OBJ = bytes(congruence.checkFileName(self.file_prerefl_for_object_medium), 'utf-8')
                    shadow_oe._oe.R_IND_IMA = self.refractive_index_in_image_medium
                    shadow_oe._oe.R_ATTENUATION_IMA = self.attenuation_in_image_medium
                elif self.optical_constants_refraction_index == 2:
                    shadow_oe._oe.R_IND_OBJ = self.refractive_index_in_object_medium
                    shadow_oe._oe.R_ATTENUATION_OBJ = self.attenuation_in_object_medium
                    shadow_oe._oe.FILE_R_IND_IMA = bytes(congruence.checkFileName(self.file_prerefl_for_image_medium), 'utf-8')
                elif self.optical_constants_refraction_index == 3:
                    shadow_oe._oe.FILE_R_IND_OBJ = bytes(congruence.checkFileName(self.file_prerefl_for_object_medium), 'utf-8')
                    shadow_oe._oe.FILE_R_IND_IMA = bytes(congruence.checkFileName(self.file_prerefl_for_image_medium), 'utf-8')

            if self.is_infinite == 0:
                shadow_oe._oe.FHIT_C = 0
            else:
                shadow_oe._oe.FHIT_C = 1
                shadow_oe._oe.FSHAPE = (self.mirror_shape+1)
                shadow_oe._oe.RLEN1  = self.dim_y_plus
                shadow_oe._oe.RLEN2  = self.dim_y_minus
                shadow_oe._oe.RWIDX1 = self.dim_x_plus
                shadow_oe._oe.RWIDX2 = self.dim_x_minus

            #####################################
            # ADVANCED SETTING
            #####################################

            if self.modified_surface == 1:
                 if self.ms_type_of_defect == 0:
                     shadow_oe._oe.F_RIPPLE = 1
                     shadow_oe._oe.F_G_S = 0
                     shadow_oe._oe.X_RIP_AMP = self.ms_ripple_ampli_x
                     shadow_oe._oe.X_RIP_WAV = self.ms_ripple_wavel_x
                     shadow_oe._oe.X_PHASE   = self.ms_ripple_phase_x
                     shadow_oe._oe.Y_RIP_AMP = self.ms_ripple_ampli_y
                     shadow_oe._oe.Y_RIP_WAV = self.ms_ripple_wavel_y
                     shadow_oe._oe.Y_PHASE   = self.ms_ripple_phase_y
                     shadow_oe._oe.FILE_RIP  = b''
                 else:
                     shadow_oe._oe.F_RIPPLE = 1
                     shadow_oe._oe.F_G_S = self.ms_type_of_defect
                     shadow_oe._oe.X_RIP_AMP = 0.0
                     shadow_oe._oe.X_RIP_WAV = 0.0
                     shadow_oe._oe.X_PHASE   = 0.0
                     shadow_oe._oe.Y_RIP_AMP = 0.0
                     shadow_oe._oe.Y_RIP_WAV = 0.0
                     shadow_oe._oe.Y_PHASE   = 0.0
                     shadow_oe._oe.FILE_RIP  = bytes(congruence.checkFileName(self.ms_defect_file_name), 'utf-8')

            elif self.modified_surface == 2:
                shadow_oe._oe.F_FACET = 1
                shadow_oe._oe.FILE_FAC=bytes(congruence.checkFileName(self.ms_file_facet_descr), 'utf-8')
                shadow_oe._oe.F_FAC_LATT=self.ms_lattice_type
                shadow_oe._oe.F_FAC_ORIENT=self.ms_orientation
                shadow_oe._oe.F_POLSEL=self.ms_lattice_type+1
                shadow_oe._oe.RFAC_LENX=self.ms_facet_width_x
                shadow_oe._oe.RFAC_PHAX=self.ms_facet_phase_x
                shadow_oe._oe.RFAC_DELX1=self.ms_dead_width_x_minus
                shadow_oe._oe.RFAC_DELX2=self.ms_dead_width_x_plus
                shadow_oe._oe.RFAC_LENY=self.ms_facet_width_y
                shadow_oe._oe.RFAC_PHAY=self.ms_facet_phase_y
                shadow_oe._oe.RFAC_DELY1=self.ms_dead_width_y_minus
                shadow_oe._oe.RFAC_DELY2=self.ms_dead_width_y_plus
            elif self.modified_surface == 3:
                shadow_oe._oe.F_ROUGHNESS = 1
                shadow_oe._oe.FILE_ROUGH=bytes(congruence.checkFileName(self.ms_file_surf_roughness), 'utf-8')
                shadow_oe._oe.ROUGH_X=self.ms_roughness_rms_x
                shadow_oe._oe.ROUGH_Y=self.ms_roughness_rms_y
            elif self.modified_surface == 4:
                shadow_oe._oe.F_KOMA = 1
                shadow_oe._oe.F_KOMA_CA=self.ms_specify_rz2
                shadow_oe._oe.FILE_KOMA=bytes(congruence.checkFileName(self.ms_file_with_parameters_rz), 'utf-8')
                shadow_oe._oe.FILE_KOMA_CA=bytes(congruence.checkFileName(self.ms_file_with_parameters_rz2), 'utf-8')
                shadow_oe._oe.F_KOMA_BOUNCE=self.ms_save_intercept_bounces
            elif self.modified_surface == 5:
                shadow_oe._oe.F_SEGMENT = 1
                shadow_oe._oe.ISEG_XNUM=self.ms_number_of_segments_x
                shadow_oe._oe.ISEG_YNUM=self.ms_number_of_segments_y
                shadow_oe._oe.SEG_LENX=self.ms_length_of_segments_x
                shadow_oe._oe.SEG_LENY=self.ms_length_of_segments_y
                shadow_oe._oe.FILE_SEGMENT=bytes(congruence.checkFileName(self.ms_file_orientations), 'utf-8')
                shadow_oe._oe.FILE_SEGP=bytes(congruence.checkFileName(self.ms_file_polynomial), 'utf-8')

            if self.mirror_movement == 1:
                 shadow_oe._oe.F_MOVE=1
                 shadow_oe._oe.OFFX=self.mm_mirror_offset_x
                 shadow_oe._oe.OFFY=self.mm_mirror_offset_y
                 shadow_oe._oe.OFFZ=self.mm_mirror_offset_z
                 shadow_oe._oe.X_ROT=self.mm_mirror_rotation_x
                 shadow_oe._oe.Y_ROT=self.mm_mirror_rotation_y
                 shadow_oe._oe.Z_ROT=self.mm_mirror_rotation_z

            if self.source_movement == 1:
                 shadow_oe._oe.FSTAT=1
                 shadow_oe._oe.RTHETA=self.sm_angle_of_incidence
                 shadow_oe._oe.RDSOUR=self.sm_distance_from_mirror
                 shadow_oe._oe.ALPHA_S=self.sm_z_rotation
                 shadow_oe._oe.OFF_SOUX=self.sm_offset_x_mirr_ref_frame
                 shadow_oe._oe.OFF_SOUY=self.sm_offset_y_mirr_ref_frame
                 shadow_oe._oe.OFF_SOUZ=self.sm_offset_z_mirr_ref_frame
                 shadow_oe._oe.X_SOUR=self.sm_offset_x_source_ref_frame
                 shadow_oe._oe.Y_SOUR=self.sm_offset_y_source_ref_frame
                 shadow_oe._oe.Z_SOUR=self.sm_offset_z_source_ref_frame
                 shadow_oe._oe.X_SOUR_ROT=self.sm_rotation_around_x
                 shadow_oe._oe.Y_SOUR_ROT=self.sm_rotation_around_y
                 shadow_oe._oe.Z_SOUR_ROT=self.sm_rotation_around_z

            shadow_oe._oe.FWRITE=self.file_to_write_out

            if self.graphical_options.is_crystal and self.diffraction_calculation == 1:
                shadow_oe._oe.F_ANGLE = 1
            else:
                shadow_oe._oe.F_ANGLE = self.write_out_inc_ref_angles

    def doSpecificSetting(self, shadow_oe):
        pass

    def checkFields(self):
        if self.graphical_options.is_screen_slit:
            self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

            if self.source_movement == 1:
                self.sm_distance_from_mirror = congruence.checkNumber(self.sm_distance_from_mirror, "Source Movement: Distance from O.E.")
        elif self.graphical_options.is_empty:
            self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

            if self.source_movement == 1:
                self.sm_distance_from_mirror = congruence.checkPositiveNumber(self.sm_distance_from_mirror, "Source Movement: Distance from O.E.")
        else:
            self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

            if self.graphical_options.is_curved:
                if self.surface_shape_parameters == 0:
                    if (self.is_cylinder==1 and self.cylinder_orientation==1):
                       if not self.graphical_options.is_spheric:
                           raise Exception("Automatic calculation of the sagittal focus supported only for Spheric O.E.")
                    else:
                       if not self.focii_and_continuation_plane == 0:
                            self.object_side_focal_distance = congruence.checkNumber(self.object_side_focal_distance, "Object side focal distance")
                            self.image_side_focal_distance = congruence.checkNumber(self.image_side_focal_distance, "Image side focal distance")

                       if self.graphical_options.is_paraboloid:
                            self.focus_location = congruence.checkNumber(self.focus_location, "Focus location")
                else:
                   if self.graphical_options.is_spheric:
                       self.spherical_radius = congruence.checkPositiveNumber(self.spherical_radius, "Spherical radius")
                   elif self.graphical_options.is_toroidal:
                       self.torus_major_radius = congruence.checkPositiveNumber(self.torus_major_radius, "Torus major radius")
                       self.torus_minor_radius = congruence.checkPositiveNumber(self.torus_minor_radius, "Torus minor radius")
                   elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                       self.ellipse_hyperbola_semi_major_axis = congruence.checkPositiveNumber(self.ellipse_hyperbola_semi_major_axis, "Semi major axis")
                       self.ellipse_hyperbola_semi_minor_axis = congruence.checkPositiveNumber(self.ellipse_hyperbola_semi_minor_axis, "Semi minor axis")
                       self.angle_of_majax_and_pole = congruence.checkPositiveNumber(self.angle_of_majax_and_pole, "Angle of MajAx and Pole")
                   elif self.graphical_options.is_paraboloid:
                       self.paraboloid_parameter = congruence.checkNumber(self.paraboloid_parameter, "Paraboloid parameter")

                if self.graphical_options.is_toroidal:
                    self.toroidal_mirror_pole_location = congruence.checkPositiveNumber(self.toroidal_mirror_pole_location, "Toroidal mirror pole location")

            if self.graphical_options.is_mirror:
                if not self.reflectivity_type == 0:
                    if self.source_of_reflectivity == 0:
                        congruence.checkFile(self.file_prerefl)
                    elif self.source_of_reflectivity == 2:
                        congruence.checkFile(self.file_prerefl_m)
            elif self.graphical_options.is_crystal:
                if self.diffraction_calculation == 1:
                    congruence.checkFile(self.file_diffraction_profile)
                else:
                    congruence.checkFile(self.file_crystal_parameters)

                    if not self.crystal_auto_setting == 0:
                        if self.units_in_use == 0:
                            self.photon_energy = congruence.checkPositiveNumber(self.photon_energy, "Photon Energy")
                        elif self.units_in_use == 1:
                            self.photon_wavelength = congruence.checkPositiveNumber(self.photon_wavelength,
                                                                                   "Photon Wavelength")

                    if self.mosaic_crystal == 1:
                        self.seed_for_mosaic = congruence.checkPositiveNumber(self.seed_for_mosaic,
                                                                             "Crystal: Seed for mosaic")
                        self.angle_spread_FWHM = congruence.checkPositiveNumber(self.angle_spread_FWHM,
                                                                               "Crystal: Angle spread FWHM")
                        self.thickness = congruence.checkPositiveNumber(self.thickness, "Crystal: thickness")
                    else:
                        if self.asymmetric_cut == 1:
                            self.thickness = congruence.checkPositiveNumber(self.thickness, "Crystal: thickness")
                        if self.johansson_geometry == 1:
                            self.johansson_radius = congruence.checkPositiveNumber(self.johansson_radius,
                                                                                  "Crystal: Johansson radius")
            elif self.graphical_options.is_grating:
                if not self.grating_auto_setting == 0:
                    if self.grating_units_in_use == 0:
                        self.grating_photon_energy = congruence.checkPositiveNumber(self.grating_photon_energy, "Photon Energy")
                    elif self.grating_units_in_use == 1:
                        self.grating_photon_wavelength = congruence.checkPositiveNumber(self.grating_photon_wavelength, "Photon Wavelength")

                    if self.grating_mount_type == 4:
                        self.grating_hunter_monochromator_length = congruence.checkPositiveNumber(self.grating_hunter_monochromator_length, "Monochromator length")
                        self.grating_hunter_distance_between_beams = congruence.checkPositiveNumber(self.grating_hunter_distance_between_beams, "Distance between beams")

                if self.grating_ruling_type == 0 or self.grating_ruling_type == 1 or self.grating_ruling_type == 3:
                    self.grating_ruling_density = congruence.checkPositiveNumber(self.grating_ruling_density, "Ruling Density")
                elif self.grating_ruling_type == 2:
                    self.grating_holo_recording_wavelength = congruence.checkPositiveNumber(self.grating_holo_recording_wavelength, "Recording Wavelength")
                elif self.grating_ruling_type == 4:
                    self.grating_ruling_density = congruence.checkPositiveNumber(self.grating_ruling_density, "Polynomial Line Density coeff.: 0th")
            elif self.graphical_options.is_refractor:
                if self.optical_constants_refraction_index == 0:
                    self.refractive_index_in_object_medium = congruence.checkPositiveNumber(self.refractive_index_in_object_medium, "Refractive Index in Object Medium")
                    self.attenuation_in_object_medium = congruence.checkNumber(self.attenuation_in_object_medium, "Refractive Index in Object Medium")
                    self.refractive_index_in_image_medium = congruence.checkPositiveNumber(self.refractive_index_in_image_medium, "Refractive Index in Image Medium")
                    self.attenuation_in_image_medium = congruence.checkNumber(self.attenuation_in_image_medium, "Refractive Index in Image Medium")
                elif self.optical_constants_refraction_index == 1:
                    congruence.checkFile(self.file_prerefl_for_object_medium)
                    self.refractive_index_in_image_medium = congruence.checkPositiveNumber(self.refractive_index_in_image_medium, "Refractive Index in Image Medium")
                    self.attenuation_in_image_medium = congruence.checkNumber(self.attenuation_in_image_medium, "Refractive Index in Image Medium")
                elif self.optical_constants_refraction_index == 2:
                    self.refractive_index_in_object_medium = congruence.checkPositiveNumber(self.refractive_index_in_object_medium, "Refractive Index in Object Medium")
                    self.attenuation_in_object_medium = congruence.checkNumber(self.attenuation_in_object_medium, "Refractive Index in Object Medium")
                    congruence.checkFile(self.file_prerefl_for_image_medium)
                elif self.optical_constants_refraction_index == 3:
                    congruence.checkFile(self.file_prerefl_for_object_medium)
                    congruence.checkFile(self.file_prerefl_for_image_medium)

            if not self.is_infinite == 0:
               self.dim_y_plus = congruence.checkPositiveNumber(self.dim_y_plus, "Dimensions: y plus")
               self.dim_y_minus = congruence.checkPositiveNumber(self.dim_y_minus, "Dimensions: y minus")
               self.dim_x_plus = congruence.checkPositiveNumber(self.dim_x_plus, "Dimensions: x plus")
               self.dim_x_minus = congruence.checkPositiveNumber(self.dim_x_minus, "Dimensions: x minus")


            #####################################
            # ADVANCED SETTING
            #####################################

            if self.modified_surface == 1:
                 if self.ms_type_of_defect == 0:
                     self.ms_ripple_ampli_x = congruence.checkPositiveNumber(self.ms_ripple_ampli_x , "Modified Surface: Ripple Amplitude x")
                     self.ms_ripple_wavel_x = congruence.checkPositiveNumber(self.ms_ripple_wavel_x , "Modified Surface: Ripple Wavelength x")
                     self.ms_ripple_ampli_y = congruence.checkPositiveNumber(self.ms_ripple_ampli_y , "Modified Surface: Ripple Amplitude y")
                     self.ms_ripple_wavel_y = congruence.checkPositiveNumber(self.ms_ripple_wavel_y , "Modified Surface: Ripple Wavelength y")
                 else:
                     congruence.checkFile(self.ms_defect_file_name)
            elif self.modified_surface == 2:
                congruence.checkFile(self.ms_file_facet_descr)
                self.ms_facet_width_x = congruence.checkPositiveNumber(self.ms_facet_width_x, "Modified Surface: Facet width x")
                self.ms_facet_phase_x = congruence.checkPositiveAngle(self.ms_facet_phase_x, "Modified Surface: Facet phase x")
                self.ms_dead_width_x_minus = congruence.checkPositiveNumber(self.ms_dead_width_x_minus, "Modified Surface: Dead width x minus")
                self.ms_dead_width_x_plus = congruence.checkPositiveNumber(self.ms_dead_width_x_plus, "Modified Surface: Dead width x plus")
                self.ms_facet_width_y = congruence.checkPositiveNumber(self.ms_facet_width_y, "Modified Surface: Facet width y")
                self.ms_facet_phase_y = congruence.checkPositiveAngle(self.ms_facet_phase_y, "Modified Surface: Facet phase y")
                self.ms_dead_width_y_minus = congruence.checkPositiveNumber(self.ms_dead_width_y_minus, "Modified Surface: Dead width y minus")
                self.ms_dead_width_y_plus = congruence.checkPositiveNumber(self.ms_dead_width_y_plus, "Modified Surface: Dead width y plus")
            elif self.modified_surface == 3:
                congruence.checkFile(self.ms_file_surf_roughness)
                self.ms_roughness_rms_x = congruence.checkPositiveNumber(self.ms_roughness_rms_x, "Modified Surface: Roughness rms x")
                self.ms_roughness_rms_y = congruence.checkPositiveNumber(self.ms_roughness_rms_y, "Modified Surface: Roughness rms y")
            elif self.modified_surface == 4:
                if self.ms_specify_rz2==0: congruence.checkFile(self.ms_file_with_parameters_rz)
                if self.ms_specify_rz2==0: congruence.checkFile(self.ms_file_with_parameters_rz2)
            elif self.modified_surface == 5:
                congruence.checkFile(self.ms_file_orientations)
                congruence.checkFile(self.ms_file_polynomial)
                self.ms_number_of_segments_x = congruence.checkPositiveNumber(self.ms_number_of_segments_x, "Modified Surface: Number of segments x")
                self.ms_number_of_segments_y = congruence.checkPositiveNumber(self.ms_number_of_segments_y, "Modified Surface: Number of segments y")
                self.ms_length_of_segments_x = congruence.checkPositiveNumber(self.ms_length_of_segments_x, "Modified Surface: Length of segments x")
                self.ms_length_of_segments_y = congruence.checkPositiveNumber(self.ms_length_of_segments_y, "Modified Surface: Length of segments y")

            if self.source_movement == 1:
                if self.sm_distance_from_mirror < 0: raise Exception("Source Movement: Distance from O.E.")

    def writeCalculatedFields(self, shadow_oe):
        if self.surface_shape_parameters == 0:
            if self.graphical_options.is_spheric:
                self.spherical_radius = shadow_oe._oe.RMIRR
            elif self.graphical_options.is_toroidal:
                self.torus_major_radius = shadow_oe._oe.R_MAJ
                self.torus_minor_radius = shadow_oe._oe.R_MIN
            elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                self.ellipse_hyperbola_semi_major_axis = shadow_oe._oe.AXMAJ
                self.ellipse_hyperbola_semi_minor_axis = shadow_oe._oe.AXMIN
                self.angle_of_majax_and_pole = shadow_oe._oe.ELL_THE
            elif self.graphical_options.is_paraboloid:
                self.paraboloid_parameter = shadow_oe._oe.PARAM

        if self.diffraction_calculation == 0 and self.crystal_auto_setting == 1:
            self.incidence_angle_mrad = round((math.pi*0.5-shadow_oe._oe.T_INCIDENCE)*1000, 2)
            self.reflection_angle_mrad = round((math.pi*0.5-shadow_oe._oe.T_REFLECTION)*1000, 2)
            self.calculate_incidence_angle_deg()
            self.calculate_reflection_angle_deg()

    def completeOperations(self, shadow_oe=None):
        self.setStatusMessage("Running SHADOW")

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        if self.trace_shadow:
            grabber = TTYGrabber()
            grabber.start()

        self.progressBarSet(50)

        ###########################################
        # TODO: TO BE ADDED JUST IN CASE OF BROKEN
        #       ENVIRONMENT: MUST BE FOUND A PROPER WAY
        #       TO TEST SHADOW
        self.fixWeirdShadowBug()
        ###########################################

        write_start_file, write_end_file = self.get_write_file_options()

        beam_out = ShadowBeam.traceFromOE(self.input_beam,
                                          shadow_oe,
                                          write_start_file=write_start_file,
                                          write_end_file=write_end_file)

        if self.graphical_options.is_crystal and self.diffraction_calculation == 1:
            beam_out = self.apply_user_diffraction_profile(beam_out)

        self.writeCalculatedFields(shadow_oe)

        if self.trace_shadow:
            grabber.stop()

            for row in grabber.ttyData:
               self.writeStdOut(row)

        self.setStatusMessage("Plotting Results")

        self.plot_results(beam_out)

        self.setStatusMessage("")

        self.send("Beam", beam_out)
        self.send("Trigger", ShadowTriggerIn(new_beam=True))

    def get_write_file_options(self):
        write_start_file = 0
        write_end_file = 0

        if self.file_to_write_out == 4:
            write_start_file = 1
            write_end_file = 1

        return write_start_file, write_end_file

    def apply_user_diffraction_profile(self, input_beam):
        str_oe_number = str(input_beam._oe_number)

        if (input_beam._oe_number < 10): str_oe_number = "0" + str_oe_number

        values = numpy.loadtxt(os.path.abspath(os.path.curdir + "/angle." + str_oe_number))

        beam_incident_angles = values[:, 1]
        beam_flags = values[:, 3]
        bragg_angles = []

        for index in range(0, len(input_beam._beam.rays)):
            wavelength = ShadowPhysics.getWavelengthfromShadowK(input_beam._beam.rays[index, 10])
            bragg_angles.append(90 - math.degrees(ShadowPhysics.calculateBraggAngle(wavelength, 1, 1, 1, 5.43123)))
            if beam_flags[index] == -55000.0: input_beam._beam.rays[index, 9] = 1

        delta_thetas = beam_incident_angles - bragg_angles

        if self.file_diffraction_profile.startswith('/'):
            values = numpy.loadtxt(os.path.abspath(self.file_diffraction_profile))
        else:
            values = numpy.loadtxt(os.path.abspath(os.path.curdir + "/" + self.file_diffraction_profile))

        crystal_incident_angles = values[:, 0]
        crystal_reflectivities = values[:, 1]

        interpolated_weight = []

        for index in range(0, len(delta_thetas)):
            values_up = crystal_incident_angles[numpy.where(crystal_incident_angles >= delta_thetas[index])]
            values_down = crystal_incident_angles[numpy.where(crystal_incident_angles < delta_thetas[index])]

            if len(values_up) == 0:
                refl_up = []
                refl_up.append(crystal_reflectivities[0])
            else:
                refl_up = crystal_reflectivities[numpy.where(crystal_incident_angles == values_up[-1])]

            if len(values_down) == 0:
                refl_down = []
                refl_down.append(crystal_reflectivities[-1])
            else:
                refl_down = crystal_reflectivities[numpy.where(crystal_incident_angles == values_down[0])]

            interpolated_weight.append(numpy.sqrt((refl_up[0] + refl_down[0]) / 2))

        output_beam = input_beam.duplicate()

        for index in range(0, len(output_beam._beam.rays)):
            output_beam._beam.rays[index, 6] = output_beam._beam.rays[index, 6] * interpolated_weight[index]
            output_beam._beam.rays[index, 7] = output_beam._beam.rays[index, 7] * interpolated_weight[index]
            output_beam._beam.rays[index, 8] = output_beam._beam.rays[index, 8] * interpolated_weight[index]
            output_beam._beam.rays[index, 15] = output_beam._beam.rays[index, 15] * interpolated_weight[index]
            output_beam._beam.rays[index, 16] = output_beam._beam.rays[index, 16] * interpolated_weight[index]
            output_beam._beam.rays[index, 17] = output_beam._beam.rays[index, 17] * interpolated_weight[index]

        return output_beam

    def traceOpticalElement(self):
        try:
            #self.error(self.error_id)
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    self.checkFields()

                    shadow_oe = self.instantiateShadowOE()

                    self.populateFields(shadow_oe)
                    self.doSpecificSetting(shadow_oe)

                    self.progressBarSet(10)

                    self.completeOperations(shadow_oe)
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception), QtGui.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

            raise exception
        self.progressBarFinished()

    def setBeam(self, beam):
        self.onReceivingInput()

        if ShadowCongruence.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.traceOpticalElement()

    def setPreProcessorData(self, data):
        if data is not None:
            if data.bragg_data_file != ShadowPreProcessorData.NONE:
                if self.graphical_options.is_crystal:
                    self.file_crystal_parameters=data.bragg_data_file
                    self.diffraction_calculation = 0

                    self.set_DiffractionCalculation()
                else:
                    QtGui.QMessageBox.warning(self, "Warning",
                              "This O.E. is not a crystal: bragg parameter will be ignored",
                              QtGui.QMessageBox.Ok)

            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                if self.graphical_options.is_mirror:
                    self.file_prerefl=data.prerefl_data_file
                    self.reflectivity_type = 1
                    self.source_of_reflectivity = 0

                    self.set_Refl_Parameters()
                elif self.graphical_options.is_screen_slit:
                    self.absorption = 1
                    self.opt_const_file_name = data.prerefl_data_file

                    self.set_Absorption()
                else:
                    QtGui.QMessageBox.warning(self, "Warning",
                              "This O.E. is not a mirror or screen/slit: prerefl parameter will be ignored",
                              QtGui.QMessageBox.Ok)

            if data.m_layer_data_file_dat != ShadowPreProcessorData.NONE:
                if self.graphical_options.is_mirror:
                    self.file_prerefl_m=data.m_layer_data_file_dat

                    self.reflectivity_type = 1
                    self.source_of_reflectivity = 2

                    self.set_Refl_Parameters()
                else:
                    QtGui.QMessageBox.warning(self, "Warning",
                              "This O.E. is not a mirror: prerefl_m parameter will be ignored",
                              QtGui.QMessageBox.Ok)

            if data.error_profile_data_file != ShadowPreProcessorData.NONE:
                if self.graphical_options.is_mirror:
                    self.ms_defect_file_name = data.error_profile_data_file
                    self.modified_surface = 1
                    self.ms_type_of_defect = 2

                    self.set_ModifiedSurface()

                    if self.is_infinite == 1:
                        changed = False

                        if self.dim_x_plus > data.error_profile_x_dim/2 or \
                           self.dim_x_minus > data.error_profile_x_dim/2 or \
                           self.dim_y_plus > data.error_profile_y_dim/2 or \
                           self.dim_y_minus > data.error_profile_y_dim/2:
                            changed = True

                        if changed:
                            if QtGui.QMessageBox.information(self, "Confirm Modification",
                                                          "Dimensions of this mirror must be changed in order to ensure congruence with the error profile surface, accept?",
                                                          QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                                if self.dim_x_plus > data.error_profile_x_dim/2:
                                    self.dim_x_plus = data.error_profile_x_dim/2
                                if self.dim_x_minus > data.error_profile_x_dim/2:
                                    self.dim_x_minus = data.error_profile_x_dim/2
                                if self.dim_y_plus > data.error_profile_y_dim/2:
                                    self.dim_y_plus = data.error_profile_y_dim/2
                                if self.dim_y_minus > data.error_profile_y_dim/2:
                                    self.dim_y_minus = data.error_profile_y_dim/2

                                QtGui.QMessageBox.information(self, "QMessageBox.information()",
                                                              "Dimensions of this mirror were changed",
                                                              QtGui.QMessageBox.Ok)
                    else:
                        if QtGui.QMessageBox.information(self, "Confirm Modification",
                                                      "This mirror must become rectangular with finite dimensions in order to ensure congruence with the error surface, accept?",
                                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                            self.is_infinite = 1
                            self.mirror_shape = 0
                            self.dim_x_plus = data.error_profile_x_dim/2
                            self.dim_x_minus = data.error_profile_x_dim/2
                            self.dim_y_plus = data.error_profile_y_dim/2
                            self.dim_y_minus = data.error_profile_y_dim/2

                            QtGui.QMessageBox.warning(self, "Warning",
                                                          "Dimensions of this mirror were changed",
                                                          QtGui.QMessageBox.Ok)

                    self.set_Dim_Parameters()
                else:
                    QtGui.QMessageBox.warning(self, "Warning",
                              "This O.E. is not a mirror: surface error file will be ignored",
                              QtGui.QMessageBox.Ok)

    def deserialize(self, shadow_file):
        if self.graphical_options.is_screen_slit:
            raise Exception("Operation non supported for Screen/Slit Widget")
        else:
            try:
                self.source_plane_distance = float(shadow_file.getProperty("T_SOURCE"))
                self.image_plane_distance = float(shadow_file.getProperty("T_IMAGE"))
                self.incidence_angle_deg = float(shadow_file.getProperty("T_INCIDENCE"))
                self.reflection_angle_deg = float(shadow_file.getProperty("T_REFLECTION"))
                self.mirror_orientation_angle = int(float(shadow_file.getProperty("ALPHA"))/90)
                self.angles_respect_to = 0

                if self.graphical_options.is_curved:
                    self.is_cylinder = int(shadow_file.getProperty("FCYL"))

                    if self.is_cylinder == 1:
                        self.cylinder_orientation = int(float(shadow_file.getProperty("CIL_ANG"))/90)

                    if self.graphical_options.is_conic_coefficients:
                        self.conic_coefficient_0 = float(shadow_file.getProperty("CCC(1)"))
                        self.conic_coefficient_1 = float(shadow_file.getProperty("CCC(2)"))
                        self.conic_coefficient_2 = float(shadow_file.getProperty("CCC(3)"))
                        self.conic_coefficient_3 = float(shadow_file.getProperty("CCC(4)"))
                        self.conic_coefficient_4 = float(shadow_file.getProperty("CCC(5)"))
                        self.conic_coefficient_5 = float(shadow_file.getProperty("CCC(6)"))
                        self.conic_coefficient_6 = float(shadow_file.getProperty("CCC(7)"))
                        self.conic_coefficient_7 = float(shadow_file.getProperty("CCC(8)"))
                        self.conic_coefficient_8 = float(shadow_file.getProperty("CCC(9)"))
                        self.conic_coefficient_9 = float(shadow_file.getProperty("CCC(10)"))
                    else:
                        self.surface_shape_parameters = int(shadow_file.getProperty("F_EXT"))

                        if self.surface_shape_parameters == 0:

                            if int(shadow_file.getProperty("F_DEFAULT")) == 1:
                                self.focii_and_continuation_plane = 0
                            elif int(shadow_file.getProperty("F_DEFAULT")) == 0:
                                self.focii_and_continuation_plane = 1

                            if self.focii_and_continuation_plane == 1:
                                self.object_side_focal_distance =  float(shadow_file.getProperty("SSOUR"))
                                self.image_side_focal_distance = float(shadow_file.getProperty("SIMAG"))
                                self.incidence_angle_respect_to_normal = float(shadow_file.getProperty("THETA"))

                            if self.graphical_options.is_paraboloid: self.focus_location = float(shadow_file.getProperty("F_SIDE"))
                        else:
                           if self.graphical_options.is_spheric:
                               self.spherical_radius = float(shadow_file.getProperty("RMIRR"))
                           elif self.graphical_options.is_toroidal:
                               self.torus_major_radius = float(shadow_file.getProperty("R_MAJ"))
                               self.torus_minor_radius = float(shadow_file.getProperty("R_MIN"))
                           elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                               self.ellipse_hyperbola_semi_major_axis = float(shadow_file.getProperty("AXMAJ"))
                               self.ellipse_hyperbola_semi_minor_axis = float(shadow_file.getProperty("AXMIN"))
                               self.angle_of_majax_and_pole = float(shadow_file.getProperty("ELL_THE"))
                           elif self.graphical_options.is_paraboloid:
                               self.paraboloid_parameter = float(shadow_file.getProperty("PARAM"))

                    if self.graphical_options.is_toroidal: self.toroidal_mirror_pole_location = int(shadow_file.getProperty("F_TORUS"))

                    self.surface_curvature == int(shadow_file.getProperty("F_CONVEX"))

                if self.graphical_options.is_mirror:
                    self.reflectivity_type = int(shadow_file.getProperty("F_REFLEC"))

                    if self.reflectivity_type > 0:
                        self.source_of_reflectivity = int(shadow_file.getProperty("F_REFL"))

                        if self.source_of_reflectivity == 0:
                            self.file_prerefl = shadow_file.getProperty("FILE_REFL")
                        elif self.source_of_reflectivity == 1:
                            self.alpha = float(shadow_file.getProperty("ALFA"))
                            self.gamma = float(shadow_file.getProperty("GAMMA"))
                        elif self.source_of_reflectivity == 2:
                            self.file_prerefl_m = shadow_file.getProperty("FILE_REFL")
                            self.m_layer_tickness = float(shadow_file.getProperty("F_THICK"))
                elif self.graphical_options.is_crystal:
                    self.diffraction_calculation = 0
                    self.diffraction_geometry = int(shadow_file.getProperty("F_REFRAC"))
                    self.file_crystal_parameters = shadow_file.getProperty("FILE_REFL")

                    self.crystal_auto_setting = int(shadow_file.getProperty("F_CENTRAL"))
                    self.mosaic_crystal = int(shadow_file.getProperty("F_MOSAIC"))
                    self.asymmetric_cut = int(shadow_file.getProperty("F_BRAGG_A"))
                    self.johansson_geometry = int(shadow_file.getProperty("F_JOHANSSON"))

                    if self.crystal_auto_setting == 1:
                        self.units_in_use = int(shadow_file.getProperty("F_PHOT_CENT"))
                        self.photon_energy = float(shadow_file.getProperty("PHOT_CENT"))
                        self.photon_wavelength = float(shadow_file.getProperty("R_LAMBDA"))

                    if self.mosaic_crystal==1:
                        self.seed_for_mosaic = int(shadow_file.getProperty("MOSAIC_SEED"))
                        self.angle_spread_FWHM = float(shadow_file.getProperty("SPREAD_MOS"))
                        self.thickness = float(shadow_file.getProperty("THICKNESS"))
                    else:
                        if self.asymmetric_cut == 1:
                            self.planes_angle = float(shadow_file.getProperty("A_BRAGG"))
                            self.below_onto_bragg_planes = float(shadow_file.getProperty("ORDER"))
                            self.thickness = float(shadow_file.getProperty("THICKNESS"))
                        if self.johansson_geometry == 1:
                            self.johansson_radius = float(shadow_file.getProperty("R_JOHANSSON"))
                elif self.graphical_options.is_grating:
                    f_ruling = int(shadow_file.getProperty("F_RULING"))

                    if f_ruling == 4:
                        raise Exception("Grating with ruling type not supported: F_RULING=4")
                    else:
                        if f_ruling == 5:
                            self.grating_ruling_type = 4
                        else:
                            self.grating_ruling_type = f_ruling

                    if self.grating_ruling_type == 0 or self.grating_ruling_type == 1:
                        self.grating_ruling_density = float(shadow_file.getProperty("RULING"))
                    elif self.grating_ruling_type == 2:
                        self.grating_holo_left_distance         = float(shadow_file.getProperty("HOLO_R1"))
                        self.grating_holo_right_distance        = float(shadow_file.getProperty("HOLO_R2"))
                        self.grating_holo_left_incidence_angle  = float(shadow_file.getProperty("HOLO_DEL"))
                        self.grating_holo_right_incidence_angle = float(shadow_file.getProperty("HOLO_GAM"))
                        self.grating_holo_recording_wavelength  = float(shadow_file.getProperty("HOLO_W"))
                        self.grating_holo_left_azimuth_from_y   = float(shadow_file.getProperty("HOLO_RT1"))
                        self.grating_holo_right_azimuth_from_y  = float(shadow_file.getProperty("HOLO_RT2"))
                        self.grating_holo_pattern_type = int(shadow_file.getProperty("F_PW"))
                        self.grating_holo_cylindrical_source = int(shadow_file.getProperty("F_PW_C"))
                        self.grating_holo_source_type = int(shadow_file.getProperty("F_VIRTUAL"))
                    elif self.grating_ruling_type == 3:
                        self.grating_groove_pole_azimuth_from_y = float(shadow_file.getProperty("AZIM_FAN"))
                        self.grating_groove_pole_distance = float(shadow_file.getProperty("DIST_FAN"))
                        self.grating_coma_correction_factor = float(shadow_file.getProperty("COMA_FAC"))
                    elif self.grating_ruling_type == 4:
                        self.grating_ruling_density = float(shadow_file.getProperty("RULING"))
                        self.grating_poly_coeff_1   = float(shadow_file.getProperty("RUL_A1"))
                        self.grating_poly_coeff_2   = float(shadow_file.getProperty("RUL_A2"))
                        self.grating_poly_coeff_3   = float(shadow_file.getProperty("RUL_A3"))
                        self.grating_poly_coeff_4   = float(shadow_file.getProperty("RUL_A4"))
                        self.grating_poly_signed_absolute = int(shadow_file.getProperty("F_RUL_ABS"))

                    self.grating_auto_setting = int(shadow_file.getProperty("F_CENTRAL"))

                    if self.grating_auto_setting == 1:
                        self.grating_mount_type = int(shadow_file.getProperty("F_MONO"))
                        self.grating_units_in_use = int(shadow_file.getProperty("F_PHOT_CENT"))
                        self.grating_photon_energy = float(shadow_file.getProperty("PHOT_CENT"))
                        self.grating_photon_wavelength = float(shadow_file.getProperty("R_LAMBDA"))

                        if self.grating_mount_type == 4:
                            self.grating_hunter_grating_selected = int(shadow_file.getProperty("F_HUNT"))-1
                            self.grating_hunter_distance_between_beams = float(shadow_file.getProperty("HUNT_H"))
                            self.grating_hunter_monochromator_length   = float(shadow_file.getProperty("HUNT_L"))
                            self.grating_hunter_blaze_angle            = float(shadow_file.getProperty("BLAZE"))

                self.is_infinite = int(shadow_file.getProperty("FHIT_C"))

                if self.is_infinite == 1:
                    self.mirror_shape = int(shadow_file.getProperty("FSHAPE")) - 1
                    self.dim_y_plus  = float(shadow_file.getProperty("RLEN1"))
                    self.dim_y_minus = float(shadow_file.getProperty("RLEN2"))
                    self.dim_x_plus  = float(shadow_file.getProperty("RWIDX1"))
                    self.dim_x_minus = float(shadow_file.getProperty("RWIDX2"))

                #####################################
                # ADVANCED SETTING
                #####################################

                self.modified_surface = 0

                if int(shadow_file.getProperty("F_RIPPLE")) == 1: self.modified_surface = 1
                elif int(shadow_file.getProperty("F_FACET")) == 1: self.modified_surface = 2
                elif int(shadow_file.getProperty("F_ROUGHNESS")) == 1: self.modified_surface = 3
                elif int(shadow_file.getProperty("F_KOMA")) == 1: self.modified_surface = 4
                elif int(shadow_file.getProperty("F_SEGMENT")) == 1: self.modified_surface = 5

                if self.modified_surface == 1:
                     self.ms_type_of_defect = int(shadow_file.getProperty("F_G_S"))

                     if self.ms_type_of_defect == 0:
                         self.ms_ripple_ampli_x = float(shadow_file.getProperty("X_RIP_AMP"))
                         self.ms_ripple_wavel_x = float(shadow_file.getProperty("X_RIP_WAV"))
                         self.ms_ripple_phase_x = float(shadow_file.getProperty("X_PHASE"))
                         self.ms_ripple_ampli_y = float(shadow_file.getProperty("Y_RIP_AMP"))
                         self.ms_ripple_wavel_y = float(shadow_file.getProperty("Y_RIP_WAV"))
                         self.ms_ripple_phase_y = float(shadow_file.getProperty("Y_PHASE"))
                     else:
                         self.ms_defect_file_name = shadow_file.getProperty("FILE_RIP")
                elif self.modified_surface == 2:
                     self.ms_file_facet_descr = shadow_file.getProperty("FILE_FAC")
                     self.ms_lattice_type = int(shadow_file.getProperty("F_FAC_LATT"))
                     self.ms_orientation = int(shadow_file.getProperty("F_FAC_ORIENT"))
                     self.ms_lattice_type = int(shadow_file.getProperty("F_POLSEL"))-1
                     self.ms_facet_width_x = float(shadow_file.getProperty("RFAC_LENX"))
                     self.ms_facet_phase_x = float(shadow_file.getProperty("RFAC_PHAX"))
                     self.ms_dead_width_x_minus = float(shadow_file.getProperty("RFAC_DELX1"))
                     self.ms_dead_width_x_plus = float(shadow_file.getProperty("RFAC_DELX2"))
                     self.ms_facet_width_y = float(shadow_file.getProperty("RFAC_LENY"))
                     self.ms_facet_phase_y = float(shadow_file.getProperty("RFAC_PHAY"))
                     self.ms_dead_width_y_minus = float(shadow_file.getProperty("RFAC_DELY1"))
                     self.ms_dead_width_y_plus = float(shadow_file.getProperty("RFAC_DELY2"))
                elif self.modified_surface == 3:
                    self.ms_file_surf_roughness = shadow_file.getProperty("FILE_ROUGH")
                    self.ms_roughness_rms_x = float(shadow_file.getProperty("ROUGH_X"))
                    self.ms_roughness_rms_y = float(shadow_file.getProperty("ROUGH_Y"))
                elif self.modified_surface == 4:
                    self.ms_specify_rz2 = int(shadow_file.getProperty("F_KOMA_CA"))
                    self.ms_file_with_parameters_rz = shadow_file.getProperty("FILE_KOMA")
                    self.ms_file_with_parameters_rz2 = shadow_file.getProperty("FILE_KOMA_CA")
                    self.ms_save_intercept_bounces = int(shadow_file.getProperty("F_KOMA_BOUNCE"))
                elif self.modified_surface == 5:
                    self.ms_number_of_segments_x = int(shadow_file.getProperty("ISEG_XNUM"))
                    self.ms_number_of_segments_y = int(shadow_file.getProperty("ISEG_YNUM"))
                    self.ms_length_of_segments_x = float(shadow_file.getProperty("SEG_LENX"))
                    self.ms_length_of_segments_y = float(shadow_file.getProperty("SEG_LENY"))
                    self.ms_file_orientations = shadow_file.getProperty("FILE_SEGMENT")
                    self.ms_file_polynomial = shadow_file.getProperty("FILE_SEGP")

                self.mirror_movement = int(shadow_file.getProperty("F_MOVE"))

                if self.mirror_movement == 1:
                     self.mm_mirror_offset_x = float(shadow_file.getProperty("OFFX"))
                     self.mm_mirror_offset_y = float(shadow_file.getProperty("OFFY"))
                     self.mm_mirror_offset_z = float(shadow_file.getProperty("OFFZ"))
                     self.mm_mirror_rotation_x = float(shadow_file.getProperty("X_ROT"))
                     self.mm_mirror_rotation_y = float(shadow_file.getProperty("Y_ROT"))
                     self.mm_mirror_rotation_z = float(shadow_file.getProperty("Z_ROT"))

                self.source_movement = int(shadow_file.getProperty("FSTAT"))

                if self.source_movement == 1:
                     self.sm_angle_of_incidence = float(shadow_file.getProperty("RTHETA"))
                     self.sm_distance_from_mirror = float(shadow_file.getProperty("RDSOUR"))
                     self.sm_z_rotation = float(shadow_file.getProperty("ALPHA_S"))
                     self.sm_offset_x_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUX"))
                     self.sm_offset_y_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUY"))
                     self.sm_offset_z_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUZ"))
                     self.sm_offset_x_source_ref_frame = float(shadow_file.getProperty("X_SOUR"))
                     self.sm_offset_y_source_ref_frame = float(shadow_file.getProperty("Y_SOUR"))
                     self.sm_offset_z_source_ref_frame = float(shadow_file.getProperty("Z_SOUR"))
                     self.sm_rotation_around_x = float(shadow_file.getProperty("X_SOUR_ROT"))
                     self.sm_rotation_around_y = float(shadow_file.getProperty("Y_SOUR_ROT"))
                     self.sm_rotation_around_z = float(shadow_file.getProperty("Z_SOUR_ROT"))

                self.file_to_write_out = int(shadow_file.getProperty("FWRITE"))
                self.write_out_inc_ref_angles = int(shadow_file.getProperty("F_ANGLE"))
            except Exception as exception:
                raise BlockingIOError("O.E. failed to load, bad file format: " + exception.args[0])
                
            self.setupUI()

    def copy_oe_parameters(self):
        global shadow_oe_to_copy
        shadow_oe_to_copy = ShadowOpticalElement.create_empty_oe()

        self.populateFields(shadow_oe_to_copy)

    def paste_oe_parameters(self):
        global shadow_oe_to_copy

        shadow_temp_file = congruence.checkFileName("tmp_oe_buffer.dat")
        shadow_oe_to_copy._oe.write(shadow_temp_file)

        shadow_file, type = ShadowFile.readShadowFile(shadow_temp_file)

        self.deserialize(shadow_file)

        os.remove(shadow_temp_file)

    def setupUI(self):
        if self.graphical_options.is_screen_slit:
            self.set_Aperturing()
            self.set_Absorption()
        else:
            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            if self.graphical_options.is_curved:
                if not self.graphical_options.is_conic_coefficients:
                    self.set_IntExt_Parameters()
                    self.set_isCyl_Parameters()

            if self.graphical_options.is_mirror:
                self.set_Refl_Parameters()
            elif self.graphical_options.is_crystal:
                self.set_Mosaic()
                self.set_DiffractionCalculation()
            elif self.graphical_options.is_grating:
                self.set_GratingAutosetting()
                self.set_GratingRulingType()
            elif self.graphical_options.is_refractor:
                self.set_RefrectorOpticalConstants()

            self.set_Dim_Parameters()
            self.set_ModifiedSurface()

        self.set_MirrorMovement()
        self.set_SourceMovement()
