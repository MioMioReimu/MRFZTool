# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import subprocess

MACHINE_ID = None

class InputCardDialog(QDialog):
	def __init__(self, parent=None):
		super(InputCardDialog, self).__init__(parent)

		mainLayout = QVBoxLayout()
		self.setLayout(mainLayout)

class AddTaskDialog(QDialog):
	def __init__(self, parent=None):
		super(AddTaskDialog, self).__init__(parent)

		mainLayout = QVBoxLayout()

		self.setWindowTitle("添加任务")
		self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

		inputLayout = QHBoxLayout()
		self.setLayout(mainLayout)
		mainLayout.addLayout(inputLayout)
		mainLayout.addSpacing(6)

		btnLayout = QHBoxLayout()
		mainLayout.addLayout(btnLayout)
		mainLayout.addSpacing(6)

		inputLayout.addWidget(QLabel("任务ID"))
		self.taskLineEdit = QLineEdit()
		inputLayout.addWidget(self.taskLineEdit)
		inputLayout.addWidget(QLabel("次数"))
		self.taskCntEdit = QLineEdit()
		inputLayout.addWidget(self.taskCntEdit)

		self.addBtn = QPushButton("添  加")
		self.addAndCloseBtn = QPushButton("添加并关闭")
		btnLayout.addWidget(self.addBtn)
		btnLayout.addWidget(self.addAndCloseBtn)

		self.addBtn.clicked.connect(self._OnClickAddBtn)
		self.addAndCloseBtn.clicked.connect(self._OnClickAddAndCloseBtn)

	def _OnClickAddBtn(self):
		pass

	def _OnClickAddAndCloseBtn(self):
		pass

class QMainDialog(QDialog):
	def __init__(self, parent=None):
		super(QMainDialog, self).__init__(parent)
		self.inputCardDialog = None
		self.addTaskDialog = None
		self.addBatchTaskDialog = None

		self.setWindowTitle("明日方舟任务助手")
		self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
		self.createInfoPanel()
		self.createTaskPanel()

		self.mainLayout = QGridLayout()
		self.mainLayout.addWidget(self.infoGroupBox, 0, 0)
		self.mainLayout.addWidget(self.taskGroupBox, 1, 0)

		self.setLayout(self.mainLayout)
		self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

	def createInfoPanel(self):
		self.infoGroupBox = QGroupBox("本机信息")

		self.infoLayout = QVBoxLayout()
		self.infoGroupBox.setLayout(self.infoLayout)

		self.infoGroupBox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
		global MACHINE_ID
		if MACHINE_ID is None:
			MACHINE_ID = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
		self.macLabel = QLabel("机 器 码: %s" % MACHINE_ID)
		self.macLabel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		self.macLabel.setMinimumHeight(40)
		self.softLayout = QHBoxLayout()
		self.infoLayout.addWidget(self.macLabel)
		self.infoLayout.addLayout(self.softLayout)

		self.softStatus = QLabel("软件状态: 试用版(今日剩余次数10)      ")
		self.inputCodeBtn = QPushButton("输入卡密")
		self.inputCodeBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		self.buyCodeBtn = QPushButton("购买卡密")
		self.buyCodeBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		self.softLayout.addWidget(self.softStatus)
		self.softLayout.addWidget(self.inputCodeBtn)
		self.softLayout.addWidget(self.buyCodeBtn)
		# self.softLayout.addStretch(1)

		self.softUpdateLayout = QHBoxLayout()
		self.softUpdateLayout.addWidget(QLabel("软件版本: v0.0.1"))
		self.updateBtn = QPushButton("检查更新")
		self.updateBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		self.softUpdateLayout.addWidget(self.updateBtn)
		self.infoLayout.addLayout(self.softUpdateLayout)

	def createTaskPanel(self):
		self.taskGroupBox = QGroupBox("任务设置")
		taskTopLayout = QVBoxLayout()
		self.taskGroupBox.setLayout(taskTopLayout)

		self.taskLayout = QHBoxLayout()
		taskTopLayout.addLayout(self.taskLayout)

		self.taskWidget = QTabWidget()
		self.taskLayout.addWidget(self.taskWidget)

		self.curTaskList = QListView()
		self.curTaskList.setAutoScroll(True)
		self.doneTaskList = QListView()
		self.doneTaskList.setAutoScroll(True)
		self.failedTaskList = QListView()
		self.failedTaskList.setAutoScroll(True)
		self.taskWidget.addTab(self.curTaskList, "当前任务")
		self.taskWidget.addTab(self.doneTaskList, "已完成任务")
		self.taskWidget.addTab(self.failedTaskList, "失败任务")

		self.taskOpContainer = QWidget()
		self.taskOpLayout = QVBoxLayout()
		self.taskOpLayout.addSpacing(20)
		self.taskOpContainer.setLayout(self.taskOpLayout)
		self.taskStartBtn = QPushButton("开始任务")
		self.taskOpLayout.addWidget(self.taskStartBtn)
		self.taskAddBtn = QPushButton("添加任务")
		self.taskOpLayout.addWidget(self.taskAddBtn)
		self.taskAddBatchBtn = QPushButton("批量添加任务")
		self.taskOpLayout.addWidget(self.taskAddBatchBtn)
		self.taskDelBtn = QPushButton("删除任务")
		self.taskOpLayout.addWidget(self.taskDelBtn)
		self.taskDelAllBtn = QPushButton("清空任务")
		self.taskOpLayout.addWidget(self.taskDelAllBtn)
		self.taskOpLayout.addStretch(1)

		self.taskLayout.addWidget(self.taskOpContainer)

		self.taskStartBtn.clicked.connect(self._OnClickStart)
		self.taskAddBtn.clicked.connect(self._OnClickAdd)
		self.taskAddBatchBtn.clicked.connect(self._OnClickBatchAdd)
		self.taskDelBtn.clicked.connect(self._OnClickDel)
		self.taskDelAllBtn.clicked.connect(self._OnClickDelAll)

	def _OnClickStart(self):
		pass

	def _OnClickAdd(self):
		if self.addTaskDialog is None:
			self.addTaskDialog = AddTaskDialog(self)
		self.addTaskDialog.show()

	def _OnClickBatchAdd(self):
		pass

	def _OnClickDel(self):
		pass

	def _OnClickDelAll(self):
		pass

	def _OnClickInputCard(self):
		if self.inputCardDialog is None:
			self.inputCardDialog = InputCardDialog(self)

	def _OnClickBuyCard(self):
		pass

	def _OnClickCheckUpdate(self):
		pass

app = QApplication([])
mainDialog = QMainDialog()
mainDialog.show()
app.exec()
