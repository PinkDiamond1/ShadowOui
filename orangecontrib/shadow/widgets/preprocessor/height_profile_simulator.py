import sys

import numpy
from PyQt4.QtCore import QRect
from PyQt4.QtGui import QTextEdit, QTextCursor, QApplication, QFont, QPalette, QColor, \
    QMessageBox

from srxraylib.metrology import profiles_simulation
from Shadow import ShadowTools as ST
from matplotlib import cm
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from oasys.widgets.widget import OWWidget
from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, EmittingStream
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

class OWheight_profile_simulator(OWWidget):
    name = "Height Profile Simulator"
    id = "height_profile_simulator"
    description = "Calculation of mirror surface height profile"
    icon = "icons/simulator.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 5
    category = ""
    keywords = ["height_profile_simulator"]

    outputs = [{"name": "PreProcessor_Data",
                "type": ShadowPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]

    want_main_area = 1
    want_control_area = 1

    WIDGET_WIDTH = 1100
    WIDGET_HEIGHT = 650

    xx = None
    yy = None
    zz = None

    kind_of_profile_x = Setting(0)
    kind_of_profile_y = Setting(0)

    step_x = Setting(1.0)
    step_y = Setting(1.0)

    dimension_x = Setting(20.1)
    dimension_y = Setting(200.1)

    power_law_exponent_beta_x = Setting(1.5)
    power_law_exponent_beta_y = Setting(1.5)

    correlation_length_x = Setting(30.0)
    correlation_length_y = Setting(30.0)

    error_type_x = Setting(profiles_simulation.FIGURE_ERROR)
    error_type_y = Setting(profiles_simulation.FIGURE_ERROR)

    rms_x = Setting(0.1)
    montecarlo_seed_x = Setting(8787)

    rms_y = Setting(1)
    montecarlo_seed_y = Setting(8788)

    heigth_profile_1D_file_name_x= Setting("mirror_1D_x.dat")
    delimiter_x = Setting(0)
    conversion_factor_x_x = Setting(0.1)
    conversion_factor_x_y = Setting(1e-6)
    renormalize_x = Setting(0)

    heigth_profile_1D_file_name_y = Setting("mirror_1D_y.dat")
    delimiter_y = Setting(0)
    conversion_factor_y_x = Setting(0.1)
    conversion_factor_y_y = Setting(1e-6)
    renormalize_y = Setting(0)

    heigth_profile_file_name = Setting('mirror.dat')

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Calculate Height Profile", self)
        self.runaction.triggered.connect(self.calculate_heigth_profile_ni)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Generate Height Profile File", self)
        self.runaction.triggered.connect(self.generate_heigth_profile_file_ni)
        self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height() * 0.95, self.WIDGET_HEIGHT))))

        gen_box = oasysgui.widgetBox(self.controlArea, "Height Profile Parameters", addSpace=True, orientation="horizontal",
                                      width=500)

        tabs_setting = gui.tabWidget(gen_box)

        tab_input = oasysgui.createTabPage(tabs_setting, "Input Parameters")

        tab_out = oasysgui.createTabPage(tabs_setting, "Output")


        tabs_input = gui.tabWidget(tab_input)
        tab_length = oasysgui.createTabPage(tabs_input, "Length")
        tab_width = oasysgui.createTabPage(tabs_input, "Width")

        #/ ---------------------------------------


        input_box_l = oasysgui.widgetBox(tab_length, "Calculation Parameters", addSpace=True, orientation="vertical", width=460)

        gui.comboBox(input_box_l, self, "kind_of_profile_y", label="Kind of Profile", labelWidth=260,
                     items=["Fractal", "Gaussian", "User File"],
                     callback=self.set_KindOfProfileY, sendSelectedValue=False, orientation="horizontal")

        gui.separator(input_box_l)

        self.kind_of_profile_y_box_1 = oasysgui.widgetBox(input_box_l, "", addSpace=True, orientation="vertical", width=440, height=300)

        oasysgui.lineEdit(self.kind_of_profile_y_box_1, self, "dimension_y", "Dimensions [cm]                                         Y (lenght)",
                           labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.kind_of_profile_y_box_1, self, "step_y", "Step [cm]                                                    Y (lenght)",
                           labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.kind_of_profile_y_box_1, self, "montecarlo_seed_y", "Monte Carlo initial seed                              Y (lenght)", labelWidth=300,
                           valueType=int, orientation="horizontal")

        self.kind_of_profile_y_box_1_1 = oasysgui.widgetBox(self.kind_of_profile_y_box_1, "", addSpace=True, orientation="vertical", width=440)

        oasysgui.lineEdit(self.kind_of_profile_y_box_1_1, self, "power_law_exponent_beta_y", "Beta Value                                                  Y (lenght)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        self.kind_of_profile_y_box_1_2 = oasysgui.widgetBox(self.kind_of_profile_y_box_1, "", addSpace=True, orientation="vertical", width=440)

        oasysgui.lineEdit(self.kind_of_profile_y_box_1_2, self, "correlation_length_y", "Correlation Length [cm]                              Y (lenght)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        gui.separator(self.kind_of_profile_y_box_1)

        gui.comboBox(self.kind_of_profile_y_box_1, self, "error_type_y", label="Normalization to", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + "\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_y_box_1, self, "rms_y", "Rms Value                                                   Y (lenght)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        self.kind_of_profile_y_box_2 = oasysgui.widgetBox(input_box_l, "", addSpace=True, orientation="vertical", width=440, height=300)

        select_file_box_2 = oasysgui.widgetBox(self.kind_of_profile_y_box_2, "", addSpace=True, orientation="horizontal")

        self.le_heigth_profile_1D_file_name_y = oasysgui.lineEdit(select_file_box_2, self, "heigth_profile_1D_file_name_y", "1D Profile File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        pushButton = gui.button(select_file_box_2, self, "...")
        pushButton.clicked.connect(self.selectFile1D_Y)

        gui.comboBox(self.kind_of_profile_y_box_2, self, "delimiter_y", label="Fields delimiter", labelWidth=260,
                     items=["Spaces", "Tabs"], sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_y_box_2, self, "conversion_factor_y_x", "Conversion from user units to cm (Abscissa)", labelWidth=350,
                           valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_y_box_2, self, "conversion_factor_y_y", "Conversion from user units to cm (Height Profile Values)", labelWidth=350,
                           valueType=float, orientation="horizontal")

        gui.separator(self.kind_of_profile_y_box_2)

        gui.comboBox(self.kind_of_profile_y_box_2, self, "renormalize_y", label="Renormalize to different RMS", labelWidth=260,
                     items=["No", "Yes"], callback=self.set_KindOfProfileY, sendSelectedValue=False, orientation="horizontal")

        self.kind_of_profile_y_box_2_1 = oasysgui.widgetBox(self.kind_of_profile_y_box_2, "", addSpace=True, orientation="vertical", width=440)

        gui.comboBox(self.kind_of_profile_y_box_2_1, self, "error_type_y", label="Normalization to", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + "\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_y_box_2_1, self, "rms_y", "Rms Value                                                   Y (lenght)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        self.set_KindOfProfileY()

        #/ ---------------------------------------

        input_box_w = oasysgui.widgetBox(tab_width, "Calculation Parameters", addSpace=True, orientation="vertical", width=460)


        gui.comboBox(input_box_w, self, "kind_of_profile_x", label="Kind of Profile", labelWidth=260,
                     items=["Fractal", "Gaussian", "User File"],
                     callback=self.set_KindOfProfileX, sendSelectedValue=False, orientation="horizontal")

        gui.separator(input_box_w)

        self.kind_of_profile_x_box_1 = oasysgui.widgetBox(input_box_w, "", addSpace=True, orientation="vertical", width=440, height=300)

        oasysgui.lineEdit(self.kind_of_profile_x_box_1, self, "dimension_x", "Dimensions [cm]                                         X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.kind_of_profile_x_box_1, self, "step_x", "Step [cm]                                                    X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.kind_of_profile_x_box_1, self, "montecarlo_seed_x", "Monte Carlo initial seed                              X (width)", labelWidth=300,
                           valueType=int, orientation="horizontal")

        self.kind_of_profile_x_box_1_1 = oasysgui.widgetBox(self.kind_of_profile_x_box_1, "", addSpace=True, orientation="vertical", width=440)

        oasysgui.lineEdit(self.kind_of_profile_x_box_1_1, self, "power_law_exponent_beta_x", "Beta Value                                                  X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        self.kind_of_profile_x_box_1_2 = oasysgui.widgetBox(self.kind_of_profile_x_box_1, "", addSpace=True, orientation="vertical", width=440)

        oasysgui.lineEdit(self.kind_of_profile_x_box_1_2, self, "correlation_length_x", "Correlation Length [cm]                              X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        gui.separator(self.kind_of_profile_x_box_1)

        gui.comboBox(self.kind_of_profile_x_box_1, self, "error_type_x", label="Normalization to", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + "\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_x_box_1, self, "rms_x", "Rms Value                                                   X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")


        self.kind_of_profile_x_box_2 = oasysgui.widgetBox(input_box_w, "", addSpace=True, orientation="vertical", width=440, height=300)

        select_file_box_1 = oasysgui.widgetBox(self.kind_of_profile_x_box_2, "", addSpace=True, orientation="horizontal")

        self.le_heigth_profile_1D_file_name_x = oasysgui.lineEdit(select_file_box_1, self, "heigth_profile_1D_file_name_x", "1D Profile File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        pushButton = gui.button(select_file_box_1, self, "...")
        pushButton.clicked.connect(self.selectFile1D_X)

        gui.comboBox(self.kind_of_profile_x_box_2 , self, "delimiter_x", label="Fields delimiter", labelWidth=260,
                     items=["Spaces", "Tabs"], sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_x_box_2, self, "conversion_factor_x_x", "Conversion from user units to cm (Abscissa)", labelWidth=350,
                           valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_x_box_2, self, "conversion_factor_x_y", "Conversion from user units to cm (Height Profile Values)", labelWidth=350,
                           valueType=float, orientation="horizontal")

        gui.separator(self.kind_of_profile_x_box_2)

        gui.comboBox(self.kind_of_profile_x_box_2, self, "renormalize_x", label="Renormalize to different RMS", labelWidth=260,
                     items=["No", "Yes"], callback=self.set_KindOfProfileX, sendSelectedValue=False, orientation="horizontal")

        self.kind_of_profile_x_box_2_1 = oasysgui.widgetBox(self.kind_of_profile_x_box_2, "", addSpace=True, orientation="vertical", width=440)

        gui.comboBox(self.kind_of_profile_x_box_2_1, self, "error_type_x", label="Normalization to", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + "\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.kind_of_profile_x_box_2_1, self, "rms_x", "Rms Value                                                   X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        self.set_KindOfProfileX()

        #/ ---------------------------------------

        self.output_box = oasysgui.widgetBox(tab_input, "Outputs", addSpace=True, orientation="vertical", width=470)

        self.select_file_box = oasysgui.widgetBox(self.output_box, "", addSpace=True, orientation="horizontal")

        self.le_heigth_profile_file_name = oasysgui.lineEdit(self.select_file_box, self, "heigth_profile_file_name", "Output File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        pushButton = gui.button(self.select_file_box, self, "...")
        pushButton.clicked.connect(self.selectFile)

        self.shadow_output = QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=600)
        out_box.layout().addWidget(self.shadow_output)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Height Profile", callback=self.calculate_heigth_profile)
        button.setFixedHeight(45)
        button.setFixedWidth(170)

        button = gui.button(button_box, self, "Generate Height Profile File", callback=self.generate_heigth_profile_file)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(200)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(120)

        gui.rubber(self.controlArea)

        self.figure = Figure(figsize=(600, 600))
        self.figure.patch.set_facecolor('white')

        self.axis = self.figure.add_subplot(111, projection='3d')

        self.axis.set_xlabel("X (cm)")
        self.axis.set_ylabel("Y (cm)")
        self.axis.set_zlabel("Z (nm)")

        self.figure_canvas = FigureCanvasQTAgg(self.figure)
        self.mainArea.layout().addWidget(self.figure_canvas)

        gui.rubber(self.mainArea)

    def set_KindOfProfileX(self):
        self.kind_of_profile_x_box_1.setVisible(self.kind_of_profile_x<2)
        self.kind_of_profile_x_box_1_1.setVisible(self.kind_of_profile_x==0)
        self.kind_of_profile_x_box_1_2.setVisible(self.kind_of_profile_x==1)
        self.kind_of_profile_x_box_2.setVisible(self.kind_of_profile_x==2)
        self.kind_of_profile_x_box_2_1.setVisible(self.kind_of_profile_x==2 and self.renormalize_x==1)

    def set_KindOfProfileY(self):
        self.kind_of_profile_y_box_1.setVisible(self.kind_of_profile_y<2)
        self.kind_of_profile_y_box_1_1.setVisible(self.kind_of_profile_y==0)
        self.kind_of_profile_y_box_1_2.setVisible(self.kind_of_profile_y==1)
        self.kind_of_profile_y_box_2.setVisible(self.kind_of_profile_y==2)
        self.kind_of_profile_y_box_2_1.setVisible(self.kind_of_profile_y==2 and self.renormalize_y==1)

    def calculate_heigth_profile_ni(self):
        self.calculate_heigth_profile(not_interactive_mode=True)

    def calculate_heigth_profile(self, not_interactive_mode=False):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            #### LENGTH

            if self.kind_of_profile_y == 2:
                combination = "E"

                if self.delimiter_y == 1:
                    profile_1D_y_x, profile_1D_y_y = numpy.loadtxt(self.heigth_profile_1D_file_name_y, delimiter='\t', unpack=True)
                else:
                    profile_1D_y_x, profile_1D_y_y = numpy.loadtxt(self.heigth_profile_1D_file_name_y, unpack=True)

                profile_1D_y_x *= self.conversion_factor_y_x
                profile_1D_y_y *= self.conversion_factor_y_y

                if self.renormalize_y == 0:
                    rms_y = None
                else:
                    if self.error_type_y == profiles_simulation.FIGURE_ERROR:
                        rms_y = self.rms_y*1e-7 # from nm to cm
                    else:
                        rms_y = self.rms_y*1e-6 # from urad to rad
            else:
                if self.kind_of_profile_y == 0: combination = "F"
                else: combination = "G"

                profile_1D_y_x = None
                profile_1D_y_y = None

                if self.error_type_y == profiles_simulation.FIGURE_ERROR:
                    rms_y = self.rms_y*1e-7 # from nm to cm
                else:
                    rms_y = self.rms_y*1e-6 # from urad to rad

            #### WIDTH

            if self.kind_of_profile_x == 2:
                combination += "E"

                if self.delimiter_x == 1:
                    profile_1D_x_x, profile_1D_x_y = numpy.loadtxt(self.heigth_profile_1D_file_name_x, delimiter='\t', unpack=True)
                else:
                    profile_1D_x_x, profile_1D_x_y = numpy.loadtxt(self.heigth_profile_1D_file_name_x, unpack=True)

                profile_1D_x_x *= self.conversion_factor_x_x
                profile_1D_x_y *= self.conversion_factor_x_y

                if self.renormalize_x == 0:
                    rms_x = None
                else:
                    if self.error_type_x == profiles_simulation.FIGURE_ERROR:
                        rms_x = self.rms_x*1e-7 # from nm to cm
                    else:
                        rms_x = self.rms_x*1e-6 # from urad to rad

            else:
                profile_1D_x_x = None
                profile_1D_x_y = None

                if self.kind_of_profile_x == 0: combination += "F"
                else: combination += "G"

                if self.error_type_x == profiles_simulation.FIGURE_ERROR:
                    rms_x = self.rms_x*1e-7 # from nm to cm
                else:
                    rms_x = self.rms_x*1e-6 # from urad to rad

            xx, yy, zz = profiles_simulation.simulate_profile_2D(combination = combination,
                                                                 mirror_length = self.dimension_y,
                                                                 step_l = self.step_y,
                                                                 random_seed_l = self.montecarlo_seed_y,
                                                                 error_type_l = self.error_type_y,
                                                                 rms_l = rms_y,
                                                                 power_law_exponent_beta_l = self.power_law_exponent_beta_y,
                                                                 correlation_length_l = self.correlation_length_y,
                                                                 x_l = profile_1D_y_x,
                                                                 y_l = profile_1D_y_y,
                                                                 mirror_width = self.dimension_x,
                                                                 step_w = self.step_x,
                                                                 random_seed_w = self.montecarlo_seed_x,
                                                                 error_type_w = self.error_type_x,
                                                                 rms_w = rms_x,
                                                                 power_law_exponent_beta_w = self.power_law_exponent_beta_x,
                                                                 correlation_length_w = self.correlation_length_x,
                                                                 x_w = profile_1D_x_x,
                                                                 y_w = profile_1D_x_y)
            self.xx = xx
            self.yy = yy
            self.zz = zz # in cm

            self.axis.clear()

            x_to_plot, y_to_plot = numpy.meshgrid(xx, yy)
            z_to_plot = zz*1e7 #nm

            self.axis.plot_surface(x_to_plot, y_to_plot, z_to_plot,
                                   rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            slope, sloperms = ST.slopes(zz.T, xx, yy)

            title = ' Slope error rms in X direction: %f $\mu$rad' % (sloperms[0]*1e6) + '\n' + \
                    ' Slope error rms in Y direction: %f $\mu$rad' % (sloperms[1]*1e6)
            self.axis.set_xlabel("X (cm)")
            self.axis.set_ylabel("Y (cm)")
            self.axis.set_zlabel("Z (nm)")

            self.axis.set_title(title)
            self.axis.mouse_init()

            if not not_interactive_mode:
                self.figure_canvas.draw()

                QMessageBox.information(self, "QMessageBox.information()",
                                        "Height Profile calculated: if the result is satisfactory,\nclick \'Generate Height Profile File\' to complete the operation ",
                                        QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)
            #raise exception

    def generate_heigth_profile_file_ni(self):
        self.generate_heigth_profile_file(not_interactive_mode=True)

    def generate_heigth_profile_file(self, not_interactive_mode=False):
        if not self.zz is None and not self.yy is None and not self.xx is None:
            try:
                congruence.checkDir(self.heigth_profile_file_name)

                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                ST.write_shadow_surface(self.zz, self.xx, self.yy, outFile=congruence.checkFileName(self.heigth_profile_file_name))
                if not not_interactive_mode:
                    QMessageBox.information(self, "QMessageBox.information()",
                                            "Height Profile file " + self.heigth_profile_file_name + " written on disk",
                                            QMessageBox.Ok)

                self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=self.heigth_profile_file_name,
                                                                      error_profile_x_dim=self.dimension_x,
                                                                      error_profile_y_dim=self.dimension_y))
            except Exception as exception:
                QMessageBox.critical(self, "Error",
                                     exception.args[0],
                                     QMessageBox.Ok)

    def call_reset_settings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass

    def check_fields(self):
        if self.kind_of_profile_y < 2:
            self.dimension_y = congruence.checkStrictlyPositiveNumber(self.dimension_y, "Dimension Y")
            self.step_y = congruence.checkStrictlyPositiveNumber(self.step_y, "Step Y")
            if self.kind_of_profile_x == 0: self.power_law_exponent_beta_y = congruence.checkPositiveNumber(self.power_law_exponent_beta_y, "Beta Value Y")
            if self.kind_of_profile_y == 1: self.correlation_length_y = congruence.checkStrictlyPositiveNumber(self.correlation_length_y, "Correlation Length Y")
            self.rms_y = congruence.checkPositiveNumber(self.rms_y, "Rms Y")
            self.montecarlo_seed_y = congruence.checkPositiveNumber(self.montecarlo_seed_y, "Monte Carlo initial seed y")
        else:
            congruence.checkFile(self.heigth_profile_1D_file_name_y)
            self.conversion_factor_y_x = congruence.checkStrictlyPositiveNumber(self.conversion_factor_y_x, "Conversion from user units to cm (Abscissa)")
            self.conversion_factor_y_y = congruence.checkStrictlyPositiveNumber(self.conversion_factor_y_y, "Conversion from user units to cm (Height Profile Values)")
            if self.renormalize_y == 1:
                self.rms_y = congruence.checkPositiveNumber(self.rms_y, "Rms Y")

        if self.kind_of_profile_x < 2:
            self.dimension_x = congruence.checkStrictlyPositiveNumber(self.dimension_x, "Dimension X")
            self.step_x = congruence.checkStrictlyPositiveNumber(self.step_x, "Step X")
            if self.kind_of_profile_x == 0: self.power_law_exponent_beta_x = congruence.checkPositiveNumber(self.power_law_exponent_beta_x, "Beta Value X")
            if self.kind_of_profile_x == 1: self.correlation_length_x = congruence.checkStrictlyPositiveNumber(self.correlation_length_x, "Correlation Length X")
            self.rms_x = congruence.checkPositiveNumber(self.rms_x, "Rms X")
            self.montecarlo_seed_x = congruence.checkPositiveNumber(self.montecarlo_seed_x, "Monte Carlo initial seed X")
        else:
            congruence.checkFile(self.heigth_profile_1D_file_name_x)
            self.conversion_factor_x_x = congruence.checkStrictlyPositiveNumber(self.conversion_factor_x_x, "Conversion from user units to cm (Abscissa)")
            self.conversion_factor_x_y = congruence.checkStrictlyPositiveNumber(self.conversion_factor_x_y, "Conversion from user units to cm (Height Profile Values)")
            if self.renormalize_x == 1:
                self.rms_x = congruence.checkPositiveNumber(self.rms_x, "Rms X")

        congruence.checkDir(self.heigth_profile_file_name)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def selectFile1D_X(self):
        self.le_heigth_profile_1D_file_name_x.setText(oasysgui.selectFileFromDialog(self, self.heigth_profile_1D_file_name_x, "Select 1D Height Profile File", file_extension_filter="*.dat; *.txt"))

    def selectFile1D_Y(self):
        self.le_heigth_profile_1D_file_name_y.setText(oasysgui.selectFileFromDialog(self, self.heigth_profile_1D_file_name_y, "Select 1D Height Profile File", file_extension_filter="*.dat; *.txt"))

    def selectFile(self):
        self.le_heigth_profile_file_name.setText(oasysgui.selectFileFromDialog(self, self.heigth_profile_file_name, "Select Output File", file_extension_filter="*.dat"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWheight_profile_simulator()
    w.show()
    app.exec()
    w.saveSettings()