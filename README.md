# HumanDetection
Human detection program for Inria Person Dataset

# installation

Download by git

```
git clone https://github.com/rupy/HumanDetection.git
```

or you can download as zip file from https://github.com/rupy/HumanDetection/archive/master.zip.

Edit configure file, config.yml for your own file system. output directories are automatically created by program.

# Usage

## AnnotationGenerator

### overview and configuration

Annotation Generator is a GUI tool to generate annotation information for each image to learn dataset by opencv_traincascade.
You can create region information of objects to be detected. To use this class, you have to change config.yml for your own file system as follow:
- pos_img_dir: Directory contains images to add annotations.
- my_annotation_dir: Directory to save annotation infomations as pickle file. This directory is automatically created.
- my_annotation_img_dir: Directory to save sample annotated images. This directory is automatically created.

### code

```python
# log level setting
logging.root.setLevel(level=logging.INFO)

# generate AnnotationGenerator
generator = AnnotationGenerator()

# generate annotations by GUI
# if given False, generator skips file you already added annotations.
# if given True, you can edit file you alreadt added annotations.
generator.generate_annotations(False)

# create positive.dat for opencv
generator.create_positive_dat()
```
