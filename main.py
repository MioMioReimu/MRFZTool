# -*- coding: utf-8 -*-
import win32gui, win32con, win32api, win32process, win32ui
import pywin32_system32

from ctypes import windll
from PIL import Image, ImageOps, ImageEnhance
import time
import os
import threading
import sys
import codecs
# sys.stdout = codecs.getwriter('gbk')(sys.stdout)
# sys.stderr = codecs.getwriter('gbk')(sys.stderr)

os.environ['PATH'] = os.environ['PATH'] + ';' + os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Tesseract')
import psutil, pytesseract
# pytesseract.tesseract_cmd = 'Tesseract/tesseract.exe'
PROC_NAME = "NemuPlayer.exe"
GAME_NAME = "明日方舟"

# 在这里配置需要执行的任务
# 例如先打10个固若金汤 PR-A-1, 再打10个 势不可挡 PR-C-1
# 则任务是
# [
# 	('PR-A-1', 10),
# 	('PR-C-1', 10),
# ]
"""
常见任务类型

芯片任务
	固若金汤 盾治疗芯片: PR-A-1, PR-A-2 ...
	摧枯拉朽 射手,法师芯片: PR-B-1, PR-B-2 ...
	势不可挡 先锋,辅助芯片: PR-C-1, PR-C-2 ...
	身先士卒 近卫,特种芯片: PR-D-1, PR-D-2 ...
"""

from config import TASKS

TASK_GUIDE = {
	r'PR\-A\-[0-9]+': ['chip_task', '固若金汤', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'PR\-C\-[0-9]+': ['chip_task', '势不可挡', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'PR\-B\-[0-9]+': ['chip_task', '摧枯拉朽', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'PR\-D\-[0-9]+': ['chip_task', '身先士卒', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'LS\-[0-9]+': ['item_task', '战术演习', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'AP\-[0-9]+': ['item_task', '粉碎防御', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'SK\-[0-9]+': ['item_task', '资源保障', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'CA\-[0-9]+': ['item_task', '空中威胁', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'CE\-[0-9]+': ['item_task', '货物运送', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'[S]{0,1}0-[0-9]+': ['main_task', 'main_ch0', ('operation|operation_s', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'[S]{0,1}1-[0-9]+': ['main_task', 'main_ch1', ('operation|operation_s', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'[S]{0,1}2-[0-9]+': ['main_task', 'main_ch2', ('operation|operation_s', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'[S]{0,1}3-[0-9]+': ['main_task', 'main_ch3', ('operation|operation_s', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'[S]{0,1}4-[0-9]+': ['main_task', 'main_ch4', ('operation|operation_s', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'[S]{0,1}5-[0-9]+': ['main_task', 'main_ch5', ('operation|operation_s', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'切尔诺伯格': ['jingshi_task', '切尔诺伯格', 'CHECK_PROXY', 'operation_start'],
	r'龙门外环': ['jingshi_task', '龙门外环', 'CHECK_PROXY', 'operation_start'],
	r'龙门市区': ['jingshi_task', '龙门市区', 'CHECK_PROXY', 'operation_start'],
	r'OF\-[0-9]+': ['of_task', 'of_task_type1', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start'],
	r'OF\-F[0-9]+': ['of_task', 'of_task_type2', ('operation', 'SELF'), 'CHECK_PROXY', 'operation_start_of'],
}

NEED_MOVE_BTN = [
	'战术演习',
	'粉碎防御',
	'资源保障',
	'空中威胁',
	'货物运送',
	'operation',
	'operation_s',
	'main_ch0',
	'main_ch1',
	'main_ch2',
	'main_ch3',
	'main_ch4',
	'main_ch5',
	'切尔诺伯格',
	'龙门外环',
	'龙门市区',
]

MARGIN_TOP = 36
MARGIN_BOTTOM = 53
MARGIN_LEFT = 0
MARGIN_RIGHT = 0


def FindWindowByProcNameAndGameName(procName, gameName):
	procId = None
	for proc in psutil.process_iter():
		if procName.lower() in proc.name().lower():
			procId = proc.pid
			break
	if not procId:
		raise Exception('mumu模拟器未运行')
	hwnds = []
	def _OnIterWindow(hwnd, _):
		_, pid = win32process.GetWindowThreadProcessId(hwnd)
		wndName = win32gui.GetWindowText(hwnd)
		if gameName in wndName:
			if pid == procId:
				hwnds.append(hwnd)
	
	win32gui.EnumWindows(_OnIterWindow, [])
	
	if len(hwnds) == 0:
		raise Exception('明日方舟未运行')
	
	return hwnds[0]

def CaptureWindow(hwnd, topMargin=0, bottomMargin=0, leftMargin=0, rightMargin=0, scale=1.0):
	user32 = windll.user32
	user32.SetProcessDPIAware()

	hwndDC = win32gui.GetWindowDC(hwnd)
	mfcDC = win32ui.CreateDCFromHandle(hwndDC)
	saveDC = mfcDC.CreateCompatibleDC()

	left, top, right, bot = win32gui.GetWindowRect(hwnd)
	w = right - left
	h = bot - top
	if win32gui.IsIconic(hwnd):
		win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
		left, top, right, bot = win32gui.GetWindowRect(hwnd)
		w = right - left
		h = bot - top

	# if (not win32gui.IsWindowVisible(hwnd)) or w < 200 or h < 200:
	# 	win32gui.ShowWindow(hwnd, win32con.WM_SHOWWINDOW)
	# 	win32gui.SetForegroundWindow(hwnd)
	#
	# 	left, top, right, bot = win32gui.GetWindowRect(hwnd)
	# 	w = right - left
	# 	h = bot - top
	
	
	saveBitMap = win32ui.CreateBitmap()
	saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
	
	saveDC.SelectObject(saveBitMap)
	
	result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
	
	bmpinfo = saveBitMap.GetInfo()
	bmpstr = saveBitMap.GetBitmapBits(True)
	
	im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
		bmpstr, 'raw', 'BGRX', 0, 1)
	imCrop = ImageOps.crop(im, (leftMargin, topMargin, rightMargin, bottomMargin))
	if scale != 1.0:
		imCrop = imCrop.resize((int(imCrop.width * scale), int(imCrop.height * scale)), Image.BICUBIC)
	return imCrop


def click(hwnd, pos):
	print('click', pos)
	pos = win32api.MAKELONG(int(pos[0] + MARGIN_LEFT), int(pos[1] + MARGIN_TOP))

	win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, pos)
	time.sleep(0.05)
	win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, pos)


def move_horz(hwnd, pos, delta_x, delta_y, speed=1):
	pos_x_end = pos[0] + delta_x
	pos_y_end = pos[1] + delta_y
	# print('move from (%d, %d) to (%d, %d)' % (pos[0], pos[1], pos_x_end, pos_y_end))
	count = int((abs(delta_x) + abs(delta_y)) / 5)
	one_delta_x = int(delta_x / float(count))
	one_delta_y = int(delta_y / float(count))
	
	pos_start = win32api.MAKELONG(pos[0] + MARGIN_LEFT, pos[1] + MARGIN_TOP)
	win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, pos_start)
	for i in range(count - 1):
		pos_move = pos[0] + i * one_delta_x, pos[1] + i * one_delta_y
		pos_move = win32api.MAKELONG(pos_move[0] + MARGIN_LEFT, pos_move[1] + MARGIN_TOP)
		win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, pos_move)
		time.sleep(0.01 / speed)

	pos_end = win32api.MAKELONG(pos_x_end + MARGIN_LEFT, pos_y_end + MARGIN_TOP)
	win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, pos_end)
	time.sleep(0.01 / speed)
	win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, pos_end)
	time.sleep(0.1)


import ImgAreaInfo

MINI_SCALE = 1
ImgAreaInfo.LoadAllImgs()


class MRFZTask(object):
	def __init__(self, name, count, guide):
		self.name = name
		self.count = count
		self.guide = guide
		self.fast_guide = guide[self.guide.index('CHECK_PROXY') - 1:]


class MRFZHelper(object):
	def __init__(self):
		self.hwnd = FindWindowByProcNameAndGameName(PROC_NAME, GAME_NAME)
		self.screen = CaptureWindow(self.hwnd, MARGIN_TOP, MARGIN_BOTTOM, 0, 0, 1.0)
		self.screen_mini = self.screen.resize((int(self.screen.width * MINI_SCALE), int(self.screen.height * MINI_SCALE)), Image.BICUBIC)
		self.task_guides = []  # list of all TASK_GUIDE, type: (taskRe, taskGuide)
		self.tasks = []  # list of MRFZTask
		self.failed_tasks = []

		self.running = False
		self.runningThread = None

	def RunTasks(self):
		if self.runningThread is None:
			import threading
			self.runningThread = threading.Thread(target=self._DoMainProc)
		self.runningThread.start()

	def StopTasks(self):
		self.running = False
		self.runningThread = None

	def AddTask(self, taskName, taskCount):
		taskGuide = self.FindTaskGuide(taskName)
		if taskGuide is None:
			return False
		task = MRFZTask(taskName, taskCount, taskGuide)
		self.tasks.append(task)
		return task

	def DelTask(self, taskIdx):
		if 0 <= taskIdx < len(self.tasks):
			self.tasks.pop(taskIdx)

	# def IncrTask(self, taskIdx):
	# 	pass
	#
	# def DecrTask(self, taskIdx):
	# 	pass

	def InitTaskGuide(self):
		import re
		for key, value in TASK_GUIDE.items():
			self.task_guides.append([re.compile(key), value])

	def FindTaskGuide(self, task_name):
		for r, guide in self.task_guides:
			if r.match(task_name):
				return guide
		return None

	def InitTasks(self):
		for taskName, taskCnt in TASKS:
			task = MRFZTask(taskName, taskCnt, self.FindTaskGuide(taskName))
			self.tasks.append(task)

	def DoneTaskOnce(self, task):
		need_remove = False
		rm_idx = 0
		for idx, _task in enumerate(self.tasks):
			if _task == task:
				_task.count -= 1
				if _task.count <= 0:
					need_remove = True
					rm_idx = idx
					break
		if need_remove:
			self.tasks.pop(rm_idx)

	def FailTask(self, task, desc):
		self.tasks.remove(task)
		self.failed_tasks.append((task.name, desc))

	def PrintTaskFailInfo(self):
		for name, desc in self.failed_tasks:
			print('任务: %s，原因: %s' % (name, desc))

	def GetOneTask(self):
		while len(self.tasks) > 0:
			task = self.tasks[0]
			if task.count <= 0:
				self.tasks.pop(0)
			return task
		return None

	def Refresh(self):
		self.screen = CaptureWindow(self.hwnd, MARGIN_TOP, MARGIN_BOTTOM, 0, 0, 1.0)
		self.screen_mini = self.screen.resize(
			(int(self.screen.width * MINI_SCALE), int(self.screen.height * MINI_SCALE)), Image.BICUBIC)

	def ClickCenter(self):
		click(self.hwnd, (self.screen.width / 2, self.screen.height / 2))
		time.sleep(1)
	
	def Click(self, rect, relative_screen):
		scale = self.screen.width / float(relative_screen.width)
		center = int((rect[0] + rect[2]) * scale * 0.5), int((rect[1] + rect[3]) * scale * 0.5)
		click(self.hwnd, center)
		time.sleep(1)

	def TryClick(self, btn_name):
		is_in, rect = ImgAreaInfo.FindImgInScreen(btn_name, self.screen_mini)
		if not is_in:
			return False

		scale = self.screen.width / float(self.screen_mini.width)
		center = int((rect[0] + rect[2]) * scale * 0.5), int((rect[1] + rect[3]) * scale * 0.5)
		click(self.hwnd, center)
		time.sleep(1)
		return True

	def TryClickWithText(self, btn_name, text):
		is_in, rect = ImgAreaInfo.FindTextInScreen(btn_name, self.screen, self.screen_mini, text)
		if not is_in:
			return False

		center = int((rect[0] + rect[2]) * 0.5), int((rect[1] + rect[3]) * 0.5)
		click(self.hwnd, center)
		time.sleep(1)
		return True
	
	def TryMoveFindBtn(self, btn_name, count=2):
		self.Refresh()
		isIn, rect = ImgAreaInfo.FindImgInScreen(btn_name, self.screen_mini)
		if isIn:
			return isIn, rect

		for i in range(count):
			move_horz(self.hwnd, (100, 400), 1000, 0, 10)
		
		time.sleep(1)
		self.Refresh()
		isIn, rect = ImgAreaInfo.FindImgInScreen(btn_name, self.screen_mini)
		if isIn:
			return isIn, rect
		
		for i in range(count):
			move_horz(self.hwnd, (1300, 400), -1000, 0)
			time.sleep(1)
			self.Refresh()
			isIn, rect = ImgAreaInfo.FindImgInScreen(btn_name, self.screen_mini)
			if isIn:
				return isIn, rect
		
		return False, None
	
	def TryMoveFindBtnWithText(self, btn_name, text='', count=5):
		print('try to scroll and find', btn_name, text)
		self.Refresh()
		isIn, rect = ImgAreaInfo.FindTextInScreen(btn_name, self.screen, self.screen_mini, text)
		if isIn:
			return isIn, rect

		for i in range(count):
			move_horz(self.hwnd, (100, 400), 1000, 0, 10)
		
		time.sleep(1)
		self.Refresh()
		isIn, rect = ImgAreaInfo.FindTextInScreen(btn_name, self.screen, self.screen_mini, text)
		if isIn:
			return isIn, rect
		for i in range(count):
			move_horz(self.hwnd, (1300, 400), -1000, 0)
			time.sleep(1)
			
			self.Refresh()
			isIn, rect = ImgAreaInfo.FindTextInScreen(btn_name, self.screen, self.screen_mini, text)
			if isIn:
				return isIn, rect
		
		return False, None

	def CheckPage(self):
		is_main, _ = ImgAreaInfo.FindImgInScreen('main_act', self.screen_mini)
		is_act, _ = ImgAreaInfo.FindImgInScreen('main_task', self.screen_mini)
		if is_main:
			return 'main'
		elif is_act:
			return 'act'
		else:
			is_in_battle_1, _ = ImgAreaInfo.FindImgInScreen('battle_tower', self.screen_mini)
			is_in_battle_2, _ = ImgAreaInfo.FindImgInScreen('battle_fee', self.screen_mini)
			if is_in_battle_1 and is_in_battle_2:
				return 'battle'
			else:
				return 'other'

	def IsInScreen(self, btn_name):
		return ImgAreaInfo.FindImgInScreen(btn_name, self.screen_mini)[0]

	def ProcessGuide(self, task, guide, scroll=True):
		needBreak = False
		# 执行导航循环
		for guide_step in guide:
			# 如果是图片的步骤
			if type(guide_step) == str:
				if guide_step == 'SELF':
					step_name = task.name
				elif guide_step == 'CHECK_PROXY':
					# 进入副本开启界面后，试图开启代理
					self.Refresh()
					if not self.IsInScreen('proxy_btn'):
						if self.IsInScreen('proxy_locked_btn'):
							print('任务: %s 不能代理指挥，无法挂机' % task.name)
							if task.guide is None:
								self.FailTask(task, '不能代理指挥，无法挂机')
								needBreak = True
								break
						else:
							r = self.TryClick('proxy_unchecked_btn')
							print('Click 开启代理 ', r)
							if not r:
								print('无法开启代理，似乎是无法代理的任务')
								self.FailTask(task, '暂不支持，无法开启代理，似乎是无法代理指挥的任务，例如TR系列')
								needBreak = True
								break
							self.Refresh()
					continue
				else:
					step_name = guide_step

				if '|' in step_name:
					r, rect = False, None
					for s in step_name.split('|'):
						if (s in NEED_MOVE_BTN) and scroll:
							r, rect = self.TryMoveFindBtn(s)
							if r:
								break
						else:
							r = self.TryClick(s)
							rect = None
						if r:
							break
					if r and rect is not None:
						self.Click(rect, self.screen_mini)
				else:
					if (step_name in NEED_MOVE_BTN) and scroll:
						r, rect = self.TryMoveFindBtn(step_name)
						if r:
							self.Click(rect, self.screen_mini)
					else:
						r = False
						for s in step_name.split('|'):
							r = self.TryClick(s)
							if r:
								break

			# 如果是图片带文字的步骤
			elif type(guide_step) in (list, tuple):
				guide_info = [x if x != 'SELF' else task.name for x in guide_step]
				if guide_step[0] == 'SELF':
					step_name = task.name
				else:
					step_name = guide_step[0]

				if '|' in step_name:
					r, rect = False, None
					for s in step_name.split('|'):
						if (s in NEED_MOVE_BTN) and scroll:
							r, rect = self.TryMoveFindBtnWithText(s, *guide_info[1:])
							if r:
								break
						else:
							r = self.TryClickWithText(s, *guide_info[1:])
							rect = None
						if r:
							break
					if r and rect is not None:
						self.Click(rect, self.screen)
				else:
					if (step_name in NEED_MOVE_BTN) and scroll:
						r, rect = self.TryMoveFindBtnWithText(*guide_info)
						if r:
							self.Click(rect, self.screen)
					else:
						r = False
						for s in step_name.split('|'):
							r = self.TryClickWithText(s, *guide_info[1:])
							if r:
								break
			else:
				raise Exception('unknown guide step')
			print('Click %s ' % str(guide_step), r)

			if not r:
				needBreak = True
				break
			self.Refresh()
		return not needBreak

	def GoToBattle(self, task):
		task = self.GetOneTask()
		for i in range(3):
			self.Refresh()
			r = self.TryClick('battle_start')
			print('Click 开始战斗 ', r)
			if not r:
				continue
			else:
				time.sleep(10)
				self.Refresh()
				page = self.CheckPage()
				if page == 'battle':
					self.DoneTaskOnce(task)
					print('战斗已开始，程序睡眠30s后继续')
					time.sleep(30)
					break
				else:
					continue

	def _DoMainProc(self):
		self.InitTaskGuide()
		self.InitTasks()

		lastTask = None
		while len(self.tasks) > 0 and self.running:
			time.sleep(1)

			self.Refresh()
			self.screen.save('a.png')
			page = self.CheckPage()
			print('game is in page %s' % page)

			if page == 'main':
				self.TryClick('main_act')
			elif page == 'act':
				task = self.GetOneTask()
				if task.guide is None:
					print('任务：%s暂不支持,找不到guide逻辑' % task.name)
					self.FailTask(task, '暂不支持,找不到guide逻辑')
					continue

				time.sleep(1)
				if not self.ProcessGuide(task, task.guide):
					continue

				# 有时候加载战斗比较慢，多试几次
				time.sleep(1)

				self.GoToBattle(task)
				lastTask = task

			elif page == 'battle':
				print('战斗正在进行中，程序睡眠10s后继续')
				time.sleep(10)
				continue

			else:
				task = self.GetOneTask()
				if lastTask is not None and lastTask.name != task.name:
					if self.TryClick('back_btn'):
						continue
					elif self.TryClick('close_btn'):
						continue
					else:
						self.ClickCenter()
						continue

				if task.guide is None:
					print('任务：%s暂不支持,找不到guide逻辑' % task.name)
					self.FailTask(task, '暂不支持,找不到guide逻辑')
					continue

				click(self.hwnd, (int(self.screen.width * 0.3), int(self.screen.height * 0.3)))
				time.sleep(1)

				self.Refresh()
				if not self.ProcessGuide(task, task.fast_guide, False):
					if self.TryClick('back_btn'):
						continue
					elif self.TryClick('close_btn'):
						continue
					else:
						self.ClickCenter()
						continue
				else:
					# 有时候加载战斗比较慢，多试几次
					time.sleep(1)

					self.GoToBattle(task)
					lastTask = task

		if len(self.failed_tasks) > 0:
			print('任务部分失败')
			self.PrintTaskFailInfo()
		else:
			print('任务全部完成')

if __name__ == '__main__':
	h = MRFZHelper()
	h.running = True
	h._DoMainProc()
