#
# uic_stdDutData.py - STDF Viewer
# 
# Author: noonchen - chennoon233@foxmail.com
# Created Date: December 20th 2020
# -----
# Last Modified: Thu Apr 15 2021
# Modified By: noonchen
# -----
# Copyright (c) 2021 noonchen
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#



# pyqt5
# from PyQt5 import QtCore, QtWidgets, QtGui
# from PyQt5.QtWidgets import QAbstractItemView, QApplication, QFileDialog
# from PyQt5.QtCore import pyqtSignal as Signal
# from deps.ui.stdfViewer_loadingUI import Ui_loadingUI
# from deps.ui.stdfViewer_dutDataUI import Ui_dutData
# pyside2
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtWidgets import QAbstractItemView, QApplication, QFileDialog
from PySide2.QtCore import Signal
from deps.ui.stdfViewer_loadingUI_side2 import Ui_loadingUI
from deps.ui.stdfViewer_dutDataUI_side2 import Ui_dutData
# pyside6
# from PySide6 import QtCore, QtWidgets, QtGui
# from PySide6.QtWidgets import QAbstractItemView, QApplication, QFileDialog
# from PySide6.QtCore import Signal
# from deps.ui.stdfViewer_loadingUI_side6 import Ui_loadingUI
# from deps.ui.stdfViewer_dutDataUI_side6 import Ui_dutData



class signal(QtCore.QObject):
    hideSignal = Signal()
    
    

class DutDataReader(QtWidgets.QWidget):
    def __init__(self, parent, selectedDutIndex, styleDelegate):
        super().__init__()
        self.UI = Ui_loadingUI()
        self.UI.setupUi(self)
        self.parent = parent
        self.selectedDutIndex = selectedDutIndex      # selected indexes of dut info table
        self.sd = styleDelegate
                
        self.setWindowTitle("Reading DUT data")
        self.UI.progressBar.setFormat("%p%")
        self.stopFlag = False
        self.signal = signal()
        self.signal.hideSignal.connect(self.hide)
        
        self.show()
        self.start()
    
    
    def start(self):
        self.test_number_List = sorted([int(ele.split("\t")[0]) for ele in self.parent.completeTestList])
        self.total = len(self.test_number_List)
        dutInfo = self.parent.prepareDataForDUTSummary(headList=[], siteList=[], selectedDutIndex=self.selectedDutIndex)
        dutData = []
        dutStat = []
        dutFlagInfo = []
        for i, test_num in enumerate(self.test_number_List):
            if self.stopFlag: return

            dutData_perTest, stat_perTest, flagInfo_perTest = self.parent.prepareDataForDUTSummary(headList=[], siteList=[], selectedDutIndex=self.selectedDutIndex, test_num=test_num, exportTestFlag=True)
            dutData.append(dutData_perTest)
            dutStat.append(stat_perTest)
            dutFlagInfo.append(flagInfo_perTest)
            
            self.updateProgressBar(int(100 * (i+1) / self.total))
            QApplication.processEvents()    # force refresh UI to update progress bar
        self.UI.progressBar.setFormat("Filling table with data...")
        QApplication.processEvents()
        dutDataDisplayer(self, (dutInfo, dutData, dutStat, dutFlagInfo), self.sd, self.signal.hideSignal)
        self.close()
            
        
    def closeEvent(self, event):
        # close by clicking X
        self.stopFlag = True
        event.accept()
             
                    
    def updateProgressBar(self, num):
        self.UI.progressBar.setValue(num)
      
        
        
class dutDataDisplayer(QtWidgets.QDialog):
    def __init__(self, parent, content, styleDelegate, hideSignal):
        super().__init__()
        self.UI = Ui_dutData()
        self.UI.setupUi(self)
        self.parent = parent
        self.dutInfo, self.dutData, self.dutStat, self.dutFlagInfo = content
        self.sd = styleDelegate
        self.hideSignal = hideSignal
        
        self.UI.save.clicked.connect(self.onSave_csv)
        self.UI.save_xlsx.clicked.connect(self.onSave_xlsx)
        self.UI.close.clicked.connect(self.close)
        self.init_Table()
        self.parent.parent.updateStatus("Please wait for data filling in the table...")
        self.refresh_Table()
        self.hideSignal.emit()
        self.parent.parent.updateStatus("")
        self.exec_()
        
        
    def init_Table(self):
        self.tmodel = QtGui.QStandardItemModel()
        self.UI.tableView_dutData.setModel(self.tmodel)
        self.UI.tableView_dutData.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.UI.tableView_dutData.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)    
        self.sd.setParent(self.UI.tableView_dutData)
        self.UI.tableView_dutData.setItemDelegate(self.sd)    


    def refresh_Table(self):
        # clear
        self.tmodel.removeColumns(0, self.tmodel.columnCount())
        self.tmodel.removeRows(0, self.tmodel.rowCount())
        # header
        self.hh = ["Part ID", "Test Head", "Test Site", "Tests Executed", "Test Time", "Hardware Bin", "Software Bin", "DUT Flag"] + [tmp[0] for tmp in self.dutData]
        vh_base = ["Test Number", "HiLimit", "LoLimit", "Unit"]
        self.vh = vh_base + ["#%d"%(i+1) for i in range(len(self.dutInfo))]
        vh_len = len(vh_base)

        # append value
        # get dut pass/fail list
        statIndex = self.hh.index("DUT Flag")
        dutStatus = [True] * vh_len + [dutInfo_perDUT[statIndex].split(" ", 1)[0] != "Failed" for dutInfo_perDUT in self.dutInfo]
        for col_tuple in zip(*self.dutInfo):
            tmpCol = ["N/A"] * vh_len + list(col_tuple)
            qitemCol = []
            for i, (item, flag) in enumerate(zip(tmpCol, dutStatus)):
                qitem = QtGui.QStandardItem(item)
                qitem.setTextAlignment(QtCore.Qt.AlignCenter)
                qitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                if i < vh_len: qitem.setData(QtGui.QColor("#0F80FF7F"), QtCore.Qt.BackgroundRole)   # add bgcolor for non-data cell
                if not flag: 
                    qitem.setData(QtGui.QColor("#FFFFFF"), QtCore.Qt.ForegroundRole)
                    qitem.setData(QtGui.QColor("#CC0000"), QtCore.Qt.BackgroundRole)
                qitemCol.append(qitem)                        
            self.tmodel.appendColumn(qitemCol)
        
        for dataCol, statCol, flagInfoCol in zip(self.dutData, self.dutStat, self.dutFlagInfo):
            qitemCol = []
            for i, (item, stat, flagInfo) in enumerate(zip(dataCol, statCol, flagInfoCol)):    # remove 1st element: test name
                if i == 0: continue     # skip test name
                qitem = QtGui.QStandardItem(item)
                qitem.setTextAlignment(QtCore.Qt.AlignCenter)
                qitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                if stat == False:
                    qitem.setData(QtGui.QColor("#FFFFFF"), QtCore.Qt.ForegroundRole)
                    qitem.setData(QtGui.QColor("#CC0000"), QtCore.Qt.BackgroundRole)
                if flagInfo != "":
                    qitem.setToolTip(flagInfo)
                if i <= vh_len: qitem.setData(QtGui.QColor("#0F80FF7F"), QtCore.Qt.BackgroundRole)
                qitemCol.append(qitem)                        
            self.tmodel.appendColumn(qitemCol)
        
        self.tmodel.setHorizontalHeaderLabels(self.hh)
        self.tmodel.setVerticalHeaderLabels(self.vh)
        self.UI.tableView_dutData.horizontalHeader().setVisible(True)
        self.UI.tableView_dutData.verticalHeader().setVisible(True)        
        # resize cells
        header = self.UI.tableView_dutData.horizontalHeader()
        for column in range(header.model().columnCount()):
            header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeToContents)
        
        
    def onSave_csv(self):
        outPath, _ = QFileDialog.getSaveFileName(None, caption="Save Report As", filter="CSV file (*.csv)")
        if outPath:
            with open(outPath, "w") as f:
                f.write(",".join([""] + self.hh)+"\n")
                for row in range(self.tmodel.rowCount()):
                    rowDataList = [self.tmodel.data(self.tmodel.index(row, col)) for col in range(self.tmodel.columnCount())]
                    f.write(",".join([self.vh[row]] + rowDataList)+"\n")
            msgbox = QtWidgets.QMessageBox(None)
            msgbox.setText("Completed")
            msgbox.setInformativeText("File is saved in %s"%outPath)
            revealBtn = msgbox.addButton(" Reveal in folder ", QtWidgets.QMessageBox.ApplyRole)
            openBtn = msgbox.addButton("Open...", QtWidgets.QMessageBox.ActionRole)
            okBtn = msgbox.addButton("OK", QtWidgets.QMessageBox.YesRole)
            msgbox.setDefaultButton(okBtn)
            msgbox.exec_()
            if msgbox.clickedButton() == revealBtn:
                self.revealFile(outPath)
            elif msgbox.clickedButton() == openBtn:
                self.openFileInOS(outPath)
            
    
    def onSave_xlsx(self):
        outPath, _ = QFileDialog.getSaveFileName(None, caption="Save Report As", filter="Excel file (*.xlsx)")
        
        if outPath:
            def write_row(sheet, row, scol, dataL, styleList):
                # write as number in default, otherwise as string
                for i in range(len(dataL)):
                    try:
                        sheet.write_number(row, scol+i, float(dataL[i]), styleList[i])
                    except (TypeError, ValueError):
                        sheet.write_string(row, scol+i, dataL[i], styleList[i])
            
            import xlsxwriter as xw
            with xw.Workbook(outPath) as wb:
                noStyle = wb.add_format({"align": "center"})
                failStyle = wb.add_format({"bg_color": "#CC0000", "bold": True, "align": "center"})
                
                sheetOBJ = wb.add_worksheet("DUT Data")
                colHeader = [""] + self.hh
                write_row(sheetOBJ, 0, 0, colHeader, [noStyle]*len(colHeader))
                col_width = [len(s) for s in colHeader]     # get max string len to adjust cell width
                
                for row in range(self.tmodel.rowCount()):
                    rowDataList = [self.vh[row]]    # row header, #num
                    rowStyleList = [noStyle]        # no style for row header
                    if len(self.vh[row]) > col_width[0]: col_width[0] = len(self.vh[row])
                    
                    for col in range(self.tmodel.columnCount()):
                        qitem = self.tmodel.item(row, col)
                        data = qitem.text()
                        color = qitem.background().color().name().lower()
                        rowDataList.append(data)
                        rowStyleList.append(failStyle if color=="#cc0000" else noStyle)
                        if len(data) > col_width[col+1]: col_width[col+1] = len(data)
                    write_row(sheetOBJ, row + 1, 0, rowDataList, rowStyleList)
                [sheetOBJ.set_column(col, col, strLen * 1.1) for col, strLen in enumerate(col_width)]
                
            msgbox = QtWidgets.QMessageBox(None)
            msgbox.setText("Completed")
            msgbox.setInformativeText("File is saved in %s"%outPath)
            revealBtn = msgbox.addButton(" Reveal in folder ", QtWidgets.QMessageBox.ApplyRole)
            openBtn = msgbox.addButton("Open...", QtWidgets.QMessageBox.ActionRole)
            okBtn = msgbox.addButton("OK", QtWidgets.QMessageBox.YesRole)
            msgbox.setDefaultButton(okBtn)
            msgbox.exec_()
            if msgbox.clickedButton() == revealBtn:
                self.revealFile(outPath)
            elif msgbox.clickedButton() == openBtn:
                self.openFileInOS(outPath)
            
    
    def openFileInOS(self, filepath):
        # https://stackoverflow.com/a/435669
        import subprocess, os, platform
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(filepath)
        else:                                   # linux variants
            subprocess.call(('xdg-open', filepath))        
            

    def revealFile(self, filepath):
        import subprocess, os, platform
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', '-R', filepath))
        elif platform.system() == 'Windows':    # Windows
            subprocess.Popen(f'explorer /select,{filepath}')
        else:                                   # linux variants
            subprocess.call(('xdg-open', os.path.dirname(filepath)))

    
    
