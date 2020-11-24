import sys
import visa
import time
from PyQt5.QtWidgets import QDialog, QApplication
from keithley2304 import *
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


keithley = KeithleyStatus()
global rm
rm = visa.ResourceManager()


def createList(num):
    listData = []
    while num > 0:
        listData.append(0)
        num = num - 1
    return listData


def convertListToFloat(listData, num):
    dataFloat = []
    i = 0
    while i < num:
        dataFloat.append(float(listData[i]))
        i += 1
    return dataFloat


class MyForm(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        # connect to functions
        self.ui.pushButtonConnect.clicked.connect(self.GPIBconnect)
        self.ui.pushButtonDisconnect.clicked.connect(self.GPIBdisconnect)
        self.ui.pushButtonON.clicked.connect(self.outputOn)
        self.ui.pushButtonOFF.clicked.connect(self.outputOff)
        self.ui.pushButtonStartRecord.clicked.connect(self.recordStart)
        self.ui.pushButtonStopRecord.clicked.connect(self.recordStop)
        self.ui.checkBoxTimestampName.stateChanged.connect(self.timeName)
        # end functions
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
            self.ui.lineEditVoltage.setText('3.7')
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
                MODEL_2304.write(':SOURce:VOLTage:LEVel:IMMediate:AMPLitude %G' % (keithley.voltage))
                MODEL_2304.write(':OUTPut:STATe %d' % (0))
                MODEL_2304.write(':SOURce:CURRent:LIMit:VALue ' + str(keithley.currentLimit) + '')
                # MODEL_2304.write(':SENSe[1]:NPLCycles ' + str(keithley.interCycle) + '')
                MODEL_2304.write(':SENSe[1]:NPLCycles 0.01')
                MODEL_2304.write(':DISPlay:ENABle ON')
                keithley.connected = 1
                self.ui.labelConnectStatus.setText("Connected successfully to Keithley 2304")
            except:
                self.ui.labelConnectStatus.setText("Error to connect Keithley 2304")

    def GPIBdisconnect(self):
        try:
            MODEL_2304.write(':DISPlay:ENABle ON')
            rm.close()
            keithley.connected = 0
            self.ui.labelConnectStatus.setText("Disconnected successfully from Keithley 2304")
        except:
            self.ui.labelConnectStatus.setText("Error to disconnect from Keithley 2304")

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
        if keithley.connected == 0 or keithley.outputStatus == 0:
            self.ui.labelRecordStatus.setText("Please connect to Keithley and On Output")
            return

        global sampleNumber
        if len(self.ui.lineEditPeriod.text()) == 0:
            self.ui.lineEditPeriod.setText('600')
            sampleNumber = 600
        else:
            sampleNumber = int(int(self.ui.lineEditPeriod.text()) * 1000 / 35)
        try:
            MODEL_2304.write(':OUTPut:STATe %d' % (1))
            MODEL_2304.write(':DISPlay:ENABle OFF')
            curr_data = createList(sampleNumber)
            self.ui.labelRecordStatus.setText("Recording...........")
            i = 0
            start = time.time_ns()
            while (i < sampleNumber):
                # curr_data[i] = MODEL_2304.query(':READ?')
                curr_data[i] = MODEL_2304.query(':MEASure:CURRent?')
                i += 1
            stop = time.time_ns()
            total_time = str(int((stop - start) / 1000000000))
        except:
            self.ui.labelRecordStatus.setText("Error while recording")
            return
        # writing file
        now = datetime.now()
        dt_string = now.strftime("%Y_%m_%d_%H_%M_%S") + '.txt'
        save_path = 'D:/OneDrive/Python/Keithley/Log'
        filename = os.path.join(save_path, self.ui.lineEditFileName.text() + '_' + dt_string)
        try:
            f = open(filename, "w")
            i = 0
            while (i < sampleNumber):
                f.write(str(curr_data[i]))
                i = i + 1
        except:
            self.ui.labelRecordStatus.setText("Error while writing data file")
        finally:
            f.close()
        self.ui.labelRecordStatus.setText("Congratulation! Finish Recording in " + total_time + ' s')

        # Caculate Results
        curr_data_float = convertListToFloat(curr_data, sampleNumber)
        avarCurrent = sum(curr_data_float) * 1000 / sampleNumber
        maxCurrent = max(curr_data_float) * 1000
        minCurrent = min(curr_data_float) * 1000
        batLifeHours = round(1250 / avarCurrent, 2)
        total_results = sampleNumber
        self.ui.lineEditTotalTime.setText(total_time)
        self.ui.lineEditTotalResults.setText(str(total_results))
        self.ui.lineEditMinCurrent.setText(str(round(minCurrent, 2)))
        self.ui.lineEditMaxCurrent.setText(str(round(maxCurrent, 2)))
        self.ui.lineEditAvarCurrent.setText(str(round(avarCurrent, 2)))
        self.ui.lineEditBatLife.setText(str(batLifeHours))

        # Plot chart
        pass

    def recordStop(self):
        pass

    def timeName(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MyForm()
    w.show()
    sys.exit(app.exec_())
