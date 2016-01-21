import sys
import numpy
from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from Shadow import ShadowTools as ST
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui import ow_automatic_element

from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow

class FocNew(ow_automatic_element.AutomaticElement):

    name = "FocNew"
    description = "Shadow: FocNew"
    icon = "icons/focnew.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 4
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 675

    want_main_area=1
    want_control_area = 1

    input_beam=None

    mode = Setting(0)
    center_x = Setting(0.0)
    center_z = Setting(0.0)

    y_range=Setting(0)
    y_range_min=Setting(-10.0)
    y_range_max=Setting(10.0)
    y_npoints=Setting(1001)

    plot_canvas_x=None
    plot_canvas_z=None
    plot_canvas_t=None

    def __init__(self, show_automatic_box=True):
        super().__init__()

        general_box = oasysgui.widgetBox(self.controlArea, "General Settings", addSpace=True, orientation="vertical", width=410, height=250)

        gui.comboBox(general_box, self, "mode", label="Mode", labelWidth=250,
                                     items=["Center at Origin",
                                            "Center at Baricenter",
                                            "Define Center..."],
                                     callback=self.set_Center, sendSelectedValue=False, orientation="horizontal")

        self.center_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=390, height=100)
        self.center_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=390, height=100)

        gui.separator(self.center_box)

        self.le_center_x = oasysgui.lineEdit(self.center_box, self, "center_x", "Center X", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_center_z = oasysgui.lineEdit(self.center_box, self, "center_z", "Center Z", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_Center()

        gui.comboBox(general_box, self, "y_range", label="Y Range",labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_YRange, sendSelectedValue=False, orientation="horizontal")

        self.yrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=390, height=100)
        self.yrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=390, height=100)

        self.le_y_range_min = oasysgui.lineEdit(self.yrange_box, self, "y_range_min", "Y min", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_y_range_max = oasysgui.lineEdit(self.yrange_box, self, "y_range_max", "Y max", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "y_npoints", "Points", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_YRange()

        gui.separator(self.controlArea, height=300)

        gui.button(self.controlArea, self, "Calculate", callback=self.calculate, height=45)

        tabs_setting = gui.tabWidget(self.mainArea)
        tabs_setting.setFixedHeight(self.IMAGE_HEIGHT+5)
        tabs_setting.setFixedWidth(self.IMAGE_WIDTH)

        tab_info = oasysgui.createTabPage(tabs_setting, "Focnew Info")
        tab_scan = oasysgui.createTabPage(tabs_setting, "Focnew Scan")

        self.focnewInfo = QtGui.QTextEdit()
        self.focnewInfo.setReadOnly(True)
        self.focnewInfo.setMaximumHeight(self.IMAGE_HEIGHT-35)

        info_box = oasysgui.widgetBox(tab_info, "", addSpace=True, orientation="horizontal", height = self.IMAGE_HEIGHT-20, width = self.IMAGE_WIDTH-20)
        info_box.layout().addWidget(self.focnewInfo)

        self.image_box = gui.widgetBox(tab_scan, "Scan", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT-30)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH-20)

    def after_change_workspace_units(self):
        label = self.le_center_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_center_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_y_range_min.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_y_range_max.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def set_Center(self):
        self.center_box.setVisible(self.mode == 2)
        self.center_box_empty.setVisible(self.mode < 2)

    def set_YRange(self):
        self.yrange_box.setVisible(self.y_range == 1)
        self.yrange_box_empty.setVisible(self.y_range == 0)

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                if self.is_automatic_run:
                    self.calculate()
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def calculate(self):
        if ShadowCongruence.checkEmptyBeam(self.input_beam):
            if ShadowCongruence.checkGoodBeam(self.input_beam):
                if self.mode==2:
                    center=[self.center_x, self.center_z]
                else:
                    center=[0.0, 0.0]

                if self.y_range == 1:
                    if self.y_range_min >= self.y_range_max:
                        raise Exception("Y range min cannot be greater or than Y range max")

                ticket = ST.focnew(self.input_beam._beam, mode=self.mode, center=center)

                self.focnewInfo.setText(ticket["text"])

                if self.plot_canvas_x is None:
                    self.plot_canvas_x = PlotWindow(roi=False, control=False, position=False, plugins=False)
                    self.plot_canvas_x.setDefaultPlotLines(True)
                    self.plot_canvas_x.setActiveCurveColor(color='blue')
                    self.plot_canvas_x.setDrawModeEnabled(False)
                    self.plot_canvas_x.setZoomModeEnabled(False)
                    self.plot_canvas_x.toolBar.setVisible(False)

                    self.plot_canvas_z = PlotWindow(roi=False, control=False, position=False, plugins=False)
                    self.plot_canvas_z.setDefaultPlotLines(True)
                    self.plot_canvas_z.setActiveCurveColor(color='red')
                    self.plot_canvas_z.setDrawModeEnabled(False)
                    self.plot_canvas_z.setZoomModeEnabled(False)
                    self.plot_canvas_z.toolBar.setVisible(False)

                    self.plot_canvas_t = PlotWindow(roi=False, control=False, position=False, plugins=False)
                    self.plot_canvas_t.setDefaultPlotLines(True)
                    self.plot_canvas_t.setActiveCurveColor(color='green')
                    self.plot_canvas_t.setDrawModeEnabled(False)
                    self.plot_canvas_t.setZoomModeEnabled(False)
                    self.plot_canvas_t.toolBar.setVisible(False)

                    gridLayout = QtGui.QGridLayout()

                    gridLayout.addWidget(self.plot_canvas_x, 0, 0)
                    gridLayout.addWidget(self.plot_canvas_z, 0, 1)
                    gridLayout.addWidget(self.plot_canvas_t, 1, 0)

                    widget = QtGui.QWidget()
                    widget.setLayout(gridLayout)

                    self.image_box.layout().addWidget(widget)

                if self.y_range == 0:
                    y = numpy.linspace(-10.0, 10.0, 1001)
                else:
                    y = numpy.linspace(self.y_range_min, self.y_range_max, self.y_npoints)

                pos = [0.25, 0.15, 0.7, 0.75]

                self.plot_canvas_x.addCurve(y, 2.35*ST.focnew_scan(ticket["AX"]*ShadowPlot.get_factor(0, self.workspace_units_to_cm), y), "x (tangential)", symbol='', color="blue", replace=True) #'+', '^', ','
                self.plot_canvas_x._plot.graph.ax.get_yaxis().get_major_formatter().set_useOffset(True)
                self.plot_canvas_x._plot.graph.ax.get_yaxis().get_major_formatter().set_scientific(True)
                self.plot_canvas_x._plot.graph.ax.set_position(pos)
                self.plot_canvas_x._plot.graph.ax2.set_position(pos)
                self.plot_canvas_x.setGraphXLabel("Y [" + self.workspace_units_label + "]")
                self.plot_canvas_x.setGraphYLabel("2.35*<X> [$\mu$m]")
                self.plot_canvas_x._plot.graph.ax.set_title("X (Tangential)", horizontalalignment='left')
                self.plot_canvas_x.replot()

                self.plot_canvas_z.addCurve(y, 2.35*ST.focnew_scan(ticket["AZ"]*ShadowPlot.get_factor(1, self.workspace_units_to_cm), y), "z (sagittal)", symbol='', color="red", replace=False) #'+', '^', ','
                self.plot_canvas_z._plot.graph.ax.get_yaxis().get_major_formatter().set_useOffset(True)
                self.plot_canvas_z._plot.graph.ax.get_yaxis().get_major_formatter().set_scientific(True)
                self.plot_canvas_z._plot.graph.ax.set_position(pos)
                self.plot_canvas_z._plot.graph.ax2.set_position(pos)
                self.plot_canvas_z.setGraphXLabel("Y [" + self.workspace_units_label + "]")
                self.plot_canvas_z.setGraphYLabel("2.35*<Z> [$\mu$m]")
                self.plot_canvas_z._plot.graph.ax.set_title("Z (Sagittal)", horizontalalignment='left')
                self.plot_canvas_z.replot()

                self.plot_canvas_t.addCurve(y, 2.35*ST.focnew_scan(ticket["AT"]*ShadowPlot.get_factor(0, self.workspace_units_to_cm), y), "combined x,z", symbol='', color="green", replace=True) #'+', '^', ','
                self.plot_canvas_t._plot.graph.ax.get_yaxis().get_major_formatter().set_useOffset(True)
                self.plot_canvas_t._plot.graph.ax.get_yaxis().get_major_formatter().set_scientific(True)
                self.plot_canvas_t._plot.graph.ax.set_position(pos)
                self.plot_canvas_t._plot.graph.ax2.set_position(pos)
                self.plot_canvas_t.setGraphXLabel("Y [" + self.workspace_units_label + "]")
                self.plot_canvas_t.setGraphYLabel("2.35*<X,Z> [$\mu$m]")
                self.plot_canvas_t._plot.graph.ax.set_title("X,Z (Combined)", horizontalalignment='left')
                self.plot_canvas_t.replot()


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FocNew()
    w.show()
    app.exec()
    w.saveSettings()
