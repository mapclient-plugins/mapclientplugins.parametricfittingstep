# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'parametricfittingwidget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from opencmiss.utils.zinc.widgets.basesceneviewerwidget import BaseSceneviewerWidget

from  . import resources_rc

class Ui_ParametricFittingWidget(object):
    def setupUi(self, ParametricFittingWidget):
        if not ParametricFittingWidget.objectName():
            ParametricFittingWidget.setObjectName(u"ParametricFittingWidget")
        ParametricFittingWidget.resize(1093, 872)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ParametricFittingWidget.sizePolicy().hasHeightForWidth())
        ParametricFittingWidget.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(ParametricFittingWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.dockWidget = QDockWidget(ParametricFittingWidget)
        self.dockWidget.setObjectName(u"dockWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.dockWidget.sizePolicy().hasHeightForWidth())
        self.dockWidget.setSizePolicy(sizePolicy1)
        self.dockWidget.setMinimumSize(QSize(353, 430))
        self.dockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.dockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.dockWidgetContents.sizePolicy().hasHeightForWidth())
        self.dockWidgetContents.setSizePolicy(sizePolicy2)
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.identifier_frame = QFrame(self.dockWidgetContents)
        self.identifier_frame.setObjectName(u"identifier_frame")
        self.identifier_frame.setMinimumSize(QSize(0, 0))
        self.identifier_frame.setFrameShape(QFrame.StyledPanel)
        self.identifier_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.identifier_frame)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(-1, 5, -1, 3)
        self.identifier_label = QLabel(self.identifier_frame)
        self.identifier_label.setObjectName(u"identifier_label")

        self.verticalLayout_4.addWidget(self.identifier_label)

        self.line = QFrame(self.identifier_frame)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_4.addWidget(self.line)


        self.verticalLayout.addWidget(self.identifier_frame)

        self.time_groupBox = QGroupBox(self.dockWidgetContents)
        self.time_groupBox.setObjectName(u"time_groupBox")
        self.gridLayout_4 = QGridLayout(self.time_groupBox)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.timePlayStop_pushButton = QPushButton(self.time_groupBox)
        self.timePlayStop_pushButton.setObjectName(u"timePlayStop_pushButton")

        self.gridLayout_4.addWidget(self.timePlayStop_pushButton, 1, 1, 1, 1)

        self.timeValue_label = QLabel(self.time_groupBox)
        self.timeValue_label.setObjectName(u"timeValue_label")

        self.gridLayout_4.addWidget(self.timeValue_label, 0, 0, 1, 1)

        self.timeValue_doubleSpinBox = QDoubleSpinBox(self.time_groupBox)
        self.timeValue_doubleSpinBox.setObjectName(u"timeValue_doubleSpinBox")
        self.timeValue_doubleSpinBox.setMaximum(12000.000000000000000)

        self.gridLayout_4.addWidget(self.timeValue_doubleSpinBox, 0, 1, 1, 1)

        self.timeLoop_checkBox = QCheckBox(self.time_groupBox)
        self.timeLoop_checkBox.setObjectName(u"timeLoop_checkBox")

        self.gridLayout_4.addWidget(self.timeLoop_checkBox, 1, 2, 1, 1)


        self.verticalLayout.addWidget(self.time_groupBox)

        self.fitting_groupBox = QGroupBox(self.dockWidgetContents)
        self.fitting_groupBox.setObjectName(u"fitting_groupBox")
        self.gridLayout_3 = QGridLayout(self.fitting_groupBox)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.fittingRigid_label = QLabel(self.fitting_groupBox)
        self.fittingRigid_label.setObjectName(u"fittingRigid_label")

        self.gridLayout_3.addWidget(self.fittingRigid_label, 2, 0, 1, 1)

        self.fittingScale_label = QLabel(self.fitting_groupBox)
        self.fittingScale_label.setObjectName(u"fittingScale_label")

        self.gridLayout_3.addWidget(self.fittingScale_label, 0, 0, 1, 1)

        self.fittingFitRigidly_pushButton = QPushButton(self.fitting_groupBox)
        self.fittingFitRigidly_pushButton.setObjectName(u"fittingFitRigidly_pushButton")

        self.gridLayout_3.addWidget(self.fittingFitRigidly_pushButton, 2, 1, 1, 1)

        self.fittingScale_pushButton = QPushButton(self.fitting_groupBox)
        self.fittingScale_pushButton.setObjectName(u"fittingScale_pushButton")

        self.gridLayout_3.addWidget(self.fittingScale_pushButton, 0, 1, 1, 1)

        self.fittingFitEpochs_label = QLabel(self.fitting_groupBox)
        self.fittingFitEpochs_label.setObjectName(u"fittingFitEpochs_label")

        self.gridLayout_3.addWidget(self.fittingFitEpochs_label, 5, 0, 1, 1)

        self.fittingFitNonRigidly_pushButton = QPushButton(self.fitting_groupBox)
        self.fittingFitNonRigidly_pushButton.setObjectName(u"fittingFitNonRigidly_pushButton")

        self.gridLayout_3.addWidget(self.fittingFitNonRigidly_pushButton, 3, 1, 1, 1)

        self.fittingNonRigid_label = QLabel(self.fitting_groupBox)
        self.fittingNonRigid_label.setObjectName(u"fittingNonRigid_label")

        self.gridLayout_3.addWidget(self.fittingNonRigid_label, 3, 0, 1, 1)

        self.fittingFitEpochs_pushButton = QPushButton(self.fitting_groupBox)
        self.fittingFitEpochs_pushButton.setObjectName(u"fittingFitEpochs_pushButton")

        self.gridLayout_3.addWidget(self.fittingFitEpochs_pushButton, 5, 1, 1, 1)


        self.verticalLayout.addWidget(self.fitting_groupBox)

        self.verticalSpacer = QSpacerItem(20, 557, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.frame = QFrame(self.dockWidgetContents)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.viewAll_button = QPushButton(self.frame)
        self.viewAll_button.setObjectName(u"viewAll_button")

        self.horizontalLayout_2.addWidget(self.viewAll_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.done_button = QPushButton(self.frame)
        self.done_button.setObjectName(u"done_button")
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.done_button.sizePolicy().hasHeightForWidth())
        self.done_button.setSizePolicy(sizePolicy3)

        self.horizontalLayout_2.addWidget(self.done_button)


        self.verticalLayout.addWidget(self.frame)

        self.dockWidget.setWidget(self.dockWidgetContents)

        self.gridLayout.addWidget(self.dockWidget, 0, 0, 1, 1)

        self.sceneviewer_widget = BaseSceneviewerWidget(ParametricFittingWidget)
        self.sceneviewer_widget.setObjectName(u"sceneviewer_widget")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(4)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.sceneviewer_widget.sizePolicy().hasHeightForWidth())
        self.sceneviewer_widget.setSizePolicy(sizePolicy4)

        self.gridLayout.addWidget(self.sceneviewer_widget, 0, 1, 1, 1)


        self.retranslateUi(ParametricFittingWidget)

        QMetaObject.connectSlotsByName(ParametricFittingWidget)
    # setupUi

    def retranslateUi(self, ParametricFittingWidget):
        ParametricFittingWidget.setWindowTitle(QCoreApplication.translate("ParametricFittingWidget", u"Parametric Fitting", None))
        self.dockWidget.setWindowTitle(QCoreApplication.translate("ParametricFittingWidget", u"Control Panel", None))
        self.identifier_label.setText(QCoreApplication.translate("ParametricFittingWidget", u"Identifier", None))
        self.time_groupBox.setTitle(QCoreApplication.translate("ParametricFittingWidget", u"Time:", None))
        self.timePlayStop_pushButton.setText(QCoreApplication.translate("ParametricFittingWidget", u"Play", None))
        self.timeValue_label.setText(QCoreApplication.translate("ParametricFittingWidget", u"Time value:", None))
        self.timeLoop_checkBox.setText(QCoreApplication.translate("ParametricFittingWidget", u"Loop", None))
        self.fitting_groupBox.setTitle(QCoreApplication.translate("ParametricFittingWidget", u"Fitting:", None))
        self.fittingRigid_label.setText(QCoreApplication.translate("ParametricFittingWidget", u"Rigid:", None))
        self.fittingScale_label.setText(QCoreApplication.translate("ParametricFittingWidget", u"Scale:", None))
        self.fittingFitRigidly_pushButton.setText(QCoreApplication.translate("ParametricFittingWidget", u"Fit rigidly", None))
        self.fittingScale_pushButton.setText(QCoreApplication.translate("ParametricFittingWidget", u"Scale", None))
        self.fittingFitEpochs_label.setText(QCoreApplication.translate("ParametricFittingWidget", u"Throughout time:", None))
        self.fittingFitNonRigidly_pushButton.setText(QCoreApplication.translate("ParametricFittingWidget", u"Fit non-rigidly", None))
        self.fittingNonRigid_label.setText(QCoreApplication.translate("ParametricFittingWidget", u"Non-Rigid:", None))
        self.fittingFitEpochs_pushButton.setText(QCoreApplication.translate("ParametricFittingWidget", u"Fit epochs", None))
        self.viewAll_button.setText(QCoreApplication.translate("ParametricFittingWidget", u"View All", None))
        self.done_button.setText(QCoreApplication.translate("ParametricFittingWidget", u"Done", None))
    # retranslateUi

