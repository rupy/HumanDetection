#coding: utf-8

import cv2
import pickle

def show_cv_image(window_name, img):
    window_name_encoded = unicode(window_name, 'utf-8').encode('cp932')
    cv2.namedWindow(window_name_encoded)
    cv2.imshow(window_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def image_crop(img,left_top, right_bottom):
    return img[left_top[1]:right_bottom[1], left_top[0]:right_bottom[0]]
