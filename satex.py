# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SatEx
                                 A QGIS plugin
Streamlined algorithms for pixel based classification of Landsat satellite
imagery using OTB.
                              -------------------
        begin                : 2015-12-14
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Michael Haas (GFZ)
        email                : mhaas@gfz-potsdam.de
 ***************************************************************************/

/****************************************************************************
 *                                                                          *
 *    This program is free software: you can redistribute it and/or modify  *
 *    it under the terms of the GNU General Public License as published by  *
 *    the Free Software Foundation, either version 3 of the License, or     *
 *    (at your option) any later version.                                   *
 *                                                                          *
 *    This program is distributed in the hope that it will be useful,       *
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *    GNU General Public License for more details.                          *
 *                                                                          *
 *    You should have received a copy of the GNU General Public License     *
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>. *
 *                                                                          *
 ****************************************************************************/
"""
import PyQt4.QtCore
import PyQt4.QtGui
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from satex_dialog import PreprocessingDialog, ClassificationDialog
import os
import qgis.utils
import subprocess

class SatEx:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = PyQt4.QtCore.QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SatEx_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = PyQt4.QtCore.QTranslator()
            self.translator.load(locale_path)

            if PyQt4.QtCore.qVersion() > '4.3.3':
                PyQt4.QtCore.QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GFZ SatEx')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SatEx')
        self.toolbar.setObjectName(u'SatEx')

        #create dialogs and keep reference
        self.Pdlg = PreprocessingDialog()
        self.Cdlg = ClassificationDialog()

        #gui interactions
        #Preprocessing
        self.Pdlg.lineEdit.clear()
        self.Pdlg.pushButton.clicked.connect(self.select_input_raster)
        self.Pdlg.lineEdit_2.clear()
        self.Pdlg.pushButton_2.clicked.connect(self.select_roi)
        self.Pdlg.lineEdit_3.clear()
        self.Pdlg.pushButton_3.clicked.connect(self.select_Poutput_name)
        self.Pdlg.toolButton.clicked.connect(self.show_help)

        #Classification
        self.Cdlg.lineEdit.clear()
        self.Cdlg.pushButton.clicked.connect(self.select_input_pan)
        self.Cdlg.lineEdit_2.clear()
        self.Cdlg.pushButton_2.clicked.connect(self.select_training)
        self.Cdlg.lineEdit_3.clear()
        self.Cdlg.pushButton_3.clicked.connect(self.select_Coutput_name)
        self.Cdlg.checkBox.clicked.connect(self.switch_external_SVM)
        self.Cdlg.checkBox_3.clicked.connect(self.switch_sieve)
        self.Cdlg.pushButton_4.clicked.connect(self.select_CSVM)
        self.Cdlg.lineEdit_6.setText('4')
        self.Cdlg.toolButton.clicked.connect(self.show_help)

        #setup subrpocess differently for windows
        self.startupinfo = None
        if os.name == 'nt':
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        #Prefent bug in directory search (added / on linux results in searching the root directory)
        self.Pdlg.lineEdit.setText(' ')
        #TODO:defaults for development
        #self.Pdlg.lineEdit.setText('C:\Users\michael\Desktop\plugin data\LC81680542015357LGN00')
        #self.Pdlg.lineEdit_2.setText('C:/Users/michael/Desktop/plugin data/adisababa.shp')
        #self.Pdlg.lineEdit_3.setText('C:/Users/michael/Desktop/test.vrt')
        #self.Pdlg.lineEdit.setText('/home/mhaas/PhD/Routines/rst/plugin/data/LC81680542015357LGN00/')
        #self.Pdlg.lineEdit_2.setText('/home/mhaas/PhD/Routines/rst/plugin/data/adisababa.shp')
        #self.Pdlg.lineEdit_3.setText('/home/mhaas/test/test.vrt')
        #TODO:defaults for development
        #self.Cdlg.lineEdit.setText('Path to vrt')
        #self.Cdlg.lineEdit_2.setText('Path to training shapefile')
        #self.Cdlg.lineEdit_3.setText('Path to output-tif')
        #self.Cdlg.lineEdit_5.setText('Training class label')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return PyQt4.QtCore.QCoreApplication.translate('SatEx', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = PyQt4.QtGui.QIcon(icon_path)
        action = PyQt4.QtGui.QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SatEx/icon_preprocessing.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Preprocessing'),
            callback=self.run_preprocessing,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/SatEx/icon_classification.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Classification'),
            callback=self.run_classification,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GFZ SatEx'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def updatePForm(self):
        #get user edits
        self.ls_path = self.Pdlg.lineEdit.text()+'/'
        self.roi = self.Pdlg.lineEdit_2.text()
        self.out_fname = self.Pdlg.lineEdit_3.text()
        if (self.ls_path ==' /' or self.roi == '' or self.out_fname == ''):
            return False
        else:
            return True

    def select_input_raster(self):
        dirname = PyQt4.QtGui.QFileDialog.getExistingDirectory(self.Pdlg, "Select input directory ","",PyQt4.QtGui.QFileDialog.ShowDirsOnly)
        self.Pdlg.lineEdit.setText(dirname)

    def select_roi(self):
        filename = PyQt4.QtGui.QFileDialog.getOpenFileName(self.Pdlg, "Select region of interest ","","Shapefile (*.shp)")
        self.Pdlg.lineEdit_2.setText(filename)

    def select_Poutput_name(self):
        filename = PyQt4.QtGui.QFileDialog.getSaveFileName(self.Pdlg, "Select output file ","","Virtual Raster Tile (*.vrt)")
        if filename.split('.')[-1]!='vrt':
            filename = filename+'.vrt'
        self.Pdlg.lineEdit_3.setText(filename)

    def updateCForm(self):
        #get user edits
        self.raster = self.Cdlg.lineEdit.text()
        self.in_train = self.Cdlg.lineEdit_2.text()
        self.out_fname = self.Cdlg.lineEdit_3.text()
        self.label = self.Cdlg.lineEdit_5.text()
        self.sieve = self.Cdlg.lineEdit_6.text()
        self.external = False
        if self.Cdlg.checkBox.isChecked():
            self.external=True
        #in case an external SVM is provided the testing is optional
        if self.external:
            if (self.raster =='' or self.out_fname == '' or self.sieve == ''):
                return False
            else:
                return True
        else:
            if (self.raster =='' or self.in_train == '' or self.out_fname == '' or self.label == '' or self.sieve == ''):
                return False
            else:
                return True

    def select_input_pan(self):
        filename = PyQt4.QtGui.QFileDialog.getOpenFileName(self.Cdlg, "Select input layerstacked virtual raster tile","","*.vrt")
        self.Cdlg.lineEdit.setText(filename)

    def select_training(self):
        filename = PyQt4.QtGui.QFileDialog.getOpenFileName(self.Cdlg, "Select training vector ","","*.shp")
        self.Cdlg.lineEdit_2.setText(filename)

    def select_CSVM(self):
        filename = PyQt4.QtGui.QFileDialog.getOpenFileName(self.Cdlg, "Select Support Vector Model file","","")
        self.Cdlg.lineEdit_4.setText(filename)

    def select_Coutput_name(self):
        filename = PyQt4.QtGui.QFileDialog.getSaveFileName(self.Cdlg, "Select output file ","","GeoTIFF (*.tif)")
        suffix=filename.split('.')[-1]
        if suffix not in ['tif','TIF']:
            filename = filename+'.tif'
        self.Cdlg.lineEdit_3.setText(filename)

    def switch_external_SVM(self):
        '''
        Activates the external SVM dialog parts
        '''
        if self.Cdlg.checkBox.isChecked():
            self.Cdlg.lineEdit_4.setEnabled(True)
            self.Cdlg.pushButton_4.setEnabled(True)
            self.Cdlg.label_5.setEnabled(True)
            self.external=True
        else:
            self.Cdlg.lineEdit_4.setDisabled(True)
            self.Cdlg.pushButton_4.setDisabled(True)
            self.Cdlg.label_5.setDisabled(True)
            self.external=False

    def switch_sieve(self):
        if self.Cdlg.checkBox_3.isChecked():
            self.Cdlg.lineEdit_6.setEnabled(True)
        else:
            self.Cdlg.lineEdit_6.setEnabled(False)

    def show_help(self):
        import webbrowser
        import sys
        import os

        source = sys.modules['SatEx'].__file__
        path = os.path.dirname(source)
        helpfile = path+'/help/html/index.html'
        url = "file://" + helpfile
        webbrowser.open(url,new=2)

    def errorMsg(self,msg):
        self.iface.messageBar().pushMessage('Error: '+ msg,self.iface.messageBar().CRITICAL)

    def run_preprocessing(self):
        """Run method that performs all the real work"""
        self.Pdlg.setModal(False)
        self.Pdlg.show()

        #Dialog event loop
        result = self.Pdlg.exec_()
        if result:
            self.processed = 0
            self.percentage = 0
            #TODO:fix
            self.ntasks = 3
            #Get user edits and check if not empty
            valid_input=self.updatePForm()

            import utils
            import traceback
            import qgis.core
            import ogr

            try:
                import otbApplication
            except:
                self.errorMsg('Plugin requires installation of OrfeoToolbox')

            #find the number of different L8 scenes
            #by reading all TIFs splitting off '_Bxy.TIF' and getting unique strings
            e = 'Unspecified error'
            #instantiate utilities function
            ut = utils.utils()
            try:
                try:
                    #check if input is not empty string
                    1/valid_input
                except ZeroDivisionError:
                    e = str('Please fill all required input fields')
                    raise Exception

                try:
                    #delete any old tmp files that might be in the directory from a killed task
                    old=ut.delete_tmps(self.ls_path)
                    if old > 0: qgis.core.QgsMessageLog.logMessage('Old *satexTMP* files were present. They were deleted.')
                except:
                    e = str('Could not delete old *satexTMP* files. Function utils.delete_tmps.')
                    raise Exception

                try:
                    pattern = '*.TIF'
                    scenes = set(['_'.join(s.split('_')[:1]) for s in ut.findFiles(self.ls_path,pattern)])
                    if len(scenes)==0:
                        pattern = '*.tif'
                        scenes = set(['_'.join(s.split('_')[:1]) for s in ut.findFiles(self.ls_path,pattern)])
                    1/len(scenes)
                except ZeroDivisionError:
                    e = str('Found no scene in {}'.format(self.ls_path))
                    raise Exception
                else:
                    qgis.core.QgsMessageLog.logMessage(str('Found {} scene(s) in {}'.format(len(scenes),self.ls_path)))

                #check shapefile roi
                try:
                    driver = ogr.GetDriverByName('ESRI Shapefile')
                    dataSource = driver.Open(self.roi,0)
                    layer = dataSource.GetLayer()
                    qgis.core.QgsMessageLog.logMessage(str('Using {} as ROI'.format(self.roi)))
                except AttributeError:
                    e = str('Could not open {}'.format(self.roi))
                    raise Exception

                #loop through all scenes
                out_files = []
                for scene in scenes:

                    #find all bands for scene exclude quality band BQA and B8
                    try:
                        bands = [b for b in ut.findFiles(self.ls_path,scene+'*_B'+pattern) if '_BQA' not in b]
                        bands = [b for b in bands if '_B8' not in b]
                        #in case of multiple scenes (and not first scene is processed) check if nr of bands are equal
                        try:
                            #only if more than one scene and at least second scene
                            nr_bands
                        except:
                            if len(bands)==0:
                                e = str('Found no bands for scene {}.'.format(scene))
                                raise Exception
                            else:
                                #store number of bands for potential additonal scenes
                                nr_bands = len(bands)
                                qgis.core.QgsMessageLog.logMessage(str('Found {} bands (if present, excluding B8 and BQA) for scene {} '.format(nr_bands,scene)))
                        else:
                            if len(bands)!=nr_bands:
                                e = str('Found {} instead of {} bands (excluding B8 and BQA) for scene {}. If multiple scenes are provided in the input directory, ensure they have equal bands!'.format(len(bands),nr_bands,scene))
                            else:
                                qgis.core.QgsMessageLog.logMessage(str('Found {} bands (if present, excluding B8 and BQA) for scene {} '.format(len(bands),scene)))
                    except:
                        raise Exception

                    #Check if ROI and scene overlap
                    try:
                        error,overlap = ut.vector_raster_overlap(self.roi,self.ls_path+bands[0])
                    except:
                        e = str('Unspecified error while trying to execute utils.vector_raster_overlap function with {} and {}'.format(self.roi,bands[0]))
                        raise Exception
                    if error!='SUCCESS':
                        e = error
                        raise Exception
                    else:
                        try:
                            1/overlap
                        except ZeroDivisionError:
                            e = str('The provided ROI {} does not overlap with scene {}'.format(self.roi,scene))
                            raise Exception

                    #use gdalwarp to cut bands to roi
                    try:
                        #go through bands
                        for band in bands:
                            cmd = ['gdalwarp','-overwrite','-q','-cutline',self.roi,'-crop_to_cutline',self.ls_path+band,self.ls_path+band[:-4]+'_satexTMP_ROI'+pattern[1:]]
                            subprocess.check_call(cmd,startupinfo=self.startupinfo)
                            qgis.core.QgsMessageLog.logMessage(str('Cropped band {} to ROI'.format(band)))
                    except subprocess.CalledProcessError:
                        e = str('Could not execute gdalwarp cmd: {}.\nError is:{}'.format(' '.join(cmd),error))
                        raise Exception

                    # Layerstack
                    try:
                        #respect order B1,B2,B3,B4,B5,B6,B7,B9,B10,B11
                        in_files = [str(self.ls_path+b[:-4]+'_satexTMP_ROI'+pattern[1:]) for b in bands]
                        in_files.sort()
                        if nr_bands==10:
                            # For Landsat 8 B10,B11 considered smaller --> resort
                            in_files = in_files[2:] + in_files[0:2]
                        out_file = str(os.path.dirname(self.out_fname)+'/'+scene+'_satex_mul'+pattern[1:])
                        #call otb wrapper
                        error = ut.otb_concatenate(in_files,out_file)
                        if error!='success': raise ZeroDivisionError
                        #append file to list
                        out_files.append(out_file)
                        qgis.core.QgsMessageLog.logMessage(str('Concatenated bands for scene {}'.format(scene)))
                    except ZeroDivisionError:
                        e = str('Could not execute OTB ConcatenateImages for scene: {}\nin_files: {}\nout_file: {}. \nError is: {}'.format(scene,in_files,out_file,error))
                        raise Exception

                # after all scenes were processed combine them to a virtual raster tile
                try:
                    cmd = ["gdalbuildvrt","-q","-srcnodata","0","-overwrite",self.out_fname]
                    for f in out_files:
                        cmd.append(f)
                    subprocess.check_call(cmd,startupinfo=self.startupinfo)
                    qgis.core.QgsMessageLog.logMessage(str('Merged {} different scenes to {}'.format(len(out_files),self.out_fname)))
                except subprocess.CalledProcessError:
                    e = str('Could not execute gdalbuildvrt cmd: {}'.format(' '.join(cmd)))
                    raise Exception

                #add to map canvas if checked
                if self.Pdlg.checkBox.isChecked():
                    try:
                        self.iface.addRasterLayer(str(self.out_fname), "SatEx_vrt")
                    except:
                        e = str('Could not add {} to the layer canvas'.format(self.out_fname))
                        raise Exception

            except:
                self.errorMsg(e)
                qgis.core.QgsMessageLog.logMessage(str('Exception: {}'.format(e)))
                qgis.core.QgsMessageLog.logMessage(str('Exception occurred...deleting temporary files'))
                ut.delete_tmps(self.ls_path)
            else:
                qgis.core.QgsMessageLog.logMessage(str('Processing sucessfully completed'))
                qgis.core.QgsMessageLog.logMessage(str('Deleting temporary files'))
                self.iface.messageBar().pushMessage('Processing successfully completed, see log for details',self.iface.messageBar().SUCCESS,duration=3)
                ut.delete_tmps(self.ls_path)

    def run_classification(self):
        """Run method that performs all the real work"""
        self.Cdlg.setModal(False)
        self.Cdlg.show()

        #Dialog event loop
        result = self.Cdlg.exec_()

        if result:
            import utils
            import traceback
            import qgis.core
            import ogr
            #import subprocess

            #Get user edits
            valid_input=self.updateCForm()
            #TODO:fix
            self.classification_type='libsvm'
            self.svmModel = self.in_train[:-4]+'_svmModel.svm'
            self.ConfMatrix = self.in_train[:-4]+'_CM.csv'

            try:
                import otbApplication
            except:
                self.errorMsg('Plugin requires installation of OrfeoToolbox')

            e = 'Unspecified error'
            try:
                #instantiate utilities functions
                ut = utils.utils()

                try:
                    #check if input is not empty string
                    1/valid_input
                except ZeroDivisionError:
                    e = str('Please fill all required input fields')
                    raise Exception

                #check if training fields overlap with raster
                if not self.external:
                    try:
                        error,overlap = ut.vector_raster_overlap(self.in_train,self.raster)
                    except:
                        e = str('Unspecified error while trying to execute utils.vector_raster_overlap function')
                        raise Exception
                    if error!='SUCCESS':
                        e = error
                        raise Exception
                    else:
                        try:
                            1/overlap
                        except ZeroDivisionError:
                            e = str('At least one feature in {} does not overlap with {}'.format(self.in_train,self.raster))
                            raise Exception

                #generate image statistics
                try:
                    self.stats = str(self.raster[:-4]+'_stats.xml')
                    error=ut.otb_image_statistics(str(self.raster),str(self.stats))
                    if error!='success':raise ZeroDivisionError
                    qgis.core.QgsMessageLog.logMessage(str('Calculated image statistics {} for {}'.format(self.stats,self.raster)))
                except ZeroDivisionError:
                    e = str('Could not execute OTB Image Statistics on: {}. \nError is:{}'.format(self.raster,error))
                    raise Exception

                #differntiate two cases case 1) external SVM provided an case 2) on the fly SVM training
                if self.external:
                    if self.in_train!='':
                        #use full training set for testing
                        self.test = self.in_train
                    #get SVM filename
                    self.svmModel = self.Cdlg.lineEdit_4.text()
                else:
                    #split training dataset in 80% train 20% testing
                    [self.error,self.test,self.train] = ut.split_train(self.in_train,self.label,self.startupinfo)
                    if self.error != 'success':
                        e=self.error
                        raise Exception
                    else:
                        qgis.core.QgsMessageLog.logMessage(str('Splitted ground truth data set in {} (~80%) and {} (~20%)'.format(self.train,self.test)))

                    #train classifier
                    #on the fly (wrong) confusion matrix gets overwritten later
                    try:
                        error=ut.otb_train_classifier(self.raster, self.train, self.stats, self.classification_type, self.label, self.svmModel, self.ConfMatrix)
                        if error!='success': raise ZeroDivisionError
                        qgis.core.QgsMessageLog.logMessage(str('Trained image classifier using {} and {}'.format(self.raster,self.train)))
                    except ZeroDivisionError:
                        e = 'Could not execute OTB TrainClassifiers with {} {} {} {} {} {} {}. \nError is:{}'.format(self.raster, self.train, self.stats, self.classification_type, self.label, self.svmModel, self.ConfMatrix,error)
                        raise Exception

                #classify image
                try:
                    error=ut.otb_classification(self.raster, self.stats, self.svmModel, self.out_fname)
                    if error!='success': raise ZeroDivisionError
                    qgis.core.QgsMessageLog.logMessage(str('Image {} classified as {}'.format(self.raster,self.out_fname)))
                except ZeroDivisionError:
                    e = 'Could not execute OTB Classifier with {}, {}, {}, {}. \n Error is: {}'.format(self.raster, self.stats, self.svmModel, self.out_fname,error)
                    raise Exception

                #confusion matrix
                try:
                    #testing is optional in case of externally provided SVM
                    if self.in_train!='':
                        error=ut.otb_confusion_matrix(self.out_fname,self.ConfMatrix,self.test,self.label)
                        if error!='success':raise ZeroDivisionError
                        qgis.core.QgsMessageLog.logMessage(str('Confusion matrix calculated on classified image {} with test set {} saved as {}'.format(self.out_fname,self.test,self.ConfMatrix)))
                except ZeroDivisionError:
                    e = 'Could not execute OTB Confusion Matrix with {}, {}, {}, {}. \nError is: {}'.format(self.out_fname, self.ConfMatrix, self.test, self.label)
                    raise Exception

                #if sieving is asked perform sieving
                if self.Cdlg.checkBox_3.isChecked():
                    try:
                        if os.name=='nt':
                            cmd = ['gdal_sieve.bat','-q','-st',str(self.sieve),'-8',str(self.out_fname)]
                        else:
                            cmd = ['gdal_sieve.py','-q','-st',str(self.sieve),'-8',str(self.out_fname)]
                        subprocess.check_call(cmd,startupinfo=self.startupinfo)
                    except subprocess.CalledProcessError:
                        e = 'Could not execute {}'.format(cmd)
                        raise Exception

                #add to map canvas if checked
                if self.Cdlg.checkBox_2.isChecked():
                    try:
                        self.iface.addRasterLayer(str(self.out_fname), "SatEx_classified_scene")
                    except:
                        e = str('Could not add {} to the layer canvas'.format(self.out_fname))
                        raise Exception

            except:
                self.errorMsg(e)
                qgis.core.QgsMessageLog.logMessage(e)
            else:
                qgis.core.QgsMessageLog.logMessage(str('Processing completed'))
                self.iface.messageBar().pushMessage('Processing successfully completed, see log for details',self.iface.messageBar().SUCCESS,duration=3)
