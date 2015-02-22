# HumanDetection
Human detection program for Inria Person Dataset

# installation

Download by git

```
git clone https://github.com/rupy/HumanDetection.git
```

edit configure file: config.yml

# Usage

## AnnotationGenerator

Annotation Generator is a GUI tool to generate annotation information for each image to learn dataset by opencv_traincascade.
You can create region information of objects to be detected. To use this class, you have to change config.yml for your own file system as follow:
- pos_img_dir: Directory contains images to add annotations.
- my_annotation_dir: Directory to save annotation infomations as pickle file.
- my_annotation_img_dir: Directory to save sample annotated images.
