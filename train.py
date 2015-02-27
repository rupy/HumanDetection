#!/usr/bin/env python
# -*- coding: utf-8 -*-

from image_dataset import ImageDataSet
import logging

if __name__ == '__main__':

    logging.root.setLevel(level=logging.INFO)
    dataset = ImageDataSet()
    dataset.train_cascade(feature_type='HOG', max_false_alarm_rate=0.4, min_hit_rate=0.995, width=24, height=24, pos_rate=0.5)

