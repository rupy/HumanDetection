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
        # self.image_label.setStyleSheet("border: 2px solid")

        self.filename_label = QtGui.QLabel()

        self.save_button = QtGui.QPushButton('save', self)
        self.save_button.clicked.connect(self.save)

        self.undo_button = QtGui.QPushButton('undo', self)
        self.undo_button.clicked.connect(self.remove_box)

        self.list_widget = QtGui.QListWidget(self)
        self.list_widget.itemSelectionChanged.connect(self.open)

        self.list_widget.setGeometry(10,10,200,200)
        self.image_label.move(220,10)
        self.save_button.setGeometry(10,220,100,40)
        self.undo_button.setGeometry(10,260,100,40)

        self.set_image_paths()
        self.list_widget.setCurrentRow(0)

    def set_image_paths(self):

        self.list_widget.clear()
        self.list_widget.addItems(self.pos_img_files)
        for i, is_made in enumerate([file + '.pkl' in self.my_annotation_files for file in self.pos_img_files]):
            if is_made:
                self.list_widget.item(i).setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogYesButton))
            else:
                self.list_widget.item(i).setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogNoButton))

    def load_bbox(self, img_path):
        if os.path.basename(img_path) in [os.path.splitext(annotation_file)[0] for annotation_file in self.my_annotation_files]:
            self.load(img_path)
        else:
            self.bboxes = []

    def set_image_label(self, img_path):
        self.cv_img = cv2.imread(img_path)
        self.cv_bbox_img = self.draw_dragging_area(self.cv_img)
        qt_img = self.convert_cv_img2qt_img(self.cv_bbox_img)
        self.image_label.setPixmap(QtGui.QPixmap.fromImage(qt_img))
        self.image_label.adjustSize()
        self.filename_label.setText(os.path.basename(img_path))
        self.adjustSize()

    def get_current_item_text(self):
        return self.list_widget.currentItem().text()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseButtonPress and source is self.image_label:
            if event.button() == QtCore.Qt.LeftButton:
                pos = event.pos()
                x = min(max(pos.x(), 0), self.cv_img.shape[1] - 1)
                y = min(max(pos.y(), 0), self.cv_img.shape[0] - 1)
                pt = (x, y)
                self.start_pt = pt
                # print "Drag start (%d, %d)" % pt
        if event.type() == QtCore.QEvent.MouseMove and source is self.image_label:
            if event.buttons() & QtCore.Qt.LeftButton: # use buttons() instead of button()
                pos = event.pos()
                x = min(max(pos.x(), 0), self.cv_img.shape[1] - 1)
                y = min(max(pos.y(), 0), self.cv_img.shape[0] - 1)
                pt = (x, y)
                self.end_pt = pt
                # print "Dragging (%d, %d)" % pt
                self.update_image_label()
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
                    self.update_image_label()
        return QtGui.QWidget.eventFilter(self, source, event)

    def draw_dragging_area(self, im_orig):
        im_copy = im_orig.copy()
        # draw rectangles
        if self.start_pt is not None and self.end_pt is not None:
            cv2.rectangle(im_copy, self.start_pt, self.end_pt, (0, 0, 255), 1)
        for box in self.bboxes:
            cv2.rectangle(im_copy, box[0], box[1], (0, 255, 0), 1)
        return im_copy

    def update_image_label(self):
        if self.cv_img is not None:
            self.cv_bbox_img = self.draw_dragging_area(self.cv_img)
            qt_img = self.convert_cv_img2qt_img(self.cv_bbox_img)
            self.image_label.setPixmap(QtGui.QPixmap.fromImage(qt_img))

    def convert_cv_img2qt_img(self, cv_img):
        height, width, dim = self.cv_img.shape
        bytes_per_line = dim * width
        qt_img = QtGui.QImage(cv_img.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        qt_img_rgb = qt_img.rgbSwapped()
        return qt_img_rgb

    def save(self):

        idx = self.list_widget.currentRow()
        img_path = self.pos_img_dir + self.pos_img_files[idx]
        # annotation path
        head, tail = os.path.split(img_path)
        # root, ext = os.path.splitext(tail)
        annotation_path = self.my_annotation_dir + tail + '.pkl'

        # bbox path
        bbox_path = self.my_annotation_img_dir + 'bbox_' + tail

        self.logger.info('saving annotation data: %s', annotation_path)
        f = open(annotation_path, 'wb')
        pickle.dump(self.bboxes, f)
        f.close()
        self.logger.info('saving bounding box data: %s', bbox_path)
        cv2.imwrite(bbox_path, self.cv_bbox_img)
        self.bboxes = []
        self.my_annotation_files = [file_name for file_name in os.listdir(self.my_annotation_dir) if not file_name.startswith('.')]
        self.my_annotation_files.sort()

    def load(self, img_path):
        # annotation path
        head, tail = os.path.split(img_path)
        # root, ext = os.path.splitext(tail)
        annotation_path = self.my_annotation_dir + tail + '.pkl'
        self.logger.info('loading annotation file: %s', annotation_path)

        f = open(annotation_path, 'rb')
        self.bboxes = pickle.load(f)
        f.close()

    def remove_box(self):
        idx = self.list_widget.currentRow()
        img_path = self.pos_img_dir + self.pos_img_files[idx]
        if len(self.bboxes) > 0:
            self.bboxes.pop()
            print self.bboxes
        else:
            self.logger.info('no bounding boxes to delete')
        self.set_image_label(img_path)

    def open(self):
        idx = self.list_widget.currentRow()
        img_path = self.pos_img_dir + self.pos_img_files[idx]
        self.logger.info('loading image file: %s', img_path)
        self.load_bbox(img_path)
        self.set_image_label(img_path)

if __name__ == '__main__':
    import sys
    # log level setting
    logging.root.setLevel(level=logging.INFO)

    app = QtGui.QApplication(sys.argv)
    ag = AnnotationGUI()
    # ag.set_image_label('/Users/rupy/Documents/recruit_data/gazo/moto/C000103107.jpg')
    ag.show()
    sys.exit(app.exec_())