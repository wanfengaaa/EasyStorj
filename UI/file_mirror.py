import json
import threading
from PyQt4 import QtCore, QtGui

from PyQt4.QtGui import QAbstractItemView
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QStandardItem
from PyQt4.QtGui import QStandardItemModel

from UI.engine import StorjEngine
from UI.node_details import NodeDetailsUI
from qt_interfaces.file_mirrors_list_ui import Ui_FileMirrorsList

from resources.html_strings import html_format_begin, html_format_end

import  storj.exception as sjexc

# Mirrors section
class FileMirrorsListUI(QtGui.QMainWindow):

    def __init__(self, parent=None, bucketid=None, fileid=None):
        QtGui.QWidget.__init__(self, parent)
        self.file_mirrors_list_ui = Ui_FileMirrorsList()
        self.file_mirrors_list_ui.setupUi(self)
        # model = self.file_mirrors_list_ui.established_mirrors_tree.model()

        self.file_mirrors_list_ui.mirror_details_bt.clicked.connect(
            lambda: self.open_mirror_details_window("established"))
        self.file_mirrors_list_ui.mirror_details_bt_2.clicked.connect(
            lambda: self.open_mirror_details_window("available"))
        self.file_mirrors_list_ui.quit_bt.clicked.connect(self.close)

        self.connect(self, QtCore.SIGNAL("showStorjBridgeException"), self.show_storj_bridge_exception)
        self.connect(self, QtCore.SIGNAL("showUnhandledException"), self.show_unhandled_exception)


        # self.connect(self.file_mirrors_list_ui.established_mirrors_tree, QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"), self.open_mirror_details_window)

        # self.connect(self.file_mirrors_list_ui.established_mirrors_tree, QtCore.SIGNAL('selectionChanged()'), self.open_mirror_details_window)

        # QtCore.QObject.connect(self.file_mirrors_list_ui.established_mirrors_tree.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'),
        # self.open_mirror_details_window)

        # self.file_mirrors_list_ui.established_mirrors_tree.

        self.bucketid = bucketid
        self.fileid = fileid

        self.file_mirrors_list_ui.file_id_label.setText(html_format_begin + str(self.fileid) + html_format_end)

        print self.fileid
        self.storj_engine = StorjEngine()  # init StorjEngine
        self.createNewMirrorListInitializationThread()

    def show_unhandled_exception(self, exception_content):
        QMessageBox.critical(self, "Unhandled error", str(exception_content))

    def show_storj_bridge_exception(self, exception_content):
        try:
            j = json.loads(str(exception_content))
            QMessageBox.critical(self, "Bridge error", str(j["error"]))

        except:
            QMessageBox.critical(self, "Bridge error", str(exception_content))

    def open_mirror_details_window(self, mirror_state):
        # self.established_mirrors_tree_view = self.file_mirrors_list_ui.established_mirrors_tree

        # daat = self.file_mirrors_list_ui.established_mirrors_tree.selectedIndexes()
        # model = self.file_mirrors_list_ui.established_mirrors_tree.model()
        # data = []

        # initialize variables
        item = ""
        index = ""
        try:
            if mirror_state == "established":
                index = self.file_mirrors_list_ui.established_mirrors_tree.selectedIndexes()[3]
                item = self.file_mirrors_list_ui.established_mirrors_tree.selectedIndexes()[3]
            elif mirror_state == "available":
                index = self.file_mirrors_list_ui.available_mirrors_tree.selectedIndexes()[3]
                item = self.file_mirrors_list_ui.available_mirrors_tree.selectedIndexes()[3]

            nodeid_to_send = item.model().itemFromIndex(index).text()

            if nodeid_to_send != "":
                self.node_details_window = NodeDetailsUI(self, nodeid_to_send)
                self.node_details_window.show()
            else:
                QMessageBox.about(self, "Warning", "Please select farmer node from list")
                print "Unhandled error"

        except:
            QMessageBox.about(self, "Warning", "Please select farmer node from list")
            print "Unhandled error"

    def createNewMirrorListInitializationThread(self):
        mirror_list_initialization_thread = threading.Thread(target=self.initialize_mirrors_tree, args=())
        mirror_list_initialization_thread.start()

    def initialize_mirrors_tree(self):
        # create model
        # model = QtGui.QFileSystemModel()
        # model.setRootPath(QtCore.QDir.currentPath())

        self.file_mirrors_list_ui.loading_label_mirrors_established.setStyleSheet('color: red')  # set loading color
        self.file_mirrors_list_ui.loading_label_mirrors_available.setStyleSheet('color: red')  # set loading color

        self.mirror_tree_view_header = ['Shard Hash / Address', 'User agent', 'Last seed', 'Node ID']

        ######################### set the model for established mirrors ##################################
        self.established_mirrors_model = QStandardItemModel()
        self.established_mirrors_model.setHorizontalHeaderLabels(self.mirror_tree_view_header)

        self.established_mirrors_tree_view = self.file_mirrors_list_ui.established_mirrors_tree
        self.established_mirrors_tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.established_mirrors_tree_view.setModel(self.established_mirrors_model)
        self.established_mirrors_tree_view.setUniformRowHeights(True)

        self.file_mirrors_list_ui.available_mirrors_tree.setModel(self.established_mirrors_model)

        divider = 0
        group = 1
        self.established_mirrors_count_for_file = 0
        recent_shard_hash = ""
        parent1 = QStandardItem('')
        try:
            for file_mirror in self.storj_engine.storj_client.file_mirrors(str(self.bucketid), str(self.fileid)):
                for mirror in file_mirror.established:
                    self.established_mirrors_count_for_file += 1
                    print file_mirror.established
                    if mirror["shardHash"] != recent_shard_hash:
                        parent1 = QStandardItem('Shard with hash {}'.format(mirror["shardHash"]))
                        divider = divider + 1
                        self.established_mirrors_model.appendRow(parent1)

                    child1 = QStandardItem(str(mirror["contact"]["address"] + ":" + str(mirror["contact"]["port"])))
                    child2 = QStandardItem(str(mirror["contact"]["userAgent"]))
                    child3 = QStandardItem(str(mirror["contact"]["lastSeen"]))
                    child4 = QStandardItem(str(mirror["contact"]["nodeID"]))
                    parent1.appendRow([child1, child2, child3, child4])

                    # span container columns
                    # self.established_mirrors_tree_view.setFirstColumnSpanned(1, self.established_mirrors_tree_view.rootIndex(), True)

                    recent_shard_hash = mirror["shardHash"]

            self.file_mirrors_list_ui.loading_label_mirrors_established.setText("")

            # dbQueryModel.itemData(treeView.selectedIndexes()[0])

            ################################### set the model for available mirrors #########################################
            self.available_mirrors_model = QStandardItemModel()
            self.available_mirrors_model.setHorizontalHeaderLabels(self.mirror_tree_view_header)

            self.available_mirrors_tree_view = self.file_mirrors_list_ui.available_mirrors_tree
            self.available_mirrors_tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)

            self.available_mirrors_tree_view.setModel(self.available_mirrors_model)
            self.available_mirrors_tree_view.setUniformRowHeights(True)

            self.file_mirrors_list_ui.available_mirrors_tree.setModel(self.available_mirrors_model)

            divider = 0
            self.available_mirrors_count_for_file = 0
            recent_shard_hash_2 = ""
            parent2 = QStandardItem('')
            for file_mirror in self.storj_engine.storj_client.file_mirrors(str(self.bucketid), str(self.fileid)):
                for mirror_2 in file_mirror.available:
                    self.available_mirrors_count_for_file += 1
                    if mirror_2["shardHash"] != recent_shard_hash_2:
                        parent2 = QStandardItem('Shard with hash {}'.format(mirror_2["shardHash"]))
                        divider = divider + 1
                        self.available_mirrors_model.appendRow(parent2)

                    child1 = QStandardItem(str(mirror_2["contact"]["address"] + ":" + str(mirror_2["contact"]["port"])))
                    child2 = QStandardItem(str(mirror_2["contact"]["userAgent"]))
                    child3 = QStandardItem(str(mirror_2["contact"]["lastSeen"]))
                    child4 = QStandardItem(str(mirror_2["contact"]["nodeID"]))
                    parent2.appendRow([child1, child2, child3, child4])

                    # span container columns
                    # self.established_mirrors_tree_view.setFirstColumnSpanned(1, self.established_mirrors_tree_view.rootIndex(), True)

                    recent_shard_hash_2 = mirror_2["shardHash"]
            self.file_mirrors_list_ui.loading_label_mirrors_available.setText("")

            self.file_mirrors_list_ui.established_mirrors_count.setText(
                html_format_begin + str(self.established_mirrors_count_for_file) + html_format_end)
            self.file_mirrors_list_ui.available_mirrors_count.setText(
                html_format_begin + str(self.available_mirrors_count_for_file) + html_format_end)
        except sjexc.StorjBridgeApiError as e:
            self.emit(QtCore.SIGNAL("showStorjBridgeException"), str(e))  # emit Storj Bridge Exception
        except Exception as e:
            self.emit(QtCore.SIGNAL("showUnhandledException"), str(e))  # emit unhandled Exception
            print str(e)

