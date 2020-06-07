# python 3.6
# -*- coding: utf-8 -*-
# @Time    : 2020/3/2 16.17
# @Author  : Frx-alexandria
# @File    : main.py
# @Version : 1.0.0

# qt多页面切换QTabWidget


import pretty_errors
import sys
import re
import numpy as np
import time
import array
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from main_ui import Ui_MainWindow
import os
import atexit

sent_text = ''

class MyGraphWindow(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self):
		# QT窗口初始化必备的操作
		super(MyGraphWindow, self).__init__()
		# 初始化窗口，调用对象的相关方法
		self.setupUi(self)

		# 创建保存接收字符的str
		self.receive_str = ''
		# 创建用于数据提取的缓存文件
		self.data_decoding_buffer = ''
		# tab标签标志
		self.tab_status = 1
		# 创建串口状态位
		self.serial_status = 0
		# 创建串口对象
		self.ser = serial.Serial()
		# 可动态改变数组的大小,double型数组
		self.data = array.array('d')
		self.data1 = array.array('d')
		# 横坐标长度
		self.historyLength = 300
		# 检测所有存在的串口，将信息存储在字典中
		self.Com_Dict = {}
		# 定时器接收数据
		self.receive_timer = QTimer(self)
		self.receive_timer.timeout.connect(self.receive_data)
		# 接收数据和发送数据数目变量
		self.data_num_received = 0
		self.data_num_send = 0

		# 初始化按键任务
		self.init()
		# 发送窗口放入字符
		self.file_dir = os.getcwd() + "//log.txt"
		self.get_last_input_information()

		# 创建绘图窗口
		self.plot1, self.curve, self.curve1 = self.set_graph_ui()

	# 初始化按键任务
	def init(self):
		# 设置窗口名字
		self.setWindowTitle("串口小助手")

		# 设置tab上的关闭按钮是否显示
		self.tabWidget.setTabsClosable(False)

		# 串口检测按钮
		self.check_serial_Button.clicked.connect(self.port_check)

		# 串口信息显示
		self.chose_port_comboBox.currentTextChanged.connect(self.port_imf)

		# 打开串口按钮
		self.open_serial_Button.clicked.connect(self.port_open)

		# 关闭串口按钮
		self.close_serial_Button.clicked.connect(self.port_close)

		# 发送数据按钮
		self.sent_text_Button.clicked.connect(self.data_send)

		# 接收数据量置0
		self.recived_data_num.setText(str(self.data_num_received))

		# 发送数据量置0
		self.sent_data_num.setText(str(self.data_num_send))

		# 清除发送窗口
		self.clear_text_Button.clicked.connect(self.send_data_clear)

		# 清除全部数据
		self.clear_all_Button.clicked.connect(self.clear_all_data)

		# 设置tab的切换操作
		self.tabWidget.currentChanged.connect(self.change_tab)

		# 清除接受的数据
		self.clear_receive_button.clicked.connect(self.clear_receive_data)

		# 检测可用串口
		self.port_check()

	# 设置绘图窗体的结构样式
	def set_graph_ui(self):
		# pg全局变量设置函数，antialias=True开启曲线抗锯齿
		pg.setConfigOptions(antialias=True)
		# 创建窗体，可实现数据界面布局自动管理
		win = pg.GraphicsWindow()

		# pg绘图窗口可以作为一个widget添加到GUI中的graph_layout，当然也可以添加到Qt其他所有的容器中
		self.graph_Layout.addWidget(win)

		# 往窗口中增加一个图形命名为plot
		plot1 = win.addPlot()
		# 栅格设置函数
		plot1.showGrid(x=True, y=True)
		# 设置显示的范围
		plot1.setRange(xRange=[0, self.historyLength], yRange=[-5, 5], padding=0)
		# 设置标注的位置及内容
		# plot1.setLabel(axis='left', text='y / V', color='#ffff00')
		plot1.setLabel(axis='left')
		# plot1.setLabel(axis='bottom', text='x / point', units='s')
		plot1.setLabel(axis='bottom', text='x / point')
		# False代表线性坐标轴，True代表对数坐标轴
		plot1.setLogMode(x=False, y=False)
		# 表格的名字
		plot1.setTitle('接收数据')
		# 也可以返回plot1对象，然后使用plot.plot(x,y,pen='r')来绘制曲线，x,y对应各轴数据
		# 需要去掉全部的curve，换成以上函数
		curve = plot1.plot()
		curve1 = plot1.plot()
		return plot1, curve, curve1

	# 串口检测
	def port_check(self):
		self.Com_Dict = {}
		port_list = list(serial.tools.list_ports.comports())
		self.chose_port_comboBox.clear()
		for port in port_list:
			self.Com_Dict["%s" % port[0]] = "%s" % port[1]
			self.chose_port_comboBox.addItem(port[0])
		if len(self.Com_Dict) == 0:
			self.statues.setText("     无串口信息")

	# 串口信息
	def port_imf(self):
		# 显示选定的串口的详细信息
		imf_s = self.chose_port_comboBox.currentText()
		if imf_s != "":
			self.statues.setText(self.Com_Dict[self.chose_port_comboBox.currentText()])

	# 打开串口
	def port_open(self):
		# 保证切换串口时能够关闭上次打开的串口
		if self.serial_status:
			self.port_close()

		self.ser.port = self.chose_port_comboBox.currentText()
		self.ser.baudrate = int(self.comboBox_2.currentText())
		self.ser.bytesize = int(self.comboBox_3.currentText())
		self.ser.stopbits = int(self.comboBox_5.currentText())
		self.ser.parity = self.comboBox_4.currentText()

		try:
			self.ser.open()
		except Exception as e:
			print('port_open:', e)
			QMessageBox.critical(self, "Port Error", "此串口不能被打开！")
			return None

		if self.ser.isOpen():
			# 打开串口接收定时器，周期为20ms
			self.receive_timer.start(20)
			self.groupBox_2.setTitle("串口状态（已打开）")
			self.close_serial_Button.setEnabled(True)
			self.serial_status = 1

			self.open_serial_Button.setStyleSheet("background-color:rgb(0,255,0)")

	# 关闭串口
	def port_close(self):
		if self.serial_status:
			try:
				self.ser.close()
				self.serial_status = 0
			except Exception as e:
				print('port_close:', e)
				pass
			self.open_serial_Button.setEnabled(True)
			self.close_serial_Button.setEnabled(False)
			self.receive_timer.stop()
			self.groupBox_2.setTitle("串口状态（已关闭）")
			self.open_serial_Button.setStyleSheet("background-color:rgb(255, 87, 58)")
		else:
			QMessageBox.critical(self, "Error", "串口没打开！")

	# 清除发送数据
	def send_data_clear(self):
		self.sent_textEdit.setText("")

	# 清除全部数据
	def clear_all_data(self):
		# 接收数据和发送数据数目置零
		self.data_num_received = 0
		self.recived_data_num.setText(str(self.data_num_received))
		self.data_num_send = 0
		self.sent_data_num.setText(str(self.data_num_send))
		self.receive_textEdit.setText("")

	# 发送数据
	def data_send(self):
		global sent_text
		# 检测串口是否是打开的,不能检测是否异常断开
		if self.ser.isOpen():
			sent_text = input_s = self.sent_textEdit.toPlainText()
			if input_s != "":
				# 非空字符串
				# ascii发送
				input_s = (input_s).encode('utf-8')

				# 返回发送的字符数
				try:
					num = self.ser.write(input_s)
					self.data_num_send += (num-1)
					self.sent_data_num.setText(str(self.data_num_send))
				except Exception as e:
					print('data_send:', e)
					self.port_close()
		else:
			QMessageBox.critical(self, 'Warning', '数据发送失败，串口尚未打开！')
			pass

	# 接收数据
	def receive_data(self):
		try:
			num = self.ser.inWaiting()
			if num > 0:
				data = self.ser.read(num)

				# 串口接收到的字符串为b'123',要转化成unicode字符串才能输出到窗口中去
				receive_data = data.decode('iso-8859-1')
				# 统计接收字符的数量
				self.data_num_received += len(receive_data)
				self.recived_data_num.setText(str(self.data_num_received))

				# 如果是在文字标签内
				if self.tab_status == 2:
					self.insert_data_to_receive_text_edit(receive_data)
				# 绘图标签内
				elif self.tab_status == 1:
					# 保存数据用于显示
					self.receive_str += receive_data

					# 提取数据用于绘图（可用于绘制多条曲线）
					# 用回车换行区分断帧
					frame_data_list = receive_data.split('\r\n')
					# 保存不完整的数据
					self.data_decoding_buffer += frame_data_list[-1]

					# 画线数量标志
					number_of_lines = 0
					# 寻找帧内数据
					if len(frame_data_list)>1:
						for i in range(len(frame_data_list)-1):
							frame_data = re.findall(r'\d+', frame_data_list[i])
							# 单帧内数据量为1，画一条曲线
							if frame_data and len(frame_data)==1:
								float_frame_data = float(frame_data[0])

								# 调整数据长度
								if len(self.data) < self.historyLength:
									self.data.append(float_frame_data)
								else:
									self.data[:-1] = self.data[1:]
									self.data[-1] = float_frame_data

								# 调整数据纵坐标显示范围
								max_data = max(self.data)
								min_data = min(self.data)
								if not (max_data == 0 and min_data == 0):
									self.plot1.setRange(yRange=[min_data * 1.05 - 0.05 * max_data,
																max_data * 1.05 - 0.05 * min_data])
								self.curve.setData(self.data, pen='g')
								# 可绘制多条曲线
								# self.curve1.setData(self.data1, pen='r')

							# 如果每帧数据长度超过一，绘制前两条
							elif frame_data and len(frame_data)>1:
								float_frame_data1 = float(frame_data[0])
								float_frame_data2 = float(frame_data[1])

								number_of_lines = 2
								if len(self.data) < self.historyLength:
									self.data.append(float_frame_data1)
									self.data1.append(float_frame_data2)
								else:
									self.data[:-1] = self.data[1:]
									self.data[-1] = float_frame_data1
									self.data1[:-1] = self.data1[1:]
									self.data1[-1] = float_frame_data2
								# 调整数据纵坐标显示范围
								max_data = max(self.data + self.data1)
								min_data = min(self.data + self.data1)
								if not (max_data == 0 and min_data == 0):
									self.plot1.setRange(yRange=[min_data * 1.05 - 0.05 * max_data,
																max_data * 1.05 - 0.05 * min_data])

						self.curve.setData(self.data, pen='g')
						if number_of_lines==2:
							number_of_lines = 0
							self.curve1.setData(self.data1, pen='r')


		except Exception as e:
			print('receive_data:', e)
			self.port_close()
			QMessageBox.critical(self, "Error", "串口异常，无法接收！")

	# 数据插入文字tab中
	def insert_data_to_receive_text_edit(self, receive_data):
		self.receive_textEdit.insertPlainText(receive_data)

		# 获取到text光标,确保下次插入到内容最后
		textCursor = self.receive_textEdit.textCursor()
		# 滚动到底部
		textCursor.movePosition(textCursor.End)
		# 设置光标到text中去
		self.receive_textEdit.setTextCursor(textCursor)

	# tab切换
	def change_tab(self):
		# 获取当前切换到的tab标签名
		tab = self.tabWidget.currentIndex()
		if tab == 0:
			self.tab_status = 1
		elif tab == 1:

			# 如果有标签切换，未显示数据要显示出来
			if len(self.receive_str) > 0:
				self.insert_data_to_receive_text_edit(self.receive_str)
			self.tab_status = 2
		else:
			pass

	# 清除接收数据
	def clear_receive_data(self):
		self.receive_textEdit.setText("")

	# 获取上次存储的信息
	def get_last_input_information(self):
		if not os.path.exists(self.file_dir):
			with open(self.file_dir, "w") as f:
				f.close()
		else:
			with open(self.file_dir, 'r', encoding='utf-8')as f:
				self.sent_textEdit.insertPlainText(f.read())



# 保存信息
@atexit.register
def save_sent_text():
	with open(os.getcwd()+ "//log.txt", "w") as f:
		f.seek(0)
		f.truncate()  # 清空文件
		f.write(sent_text)
		f.close()

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	myWin = MyGraphWindow()
	myWin.show()
	sys.exit(app.exec_())
