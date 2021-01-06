import sys
import pyvisa as visa
import time
import threading
import pathlib
from PyQt5.QtWidgets import QDialog, QApplication
from keithley2304 import *
from lineChart import *
from utilList import *
from datetime import datetime
import os.path


class KeithleyStatus:
    GPIBAddress = 0
    voltage = 0.0
    currentLimit = 0.0
    interCycle = 0.0
    connected = 0
    outputStatus = 0
    recording = 0

    def __init__(self):
        pass

# resource init
keithley = KeithleyStatus()
global rm
rm = visa.ResourceManager()

class recordThread(threading.Thread):
    def __init__(self, w):
        threading.Thread.__init__(self)
        self.w = w
    def run(self):
        print("Recording Thread in running!")
        global sampleNumber
        if len(w.ui.lineEditPeriod.text()) == 0:
            w.ui.lineEditPeriod.setText('600')
            sampleNumber = 600
        else:
            sampleNumber = int(int(w.ui.lineEditPeriod.text()) * 1000 / 31)
        try:
            MODEL_2304.write(':OUTPut:STATe %d' % (1))
            MODEL_2304.write(':DISPlay:ENABle OFF')
            # Config data output while executing READ? command
            MODEL_2304.write(':FORMart:CURRent?')
            # Change current range following the configuration
            w.change_current_range()
            curr_data = createList(sampleNumber)
            i = 0
            start = time.time_ns()
            while (i < sampleNumber):
                curr_data[i] = MODEL_2304.query(':READ?')
                #curr_data[i] = MODEL_2304.query(':MEAS:CURR?')
                i += 1
            stop = time.time_ns()
            total_time = str(int((stop - start) / 1000000000))
        except:
            w.ui.labelRecordStatus.setText("Error while recording")
            return

        # Caculate Results
        curr_data_float = convertListToFloat(curr_data, sampleNumber)
        avarCurrent = sum(curr_data_float) * 1000 / sampleNumber
        maxCurrent = max(curr_data_float) * 1000
        minCurrent = min(curr_data_float) * 1000
        if w.ui.comboBoxCurrentRange.currentText() == "500 mA":
            error_current = 0.002 * avarCurrent + 0.04
        else:
            error_current = 0.002 * avarCurrent + 0.4
        if avarCurrent != 0:
            batLifeHours = round(1250 / avarCurrent, 2)
        else:
            batLifeHours = 9999999
        total_results = sampleNumber
        w.ui.lineEditTotalTime.setText(total_time)
        w.ui.lineEditTotalResults.setText(str(total_results))
        w.ui.lineEditMinCurrent.setText(str(round(minCurrent, 2)))
        w.ui.lineEditMaxCurrent.setText(str(round(maxCurrent, 2)))
        w.ui.lineEditAvarCurrent.setText(str(round(avarCurrent, 2)) + '+-(' + str(round(error_current, 2)) + ')')
        w.ui.lineEditBatLife.setText(str(batLifeHours))

        # writing file
        now = datetime.now()
        dt_string = now.strftime("%Y_%m_%d_%H_%M_%S") + '.txt'
        nl_path = os.path.normpath(os.path.join(pathlib.Path().absolute(),"Log"))
        save_path = nl_path.replace("\\","/")
        filename = os.path.join(save_path, w.ui.lineEditFileName.text() + '_' + dt_string)
        try:
            f = open(filename, "w")
            i = 0
            while (i < sampleNumber):
                f.write(str(curr_data[i]))
                i = i + 1
        except:
            w.ui.labelRecordStatus.setText("Error while writing data file")
        finally:
            f.close()
        w.ui.labelRecordStatus.setText("Congratulation! Finish Recording in " + total_time + ' s')

        # Plot chart
        w.w = LineChartWindow()
        w.w.createLineChart(curr_data_float, sampleNumber)
        w.w.show()


class MyForm(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Ginno_Keithley()
        self.ui.setupUi(self)
        # connect to functions
        self.ui.pushButtonConnect.clicked.connect(self.GPIBconnect)
        self.ui.pushButtonSendConfig.clicked.connect(self.sendConfig)
        self.ui.pushButtonON.clicked.connect(self.outputOn)
        self.ui.pushButtonOFF.clicked.connect(self.outputOff)
        self.ui.pushButtonStartRecord.clicked.connect(self.recordStart)
        self.ui.pushButtonStopRecord.clicked.connect(self.recordStop)
        self.ui.comboBoxCurrentRange.currentIndexChanged.connect(self.change_current_range)
        # end functions
        self.w = LineChartWindow()
        self.show()

    # Check GPIB parameter
    def checkGPIBAddressParam(self):
        if len(self.ui.lineEditGPIBAddress.text()) == 0:
            self.ui.labelConnectStatus.setText("Please set an GPIB address!")
            return 0
        if int(self.ui.lineEditGPIBAddress.text()) > 32:
            self.ui.labelConnectStatus.setText("GPIB address can not bigger than 32!")
            return 0
        keithley.GPIBAddress = int(self.ui.lineEditGPIBAddress.text())
        return 1

    # Check Voltage Parameter
    def checkVoltageParam(self):
        if (len(self.ui.lineEditVoltage.text()) == 0) or (float(self.ui.lineEditVoltage.text()) > 20):
            self.ui.lineEditVoltage.setText('3.8')
        keithley.voltage = float(self.ui.lineEditVoltage.text())
        return 1

    # Check current limit parameter
    def checkCurrLimitParam(self):
        if (len(self.ui.lineEditCurrLimit.text())) == 0:
            self.ui.lineEditCurrLimit.setText('5.0')
        keithley.currentLimit = float(self.ui.lineEditCurrLimit.text())
        return 1

    # Check Integration Cycle
    def checkInterCycle(self):
        if ((len(self.ui.lineEditIntergationCycle.text())) == 0) or \
                (float(self.ui.lineEditIntergationCycle.text()) < 0.01) or \
                (float(self.ui.lineEditIntergationCycle.text()) > 10):
            self.ui.lineEditIntergationCycle.setText('0.01')
        keithley.interCycle = float(self.ui.lineEditIntergationCycle.text())
        return 1

    def GPIBconnect(self):
        if self.checkGPIBAddressParam() and \
                self.checkVoltageParam() and \
                self.checkInterCycle() and \
                self.checkCurrLimitParam():
            try:
                global MODEL_2304
                MODEL_2304 = rm.open_resource('GPIB0::' + str(keithley.GPIBAddress) + '::INSTR')
                MODEL_2304.write(':DISPlay:ENABle ON')
                keithley.connected = 1
                self.ui.labelConnectStatus.setText("Connected successfully to Keithley 2304")
            except:
                self.ui.labelConnectStatus.setText("Error to connect Keithley 2304")

    def sendConfig(self):
        try:
            if keithley.connected == 0 or keithley.outputStatus == 1:
                self.ui.labelConnectStatus.setText("Please connect and turn OFF Keithley!!!")
                return
            MODEL_2304.write(':SOURce:VOLTage ' + str(keithley.voltage))
            MODEL_2304.write(':OUTPut:STATe %d' % (0))
            MODEL_2304.write(':SOURce:CURRent ' + str(keithley.currentLimit))
            MODEL_2304.write(':SENSe:NPLCycles ' + str(keithley.interCycle))
            MODEL_2304.write(':SENSe:AVERage 1')
            MODEL_2304.write(':DISPlay:ENABle ON')
            self.ui.labelConnectStatus.setText("Final send config to Keithley 2304")
        except:
            self.ui.labelConnectStatus.setText("Error to send config to Keithley 2304")

    def outputOn(self):
        if keithley.connected:
            try:
                MODEL_2304.write(':OUTPut:STATe %d' % (1))
                keithley.outputStatus = 1
                self.ui.labelConnectStatus.setText("Output ON")
            except:
                self.ui.labelConnectStatus.setText("Error while Output ON")

    def outputOff(self):
        if keithley.connected:
            try:
                MODEL_2304.write(':OUTPut:STATe %d' % (0))
                keithley.outputStatus = 0
                self.ui.labelConnectStatus.setText("Output OFF")
            except:
                self.ui.labelConnectStatus.setText("Error while Output OFF")
        pass

    def recordStart(self):
        if keithley.connected == 0:
            self.ui.labelRecordStatus.setText("Please connect to Keithley and On Output")
            return
        self.ui.labelRecordStatus.setText("Recording...........")
        # run record Thread
        newThread = recordThread(self)
        newThread.run()

    def recordStop(self):
        pass

    def change_current_range(self):
        if keithley.connected == 0:
            self.ui.labelConnectStatus.setText("Please connect to Keithley!!!")
            return
        if self.ui.comboBoxCurrentRange.currentText() == "5 A":
            print ("Change current range to 5 A")
            MODEL_2304.write(':SENSe:CURRent:RANGe MAXimum')
            pass
        if self.ui.comboBoxCurrentRange.currentText() == "500 mA":
            print("Change current range to 500 mA")
            MODEL_2304.write(':SENSe:CURRent:RANGe MINimum')
            pass
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MyForm()
    w.setWindowTitle("Ginno Keithley Tool")
    w.show()
    sys.exit(app.exec_())
