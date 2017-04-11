import sys, numpy, copy

from PyQt4 import QtGui
from PyQt4.QtGui import QPalette, QColor, QFont, QDialog, QWidget

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowTriggerIn, ShadowOpticalElement, ShadowBeam, ShadowFile
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPhysics
from orangecontrib.shadow.widgets.gui.ow_generic_element import GenericElement

import xraylib
from oasys.util.oasys_util import ChemicalFormulaParser


AMPLITUDE_ZP = 0
PHASE_ZP = 1

LOST = -101
GOOD = 1
GOOD_ZP = 2

class ZonePlate(GenericElement):

    name = "Zone Plate"
    description = "Shadow OE: Zone Plate"
    icon = "icons/zone_plate.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 23
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"},
               {"name":"Trigger",
                "type": ShadowTriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"}]

    input_beam = None
    output_beam = None

    NONE_SPECIFIED = "NONE SPECIFIED"

    ONE_ROW_HEIGHT = 65
    TWO_ROW_HEIGHT = 110
    THREE_ROW_HEIGHT = 170

    INNER_BOX_WIDTH_L3=322
    INNER_BOX_WIDTH_L2=335
    INNER_BOX_WIDTH_L1=358
    INNER_BOX_WIDTH_L0=375

    source_plane_distance = Setting(10.0)
    image_plane_distance = Setting(20.0)

    delta_rn = Setting(25) # nm
    diameter = Setting(618) # micron
    source_distance = Setting(0.0)

    type_of_zp = Setting(1)

    zone_plate_material = Setting("Au")
    zone_plate_thickness = Setting(200) # nm
    substrate_material = Setting("Si3N4")
    substrate_thickness = Setting(50) # nm

    avg_wavelength = 0.0
    focal_distance = 0.0
    image_position = 0.0
    magnification  = 0.0
    efficiency     = 0.0

    ##################################################

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

    file_to_write_out = Setting(3) # Mirror: users found difficoult to activate the "Footprint" option.
    write_out_inc_ref_angles = Setting(0)

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Run Shadow/Trace", self)
        self.runaction.triggered.connect(self.traceOpticalElement)
        self.addAction(self.runaction)

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

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_adv = oasysgui.createTabPage(tabs_setting, "Advanced Setting")

        ##########################################
        ##########################################
        # BASIC SETTINGS
        ##########################################
        ##########################################

        tabs_basic_setting = gui.tabWidget(tab_bas)

        tab_zone_plate = oasysgui.createTabPage(tabs_basic_setting, "Zone Plate")

        zp_box = oasysgui.widgetBox(tab_zone_plate, "Zone Plate Input Parameters", addSpace=False, orientation="vertical", height=230)

        oasysgui.lineEdit(zp_box, self, "delta_rn",  u"\u03B4" + "rn [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(zp_box, self, "diameter", "Z.P. Diameter [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_source_distance = oasysgui.lineEdit(zp_box, self, "source_distance", "Source Distance", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(zp_box, self, "type_of_zp", label="Type of Zone Plate", labelWidth=350,
                     items=["Amplitude", "Phase"],
                     callback=self.set_TypeOfZP, sendSelectedValue=False, orientation="horizontal")

        gui.separator(zp_box, height=5)

        self.zp_box_1 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.zp_box_1, self, "zone_plate_material",  "Zone Plate Material", labelWidth=260, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.zp_box_1, self, "zone_plate_thickness",  "Zone Plate Thickness [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.zp_box_1, self, "substrate_material", "Substrate Material", labelWidth=260, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.zp_box_1, self, "substrate_thickness",  "Substrate Thickness [nm]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_TypeOfZP()

        zp_out_box = oasysgui.widgetBox(tab_zone_plate, "Zone Plate Output Parameters", addSpace=False, orientation="vertical", height=230)

        self.le_avg_wavelength = oasysgui.lineEdit(zp_out_box, self, "avg_wavelength", "Average Wavelenght [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_avg_wavelength.setReadOnly(True)
        font = QtGui.QFont(self.le_avg_wavelength.font())
        font.setBold(True)
        self.le_avg_wavelength.setFont(font)
        palette = QtGui.QPalette(self.le_avg_wavelength.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        self.le_avg_wavelength.setPalette(palette)

        self.le_focal_distance = oasysgui.lineEdit(zp_out_box, self, "focal_distance", "Focal Distance", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_focal_distance.setReadOnly(True)
        font = QtGui.QFont(self.le_focal_distance.font())
        font.setBold(True)
        self.le_focal_distance.setFont(font)
        palette = QtGui.QPalette(self.le_focal_distance.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        self.le_focal_distance.setPalette(palette)

        self.le_image_position = oasysgui.lineEdit(zp_out_box, self, "image_position", "Image Position (Q)", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_image_position.setReadOnly(True)
        font = QtGui.QFont(self.le_image_position.font())
        font.setBold(True)
        self.le_image_position.setFont(font)
        palette = QtGui.QPalette(self.le_image_position.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        self.le_image_position.setPalette(palette)

        self.le_magnification = oasysgui.lineEdit(zp_out_box, self, "magnification", "Magnification", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_magnification.setReadOnly(True)
        font = QtGui.QFont(self.le_magnification.font())
        font.setBold(True)
        self.le_magnification.setFont(font)
        palette = QtGui.QPalette(self.le_magnification.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        self.le_magnification.setPalette(palette)

        self.le_efficiency = oasysgui.lineEdit(zp_out_box, self, "efficiency", "Efficiency(Avg. Wavelength)", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_efficiency.setReadOnly(True)
        font = QtGui.QFont(self.le_efficiency.font())
        font.setBold(True)
        self.le_efficiency.setFont(font)
        palette = QtGui.QPalette(self.le_efficiency.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        self.le_efficiency.setPalette(palette)


        ##########################################
        ##########################################
        # ADVANCED SETTINGS
        ##########################################
        ##########################################

        tabs_advanced_setting = gui.tabWidget(tab_adv)

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
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(adv_other_box, self, "write_out_inc_ref_angles", label="Write out Incident/Reflected angles [angle.xx]", labelWidth=300,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")


        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def traceOpticalElement(self):
        try:
            #self.error(self.error_id)
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    self.checkFields()

                    sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                    if self.trace_shadow:
                        grabber = TTYGrabber()
                        grabber.start()

                    ###########################################
                    # TODO: TO BE ADDED JUST IN CASE OF BROKEN
                    #       ENVIRONMENT: MUST BE FOUND A PROPER WAY
                    #       TO TEST SHADOW
                    self.fixWeirdShadowBug()
                    ###########################################

                    self.progressBarSet(10)


                    zone_plate_beam = self.get_zone_plate_beam()

                    go = numpy.where(zone_plate_beam._beam.rays[:, 9] == 1)

                    self.avg_wavelength = numpy.round(ShadowPhysics.getWavelengthFromShadowK(numpy.average(zone_plate_beam._beam.rays[go, 10]))*1e-1, 4) #ANGSTROM->nm

                    self.focal_distance = numpy.round((self.delta_rn*(self.diameter*1000)/self.avg_wavelength)* (1e-9/self.workspace_units_to_m), 4)
                    self.image_position = numpy.round(self.focal_distance*self.source_distance/(self.source_distance-self.focal_distance), 4)
                    self.magnification = numpy.round(numpy.abs(self.image_position/self.source_distance), 4)


                    if self.type_of_zp == PHASE_ZP:
                        avg_energy_in_KeV = ShadowPhysics.getEnergyFromWavelength(self.avg_wavelength*10)/1000

                        density = xraylib.ElementDensity(xraylib.SymbolToAtomicNumber(self.zone_plate_material))
                        delta = (1-xraylib.Refractive_Index_Re(self.zone_plate_material, avg_energy_in_KeV, density))
                        beta  = xraylib.Refractive_Index_Im(self.zone_plate_material, avg_energy_in_KeV, density)
                        phi = 2*numpy.pi*self.zone_plate_thickness*delta/self.avg_wavelength
                        r = beta/delta

                        self.efficiency = numpy.round(((1 + numpy.exp(-2*r*phi) - (2*numpy.exp(-r*phi)*numpy.cos(phi)))/numpy.pi)**2, 6)
                    else:
                        self.efficiency = numpy.round(1/(numpy.pi**2), 4)

                    focused_beam = ZonePlate.apply_fresnel_zone_plate(zone_plate_beam,
                                                                      self.type_of_zp,
                                                                      self.diameter,
                                                                      self.delta_rn,
                                                                      self.substrate_material,
                                                                      self.substrate_thickness,
                                                                      self.zone_plate_material,
                                                                      self.zone_plate_thickness)


                    focused_beam._beam.retrace(self.image_plane_distance)

                    beam_out = focused_beam

                    if self.trace_shadow:
                        grabber.stop()

                        for row in grabber.ttyData:
                           self.writeStdOut(row)

                    self.setStatusMessage("Plotting Results")

                    self.plot_results(beam_out)

                    self.setStatusMessage("")

                    self.send("Beam", beam_out)
                    self.send("Trigger", ShadowTriggerIn(new_beam=True))


                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception), QtGui.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

            #raise exception

        self.progressBarFinished()

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.traceOpticalElement()

    def checkFields(self):
        self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
        self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

        congruence.checkStrictlyPositiveNumber(self.delta_rn, u"\u03B4" + "rn" )
        congruence.checkStrictlyPositiveNumber(self.diameter, "Z.P. Diameter")
        congruence.checkPositiveNumber(self.source_distance, "Source Distance" )

        if self.type_of_zp == PHASE_ZP:
            congruence.checkEmptyString(self.zone_plate_material, "Zone Plate Material")
            congruence.checkStrictlyPositiveNumber(self.zone_plate_thickness, "Zone Plate Thickness")
            congruence.checkEmptyString(self.substrate_material, "Substrate Material")
            congruence.checkStrictlyPositiveNumber(self.substrate_thickness, "Substrate Thickness")
            
  
    def after_change_workspace_units(self):
        label = self.le_source_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_image_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

        label = self.le_source_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_focal_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_image_position.parent().layout().itemAt(0).widget()
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

    def callResetSettings(self):
        super().callResetSettings()
        self.setupUI()

    def set_SourceMovement(self):
        self.sou_mov_box_1.setVisible(self.source_movement == 1)

    def set_MirrorMovement(self):
        self.mir_mov_box_1.setVisible(self.mirror_movement == 1)

    def set_TypeOfZP(self):
        self.zp_box_1.setVisible(self.type_of_zp == PHASE_ZP)


    ######################################################################
    # ZONE PLATE CALCULATION
    ######################################################################

    def get_zone_plate_beam(self):

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element._oe.DUMMY = 1.0 # self.workspace_units_to_cm

        empty_element._oe.T_SOURCE     = self.source_plane_distance
        empty_element._oe.T_IMAGE      = 0.0
        empty_element._oe.T_INCIDENCE  = 0.0
        empty_element._oe.T_REFLECTION = 180.0
        empty_element._oe.ALPHA        = 0.0

        empty_element._oe.FWRITE = 3
        empty_element._oe.F_ANGLE = 0

        n_screen = 1
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_abs = numpy.zeros(10)
        i_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_stop = numpy.zeros(10)
        k_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = 0.0
        rx_slit[0] = self.diameter*1e-6/self.workspace_units_to_m
        rz_slit[0] = self.diameter*1e-6/self.workspace_units_to_m
        cx_slit[0] = 0.0
        cz_slit[0] = 0.0

        empty_element._oe.set_screens(n_screen,
                                      i_screen,
                                      i_abs,
                                      sl_dis,
                                      i_slit,
                                      i_stop,
                                      k_slit,
                                      thick,
                                      file_abs,
                                      rx_slit,
                                      rz_slit,
                                      cx_slit,
                                      cz_slit,
                                      file_scr_ext)


        return ShadowBeam.traceFromOE(self.input_beam, empty_element, history=True)

    # ALGORITHM EXTRACTED FROM webAbsorb.py by 11BM - Argonne National Laboratory
    @classmethod
    def get_material_density(cls, material):
        elements = ChemicalFormulaParser.parse_formula(material)
        
        mass = 0.0
        volume = 0.0
        
        for element in elements:
            mass += element._molecular_weight*element._n_atoms
            volume += 10.*element._n_atoms
                    
        rho = mass/(0.602*volume) 
    
        return rho
    
    @classmethod  
    def get_material_weight_factor(cls, shadow_rays, material, thickness):
        mu = numpy.zeros(len(shadow_rays))
        
        for i in range(0, len(mu)):
            mu[i] = xraylib.CS_Total_CP(material, ShadowPhysics.getEnergyFromShadowK(shadow_rays[i, 10])/1000) # energy in KeV
        
        rho = ZonePlate.get_material_density(material)
                    
        return numpy.sqrt(numpy.exp(-mu*rho*thickness*1e-7)) # thickness in CM
        
    
    @classmethod  
    def get_delta_beta(cls, shadow_rays, material):
        beta = numpy.zeros(len(shadow_rays))
        delta = numpy.zeros(len(shadow_rays))
        density = xraylib.ElementDensity(xraylib.SymbolToAtomicNumber(material))
    
        for i in range(0, len(shadow_rays)):
            energy_in_KeV = ShadowPhysics.getEnergyFromShadowK(shadow_rays[i, 10])/1000
            delta[i] = (1-xraylib.Refractive_Index_Re(material, energy_in_KeV, density))
            beta[i]  = xraylib.Refractive_Index_Im(material, energy_in_KeV, density)
    
        return delta, beta 
    
    @classmethod
    def analyze_zone(cls, zones, focused_beam):
        x = focused_beam._beam.rays[:, 0]
        z = focused_beam._beam.rays[:, 2]
        r = numpy.sqrt(x**2 + z**2) 

        for zone in zones:
            t = numpy.where(numpy.logical_and(r >= zone[0], r <= zone[1]))
    
            intercepted_rays = focused_beam._beam.rays[t]
                    
            # (see formulas in A.G. Michette, "X-ray science and technology"
            #  Institute of Physics Publishing (1993))
    
            x_int = intercepted_rays[:, 0]
            z_int = intercepted_rays[:, 2]
            xp_int = intercepted_rays[:, 3]
            zp_int = intercepted_rays[:, 5]
            k_mod_int = intercepted_rays[:, 10]
    
            r_int = numpy.sqrt(x_int**2 + z_int**2) 
          
            k_x_int = k_mod_int*xp_int
            k_z_int = k_mod_int*zp_int
            d = zone[1] - zone[0]
            
            # computing G (the "grating" wavevector in Angstrom^-1)
            gx = -numpy.pi / d * (x_int/r_int)
            gz = -numpy.pi / d * (z_int/r_int)
           
            k_x_out = k_x_int + gx
            k_z_out = k_z_int + gz
            xp_out = k_x_out / k_mod_int
            zp_out = k_z_out / k_mod_int
       
            intercepted_rays[:, 3] = xp_out # XP
            intercepted_rays[:, 5] = zp_out # ZP
            intercepted_rays[:, 9] = GOOD_ZP
                        
            focused_beam._beam.rays[t, 3] = intercepted_rays[:, 3]       
            focused_beam._beam.rays[t, 4] = intercepted_rays[:, 4]       
            focused_beam._beam.rays[t, 5] = intercepted_rays[:, 5]       
            focused_beam._beam.rays[t, 9] = intercepted_rays[:, 9]    
    
    @classmethod
    def apply_fresnel_zone_plate(cls, 
                                 zone_plate_beam,
                                 type_of_zp, 
                                 diameter, 
                                 delta_rn,                              
                                 substrate_material, 
                                 substrate_thickness,
                                 zone_plate_material,
                                 zone_plate_thickness):
        
        max_zones_number = int(diameter*1000/(4*delta_rn))
    
        print ("Max Zone Number", max_zones_number)
    
        focused_beam = zone_plate_beam.duplicate(history=True)

        go = numpy.where(zone_plate_beam._beam.rays[:, 9] == GOOD)

        print("Number of input rays in the ZP", len(zone_plate_beam._beam.rays[go]))

        if type_of_zp == PHASE_ZP: 
            substrate_weight_factor = ZonePlate.get_material_weight_factor(focused_beam._beam.rays[go], substrate_material, substrate_thickness)
        
            focused_beam._beam.rays[go, 6] = focused_beam._beam.rays[go, 6]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 7] = focused_beam._beam.rays[go, 7]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 8] = focused_beam._beam.rays[go, 8]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 15] = focused_beam._beam.rays[go, 15]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 16] = focused_beam._beam.rays[go, 16]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 17] = focused_beam._beam.rays[go, 17]*substrate_weight_factor[:]
        
        clear_zones = []
        dark_zones = []
        r_zone_i_previous = 0.0
        for i in range(1, max_zones_number+1):
            r_zone_i = numpy.sqrt(i*diameter*1000*delta_rn)*1e-7
            if i % 2 == 0: clear_zones.append([r_zone_i_previous, r_zone_i])
            else: dark_zones.append([r_zone_i_previous, r_zone_i])
            r_zone_i_previous = r_zone_i
               
        focused_beam._beam.rays[go, 9] = LOST
        
        ZonePlate.analyze_zone(clear_zones, focused_beam)
        if type_of_zp == PHASE_ZP: ZonePlate.analyze_zone(dark_zones, focused_beam)
    
        go_2 = numpy.where(focused_beam._beam.rays[:, 9] == GOOD_ZP)
        lo_2 = numpy.where(focused_beam._beam.rays[:, 9] == LOST)
    
        intensity_go_2 = numpy.sum(focused_beam._beam.rays[go_2, 6] ** 2 + focused_beam._beam.rays[go_2, 7] ** 2 + focused_beam._beam.rays[go_2, 8] ** 2 + \
                                   focused_beam._beam.rays[go_2, 15] ** 2 + focused_beam._beam.rays[go_2, 16] ** 2 + focused_beam._beam.rays[go_2, 17] ** 2)
    
        intensity_lo_2 = numpy.sum(focused_beam._beam.rays[lo_2, 6] ** 2 + focused_beam._beam.rays[lo_2, 7] ** 2 + focused_beam._beam.rays[lo_2, 8] ** 2 + \
                                   focused_beam._beam.rays[lo_2, 15] ** 2 + focused_beam._beam.rays[lo_2, 16] ** 2 + focused_beam._beam.rays[lo_2, 17] ** 2)

        if type_of_zp == PHASE_ZP:
            wavelength = ShadowPhysics.getWavelengthFromShadowK(focused_beam._beam.rays[go, 10])*1e-8 #cm
            delta, beta = ZonePlate.get_delta_beta(focused_beam._beam.rays[go], zone_plate_material)
            
            phi = 2*numpy.pi*(zone_plate_thickness*1e-7)*delta/wavelength
            r = beta/delta
               
            efficiency_zp = ((1 + numpy.exp(-2*r*phi) - (2*numpy.exp(-r*phi)*numpy.cos(phi)))/numpy.pi)**2
    
            efficiency_weight_factor = numpy.sqrt(efficiency_zp)
        elif type_of_zp == AMPLITUDE_ZP:
            efficiency_zp = numpy.ones(len(focused_beam._beam.rays[go_2]))/(numpy.pi**2)
            efficiency_weight_factor = numpy.sqrt(efficiency_zp*(1 + (intensity_lo_2/intensity_go_2)))
        
        print ("Efficiency (max, min)", numpy.max(efficiency_weight_factor**2), numpy.min(efficiency_weight_factor**2))

        focused_beam._beam.rays[go_2, 6] = focused_beam._beam.rays[go_2, 6]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 7] = focused_beam._beam.rays[go_2, 7]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 8] = focused_beam._beam.rays[go_2, 8]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 15] = focused_beam._beam.rays[go_2, 15]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 16] = focused_beam._beam.rays[go_2, 16]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 17] = focused_beam._beam.rays[go_2, 17]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 9] = GOOD

        return focused_beam
