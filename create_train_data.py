#!/usr/bin/env python
# -*- coding: utf-8 -*-

from image_dataset import ImageDataSet
import logging

if __name__ == '__main__':

    logging.root.setLevel(level=logging.INFO)
    dataset = ImageDataSet()
    dataset.create_positive_dat_with_my_annotation()
    dataset.create_negative_dat()
    dataset.create_samples(use_my_annotation=True, width=24, height=24)

