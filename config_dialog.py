from PySide import QtCore, QtGui

class ConfigDialig(QtGui.QDialog):
 
    def __init__(self, parent, dataset):
        super(ConfigDialig, self).__init__(parent)

        self.dataset = dataset
        self.tmp_config = self.dataset.config

        self.setWindowTitle('title')
        # self.setWindowFlags(QtCore.Qt.Tool)

        self.layout = QtGui.QVBoxLayout()

        self.pos_label = QtGui.QLabel()
        self.pos_label.setText('Positive Directory')
        self.layout.addWidget(self.pos_label)
        self.pos_dir_line_edit = QtGui.QLineEdit(self.dataset.pos_img_dir)
        self.layout.addWidget(self.pos_dir_line_edit)
        self.pos_dir_button = QtGui.QPushButton('Browse')
        self.pos_dir_button.clicked.connect(self.set_config_pos)
        self.layout.addWidget(self.pos_dir_button)

        self.neg_label = QtGui.QLabel()
        self.neg_label.setText('Negative Directory')
        self.layout.addWidget(self.neg_label)
        self.neg_dir_line_edit = QtGui.QLineEdit(self.dataset.neg_img_dir)
        self.layout.addWidget(self.neg_dir_line_edit)
        self.neg_dir_button = QtGui.QPushButton('Browse')
        self.neg_dir_button.clicked.connect(self.set_config_neg)
        self.layout.addWidget(self.neg_dir_button)

        self.test_label = QtGui.QLabel()
        self.test_label.setText('Test Directory')
        self.layout.addWidget(self.test_label)
        self.test_dir_line_edit = QtGui.QLineEdit(self.dataset.test_img_dir)
        self.layout.addWidget(self.test_dir_line_edit)
        self.test_dir_button = QtGui.QPushButton('Browse')
        self.test_dir_button.clicked.connect(self.set_config_test)
        self.layout.addWidget(self.test_dir_button)

        self.output_label = QtGui.QLabel()
        self.output_label.setText('Output Directory')
        self.layout.addWidget(self.output_label)
        self.output_dir_line_edit = QtGui.QLineEdit(self.dataset.output_dir)
        self.layout.addWidget(self.output_dir_line_edit)
        self.output_dir_button = QtGui.QPushButton('Browse')
        self.output_dir_button.clicked.connect(self.set_config_output)
        self.layout.addWidget(self.output_dir_button)

        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok| QtGui.QDialogButtonBox.Cancel)
        # self.dialog_button.addButton(ok_button, QtGui.QDialogButtonBox.ActionRole)
        # self.dialog_button.addButton(ng_button, QtGui.QDialogButtonBox.ActionRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def set_config_pos(self):
        get_dir = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory")
        if get_dir:
            if not get_dir.endswith('/'):
                get_dir += '/'
            self.pos_dir_line_edit.setText(get_dir)
            self.tmp_config['dataset']['pos_img_dir'] = get_dir

    def set_config_neg(self):
        get_dir = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory")
        if get_dir:
            if not get_dir.endswith('/'):
                get_dir += '/'
            self.neg_dir_line_edit.setText(get_dir)
            self.tmp_config['dataset']['neg_img_dir'] = get_dir

    def set_config_test(self):
        get_dir = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory")
        if get_dir:
            if not get_dir.endswith('/'):
                get_dir += '/'
            self.test_dir_line_edit.setText(get_dir)
            self.tmp_config['dataset']['test_img_dir'] = get_dir

    def set_config_output(self):
        get_dir = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory")
        if get_dir:
            if not get_dir.endswith('/'):
                get_dir += '/'
            self.output_dir_line_edit.setText(get_dir)
            self.tmp_config['dataset']['output_img_dir'] = get_dir
