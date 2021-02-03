from typing import Optional
from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtNetwork import QLocalServer, QLocalSocket
from PySide2.QtCore import QTextStream, Signal


class QSingleApplication(QApplication):

    onMassageRecived = Signal(str)  # Text Massege Event;

    def init(self, uid: str) -> bool:
        """ Try To Connect or Create : If Created Then Return True """
        self._stream_str: Optional[QTextStream] = None
        self._server: Optional[QLocalServer] = None
        self._socket: Optional[QLocalSocket] = None
        self._uid: str = uid
        if not self.__connect():
            self.__createServer()
            return True
        return False

    def sendTextMassege(self, msg: str):
        """ Send A Text Massege To Running Instance """
        if self._socket and self._stream_str and not self._server:
            self._stream_str << msg << '\n'
            self._stream_str.flush()
            return self._socket.waitForBytesWritten()
        else:
            return False

    def __connect(self):
        """ Create A Local Socket And Try To Connect """
        if self._socket:
            self._socket.close()

        socket = QLocalSocket()
        socket.connectToServer(self._uid)
        connected = socket.waitForConnected()

        if not connected:
            socket.close()
            return False

        self._socket = socket
        self._stream_str = QTextStream(self._socket)
        self._stream_str.setCodec('UTF-8')
        return True

    def __createServer(self):
        """ Create A Server & Listen as UID """
        self._server = QLocalServer()
        self._server.listen(self._uid)
        self._server.newConnection.connect(self.__onNewConnection)

    def __onNewConnection(self):
        """ On New Socket Connection From Clint """
        if self._socket:
            self._socket.readyRead.disconnect(self.__onReadyRead)

        self._socket = self._server.nextPendingConnection()
        if not self._socket:
            return

        self._stream_str = QTextStream(self._socket)
        self._stream_str.setCodec('UTF-8')
        self._socket.readyRead.connect(self.__onReadyRead)

    def __onReadyRead(self):
        """ Stream Ready To Read """
        while True:
            msg = self._stream_str.readLine()
            if not msg:
                break
            self.onMassageRecived.emit(msg)


# Test Run;
if __name__ == "__main__":
    app = QSingleApplication()
    if not app.init('ANY_UNIQE_KEY'):
        app.sendTextMassege("Hello Boss!\n")
        quit()
    else:
        app.onMassageRecived.connect(lambda x: print(x))
    win = QMainWindow()
    win.show()
    app.exec_()
