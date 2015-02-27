#coding: utf-8

import os
import cv2
import image_util as iu
import logging
import sys
import yaml
import subprocess
import my_util

class ImageDataSet:

    CONFIG_YAML = 'nail_config.yml'

    OUT_DIR = 'outdir/'
    CROPPED_DIR = 'cropped/'
    CASCADE_XML_DIR = 'hog/'
    MY_ANNOTATION_DIR = 'my_annotation/'
    MY_ANNOTATION_IMG_DIR = 'bbox/'

    def __init__(self):

        # log setting
        program = os.path.basename(sys.argv[0])
        self.logger = logging.getLogger(program)
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')

        # load config file
        f = open(self.CONFIG_YAML, 'r')
        self.config = yaml.load(f)
        f.close()

        self.__init_dir()

        self.cascade = None

    def __init_dir(self):

        # assign empty value if dictionary is not set
        if 'dataset' not in self.config:
            self.config['dataset'] = None
        if 'pos_img_dir' not in self.config['dataset']:
            self.config['dataset']['pos_img_dir'] = ''
        if 'neg_img_dir' not in self.config['dataset']:
            self.config['dataset']['neg_img_dir'] = ''
        if 'test_img_dir' not in self.config['dataset']:
            self.config['dataset']['test_img_dir'] = ''
        if 'output' not in self.config:
            self.config['output'] = None
        if 'output_dir' not in self.config['output']:
            self.config['dataset']['output_dir'] = ''

        # set dataset path
        self.pos_img_dir = self.config['dataset']['pos_img_dir']
        self.neg_img_dir = self.config['dataset']['neg_img_dir']
        self.test_img_dir = self.config['dataset']['test_img_dir']

        # set output path
        self.output_dir = self.config['output']['output_dir']
        self.out_dir = self.output_dir + self.OUT_DIR
        self.cascade_xml_dir = self.output_dir + self.CASCADE_XML_DIR
        self.my_annotation_dir = self.output_dir + self.MY_ANNOTATION_DIR
        self.cropped_dir = self.output_dir + self.CROPPED_DIR
        self.my_annotation_img_dir = self.output_dir + self.MY_ANNOTATION_IMG_DIR

        # create output paths
        if not os.path.isdir(self.out_dir):
            os.makedirs(self.out_dir)
        if not os.path.isdir(self.cascade_xml_dir):
            os.makedirs(self.cascade_xml_dir)
        if not os.path.isdir(self.my_annotation_dir):
            os.makedirs(self.my_annotation_dir)
        if not os.path.isdir(self.cropped_dir):
            os.makedirs(self.cropped_dir)
        if not os.path.isdir(self.my_annotation_img_dir):
            os.makedirs(self.my_annotation_img_dir)

        # set array of all file names
        self.pos_img_files = [file_name for file_name in os.listdir(self.pos_img_dir) if not file_name.startswith('.')]
        self.pos_img_files.sort()
        self.neg_img_files = [file_name for file_name in os.listdir(self.neg_img_dir) if not file_name.startswith('.')]
        self.neg_img_files.sort()
        self.test_img_files = [file_name for file_name in os.listdir(self.test_img_dir) if not file_name.startswith('.')]
        self.test_img_files.sort()
        self.my_annotation_files = [file_name for file_name in os.listdir(self.my_annotation_dir) if not file_name.startswith('.')]
        self.my_annotation_files.sort()
        self.cropped_files = [file_name for file_name in os.listdir(self.cropped_dir) if not file_name.startswith('.')]
        self.cropped_files.sort()

    def save_config(self):

        # save config.yml
        self.logger.info("saving config file")
        f = open(self.CONFIG_YAML, 'w')
        f.write(yaml.dump(self.config, default_flow_style=False))
        f.close()

        # reload valuables related directories
        self.__init_dir()

    def create_crop_with_my_annotation(self):

        self.logger.info("begin creating crop file")
        for annotation_file_name in self.my_annotation_files:

            # read image
            img_file_name = os.path.splitext(annotation_file_name)[0]
            img = cv2.imread(self.pos_img_dir + img_file_name)
            self.logger.info("cropping: %s", img_file_name)

            # read my annotation
            annotation_path = self.my_annotation_dir + annotation_file_name
            bboxes = my_util.my_unpickle(annotation_path)

            # crop
            for i, box in enumerate(bboxes):
                left_up_x = min(box[0][0], box[1][0])
                left_up_y = min(box[0][1], box[1][1])
                right_down_x = max(box[0][0], box[1][0])
                right_down_y = max(box[0][1], box[1][1])
                im_crop = iu.image_crop(img, (left_up_x, left_up_y), (right_down_x, right_down_y))
                root, ext = os.path.splitext(img_file_name)
                crop_file_name = root + str(i) + ext
                cv2.imwrite(self.cropped_dir + crop_file_name, im_crop)
        self.logger.info("completed creating crop file")

    def create_positive_dat_with_my_annotation(self):
        output_text = ""
        self.logger.info("begin creating positive.dat")
        for file_name in self.my_annotation_files:

            # annotation path
            annotation_path = self.my_annotation_dir + file_name
            bboxes = my_util.my_unpickle(annotation_path)
            root, ext = os.path.splitext(file_name)
            output_text += "%s  %d  " % (self.pos_img_dir + root, len(bboxes))
            for bbox in bboxes:
                x_min, y_min = min(bbox[0][0], bbox[1][0]), min(bbox[0][1], bbox[1][1])
                x_max, y_max = max(bbox[0][0], bbox[1][0]), max(bbox[0][1], bbox[1][1])
                w = x_max - x_min
                h = y_max - y_min
                output_text += "%d %d %d %d  " % (x_min, y_min, w, h)
            output_text += "\n"

        self.logger.info("writing data to positive.dat")
        f = open('positive.dat', 'w')
        f.write(output_text)
        f.close()
        self.logger.info("completed writing data to positive.dat")

    def create_positive_dat_by_image_size(self):
        output_text = ""
        self.logger.info("begin creating positive.dat")
        for file_name in self.pos_img_files:

            file_path = self.pos_img_dir + file_name
            im = cv2.imread(file_path)
            output_text += "%s  %d  " % (file_path, 1)
            output_text += "%d %d %d %d  \n" % (0, 0, im.shape[0], im.shape[1])
        self.logger.info("writing data to positive.dat")
        f = open('positive.dat', 'w')
        f.write(output_text)
        f.close()
        self.logger.info("completed writing data to positive.dat")

    def create_samples(self, use_my_annotation=False, width=24, height=24):

        if use_my_annotation:
            self.create_positive_dat_with_my_annotation()
        else:
            self.create_positive_dat_by_image_size()
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
        self.logger.info("writing data to negative.dat")
        f = open('negative.dat', 'w')
        f.write(output_text)
        f.close()
        self.logger.info("completed writing data to negative.dat")

    def train_cascade(self, feature_type='HOG', max_false_alarm_rate=0.4, min_hit_rate=0.995 ,width=24, height=24, pos_rate=0.8):
        pos_size = len(self.pos_img_files)
        neg_size = len(self.neg_img_files)

        params = {
            'data': self.cascade_xml_dir,
            'vec': 'positive.vec',
            'bg': 'negative.dat',
            'num_pos': pos_size * pos_rate,
            'num_neg': neg_size,
            'feature_type': feature_type,
            'min_hit_rate': min_hit_rate,
            'max_false_alarm_rate': max_false_alarm_rate,
            'width': width,
            'height': height
        }

        cmd = "opencv_traincascade -data %(data)s -vec %(vec)s -bg %(bg)s -numPos %(num_pos)d -numNeg %(num_neg)d -featureType %(feature_type)s -minHitRate %(min_hit_rate)s -maxFalseAlarmRate %(max_false_alarm_rate)s -w %(width)d -h %(height)d" % params

        self.logger.info("running command: %s", cmd)
        subprocess.call(cmd.strip().split(" "))

    def inside(self, r, q):
        rx, ry, rw, rh = r
        qx, qy, qw, qh = q
        return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh


    def draw_detections(self, img, rects, thickness = 1):
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
                if ri != qi and self.inside(r, q):
                    break
                else:
                    found_filtered.append(r)

        # draw detection areas
        self.draw_detections(img, found)
        self.draw_detections(img, found_filtered, 3)
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
        for file in self.test_img_files:
            self.detect(self.test_img_dir + file)

    def count_all_bboxes(self):
        sum = 0
        for annotation_file in self.my_annotation_files:
            annotation_path = self.my_annotation_dir + annotation_file
            # print annotation_path
            bboxes = my_util.my_unpickle(annotation_path)
            sum += len(bboxes)
        return sum

    def get_annotation_existence_list(self):
        return [file + '.pkl' in self.my_annotation_files for file in self.pos_img_files]

    def get_annotated_image_files(self):
        return [os.path.splitext(annotation_file)[0] for annotation_file in self.my_annotation_files]

    def get_annotation_path(self, img_file):
        annotation_path = self.my_annotation_dir + img_file + '.pkl'
        return annotation_path

    def get_img_file_by_annotation_file(self, annotation_file):
        img_file = os.path.splitext(annotation_file)[0]
        return img_file


    def load_annotation(self, img_file):
        bboxes = []
        if img_file in self.get_annotated_image_files():

            # annotation path
            annotation_path = self.get_annotation_path(img_file)

            self.logger.info('loading annotation file: %s', annotation_path)

            # load pickle
            bboxes = my_util.my_unpickle(annotation_path)
        return bboxes

    def save_annotation(self, img_file, bboxes):
        annotation_path = self.get_annotation_path(img_file)
        self.logger.info('saving annotation data: %s', annotation_path)
        my_util.my_pickle(bboxes, annotation_path)

    def draw_areas(self, im_orig, start_pt, end_pt, bboxes):
        im_copy = im_orig.copy()
        # draw rectangles
        if start_pt is not None and end_pt is not None:
            cv2.rectangle(im_copy, start_pt, end_pt, (0, 0, 255), 1)
        for box in bboxes:
            cv2.rectangle(im_copy, box[0], box[1], (0, 255, 0), 1)
        return im_copy

    def read_img(self, img_file):
        self.logger.info('loading image file: %s', img_file)
        img_path = self.pos_img_dir + img_file

        # read image
        cv_img = cv2.imread(img_path)
        return cv_img

    def draw_bounding_boxes_for_all(self):
        self.logger.info("begin drawing bounding boxes")
        for file_name in self.my_annotation_files:

            img_file = self.get_img_file_by_annotation_file(file_name)
            cv_img = self.read_img(img_file)
            bboxes = self.load_annotation(img_file)
            cv_bbox_img = self.draw_areas(cv_img, None, None, bboxes)
            # draw bounding box
            self.write_bbox_img(img_file, cv_bbox_img)


    def write_bbox_img(self, img_file, cv_bbox_img):
        bbox_path = self.my_annotation_img_dir + 'bbox_' + img_file
        self.logger.info('saving bounding box data: %s', bbox_path)
        cv2.imwrite(bbox_path, cv_bbox_img)

    def reload_my_annotation_files(self):
        self.my_annotation_files = [file_name for file_name in os.listdir(self.my_annotation_dir) if not file_name.startswith('.')]
        self.my_annotation_files.sort()

if __name__ == '__main__':

    logging.root.setLevel(level=logging.INFO)

    dataset = ImageDataSet()

    dataset.create_crop_with_my_annotation()
    # dataset.create_samples(True, 24, 24)
    # dataset.train_cascade('HOG', 0.4, 0.995 24, 24)

    # dataset.load_cascade_file()
    # dataset.detect_all()
    # dataset.detect('./INRIAPerson/Train/pos/crop001509.png')
#