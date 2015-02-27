#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os
import cv2
import logging
from PySide import QtCore, QtGui
try:
   import cPickle as pickle
except:
   import pickle
import image_dataset
import config_dialog

class AnnotationGUI(QtGui.QMainWindow):

    def __init__(self):

        # log setting
        program = os.path.basename(sys.argv[0])
        self.logger = logging.getLogger(program)
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')

        super(AnnotationGUI, self).__init__()
        self.setWindowTitle('Annotation Tool')

        self.dataset = image_dataset.ImageDataSet()


        self.dialog = None
        if self.dataset.pos_img_dir == ''\
                or self.dataset.output_dir == ''\
                or not os.path.isdir(self.dataset.pos_img_dir)\
                or not os.path.isdir(self.dataset.output_dir):
            self.open_dir_dialog()

        self.cv_img = None
        self.cv_bbox_img = None
        self.start_pt = None
        self.end_pt = None
        self.bboxes = []

        self.resize(800, 600)
        self.__init_menu_bar()
        self.__init_tool_bar()
        self.__init_status_bar()
        self.__init_ui()



    def __init_ui(self):

        self.image_label = QtGui.QLabel(self)
        self.image_label.setBackgroundRole(QtGui.QPalette.Base)
        self.image_label.installEventFilter(self)

        self.list_widget = QtGui.QListWidget(self)
        self.list_widget.itemSelectionChanged.connect(self.open)

        self.list_widget.setGeometry(10, 50, 200, 500)
        self.image_label.move(220, 50)

        self.__init_list_widget()

    def __init_menu_bar(self):
        menu_bar = QtGui.QMenuBar()
        file_menu = QtGui.QMenu('File', self)
        open_action = file_menu.addAction('Open')
        open_action.triggered.connect(self.open_dir_dialog)
        exit_action = file_menu.addAction('Close Annotation Tool')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(QtGui.qApp.quit)
        menu_bar.addMenu(file_menu)
        self.setMenuBar(menu_bar)

    def __init_tool_bar(self):
        open_action = QtGui.QAction(self.style().standardIcon(QtGui.QStyle.SP_DirOpenIcon), 'Open', self)
        open_action.triggered.connect(self.open_dir_dialog)
        open_action.setShortcut('Ctrl+O')

        save_action = QtGui.QAction(self.style().standardIcon(QtGui.QStyle.SP_DialogSaveButton), 'Save', self)
        save_action.triggered.connect(self.save)
        save_action.setShortcut('Ctrl+S')

        undo_action = QtGui.QAction(self.style().standardIcon(QtGui.QStyle.SP_TrashIcon), 'Undo', self)
        undo_action.triggered.connect(self.remove_box)
        undo_action.setShortcut('Ctrl+Z')

        count_action = QtGui.QAction(self.style().standardIcon(QtGui.QStyle.SP_MessageBoxInformation), 'Count', self)
        count_action.triggered.connect(self.count_all_bbox)
        count_action.setShortcut('Ctrl+C')

        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(open_action)
        self.toolbar.addAction(save_action)
        self.toolbar.addAction(undo_action)
        self.toolbar.addAction(count_action)

    def __init_status_bar(self):
        self.status_label = QtGui.QLabel()
        self.status_label.setText('')
        self.status_bar = self.statusBar()
        self.status_bar.addWidget(self.status_label)

    def __init_list_widget(self):

        # add list items
        self.list_widget.clear()
        self.list_widget.addItems(self.dataset.pos_img_files)

        # set icon
        for i, is_made in enumerate(self.dataset.get_annotation_existence_list()):
            if is_made:
                self.list_widget.item(i).setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogYesButton))
            else:
                self.list_widget.item(i).setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogNoButton))
        self.list_widget.setCurrentRow(0)

    def open_dir_dialog(self):
        self.dialog = config_dialog.ConfigDialig(self, self.dataset)
        result = self.dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            self.dataset.save_config()
            self.__init_list_widget()
            self.open()
        elif result == QtGui.QDialog.Rejected:
            pass
        print result

    def count_all_bbox(self):

        # show count in message box
        msgBox = QtGui.QMessageBox()
        msgBox.setText("all boxes count: %d" % self.dataset.count_all_bboxes())
        msgBox.exec_()

    def convert_cv_img2qt_img(self, cv_img):
        height, width, dim = cv_img.shape
        bytes_per_line = dim * width
        qt_img = QtGui.QImage(cv_img.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        qt_img_rgb = qt_img.rgbSwapped() # BGR to RGB
        return qt_img_rgb

    def load_image(self, img_file):

        # read image
        self.cv_img = self.dataset.read_img(img_file)

        # draw bounding boxes
        self.draw_bbox()
        self.set_image_label()

        # set labels
        self.status_label.setText("box num: %d" % len(self.bboxes))

    def eventFilter(self, source, event):
        # drag start
        if event.type() == QtCore.QEvent.MouseButtonPress and source is self.image_label:
            if event.button() == QtCore.Qt.LeftButton:
                pos = event.pos()
                x = min(max(pos.x(), 0), self.cv_img.shape[1] - 1)
                y = min(max(pos.y(), 0), self.cv_img.shape[0] - 1)
                pt = (x, y)
                self.start_pt = pt
                # print "Drag start (%d, %d)" % pt
        # dragging
        if event.type() == QtCore.QEvent.MouseMove and source is self.image_label:
            if event.buttons() & QtCore.Qt.LeftButton: # use buttons() instead of button()
                pos = event.pos()
                x = min(max(pos.x(), 0), self.cv_img.shape[1] - 1)
                y = min(max(pos.y(), 0), self.cv_img.shape[0] - 1)
                pt = (x, y)
                self.end_pt = pt
                # print "Dragging (%d, %d)" % pt
                self.draw_bbox()
                self.set_image_label()
        # drag end
        if event.type() == QtCore.QEvent.MouseButtonRelease and source is self.image_label:
            if event.button() == QtCore.Qt.LeftButton:
                if self.start_pt is not None:
                    pos = event.pos()
                    x = min(max(pos.x(), 0), self.cv_img.shape[1] - 1)
                    y = min(max(pos.y(), 0), self.cv_img.shape[0] - 1)
                    pt = (x, y)
                    self.end_pt = pt
                    self.bboxes.append((self.start_pt, self.end_pt))
                    self.start_pt = self.end_pt = None
                    # print "Drag end (%d, %d)" % pt
                    self.draw_bbox()
                    self.set_image_label()
                self.status_label.setText("box num: %d" % len(self.bboxes))

        return QtGui.QWidget.eventFilter(self, source, event)

    def draw_bbox(self):
        if self.cv_img is not None:
            self.cv_bbox_img = self.dataset.draw_areas(self.cv_img, self.start_pt, self.end_pt, self.bboxes)

    def set_image_label(self):
        if self.cv_bbox_img is not None:
            qt_img = self.convert_cv_img2qt_img(self.cv_bbox_img)
            self.image_label.setPixmap(QtGui.QPixmap.fromImage(qt_img))
            self.image_label.adjustSize()

    def save(self):

        # image path
        idx = self.list_widget.currentRow()
        img_file = self.dataset.pos_img_files[idx]

        # save
        self.dataset.save_annotation(img_file, self.bboxes)
        self.dataset.write_bbox_img(img_file, self.cv_bbox_img)

        # reload annotation files
        self.dataset.reload_my_annotation_files()

        # change current icon yes
        self.list_widget.item(idx).setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogYesButton))

        # show msg box
        msgBox = QtGui.QMessageBox()
        msgBox.setText("saved")
        msgBox.exec_()

    def remove_box(self):
        # get current image path
        idx = self.list_widget.currentRow()
        img_file = self.dataset.pos_img_files[idx]

        # delete last box
        if len(self.bboxes) > 0:
            self.bboxes.pop()
            print self.bboxes
        else:
            self.logger.info('no bounding boxes to delete')
        self.load_image(img_file)

    def open(self):
        # get current image path
        idx = self.list_widget.currentRow()
        img_file = self.dataset.pos_img_files[idx]

        # load
        self.bboxes = self.dataset.load_annotation(img_file)
        self.load_image(img_file)

if __name__ == '__main__':

    import sys

    # log level setting
    logging.root.setLevel(level=logging.INFO)

    app = QtGui.QApplication(sys.argv)
    # app.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
    ag = AnnotationGUI()
    ag.show()
    sys.exit(app.exec_())