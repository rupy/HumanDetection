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
import yaml

class AnnotationGUI(QtGui.QWidget):

    CONFIG_YAML = 'config.yml'

    def __init__(self):

        # log setting
        program = os.path.basename(sys.argv[0])
        self.logger = logging.getLogger(program)
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')

        super(AnnotationGUI, self).__init__()
        self.setWindowTitle('Annotation Tool')

        # load config file
        f = open(self.CONFIG_YAML, 'r')
        self.config = yaml.load(f)
        f.close()

        # set dataset path
        self.pos_img_dir = self.config['dataset']['pos_img_dir']

        # set output path
        self.my_annotation_dir = self.config['output']['my_annotation_dir']
        self.my_annotation_img_dir = self.config['output']['my_annotation_img_dir']

        # create output paths
        if not os.path.isdir(self.my_annotation_dir):
            os.makedirs(self.my_annotation_dir)
        if not os.path.isdir(self.my_annotation_img_dir):
            os.makedirs(self.my_annotation_img_dir)

        # set array of all file names
        self.my_annotation_files = [file_name for file_name in os.listdir(self.my_annotation_dir) if not file_name.startswith('.')]
        self.my_annotation_files.sort()
        self.pos_img_files = [file_name for file_name in os.listdir(self.pos_img_dir) if not file_name.startswith('.')]
        self.pos_img_files.sort()

        self.cv_img = None
        self.cv_bbox_img = None
        self.start_pt = None
        self.end_pt = None
        self.bboxes = []

        self.__init_ui()


    def __init_ui(self):

        self.image_label = QtGui.QLabel(self)
        self.image_label.setBackgroundRole(QtGui.QPalette.Base)
        self.image_label.installEventFilter(self)

        self.filename_label = QtGui.QLabel(self)
        self.filename_label.setText("a")

        self.save_button = QtGui.QPushButton('save', self)
        self.save_button.clicked.connect(self.__save)

        self.undo_button = QtGui.QPushButton('undo', self)
        self.undo_button.clicked.connect(self.__remove_box)

        self.count_button = QtGui.QPushButton('count all boxes', self)
        self.count_button.clicked.connect(self.count_all_bbox)

        self.list_widget = QtGui.QListWidget(self)
        self.list_widget.itemSelectionChanged.connect(self.__open)

        self.box_num_label = QtGui.QLabel(self)

        self.list_widget.setGeometry(10, 10, 200, 200)
        self.image_label.move(220, 10)
        self.save_button.move(10, 220)
        self.undo_button.move(100, 220)
        self.count_button.move(10, 250)
        self.filename_label.move(10, 280)
        self.box_num_label.move(10, 310)

        self.__init_list_widget()

    def __init_list_widget(self):

        # add list items
        self.list_widget.clear()
        self.list_widget.addItems(self.pos_img_files)

        # set icon
        for i, is_made in enumerate([file + '.pkl' in self.my_annotation_files for file in self.pos_img_files]):
            if is_made:
                self.list_widget.item(i).setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogYesButton))
            else:
                self.list_widget.item(i).setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogNoButton))
        self.list_widget.setCurrentRow(0)

    def __change_current_icon_yes(self):
        idx = self.list_widget.currentRow()
        self.list_widget.item(idx).setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogYesButton))

    def count_all_bbox(self):
        c = 0
        for annotation_file in self.my_annotation_files:
            annotation_path = self.my_annotation_dir + annotation_file
            f = open(annotation_path, 'rb')
            bboxes = pickle.load(f)
            f.close()
            c += len(bboxes)

        # show count in message box
        msgBox = QtGui.QMessageBox()
        msgBox.setText("all boxes count: %d" % c)
        msgBox.exec_()

    def __load_bbox(self, img_path):
        if os.path.basename(img_path) in [os.path.splitext(annotation_file)[0] for annotation_file in self.my_annotation_files]:

            # annotation path
            base = os.path.basename(img_path)
            annotation_path = self.my_annotation_dir + base + '.pkl'

            self.logger.info('loading annotation file: %s', annotation_path)

            # load pickle
            f = open(annotation_path, 'rb')
            self.bboxes = pickle.load(f)
            f.close()
        else:
            self.bboxes = []

    def __convert_cv_img2qt_img(self, cv_img):
        height, width, dim = self.cv_img.shape
        bytes_per_line = dim * width
        qt_img = QtGui.QImage(cv_img.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        qt_img_rgb = qt_img.rgbSwapped() # BGR to RGB
        return qt_img_rgb

    def __load_image(self, img_path):

        # read image
        self.cv_img = cv2.imread(img_path)

        # draw bounding boxes
        self.__draw_bbox_and_set_image_label()

        # set labels
        self.filename_label.setText(os.path.basename(img_path))
        self.box_num_label.setText("box num: %d" % len(self.bboxes))

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
                self.__draw_bbox_and_set_image_label()
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
                    self.__draw_bbox_and_set_image_label()
                self.box_num_label.setText("box num: %d" % len(self.bboxes))

        return QtGui.QWidget.eventFilter(self, source, event)

    def __draw_dragging_area(self, im_orig):
        im_copy = im_orig.copy()
        # draw rectangles
        if self.start_pt is not None and self.end_pt is not None:
            cv2.rectangle(im_copy, self.start_pt, self.end_pt, (0, 0, 255), 1)
        for box in self.bboxes:
            cv2.rectangle(im_copy, box[0], box[1], (0, 255, 0), 1)
        return im_copy

    def __draw_bbox_and_set_image_label(self):
        if self.cv_img is not None:
            self.cv_bbox_img = self.__draw_dragging_area(self.cv_img)
            qt_img = self.__convert_cv_img2qt_img(self.cv_bbox_img)
            self.image_label.setPixmap(QtGui.QPixmap.fromImage(qt_img))
            self.image_label.adjustSize()

    def __save(self):

        # image path
        idx = self.list_widget.currentRow()
        img_path = self.pos_img_dir + self.pos_img_files[idx]
        # annotation path
        base = os.path.basename(img_path)
        annotation_path = self.my_annotation_dir + base + '.pkl'
        # bbox path
        bbox_path = self.my_annotation_img_dir + 'bbox_' + base

        # save
        self.logger.info('saving annotation data: %s', annotation_path)
        f = open(annotation_path, 'wb')
        pickle.dump(self.bboxes, f)
        f.close()
        self.logger.info('saving bounding box data: %s', bbox_path)
        cv2.imwrite(bbox_path, self.cv_bbox_img)

        # reload annotation files
        self.my_annotation_files = [file_name for file_name in os.listdir(self.my_annotation_dir) if not file_name.startswith('.')]
        self.my_annotation_files.sort()

        # change list widget
        self.__change_current_icon_yes()

        # show msg box
        msgBox = QtGui.QMessageBox()
        msgBox.setText("saved")
        msgBox.exec_()

    def __remove_box(self):
        # get current image path
        idx = self.list_widget.currentRow()
        img_path = self.pos_img_dir + self.pos_img_files[idx]

        # delete last box
        if len(self.bboxes) > 0:
            self.bboxes.pop()
            print self.bboxes
        else:
            self.logger.info('no bounding boxes to delete')
        self.__load_image(img_path)

    def __open(self):
        # get current image path
        idx = self.list_widget.currentRow()
        img_path = self.pos_img_dir + self.pos_img_files[idx]

        # load
        self.logger.info('loading image file: %s', img_path)
        self.__load_bbox(img_path)
        self.__load_image(img_path)

if __name__ == '__main__':
    import sys
    # log level setting
    logging.root.setLevel(level=logging.INFO)

    app = QtGui.QApplication(sys.argv)
    ag = AnnotationGUI()
    ag.show()
    sys.exit(app.exec_())