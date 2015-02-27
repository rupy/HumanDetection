#!/usr/bin/env python
# -*- coding: utf-8 -*-

from image_dataset import ImageDataSet
import logging

if __name__ == '__main__':

    logging.root.setLevel(level=logging.INFO)
    dataset = ImageDataSet()
    dataset.draw_bounding_boxes_for_all()
