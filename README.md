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

### simple code

```python
# log level setting
logging.root.setLevel(level=logging.INFO)

# generate AnnotationGenerator
generator = AnnotationGenerator()

# generate annotations by GUI
# if given True, generator skips file you already added annotations(default).
# if given False, you can edit file you already added annotations.
generator.generate_annotations(True)

# create positive.dat for opencv
generator.create_positive_dat()
```
### how to annotate

You can drag point to point in image to create regions. You can use keys as follow:
- [d] key: Delete a region added last.
- [space] key: Save regions as pickle & go to next image
- [q] key: Quit annotation work

You can quit annotation work. You can start from the image you quit brefore if you give True to generate_annotations().
