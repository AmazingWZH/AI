from PyQt5.Qt import *
import ui2
import cv2
import os
import sys
import time

import cv2
import numpy as np
from PIL import Image

from yolo import YOLO


class Mainwindow(ui2.Ui_Unframewindow, QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(None,Qt.FramelessWindowHint)

        # self.setui(self)
        self.setupUi(self)
        self.setWindowTitle('目标识别系统')
        self.setWindowIcon(QIcon('./resources/OCR-orange.png'))
        self.page.setStyleSheet("QWidget#page{background-color: rgb(245, 249, 252);}")
        self.yolo = YOLO()

        for i in range(3):
            item = self.left_widget.item(i)  # 选中QlistWidget的不同按钮
            item.setSizeHint(QSize(30, 60))  # 设置按钮大小

        # 初始化界面1
        self.timer = QTimer(self)   # 刷新视频流
        self.timer_camera = QTimer(self)   # 需要定时器刷新摄像头界面
        self.cap = cv2.VideoCapture()
        self.cap_num = 0


        self.initDrag()
        self.slot_init()
        self.setCloseButton(True)
        self.setMinMaxButtons(True)
        self.minWidth = 1280
        self.minHeight = 720
        self.setMinimumWidth(self.minWidth)  # 设置主界面最小长宽
        self.setMinimumHeight(self.minHeight)
        self.setMouseTracking(True)  # 设置widget鼠标跟踪
        self.statusBar().hide()  # 隐藏状态栏
        self.radioButton.setChecked(True)  # 第一个复选框默认框选
        # 对进行listwidget和stackwidget进行链接
        self.left_widget.currentRowChanged.connect(self.display)
        self.label_show_camera.setAlignment(Qt.AlignCenter) # 让label_show_camera里面的内容居中

        # 第二页需要用的组件
        # label_pic 用于替换第二页中的图标，用于展示图片
        self.label_pic = QLabel(self.pic_widget)  # 该Label用显示 '文字识别'页面的图片
        self.label_pic.hide()  # 隐藏该组件，点击按钮时才显示并放入图片
        self.delete_pic.hide()
        self.verticalLayout_4.addWidget(self.label_pic, 0, Qt.AlignCenter)

        # 第三页需要用的
        # self.timer_camera = QTimer()  # 需要定时器刷新摄像头界面
        self.detect_flag = 0
        self.label_imgshow.setScaledContents(True)  # 图片自适应显示
        self.label_imgshow_res.setScaledContents(True)  # 检测结果图片自适应显示


    def slot_init(self):
        self.video_button.clicked.connect(self.upload_video)
        self.stop_button.clicked.connect(self.video_stop)
        self.video_continue.clicked.connect(self.video_start)
        self.timer.timeout.connect(self.timer_update)
        self.timer_camera.timeout.connect(self.show_camera)
        self.page3_cam.clicked.connect(self.btn_open_cam_click)
        self.page3_cut.clicked.connect(self.photo_catch)
        # self.cam_open.clicked.connect(self.photo_catch)
        # self.cam_pic.clicked.connect(self.show_dialog)
        # self.exit.clicked.connect(self.quit)
        self.upload_pic_5.clicked.connect(self.yolo_recog)  # 图片上传页面识别
        self.upload_pic.clicked.connect(self.up_photo)  # 点击该按钮展示图片
        self.delete_pic.clicked.connect(self.return_pic)  # 点击该按钮返回上传界面



    def display(self, index):  # 将stackwidget和 listwidget进行连接
        self.stack_page.setCurrentIndex(index)

    def initDrag(self):
        # 设置鼠标跟踪判断扳机默认值
        self._move_drag = False
        self._bottom_drag = False
        self._right_drag = False
        self._left_drag = False
        self._right_bottom_corner_drag = False
        self._left_bottom_corner_drag = False

    def setCloseButton(self, bool):
        # 给widget定义一个setCloseButton函数，为True时设置一个关闭按钮
        if bool == True:
            self.CloseButton.clicked.connect(self.close)  # 按钮信号连接到关闭窗口的槽函数

    def resizeEvent(self, QResizeEvent):
        # 自定义窗口调整大小事件

        # 设置在边缘多少位置范围会触发，如左部拉伸则会在距离左边缘的5，高度为(控件高-5)的高度
        self._left_rect = [QPoint(x, y) for x in range(0, 5)
                           for y in range(5, self.height() - 5)]
        # print(self._left_rect)
        self._right_rect = [QPoint(x, y) for x in range(self.width() - 5, self.width() + 1)
                            for y in range(5, self.height() - 5)]
        self._bottom_rect = [QPoint(x, y) for x in range(5, self.width() - 5)
                             for y in range(self.height() - 5, self.height() + 1)]
        self._right_bottom_corner_rect = [QPoint(x, y) for x in range(self.width() - 5, self.width() + 1)
                                          for y in range(self.height() - 5, self.height() + 1)]
        self._left_bottom_corner_rect = [QPoint(x, y) for x in range(0, 5)
                                         for y in range(self.height() - 5, self.height() + 1)]

    def mouseMoveEvent(self, event):
        # 判断鼠标位置切换鼠标手势
        if event.pos() in self._right_bottom_corner_rect:
            self.setCursor(Qt.SizeFDiagCursor)

        elif event.pos() in self._left_bottom_corner_rect:
            self.setCursor(Qt.SizeBDiagCursor)

        elif event.pos() in self._bottom_rect:
            self.setCursor(Qt.SizeVerCursor)

        elif event.pos() in self._right_rect:
            self.setCursor(Qt.SizeHorCursor)

        elif event.pos() in self._left_rect:
            self.setCursor(Qt.SizeHorCursor)

        else:
            self.setCursor(Qt.ArrowCursor)

        # 当鼠标左键点击不放及满足点击区域的要求后，分别实现不同的窗口调整
        if Qt.LeftButton and self._right_drag:
            # 右侧调整窗口宽度
            self.resize(event.pos().x(), self.height())
            event.accept()
        elif Qt.LeftButton and self._left_drag:
            # 左侧调整窗口高度
            if self.width() - event.pos().x() > self.minWidth:
                self.resize(self.width() - event.pos().x(), self.height())
                self.move(self.x() + event.pos().x(), self.y())
            event.accept()
        elif Qt.LeftButton and self._bottom_drag:
            # 下侧调整窗口高度
            self.resize(self.width(), event.pos().y())
            event.accept()
        elif Qt.LeftButton and self._right_bottom_corner_drag:
            # 右下角同时调整高度和宽度
            self.resize(event.pos().x(), event.pos().y())
            event.accept()
        elif Qt.LeftButton and self._left_bottom_corner_drag:
            # 左下角同时调整高度和宽度
            if self.width() - event.pos().x() > self.minWidth:
                self.resize(self.width() - event.pos().x(), event.pos().y())
                self.move(self.x() + event.pos().x(), self.y())
            event.accept()
        elif Qt.LeftButton and self._move_drag:
            # 标题栏拖放窗口位置
            self.move(event.globalPos() - self.move_DragPosition)
            event.accept()


    def mousePressEvent(self, event):
        # 重写鼠标点击的事件
        if (event.button() == Qt.LeftButton) and (event.pos() in self._right_bottom_corner_rect):
            # 鼠标左键点击右下角边界区域
            self._right_bottom_corner_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._left_bottom_corner_rect):
            # 鼠标左键点击左下角边界区域
            self._left_bottom_corner_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._left_rect):
            # 鼠标左键点击左侧边界区域
            self._left_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._right_rect):
            # 鼠标左键点击右侧边界区域
            self._right_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.pos() in self._bottom_rect):
            # 鼠标左键点击下侧边界区域
            self._bottom_drag = True
            event.accept()
        elif (event.button() == Qt.LeftButton) and (event.y() < 30):  # 距离标题最上方小于30时，变为拖拽
            # 鼠标左键点击标题栏区域
            self._move_drag = True
            self.move_DragPosition = event.globalPos() - self.pos()
            event.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        # 鼠标释放后，各扳机复位
        self._move_drag = False
        self._right_bottom_corner_drag = False
        self._bottom_drag = False
        self._right_drag = False
        self._left_drag = False
        self._left_bottom_corner_drag = False

    def mouseDoubleClickEvent(self, event):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        return QWidget().mouseDoubleClickEvent(event)


    def setMinMaxButtons(self, bool):
        # 给widget定义一个setMinMaxButtons函数，为True时设置一组最小化最大化按钮
        if bool == True:
            # 最小化按钮
            self.MinButton.clicked.connect(self.showMinimized)  # 按钮信号连接到最小化窗口的槽函数

            # 最大化按钮
            self.MaxButton.clicked.connect(self._changeNormalButton)  # 按钮信号连接切换到恢复窗口大小按钮函数

    def _changeNormalButton(self):
        # 切换到恢复窗口大小按钮
        try:
            self.showMaximized()  # 先实现窗口最大化
            # self._MaximumButton.setText(b'\xef\x80\xb2'.decode("utf-8"))  # 更改按钮文本
            self.MaxButton.setToolTip("恢复")  # 更改按钮提示
            self.MaxButton.disconnect()  # 断开原本的信号槽连接
            self.MaxButton.clicked.connect(self._changeMaxButton)  # 重新连接信号和槽
        except:
            pass

    def upload_video(self):  # 读取视频
        self.video = QFileDialog.getOpenFileName(self, 'Open file', "", "*.avi;;*.mp4;;All Files(*)")
        fps = 0.0
        self.timer.start(30)
        if self.video == ('', ''):
            pass
        else:
            self.cap = cv2.VideoCapture(self.video[0]) #打开影片
            if not self.cap.isOpened():
                print("Cannot open Video File")
                exit()

        if self.cap.isOpened():
            # 尝试获取视频的FPS
            # FPS ---- 每秒多少帧
            try:
                self.FPS = self.cap.get(cv2.CAP_PROP_FPS)
                if isinstance(self.FPS, float):  # 正常获取的FPS是float
                    self.FPS = int(self.FPS)  # 如果正确获取FPS就保存在变量
                    if self.FPS == 0:
                        self.FPS = 20
            except:
                self.FPS = 20  # 没正确获取则设为 20帧/s

            self.timer.start(int(1000 / self.FPS))

    def timer_update(self):   #与计时器进行连接，对视频进行实时监测
        """
        计时器槽函数
        :return:
        """
        fps = 0.0
        t1 = time.time()
        if self.cap.isOpened():

            # 读取某一帧
            ref, frame = self.cap.read()
            if not ref:  # 视频播放完毕
                # 计时器停止计时
                self.timer.stop()
                # 不检测

                # 对话框提示
                QMessageBox.information(self, '播放提示', '视频已播放完毕！')
                # 释放摄像头
                if hasattr(self, 'cap'):
                    self.cap.release()
                    del self.cap
                return

            # 格式转变，BGRtoRGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 转变成Image
            frame = Image.fromarray(np.uint8(frame))
            # 进行检测

            fname,self.result = self.yolo.detect_image(frame)
            frame = np.array(fname)
            # detect_image(frame) 返回两个参数，第一个是绘制方框后的图片，第二个是结果，包括[类别，置信度，位置]

            # RGBtoBGR满足opencv显示格式
            # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            fps = (fps + (1. / (time.time() - t1))) / 2
            print("fps= %.2f" % (fps))
            frame = cv2.putText(frame, "fps= %.2f" % (fps), (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # cv2.imshow("video", frame)

            QtImg = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[1] * 3,
                           QImage.Format_RGB888)

            self.label_show_camera.setPixmap(QPixmap.fromImage(QtImg))  # 在label_show_camera显示图像
            size = QtImg.size()
            # self.ImgDisp.resize(size)  # 根据帧大小调整标签大小
            self.label_show_camera.show()  # 刷新界面

    def video_stop(self):
        # self.cap.release()
        self.timer.stop()
        # 文本显示
        head = '序号\t类名\t置信度\t位置\n'
        temp = ''
        for i, obj in enumerate(self.result):
            name, score, xmin, ymin, xmax, ymax = obj
            score = float(score)
            text = '{i:}\t{name:}\t{score:.2f}\t' \
                   '({xmin:},{ymin:},{xmax:},{ymax:})\n'.format(i=i, name=name, score=score,
                                                                xmin=xmin, ymin=ymin,
                                                                 xmax=xmax, ymax=ymax)
            temp += text
        self.textedit_2.setText(head + temp)

    def video_start(self):
        self.timer.start(int(1000 / self.FPS))
        # self.pushButton_pause.setText('暂停')

    def up_photo(self):   # 在图像识别区域上传图片

        self.fname = QFileDialog.getOpenFileName(self, 'Open file', "", "*.jpg;;*.png;;All Files(*)")
        if self.fname == ('', ''):
            pass
        else:
            img = cv2.imread(self.fname[0])
            # print(self.fname[0])
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            height, width = img.shape[:2]

            if (height, width) > (480, 640):  # 将尺寸大于640,480的图片压缩
                img = cv2.resize(img, (0, 0),fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
            # print(img.shape[:2])
            # opencv 读取图片的样式，不能通过Qlabel进行显示，需要转换为Qimage QImage(uchar * data, int width,
            # int height, Format format, QImageCleanupFunction cleanupFunction = 0, void *cleanupInfo = 0)
            img = QImage(img.data, img.shape[1], img.shape[0], img.shape[1] * 3,
                         QImage.Format_RGB888)
            img = QPixmap.fromImage(img)

            # 将当前pic_widget 所有控件隐藏
            self.pic_label_1.hide()
            self.pic_label_2.hide()
            self.upload_pic.hide()
            self.spaceitem.hide()

            # 展示选择的图片到label_pic
            self.delete_pic.show()
            self.label_pic.show()
            self.label_pic.setPixmap(img)
            # 识别按钮此时激活
            self.upload_pic_5.setEnabled(True)

    def return_pic(self):
        # 隐藏两个控件
        self.delete_pic.hide()
        self.label_pic.hide()

        # 展示四个控件
        self.pic_label_1.show()
        self.pic_label_2.show()
        self.upload_pic.show()
        self.spaceitem.show()
        self.upload_pic_5.setEnabled(False)  # 取消激活识别按钮

    def yolo_recog(self):
        fps = 0.0
        t1 = time.time()

        frame = cv2.imread(self.fname[0])
        height, width = frame.shape[:2]
        if (height, width) > (480, 640):  # 将尺寸大于640,480的图片压缩
            frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
        # 格式转变，BGRtoRGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 转变成Image
        frame = Image.fromarray(np.uint8(frame))
        # 进行检测
        fname, result = self.yolo.detect_image(frame)  #获取识别的图片和结果
        frame = np.array(fname)

        fps = (fps + (1. / (time.time() - t1))) / 2
        print("fps= %.2f" % (fps))
        frame = cv2.putText(frame, "fps= %.2f" % (fps), (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        QtImg = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[1] * 3,QImage.Format_RGB888)
        self.label_pic.setPixmap(QPixmap.fromImage(QtImg))  # 在label_pic显示画框框后的图片

        # 文本显示
        head = '序号\t类名\t置信度\t位置\n'
        temp = ''
        for i, obj in enumerate(result):
            name, score, xmin, ymin, xmax, ymax = obj
            score = float(score)
            text = '{i:}\t{name:}\t{score:.2f}\t' \
                   '({xmin:},{ymin:},{xmax:},{ymax:})\n'.format(i=i, name=name, score=score,
                                                                xmin=xmin, ymin=ymin,
                                                                xmax=xmax, ymax=ymax)
            temp += text
        self.textEdit.setText(head + temp)


    def btn_open_cam_click(self):  # 检测是否连接相机
        if self.timer_camera.isActive() == False:  # 当检测到相机未连接时
            flag = self.cap.open(self.cap_num)

            if flag == False:
                msg = QMessageBox.warning(self, 'Warning', '请检查相机是否与电脑连接正确',
                                          buttons=QMessageBox.ok, defaultButton=QMessageBox.Ok)
            else:
                self.timer_camera.start(30)
                self.cap.set(3, 1920)  # 设置相机的分辨率 为1920*1080
                self.cap.set(4, 1080)
                self.page3_cam.setText('关闭相机')
        # 检测到相机
        else:
            self.timer_camera.stop()
            self.cap.release()
            self.label_imgshow.clear()
            self.page3_cam.setText(u'打开相机')

    def show_camera(self):

        if self.detect_flag == 0:
            fps = 0.0
            t1 = time.time()
            ret, frame = self.cap.read()
            frame = cv2.resize(frame, (640, 480))
            # 格式转变，BGRtoRGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 转变成Image
            frame = Image.fromarray(np.uint8(frame))
            # 进行检测
            self.frame1, self.result1 = self.yolo.detect_image(frame)
            self.frame1 = np.array(self.frame1)
            # RGBtoBGR满足opencv显示格式
            # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            fps = (fps + (1. / (time.time() - t1))) / 2
            print("fps= %.2f" % (fps))
            self.frame1 = cv2.putText(self.frame1, "fps= %.2f" % (fps), (0, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # opencv 读取图片的样式，不能通过Qlabel进行显示，需要转换为Qimage QImage(uchar * data, int width,
            # int height, Format format, QImageCleanupFunction cleanupFunction = 0, void *cleanupInfo = 0)
            QtImg = QImage(self.frame1.data, self.frame1.shape[1], self.frame1.shape[0], self.frame1.shape[1] * 3,
                           QImage.Format_RGB888)
            self.label_imgshow.setPixmap(QPixmap.fromImage(QtImg))  # 在label_show_camera显示图像

    def photo_catch(self):
        QtImg = QImage(self.frame1.data, self.frame1.shape[1], self.frame1.shape[0], self.frame1.shape[1] * 3,
                       QImage.Format_RGB888)
        self.label_imgshow_res.setPixmap(QPixmap.fromImage(QtImg))  # 在label_show_camera显示图像
        # 文本显示
        head = '序号\t类名\t置信度\t位置\n'
        temp = ''
        for i, obj in enumerate(self.result1):
            name, score, xmin, ymin, xmax, ymax = obj
            score = float(score)
            text = '{i:}\t{name:}\t{score:.2f}\t' \
                   '({xmin:},{ymin:},{xmax:},{ymax:})\n'.format(i=i, name=name, score=score,
                                                                xmin=xmin, ymin=ymin,
                                                                xmax=xmax, ymax=ymax)
            temp += text
        self.textEdit_2.setText(head + temp)

if __name__ == '__main__':
    app=QApplication(sys.argv)

    window=Mainwindow()
    window.show()
    sys.exit(app.exec_())
