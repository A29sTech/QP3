from typing import List
from core.WidgetsQt import QSingleApplication
from core.Qropy import ImageCropperQt
from PySide2.QtWidgets import QApplication, QWidget, QFrame, QPushButton, QProgressBar, QMessageBox
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineDownloadItem
from PySide2.QtCore import Qt, QRect, QUrl, QSize, Signal
import os
from PIL import Image
import tempfile

# Require To Set env : PS_PATH: $(*/photoshop.exe)

TEMP_DIR_NAME = '$RMBG'

# This Script Only To Improve Perfamance;
script = """
    document.querySelector("nav").remove();
    document.querySelector("main").style.marginTop = 0;
    document.querySelector("footer").remove();
    document.querySelector(".newsletter-section").remove();
    document.querySelectorAll(".home-section").forEach( (e, k) => { if(k!=0)e.remove(); } );

"""


class QWebPage(QWebEnginePage):
    """ Auto Download Accepted """
    __file: str = ''

    def setInputFile(self, file: str):
        if self.__file != '' and os.path.exists(self.__file):
            os.remove(self.__file)

        self.__file = file

    def getInputFile(self): return self.__file

    def chooseFiles(self, mode, oldFiles, acceptedMimeTypes):
        return [self.__file]
        # return super().chooseFiles(mode, oldFiles, acceptedMimeTypes)
        # def acceptNavigationRequest(self, url, _type, isMainFrame):
        #     print( "\n",url, "*", _type, "*", isMainFrame  )
        #     return super().acceptNavigationRequest(url, _type, isMainFrame)


class QWebView(QWebEngineView):
    """ QWebView Like A Tab """
    __popup = None

    def getPopup(self): return self.__popup

    def createWindow(self, windowType):
        if windowType == QWebEnginePage.WebBrowserTab:
            self.deletePopup()
            self.__popup = QWebView()
            self.__popup.setPage(QWebPage())
            self.__popup.setAttribute(Qt.WA_DeleteOnClose, True)
            self.__popup.setWindowTitle('Pop-Up Window')
            self.__popup.setFixedSize(300, 200)
            # self.__popup.show()
            return self.__popup

        return super().createWindow(windowType)

    def contextMenuEvent(self, arg__1): return None

    def deletePopup(self):
        if self.__popup:
            self.__popup.destroy()
            self.__popup = None


class QWebBrowser(QFrame):
    """ Main Web Browser with Cromium"""
    __web_page: QWebPage
    __web_view: QWebEngineView
    __progress = None
    onDone = Signal()

    def __init__(self):
        super().__init__()  # Require;
        # ````````````````````````````
        self.setWindowTitle("A29sTech :: Remove.bg")
        self.__web_page = QWebPage()
        self.__web_view = QWebView(self)
        self.__web_view.setPage(self.__web_page)
        self._prof: QWebEngineProfile = self.__web_page.profile()
        self.__web_page.setUrl(QUrl('https://www.remove.bg'))
        self.__web_page.profile().downloadRequested.connect(self.__handleDownload)
        self.__web_page.loadProgress.connect(self.__handleProgress)

        # Register Single Instence;
        app: QSingleApplication = QSingleApplication.instance()
        if app:
            app.onMassageRecived.connect(lambda arg: self.changeImage(arg))

    def addUi(self):
        self._btn = QPushButton()
        rect: QSize = self.size()
        self._btn.setGeometry(
            QRect(rect.width() - 30, rect.height() - 30, rect.width(), rect.height()))
        self._btn.setStyleSheet(
            "QPushButton{border-radius:30px;background:green;}QPushButton:pressed{background-color:orange;}")
        self._btn.setParent(self)
        self._btn.clicked.connect(lambda: self.onDone.emit())
        self._btn.show()

    def __handleProgress(self, frc):
        if not self.__progress:
            self.__progress = QProgressBar()
            self.__progress.setRange(0, 100)
            self.__progress.setValue(frc)
            self.__progress.setGeometry(
                QRect(0 + 20, (self.height()/2)-20, self.width() - 20, 20))
            self.__progress.setParent(self)
            self.__progress.setStyleSheet("background-color: red;")
            self.__progress.show()

        self.__progress.setValue(frc)

        if frc >= 99:
            self.__progress.deleteLater()
            self.__progress = None
            self.__web_page.runJavaScript(script)

    def __handleDownload(self, req: QWebEngineDownloadItem):
        if not self.__web_view.getPopup():  # Close Download Btn if in edit mode;
            self.__web_page.runJavaScript(
                'document.querySelector(".close-btn").click()')
        else:  # Delete Popup Window;
            self.__web_view.deletePopup()

        orginal_filename = os.path.basename(self.__web_page.getInputFile()) + '.png'

        if os.path.exists(os.path.join(req.downloadDirectory(), orginal_filename)):

            reply = QMessageBox.question(
                self, "File Exsists!", 'Download again ?', QMessageBox.Yes, QMessageBox.No
            )

            if reply == QMessageBox.No:
                req.cancel()
                return
            else:
                orginal_filename = '_' + orginal_filename

        # Continue :
        req.setDownloadFileName(orginal_filename)
        req.accept()
        req.finished.connect(lambda: self.__onDownloadFinished(req.path()))

    def __onDownloadFinished(self, path):
        reply = QMessageBox.question(
            self, "Download Finished.", "Do You Went To Open With PS.", QMessageBox.Yes, QMessageBox.No
        )

        # Check Reply;
        if reply == QMessageBox.Yes:
            if os.environ.get('PS_PATH', None):
                os.popen('"{}" "{}"'.format(os.environ['PS_PATH'], os.path.realpath(path)))

    def resizeEvent(self, event):
        self.__web_view.setFixedSize(self.width(), self.height())

    def changeImage(self, image_files: str):
        self.showNormal()
        self.setFocus(Qt.ActiveWindowFocusReason)
        self.__web_page.setInputFile(image_files)
        #self.__web_view.setHtml("<a href='http://google.com' target='_blank'>Click Me</a>")


def crop_before_upload(image_path: str, app: QApplication):
    # Create A Temp Dir and make a path;
    temp_dir = os.path.join(tempfile.gettempdir(), TEMP_DIR_NAME)
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)

    temp_file = os.path.join(temp_dir, os.path.basename(image_path))

    img = Image.open(image_path)
    croper = ImageCropperQt(img)
    # Crop Result Handler;

    def resultHandler(_img: Image.Image):
        if _img.width > 600:  # If Image Is Bigger Then 600 Crop;
            ratio = _img.height / _img.width
            _img = _img.resize((600,  round(600*ratio)), Image.BICUBIC)

        _img.save(temp_file)
        app.exit(1)

    croper.result.connect(resultHandler)
    croper.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
    croper.setWindowFlag(Qt.Tool)
    croper.show()
    app.exec_()
    return temp_file


# Test Run;
if __name__ == "__main__":

    import sys
    if len(sys.argv) < 2:
        sys.exit(1)

    app = QSingleApplication()

    img_path = crop_before_upload(sys.argv[1], app)

    if not app.init("rmbg.app"):
        app.sendTextMassege(img_path)
        sys.exit(1)

    win = QWebBrowser()
    win.setFixedSize(400, 600)
    win.changeImage(img_path)
    win.addUi()
    win.show()
    app.exec_()
    # Delete Temp Dir After Programe Exit;
    import shutil
    temp_dir = os.path.join(tempfile.gettempdir())
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
