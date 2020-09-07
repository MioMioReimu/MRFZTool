# -*- coding: utf-8 -*-
from PIL import Image, ImageOps
import cv2
import numpy as np
import os
import pytesseract

TPL_MATCH_THRESHOLD = 0.85
BINARY_THRESHOLD = 128

imgAreas = {} # key: name, value: ImgAreaInfo

def LoadAllImgs():
	from entry_data import info
	for key, value in info.imgInfo.items():
		img = Image.open(u'entry_data/%s' % value['file'])
		if 'text_box' in value:
			area = ImgTextAreaInfo(key, img, value['screen_size'], value['text_box'])
		else:
			if value.get('pos', None) is not None:
				x_percent, y_percent = [x / float(y) for x, y in zip(value['pos'], value['screen_size'])]
			else:
				x_percent, y_percent = None, None
			area = ImgAreaInfo(key, img, value['screen_size'], x_percent, y_percent)
		imgAreas[key] = area

def FindImgInScreen(name, screen_img):
	imgArea = imgAreas.get(name, None)
	if imgArea is None:
		raise Exception('img area name is not loaded or existed.')
	return imgArea.FindImgInScreen(screen_img)

def FindTextInScreen(name, high_dpi_screen, screen, text=""):
	imgArea = imgAreas.get(name, None)
	if imgArea is None:
		raise Exception('img area name is not loaded or existed.')
	if type(imgArea) is not ImgTextAreaInfo:
		raise Exception('img area is not a text img area.')
	return imgArea.FindTextInScreen(high_dpi_screen, screen, text)


def is_box_intersect(box1, box2):
	return not (box1[2] < box2[0] or box2[2] < box1[0] or box1[3] < box2[1] or box2[3] < box1[1])


class ImgAreaInfo(object):
	def __init__(self, name, img, screen_size, x_percent=None, y_percent=None):
		if type(img) is str:
			self.img = Image.open(img, 'r')
		else:
			self.img = img
		self.name = name
		self.width = self.img.width
		self.height = self.img.height
		self.screen_width = screen_size[0]    # 截取的屏幕的宽度
		self.screen_height = screen_size[1]  # 截取的屏幕的高度
		self.x_percent = x_percent          # 左下角的x百分比
		self.y_percent = y_percent          # 右上角的y百分比

	@property
	def screen_size(self):
		return self.screen_width, self.screen_height

	def FindImgInScreen(self, screen_img):
		scale = screen_img.width / float(self.screen_width)
		if self.x_percent is None:
			if scale != 1.0:
				img_size = (int(self.img.width * scale), int(self.img.height * scale))
				tpl = self.img.resize(img_size)
			else:
				img_size = (self.img.width, self.img.height)
				tpl = self.img
			crop_screen = screen_img
			crop_box = [0, 0, screen_img.width, screen_img.height]
		else:
			if scale != 1.0:
				img_size = (int(self.img.width * scale), int(self.img.height * scale))
				img_pos = (int(self.x_percent * screen_img.width), int(self.y_percent * screen_img.height))
				tpl = self.img.resize(img_size)
			else:
				img_size = (self.img.width, self.img.height)
				img_pos = (int(self.x_percent * screen_img.width), int(self.y_percent * screen_img.height))
				tpl = self.img

			search_delta = 20
			crop_box = max(img_pos[0] - search_delta, 0), max(img_pos[1] - search_delta, 0), \
					   min(img_pos[0] + img_size[0] + search_delta, screen_img.width), \
					   min(img_pos[1] + img_size[1] + search_delta, screen_img.height)

			crop_screen = screen_img.crop(crop_box)

		pil_image = crop_screen.convert('RGB')
		open_cv_image = np.array(pil_image)
		screen_img_cv = open_cv_image[:, :, ::-1].copy()

		pil_image = tpl.convert('RGB')
		open_cv_image = np.array(pil_image)
		tpl_img_cv = open_cv_image[:, :, ::-1].copy()

		res = cv2.matchTemplate(screen_img_cv, tpl_img_cv, cv2.TM_CCOEFF_NORMED)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		print(self.name, max_val)
		if max_val <= TPL_MATCH_THRESHOLD:
			return False, None
		left_top = max_loc[0] + crop_box[0], max_loc[1] + crop_box[1]
		return True, (left_top[0], left_top[1], left_top[0] + img_size[0], left_top[1] + img_size[1])

	def FindAllInScreen(self, screen_img):
		scale = screen_img.width / float(self.screen_width)

		if self.x_percent is None:
			if scale != 1.0:
				img_size = (int(self.img.width * scale), int(self.img.height * scale))
				tpl = self.img.resize(img_size)
			else:
				img_size = (self.img.width, self.img.height)
				tpl = self.img
			crop_screen = screen_img
			crop_box = [0, 0, screen_img.width, screen_img.height]
		else:
			if scale != 1.0:
				img_size = (int(self.img.width * scale), int(self.img.height * scale))
				img_pos = (int(self.x_percent * screen_img.width), int(self.y_percent * screen_img.height))
				tpl = self.img.resize(img_size)
			else:
				img_size = (self.img.width, self.img.height)
				img_pos = (int(self.x_percent * screen_img.width), int(self.y_percent * screen_img.height))
				tpl = self.img

			search_delta = 20
			crop_box = max(img_pos[0] - search_delta, 0), max(img_pos[1] - search_delta, 0), \
					   min(img_pos[0] + img_size[0] + search_delta, screen_img.width), \
					   min(img_pos[1] + img_size[1] + search_delta, screen_img.height)

			crop_screen = screen_img.crop(crop_box)

		pil_image = crop_screen.convert('RGB')
		open_cv_image = np.array(pil_image)
		screen_img_cv = open_cv_image[:, :, ::-1].copy()

		pil_image = tpl.convert('RGB')
		open_cv_image = np.array(pil_image)
		tpl_img_cv = open_cv_image[:, :, ::-1].copy()

		match_res = cv2.matchTemplate(screen_img_cv, tpl_img_cv, cv2.TM_CCOEFF_NORMED)
		loc = np.where(match_res >= TPL_MATCH_THRESHOLD)
		result = []
		for pt in zip(*loc[::-1]):
			v = match_res[pt[1]][pt[0]]
			biased_pt = pt[0] + crop_box[0], pt[1] + crop_box[1]
			box = biased_pt[0], biased_pt[1], biased_pt[0] + img_size[0], biased_pt[1] + img_size[1]

			has_intersect = False

			for res_item in result:
				if is_box_intersect(box, res_item[0]):
					has_intersect = True
					if v > res_item[1]:
						res_item[0] = box
						res_item[1] = v
						break
			if not has_intersect:
				result.append([box, v])
		return [x[0] for x in result]

class ImgTextAreaInfo(ImgAreaInfo):
	def __init__(self, name, loc_img, screen_size, text_rect):
		"""
		:param name:
		:param loc_img: 用于定位的
		:param screen_width:
		:param screen_height:
		:param text_rect: 查找定位文字的矩形，相对于loc_img的起点而言的, (x_min, y_min, x_max, y_max)
		"""
		super(ImgTextAreaInfo, self).__init__(name, loc_img, screen_size)
		self.text_rect = text_rect


	def FindTextInScreen(self, high_dpi_screen, screen, text=""):
		"""从低分辨率图片中寻找loc_img，然后相应的在高分辨率图片中进行识别文字"""
		scale = high_dpi_screen.width / float(self.screen_width)

		min_x = self.text_rect[0] * scale
		min_y = self.text_rect[1] * scale
		width = (self.text_rect[2] - self.text_rect[0]) * scale
		height = (self.text_rect[3] - self.text_rect[1]) * scale

		isAscii = all(ord(c) < 128 for c in text)
		find_areas = self.FindAllInScreen(screen)
		print('find area', find_areas)
		i = 0
		for idx, rect in enumerate(find_areas):
			i += 1
			scale_local = high_dpi_screen.width / float(screen.width)
			left_top = rect[0] * scale_local + min_x, rect[1] * scale_local + min_y
			crop_rect = left_top[0], left_top[1], left_top[0] + width, left_top[1] + height
			crop_rect = [int(x) for x in crop_rect]
			search_text_img = high_dpi_screen.crop(crop_rect)
			
			fn = lambda x: 255 if x > BINARY_THRESHOLD else 0
			search_text_img = search_text_img.convert('L').point(fn, mode='1')
			search_text_img = search_text_img.convert('RGB')
			h = search_text_img.histogram()
			if h[0] > h[255]:
				search_text_img = ImageOps.invert(search_text_img)

			search_text_img.save('tmp.png')
			
			if isAscii:
				t = pytesseract.image_to_string('tmp.png', lang='eng',)
			else:
				t = pytesseract.image_to_string('tmp.png', lang='chi_sim')
			t = t.strip().replace(u'$', u'S').replace(u'§', u'S')
			s = []
			for c in t:
				if c in ['-'] or c.isalnum():
					s.append(c)
			t = ''.join(s)
			print('test detected value:', t, 'true value:', text)
			if not t:
				continue
			if t == text:
				return True, crop_rect
		return False, None

	def FindAllTextInScreen(self, high_dpi_screen, screen, text=""):
		scale = high_dpi_screen.width / float(self.img.screen_width)
		min_x = self.text_rect[0] * scale
		min_y = self.text_rect[1] * scale
		width = (self.text_rect[2] - self.text_rect[0]) * scale
		height = (self.text_rect[3] - self.text_rect[1]) * scale

		isAscii = all(ord(c) < 128 for c in text)
		find_areas = self.FindAllInScreen(screen)

		result = []
		for rect in find_areas:
			scale_local = high_dpi_screen.width / float(screen.width)
			left_top = rect[0] * scale_local + min_x, rect[1] * scale_local + min_y
			crop_rect = left_top[0], left_top[1], left_top[0] + width, left_top[1] + height
			crop_rect = [int(x) for x in crop_rect]
			search_text_img = high_dpi_screen.crop(crop_rect)
			if isAscii:
				t = pytesseract.image_to_string(search_text_img, lang='eng')
			else:
				t = pytesseract.image_to_string(search_text_img, lang='chi_sim')
			result.append([t, crop_rect])
