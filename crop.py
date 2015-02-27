#!/usr/bin/env python
# -*- coding: utf-8 -*-

from image_dataset import ImageDataSet
import logging

if __name__ == '__main__':

    logging.root.setLevel(level=logging.INFO)
    dataset = ImageDataSet()
    dataset.create_crop_with_my_annotation()

