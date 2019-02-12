import sys

from fbs_runtime.application_context import ApplicationContext, cached_property
from matplotlib.backends.qt_compat import QtCore, QtWidgets, QtGui, is_pyqt5

from my_widgets import *

if is_pyqt5():
    pass
else:
    pass

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class AppContext(ApplicationContext):
    def run(self):
        self.window.show()
        return self.app.exec_()

    @cached_property
    def window(self):
        return ApplicationWindow()


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self._main = QtWidgets.QStackedWidget()
        # self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        self.setWindowTitle("UHSLC QC Software")
        self.setWindowIcon(QtGui.QIcon('uhslclogotext72_pfL_icon.ico'))
        self.resize(1837, 1200)

        # Create Screen objects
        self.start_screen = Start(self)
        self.second_screen = HelpScreen(self)
        self._main.addWidget(self.start_screen)
        self._main.addWidget(self.second_screen)

        self._main.setCurrentWidget(self.start_screen)

        self.start_screen.clicked.connect(lambda: self._main.setCurrentWidget(self.second_screen))
        self.second_screen.clicked.connect(lambda: self._main.setCurrentWidget(self.start_screen))

        self.setStatusTip("Permanent status bar")
        # Create an action in the menu bar that is later on assigned to one of
        # the options (e.g. File, Edit, View etc) in the menu bar
        close_app = QtWidgets.QAction("&Exit", self)
        close_app.setShortcut("Ctrl+Q")
        # Show the tip in the status bar on hover
        close_app.setStatusTip('Leave the app')
        close_app.triggered.connect(self.close_application)

        open_help_menu = QtWidgets.QAction("&Instructions", self)
        open_help_menu.setShortcut("F1")
        open_help_menu.triggered.connect(self.start_screen.clicked.emit)
        # open_help_menu.triggered.connect(self.open_help_menu)

        open_file = QtWidgets.QAction("&Open", self)
        open_file.setShortcut("Ctrl+O")
        open_file.setStatusTip('Load a File')
        open_file.triggered.connect(self.file_open)

        self.statusBar()

        # Create dropwon menu
        main_menu = self.menuBar()

        # Add options to the menuBar
        file_menu = main_menu.addMenu('&File')
        help_menu = main_menu.addMenu('&Help')

        # Connect action with the option
        file_menu.addAction(open_file)
        file_menu.addAction(close_app)
        help_menu.addAction(open_help_menu)

    def file_open(self):
        filters = "s*.dat;; ts*.dat"
        if st.get_path(st.LOAD_KEY):
            path = st.get_path(st.LOAD_KEY)
        else:
            # path = "C:\\Users\\komar\\OneDrive\\Desktop\\monp"
            path = os.path.expanduser('~')
        file_name = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open File', path, filters)
        # file_name = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open File', filter)

        # Validating files selected, put this into a function
        if self.is_valid_files(file_name):
            pass
        else:
            self.warning_dialog()
            return

        try:
            # in_file = open(name[0],'r')
            self.month_count = len(file_name[0])
            print('FILENAME', file_name[0])
            self.start_screen.sens_objects = {}  # Collection of Sensor objects for station for one month

            comb_data = np.ndarray(
                0)  # ndarray of concatonated data for all the months that were loaded for a particular station
            comb_time_col = []  # combined rows of all time columns for all the months that were loaded for a
            # particular station
            de = []  # List od DataExtractor objects for each month loaded which hold all the necessary data
            line_count = []  # array for the number of lines (excluding headers and 9999s)for each month that were
            # loaded for a particular station. Added as an attribute to respective sensor objects

            # clear residual figure on new file load
            self.start_screen.residual_canvas.figure.clf()
            self.start_screen.residual_canvas.draw()

            # Create DataExtractor for each month that was loaded into program
            for j in range(self.month_count):
                de.append(DataExtractor(file_name[0][j]))
            # The reason de[0] is used is because the program only allows to load
            # multiple months for the same station, so the station name will be the same
            station_name = de[0].headers[0][:6]
            my_station = Station(station_name, [0, 1])

            # Cycle through all the Sensors
            # The reason de[0] is used is because the program only allows to load
            # multiple months for the same station, so the station sensors should be the same
            # But what if a sensor is ever added to a station??? Check with fee it this ever happens
            for i in range(len(de[0].sensor_ids)):
                # cycle through all the months loaded (ie. DataExtractor objects)
                for d in de:
                    comb_data = np.append(comb_data, d.data_all[de[0].sensor_ids[i][-3:]])
                    comb_time_col = comb_time_col + d.infos_time_col[de[0].sensor_ids[i][-3:]]
                    line_count.append(len(d.infos_time_col[de[0].sensor_ids[i][-3:]]))
                self.start_screen.sens_objects[de[0].sensor_ids[i][-3:]] = Sensor(my_station, de[0].frequencies[i],
                                                                                  de[-1].refs[i], de[0].sensor_ids[i],
                                                                                  de[0].init_dates[i], comb_data,
                                                                                  comb_time_col, de[0].headers[i])
                self.start_screen.sens_objects[
                    de[0].sensor_ids[i][-3:]].line_num = line_count  # adding a line_num attribute for each sensor
                # Empty the combined data
                comb_time_col = []
                comb_data = np.ndarray(0)
                line_count = []

            self.start_screen.make_sensor_buttons(self.start_screen.sens_objects)


            self.sens_str = "PRD"
            self.data_flat = self.start_screen.sens_objects[self.sens_str].get_flat_data()
            self.time = self.start_screen.sens_objects[self.sens_str].get_time_vector()

            ## Set 9999s to NaN so they don't show up on the graph
            ## when initially plotted
            ## nans are converted back to 9999s when file is saved
            self.start_screen.lineEdit.setText(self.start_screen.sens_objects[self.sens_str].header)
            nines_ind = np.where(self.data_flat == 9999)
            self.data_flat[nines_ind] = float('nan')

            self.start_screen.plot(self.time, self.data_flat)

        except (FileNotFoundError, IndexError) as e:
            print('Error:', e)

    def warning_dialog(self):
        # choice = QtWidgets.QMessageBox.critical(self, 'Warning, wrong files selected',  "The data files selected do
        # not belong to the adjacent months and/or do not belong the same station. Please select valid files to
        # continue\nTST", QtWidgets.QMessageBox.Ok)
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle("ERROR!")
        msg_box.setText("Warning, wrong files selected")
        msg_box.setInformativeText(
            "The files need to belong to the adjacent months and the same station. Please select valid files to "
            "continue.")
        # msg_box.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard |
        # QtWidgets.QMessageBox.Cancel)
        msg_box.setDetailedText('''MAC:
        The files are loaded in order in which they were selected. Select files from the oldest to the youngest.\nWINDOWS:
        The order is determined by the file order in the File Explorer. The files should be sorted by name before selecting them.
        ''')
        msg_box.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()
        # if(choice == QtWidgets.QMessageBox.Yes):
        #     sys.exit()
        # else:
        #     pass

    def pairwise_diff(self, lst):
        diff = 0
        result = []
        for i in range(len(lst) - 1):
            # subtracting the alternate numbers
            diff = lst[i] - lst[i + 1]
            result.append(diff)
        return result

    def is_valid_files(self, files):
        dates = []
        names = []
        result = []
        # extract dates and station 4 letter codes for every file that was loaded
        for file in files[0]:
            if file[-8:-4].isdigit():
                dates.append(int(file[-8:-4]))
                # check if monp file or a TS file
                if file.split("/")[-1][0] == "s":
                    names.append(file.split("/")[-1][1:5])
                else:
                    names.append(file.split("/")[-1][0:4])
        # check the difference between all dates
        for val in self.pairwise_diff(dates):
            if val != -1 and val != -89:
                result.append(val)
        # check if the files selected are all from the same station
        if names[1:] != names[:-1]:
            return False

        return len(result) == 0

    def close_application(self):
        choice = QtWidgets.QMessageBox.question(self, 'Warning', "Are you sure you want to quit?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()
        else:
            pass


if __name__ == '__main__':
    appctxt = AppContext()
    exit_code = appctxt.run()
    sys.exit(exit_code)
