from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *

class LineChartWindow (QMainWindow):
    def __init__(self):
        super().__init__()
        # draw line chart
        self.setWindowTitle("Current Chart")
        self.setGeometry(100, 100, 680, 500)
    # Create a line chart
    def createLineChart(self, dataList, number):
        series = QLineSeries(self)
        i = 0
        while i < number:
            series.append(i*31, 1000*dataList[i])
            i += 1

        chart = QChart()

        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.axisX().setTitleText("ms")
        chart.axisY().setTitleText("mA")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Current vs Time")

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)
        self.setCentralWidget(chartview)