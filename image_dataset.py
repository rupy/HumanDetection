#coding: utf-8

import os
import re
import cv2
import image_util as iu
import logging
import sys
import yaml
import subprocess

class ImageDataSet:

    CONFIG_YAML = 'config.yml'

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
        self.neg_img_dir = self.config['dataset']['neg_img_dir']

        # set output path
        self.out_dir = self.config['output']['out_dir']
        self.cascade_xml_dir = self.config['output']['cascade_xml_dir']

        # create output paths
        if not os.path.isdir(self.out_dir):
            os.makedirs(self.out_dir)
        if not os.path.isdir(self.cascade_xml_dir):
            os.makedirs(self.cascade_xml_dir)

        # set array of all file names
        self.pos_img_files = [file_name for file_name in os.listdir(self.pos_img_dir) if not file_name.startswith('.')]
        self.pos_img_files.sort()
        self.neg_img_files = [file_name for file_name in os.listdir(self.neg_img_dir) if not file_name.startswith('.')]
        self.neg_img_files.sort()

        self.cascade = None

    def create_positive_dat(self):
        output_text = ""
        self.logger.info("begin creating positive.dat")
        for file_name in self.pos_img_files:

            file_path = self.pos_img_dir + file_name
            im = cv2.imread(file_path)
            output_text += "%s  %d  " % (file_path, 1)
            output_text += "%d %d %d %d  \n" % (0, 0, im.shape[0], im.shape[1])
        # print output_text
        self.logger.info("writing data to positive.dat")
        f = open('positive.dat', 'w')
        f.write(output_text)
        f.close()
        self.logger.info("completed writing data to positive.dat")

    def create_samples(self, width=24, height=24):

        self.create_positive_dat()
        self.create_negative_dat()

        params = {
            'info': 'positive.dat',
            'vec': 'positive.vec',
            'num': len(self.pos_img_files),
            'width': width,
            'height': height
        }
        cmd = "opencv_createsamples -info %(info)s -vec %(vec)s -num %(num)d -w %(width)d -h %(height)d" % params
        self.logger.info("running command: %s", cmd)
        subprocess.call(cmd.strip().split(" "))

    def create_negative_dat(self):
        output_text = ""
        self.logger.info("begin creating negative.dat")
        for file_name in self.neg_img_files:

            file_path = self.neg_img_dir + file_name
            output_text += file_path
            output_text += "\n"
        # print output_text
        self.logger.info("writing data to negative.dat")
        f = open('negative.dat', 'w')
        f.write(output_text)
        f.close()
        self.logger.info("completed writing data to negative.dat")

    def train_cascade(self, feature_type='HOG', max_false_alarm_rate=0.4, width=24, height=24):
        pos_size = len(self.pos_img_files)
        neg_size = len(self.neg_img_files)

        params = {
            'data': self.cascade_xml_dir,
            'vec': 'positive.vec',
            'bg': 'negative.dat',
            'num_pos': pos_size * 0.8,
            'num_neg': neg_size,
            'feature_type': feature_type,
            'max_false_alarm_rate': max_false_alarm_rate,
            'width': width,
            'height': height
        }

        cmd = "opencv_traincascade -data %(data)s -vec %(vec)s -bg %(bg)s -numPos %(num_pos)d -numNeg %(num_neg)d -featureType %(feature_type)s -maxFalseAlarmRate %(max_false_alarm_rate)s -w %(width)d -h %(height)d" % params

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

    def load_cascade_file(self, cascade_file='cascade.xml'):
        cascade_path = self.cascade_xml_dir + cascade_file
        self.logger.info("loading cascade file: " + cascade_path)
        self.cascade = cv2.CascadeClassifier(cascade_path)
        if self.cascade.empty():
            Exception("cannot load cascade file: " + cascade_path)

    def detect(self, image_path):

        # read image
        self.logger.info("loading image file: " + image_path)
        img = cv2.imread(image_path)
        if img is None:
            Exception("cannot load image file: " + image_path)

        # detection
        self.logger.info("detecting")
        found = self.cascade.detectMultiScale(img, 1.1, 3)
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
        # cv2.imshow('img', img)

        # write file
        head, tail = os.path.split(image_path)
        new_img_path = self.out_dir + tail + '.png'
        cv2.imwrite(new_img_path, img)

        # wait key
        ch = 0xFF & cv2.waitKey()
        if ch == 27:
            return
        cv2.destroyAllWindows()

    def detect_all(self):
        for file in self.pos_img_files:
            self.detect(self.pos_img_dir + file)
