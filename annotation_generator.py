#coding: utf-8

import os
import cv2
import logging
import sys
import yaml
try:
   import cPickle as pickle
except:
   import pickle

class AnnotationGenerator:

    CONFIG_YAML = 'config.yml'
    GENERATOR_WINDOW_NAME = 'generator'

    def __init__(self):

        # log setting
        program = os.path.basename(sys.argv[0])
        self.logger = logging.getLogger(program)
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')

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

        # initialize mouse event
        cv2.namedWindow(self.GENERATOR_WINDOW_NAME)
        cv2.setMouseCallback(self.GENERATOR_WINDOW_NAME, self.on_mouse)

        # mouse location
        self.im_orig = None
        self.start_pt = (0, 0)
        self.end_pt = (0, 0)
        self.mouse_dragging = False
        self.bboxes = []

    def on_mouse(self, event, x, y, flags, param):

        if event == cv2.EVENT_LBUTTONDOWN:
            self.logger.info('DOWN: %d, %d', x, y)
            self.start_pt = (x, y)
            self.end_pt = (x, y)
            self.mouse_dragging = True
        elif event == cv2.EVENT_LBUTTONUP:
            self.logger.info('UP: %d, %d', x, y)
            self.end_pt = (x, y)
            self.bboxes.append((self.start_pt, self.end_pt))
            self.start_pt = self.end_pt = (0, 0)
            self.mouse_dragging = False
        elif event == cv2.EVENT_MOUSEMOVE and self.mouse_dragging:
            # self.logger.info('DRAG: %d, %d', x, y)
            self.end_pt = (x, y)


    def generate_my_annotation(self, img_path, edit=False):

        # annotation path
        head, tail = os.path.split(img_path)
        # root, ext = os.path.splitext(tail)
        annotation_path = self.my_annotation_dir + tail + '.pkl'

        # bbox path
        bbox_path = self.my_annotation_img_dir + 'bbox_' + tail

        # load image
        self.im_orig = cv2.imread(img_path)

        # if edit is true, load bbox info from annotation file
        if edit:
            f = open(annotation_path, 'rb')
            self.bboxes = pickle.load(f)
            f.close()

        while True:
            im_copy = self.im_orig.copy()

            # draw rectangles
            if self.start_pt is not (0, 0) and self.end_pt is not (0, 0):
                cv2.rectangle(im_copy, self.start_pt, self.end_pt, (0, 0, 255), 1)
            for box in self.bboxes:
                cv2.rectangle(im_copy, box[0], box[1], (0, 255, 0), 1)

            # show image to generate annotations
            cv2.imshow(self.GENERATOR_WINDOW_NAME, im_copy)
            key = cv2.waitKey(10)
            if key == ord('q'): # 'q' key
                cv2.destroyAllWindows()
                return False
            elif key == 32: # sapce key
                self.logger.info('saving annotation data: %s', annotation_path)
                f = open(annotation_path, 'wb')
                pickle.dump(self.bboxes, f)
                f.close()
                self.logger.info('saving bounding box data: %s', bbox_path)
                cv2.imwrite(bbox_path, im_copy)
                self.bboxes = []
                return True
            elif key == ord('d'): # 'd' key
                if len(self.bboxes) > 0:
                    self.bboxes.pop()
                else:
                   self.logger.info('no bounding boxes to delete')

    def generate_annotations(self, skip=True):

        for pos_image_file in self.pos_img_files:

            edit = False
            if pos_image_file in [os.path.splitext(annotation_file)[0] for annotation_file in self.my_annotation_files]:
                if skip:
                    self.logger.info('skipping: %s is already added annotation', pos_image_file)
                    continue
                else:
                    self.logger.info('edit: %s is already added annotation', pos_image_file)
                    edit = True
            else:
                self.logger.info('new: %s', pos_image_file)

            pos_img_path = self.pos_img_dir + pos_image_file
            is_continue = self.generate_my_annotation(pos_img_path, edit)
            if not is_continue:
                return

    def create_positive_dat(self):
        output_text = ""
        self.logger.info("begin creating positive.dat")
        for file_name in self.my_annotation_files:

            # annotation path
            annotation_path = self.my_annotation_dir + file_name
            f = open(annotation_path, 'rb')
            bboxes = pickle.load(f)
            f.close()
            root, ext = os.path.splitext(file_name)
            output_text += "%s  %d  " % (self.pos_img_dir + root, len(bboxes))
            for bbox in bboxes:
                x_min, y_min = min(bbox[0][0], bbox[1][0]), min(bbox[0][1], bbox[1][1])
                x_max, y_max = max(bbox[0][0], bbox[1][0]), max(bbox[0][1], bbox[1][1])
                w = x_max - x_min
                h = y_max - y_min
                output_text += "%d %d %d %d  " % (x_min, y_min, w, h)
            output_text += "\n"
        # print output_text
        self.logger.info("writing data to positive.dat")
        f = open('positive.dat', 'w')
        f.write(output_text)
        f.close()
        self.logger.info("completed writing data to positive.dat")

if __name__ == '__main__':

    logging.root.setLevel(level=logging.INFO)

    generator = AnnotationGenerator()
    generator.generate_annotations(False)
    generator.create_positive_dat()

