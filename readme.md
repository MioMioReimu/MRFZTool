## 安装环境
pip install pywin32    
pip install psutil    
pip install pillow    
pip install pytesseract    
pip install opencv-python    

从 https://github.com/UB-Mannheim/tesseract/wiki 下载最新的tesseract
安装后，设置Path变量，把tesseract的文件夹加到Path环境里
使得 tesseract能够在cmd中打出来

## 使用
本辅助支持所有已经三星了的关卡的扫荡。

打开main.py, 编辑 TASKS变量，
例如
```python
TASKS = [
	('3-1', 3),
	('PR-B-1', 6),
	('2-1', 30),
]
```
表示3-1关卡打3次，然后打PR-B-1 6次，然后打2-1 30次。

类似的可以指定各种任务序列，目前支持 主线0-5章关卡，支持各种资源的关卡的扫荡

设定好main.py中的任务后，在命令行执行 main.py。
注意，必须以管理员权限执行main.py，否则没权限无法截图
