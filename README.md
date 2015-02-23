# HumanDetection
Human detection program for Inria Person Dataset

# Installation

Download by git

```
git clone https://github.com/rupy/HumanDetection.git
```

or you can download as zip file from https://github.com/rupy/HumanDetection/archive/master.zip.

## Dependency

You need environment like:

```
Python 2.7
OpenCV 2.4.9
Numpy 1.9.1
PyYAML 3.11
```
If you don't have Numpy and PyYAML, you can install these by pip like:

```Shell
$ pip install numpy
$ pip install pyyaml
$ pip install pyside
```

## Configure file

Edit configure file, config.yml for your own file system. output directories are automatically created by program. Inria Person Dataset is in http://pascal.inrialpes.fr/data/human/.

# Usage

## AnnotationGenerator

### Overview and configuration

Annotation Generator is a GUI tool to generate annotation information for each image to learn dataset by opencv_traincascade.
You don't need to use this class if you use Inria Person Dataset because it has annotation information in it. This program is for the dataset which has no annotation informations. 

You can create region information of objects to be detected. To use this class, you have to change config.yml for your own file system as follow:
- pos_img_dir: Directory contains images to add annotations.
- my_annotation_dir: Directory to save annotation infomations as pickle file. This directory is automatically created.
- my_annotation_img_dir: Directory to save sample annotated images. This directory is automatically created.

### Simple code

Write code as follow:

```python
from annotation_generator import AnnotationGenerator

# log level setting
logging.root.setLevel(level=logging.INFO)

# initialize AnnotationGenerator
generator = AnnotationGenerator()

# Do annotation work by GUI
# if given True, generator skips file you already added annotations(default).
# if given False, you can edit file you already added annotations.
generator.generate_annotations(True)

# create positive.dat for opencv
generator.create_positive_dat()
```

or just run python like this:

```Shell
$ python annotation_generator.py
```
### How to annotate

Drag point to point in image to create regions. You can use keys as follow:
- [d] key: Delete a region added last.
- [space] key: Save regions as pickle & go to next image.
- [q] key: Quit annotation work.

You can quit annotation work anytime. You can start from the image you quit brefore if you give True to generate_annotations().

## AnnotationGUI

### Overview and configuration

Annotation GUI is a GUI tool to generate annotation information for each image to learn dataset by opencv_traincascade.
You don't need to use this class if you use Inria Person Dataset because it has annotation information in it. This program is for the dataset which has no annotation informations.

You can create region information of objects to be detected. To use this class, you have to change config.yml for your own file system as follow:
- pos_img_dir: Directory contains images to add annotations.
- my_annotation_dir: Directory to save annotation infomations as pickle file. This directory is automatically created.
- my_annotation_img_dir: Directory to save sample annotated images. This directory is automatically created.

### Simple code

Write code as follow:

```python
from annotation_generator import AnnotationGenerator

# log level setting
logging.root.setLevel(level=logging.INFO)

# run app
app = QtGui.QApplication(sys.argv)
ag = AnnotationGUI()
ag.show()
sys.exit(app.exec_())
```
or just run python like this:

```Shell
$ python annotation_gui.py
```
### How to annotate

First, choose file name from list, then image will be loaded. Drag point to point in image to create regions. You can save and undo by button. Green icon in the list shows file has annotation information already and red shows no information.

## InriaPersonDataSet

## ImageDataSet
