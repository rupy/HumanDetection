#coding: utf-8

import os
import re
import cv2
import image_util as iu
import logging
import sys
import yaml
import subprocess

class InriaPersonDataSet:

    CONFIG_YAML = 'config.yml'

    def __init__(self):

        # log setting
        program = os.path.basename(sys.argv[0])
        self.logger = logging.getLogger(program)
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')

        # load config file
        f = open(InriaPersonDataSet.CONFIG_YAML, 'r')
        self.config = yaml.load(f)
        f.close()

        # set dataset path
        self.pos_img_dir = self.config['dataset']['pos_img_dir']
        self.neg_img_dir = self.config['dataset']['neg_img_dir']
        self.annotation_dir = self.config['dataset']['annotation_dir']

        # set output path
        self.cropped_dir = self.config['output']['cropped_dir']
        self.bounding_box_out_dir = self.config['output']['bounding_box_out_dir']
        self.out_dir = self.config['output']['out_dir']
        self.cascade_xml_dir = self.config['output']['cascade_xml']

        # create output paths
        if not os.path.isdir(self.cropped_dir):
            os.mkdir(self.cropped_dir)
        if not os.path.isdir(self.bounding_box_out_dir):
            os.mkdir(self.bounding_box_out_dir)
        if not os.path.isdir(self.out_dir):
            os.mkdir(self.out_dir)
        if not os.path.isdir(self.cascade_xml_dir):
            os.mkdir(self.cascade_xml_dir)

        # set array of all file names
        self.pos_img_files = [file_name for file_name in os.listdir(self.pos_img_dir) if not file_name.startswith('.')]
        self.neg_img_files = [file_name for file_name in os.listdir(self.neg_img_dir) if not file_name.startswith('.')]
        self.cropped_files = [file_name for file_name in os.listdir(self.cropped_dir) if not file_name.startswith('.')]

    def parse_annotation_file(self, img_file_name):

        # image annotation path
        annotation_path = self.annotation_dir + os.path.splitext(img_file_name)[0] + '.txt'

        # open annotation file
        f = open(annotation_path)
        lines = f.readlines()
        f.close()

        # parse annotation file
        object_list = []
        object_info = {}
        ground_truth = None
        img_size = None

        for line in lines:
            # print line,

            # get image size
            m = re.match(r'Image size \(X x Y x C\) : (\d+) x (\d+) x 3', line)
            if m:
                img_size = (int(m.group(1)), int(m.group(2)))
                # print img_size

            # get ground truth
            m = re.match(r'Objects with ground truth : (\d+)', line)
            if m:
                ground_truth = int(m.group(1))
                # print ground_truth

            if line.find('# Details for object') != -1:
                object_info = {}
                # print '# Details for object'

            # get center
            m = re.match(r'Center point on object (\d)+ "PASperson" \(X, Y\) : \((\d+), (\d+)\)', line)
            if m:
                center = (int(m.group(2)), int(m.group(3)))
                # print center
                object_info['center'] = center

            # get bounding box
            m = re.match(r'Bounding box for object (\d+) "PASperson" \(Xmin, Ymin\) - \(Xmax, Ymax\) : \((\d+), (\d+)\) - \((\d+), (\d+)\)', line)
            if m:
                bounding_box = [(int(m.group(2)), int(m.group(3))), (int(m.group(4)), int(m.group(5)))]
                # print bounding_box
                object_info['bounding_box'] = bounding_box
                object_list.append(object_info)

        # check number of objects
        if len(object_list) != ground_truth:
            Exception("parsing error: ground truth does not match with object number.")
            return None

        # create annotation info
        annotation_info = {
            'img_size': img_size,
            'ground_truth': ground_truth,
            'object_list': object_list
        }

        return annotation_info

    def draw_bounding_boxes_for_all(self):
        self.logger.info("begin drawing bounding boxes")
        for file_name in self.pos_img_files:

            # draw bounding box
            self.draw_bounding_boxes_and_write_file(file_name)

    def draw_bounding_boxes_and_write_file(self, file_name):

        file_path = self.pos_img_dir + file_name
        self.logger.info("drawing bounding box: " + file_path)

        # read image
        img = cv2.imread(file_path, cv2.IMREAD_COLOR)

        # read annotation file to get annotation info
        annotation_info = self.parse_annotation_file(file_name)

        # iterate object list and draw bounding boxes
        for object_info in annotation_info['object_list']:
            bounding_box = object_info['bounding_box']
            cv2.rectangle(img, bounding_box[0], bounding_box[1], (0, 0, 255), 5)

        # output file
        cv2.imwrite(self.bounding_box_out_dir + 'b_' + file_name, img)

    def create_crop_for_all(self):
        self.logger.info("begin creating crop image")
        for file_name in self.pos_img_files:

            # create crop
            self.create_crop_write_file(file_name)

    def create_crop_write_file(self, file_name):

        file_path = self.pos_img_dir + file_name
        self.logger.info("creating crop image: " + file_path)

        # read image
        img = cv2.imread(file_path, cv2.IMREAD_COLOR)

        # read annotation file to get annotation info
        annotation_info = self.parse_annotation_file(file_name)

        # iterate object list and create crop images
        for i, object_info in enumerate(annotation_info['object_list']):
            crop_box = object_info['bounding_box']
            cropped_img = iu.image_crop(img, crop_box[0], crop_box[1])
            out_file_name = 'c_' + os.path.splitext(file_name)[0] + '_' + str(i) + '.' + os.path.splitext(file_name)[1]
            cv2.imwrite(self.cropped_dir + out_file_name, cropped_img)

    def create_positive_dat(self):
        output_text = ""
        self.logger.info("begin creating positive.dat")
        for file_name in self.pos_img_files:

            file_path = self.pos_img_dir + file_name
            annotation_info = self.parse_annotation_file(file_name)
            output_text += "%s  %d  " % (file_path, annotation_info['ground_truth'])
            for object_info in annotation_info['object_list']:
                x_min, y_min = object_info['bounding_box'][0]
                x_max, y_max = object_info['bounding_box'][1]
                width = x_max - x_min
                height = y_max - y_min
                output_text += "%d %d %d %d  " % (x_min, y_min, width, height)
            output_text += "\n"
        # print output_text
        self.logger.info("writing data to positive.dat")
        f = open('positive.dat', 'w')
        f.write(output_text)
        f.close()
        self.logger.info("completed writing data to positive.dat")

        params = {
            'info': 'positive.dat',
            'vec': 'positive.vec',
            'num': len(self.pos_img_files),
            'width': 40,
            'height': 40
        }
        cmd = "opencv_createsamples -info %(info)s -vec %(vec)s -num %(num)d -w %(width)d -h %(height)d" % params
        self.logger.info("running command: %s", cmd)
        subprocess.call(cmd.strip().split(" "))

    def create_negative_dat(self):
        output_text = ""
        self.logger.info("begin creating positive.dat")
        for file_name in self.neg_img_files:

            file_path = self.neg_img_dir + file_name
            output_text += file_path
            output_text += "\n"
        # print output_text
        self.logger.info("writing data to negative.dat")
        f = open('negative.dat', 'w')
        f.write(output_text)
        f.close()
        self.logger.info("completed writing data to positive.dat")

    def opencv_train_cascade(self, feature_type='HOG'):
        pos_size = len(self.pos_img_files)
        neg_size = len(self.neg_img_files)

        params = {
            'data': self.cascade_xml_dir,
            'vec': 'positive.vec',
            'bg': 'negative.dat',
            'num_pos': pos_size * 0.9,
            'num_neg': neg_size,
            'feature_type': feature_type,
            'max_false_alarm_rate': 0.4,
            'width': 40,
            'height': 40
        }

        cmd = "opencv_traincascade -data %(data)s -vec %(vec)s -bg %(bg)s -numPos %(num_pos)d -numNeg %(num_neg)d -featureType %(feature_type)s -maxFalseAlarmRate %(max_false_alarm_rate)f -w %(width)d -h %(height)d" % params

        self.logger.info("running command: %s", cmd)
        subprocess.call(cmd.strip().split(" "))

    def __inside(self, r, q):
        rx, ry, rw, rh = r
        qx, qy, qw, qh = q
        return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh


    def __draw_detections(self, img, rects, thickness = 1):
        for x, y, w, h in rects:
            # the HOG detector returns slightly larger rectangles than the real objects.
            # so we slightly shrink the rectangles to get a nicer output.
            pad_w, pad_h = int(0.15*w), int(0.05*h)
            cv2.rectangle(img, (x+pad_w, y+pad_h), (x+w-pad_w, y+h-pad_h), (0, 255, 0), thickness)

    def detect(self, image_path, cascade_file='cascade.xml'):

        # read image
        self.logger.info("loading image file: " + image_path)
        img = cv2.imread(image_path)
        if img is None:
            Exception("cannot load image file: " + image_path)

        # read cascade file
        cascade_path = self.cascade_xml_dir + cascade_file
        self.logger.info("loading cascade file: " + cascade_path)
        cascade = cv2.CascadeClassifier(cascade_path)
        if cascade.empty():
            Exception("cannot load cascade file: " + cascade_path)

        # detection
        self.logger.info("detecting")
        found = cascade.detectMultiScale(img, 1.1, 3)
        print found

        # join detection areas
        found_filtered = []
        for ri, r in enumerate(found):
            for qi, q in enumerate(found):
                if ri != qi and self.__inside(r, q):
                    break
                else:
                    found_filtered.append(r)

        # draw detection areas
        self.__draw_detections(img, found)
        self.__draw_detections(img, found_filtered, 3)
        print '%d (%d) found' % (len(found_filtered), len(found))

        # show result
        cv2.imshow('img', img)

        # write file
        cv2.imwrite('result_people_detect.png',img)

        # wait key
        ch = 0xFF & cv2.waitKey()
        if ch == 27:
            return
        cv2.destroyAllWindows()

    def detect_all(self):
        for file in self.pos_img_files:
            self.detect(self.pos_img_dir + file)

if __name__ == '__main__':

    logging.root.setLevel(level=logging.INFO)

    inria = InriaPersonDataSet()

    # inria.draw_bounding_boxes_for_all()
    #
    # inria.create_crop_for_all()
    inria.create_positive_dat()
    inria.create_negative_dat()
    inria.opencv_train_cascade()

    # inria.detect_all()
    # inria.detect('./INRIAPerson/Train/pos/crop001509.png')
