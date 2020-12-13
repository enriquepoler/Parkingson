import datetime
import sys

from PyQt5 import QtCore, QtGui, Qt
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout


# https://stackoverflow.com/a/33583019/12725251
class QRoundProgressBar(QWidget):
    """ Clase sacada de un post de stack Overflow, enlace https://stackoverflow.com/a/33583019/12725251"""
    StyleDonut = 1
    StylePie = 2
    StyleLine = 3

    PositionLeft = 180
    PositionTop = 90
    PositionRight = 0
    PositionBottom = -90

    UF_VALUE = 1
    UF_PERCENT = 2
    UF_MAX = 4

    def __init__(self):
        super().__init__()
        self.min = 0
        self.max = 100
        self.value = 25

        self.nullPosition = self.PositionTop
        self.barStyle = self.StyleDonut
        self.outlinePenWidth = 1
        self.dataPenWidth = 1
        self.rebuildBrush = False
        self.format = "%p%"
        self.decimals = 1
        self.updateFlags = self.UF_PERCENT
        self.gradientData = []
        self.donutThicknessRatio = 0.75

    @property
    def min(self):  # in seconds and microseconds
        if not isinstance(self._min, datetime.timedelta):
            return self._min
        else:
            return self._min.seconds + (self._min.microseconds / (10 ** 6))

    @property
    def max(self):  # in seconds and microseconds
        if not isinstance(self._max, datetime.timedelta):
            return self._max
        else:
            return self._max.seconds + (self._max.microseconds / (10 ** 6))

    @property
    def value(self):  # in seconds and microseconds
        if not isinstance(self._value, datetime.timedelta):
            return self._value
        else:
            return self._value.seconds + (self._value.microseconds / (10 ** 6))

    @min.setter
    def min(self, min):
        self._min = min

    @max.setter
    def max(self, max):
        self._max = max

    @value.setter
    def value(self, value):
        self._value = value

    def setRange(self, min, max):
        self.min = min
        self.max = max

        if self.max < self.min:
            self.max, self.min = self.min, self.max

        if self.value < self.min:
            self.value = self.min
        elif self.value > self.max:
            self.value = self.max

        if not self.gradientData:
            self.rebuildBrush = True
        self.update()

    def setMinimun(self, min):
        self.setRange(min, self.max)

    def setMaximun(self, max):
        self.setRange(self.min, max)

    def setValue(self, val):
        if self.value != val:
            if val < self.min:
                self.value = self.min
            elif val > self.max:
                self.value = self.max
            else:
                self.value = val
            self.update()

    def setNullPosition(self, position):
        if position != self.nullPosition:
            self.nullPosition = position
            if not self.gradientData:
                self.rebuildBrush = True
            self.update()

    def setBarStyle(self, style):
        if style != self.barStyle:
            self.barStyle = style
            self.update()

    def setOutlinePenWidth(self, penWidth):
        if penWidth != self.outlinePenWidth:
            self.outlinePenWidth = penWidth
            self.update()

    def setDataPenWidth(self, penWidth):
        if penWidth != self.dataPenWidth:
            self.dataPenWidth = penWidth
            self.update()

    def setDataColors(self, stopPoints):
        if stopPoints != self.gradientData:
            self.gradientData = stopPoints
            self.rebuildBrush = True
            self.update()

    def setFormat(self, format):
        if format != self.format:
            self.format = format
            self.valueFormatChanged()

    def resetFormat(self):
        self.format = ''
        self.valueFormatChanged()

    def setDecimals(self, count):
        if count >= 0 and count != self.decimals:
            self.decimals = count
            self.valueFormatChanged()

    def setDonutThicknessRatio(self, val):
        self.donutThicknessRatio = max(0., min(val, 1.))
        self.update()

    def paintEvent(self, event):
        outerRadius = min(self.width(), self.height())
        baseRect = QtCore.QRectF(1, 1, outerRadius - 2, outerRadius - 2)

        buffer = QtGui.QImage(outerRadius, outerRadius, QtGui.QImage.Format_ARGB32)
        buffer.fill(0)

        p = QtGui.QPainter(buffer)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        # data brush
        self.rebuildDataBrushIfNeeded()

        # background
        self.drawBackground(p, buffer.rect())
        # base circle
        self.drawBase(p, baseRect)

        # data circle
        # TODO crear properties para recibir integers o floats, mejor floats
        result = (self.max - self.min) * self.value
        if result != 0:
            arcStep = 360.0 / result
        else:
            arcStep = 0
        self.drawValue(p, baseRect, self.value, arcStep)

        # center circle
        innerRect, innerRadius = self.calculateInnerRect(baseRect, outerRadius)
        self.drawInnerBackground(p, innerRect)

        # text
        self.drawText(p, innerRect, innerRadius / 3, self.value)

        # finally draw the bar
        p.end()

        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, buffer)

    def drawBackground(self, p, baseRect):
        """Esta linea tira error porque self.palette().background() no existia"""
        p.fillRect(baseRect, self.palette().brush(self.palette().Background))

    def drawBase(self, p, baseRect):
        bs = self.barStyle
        if bs == self.StyleDonut:
            p.setPen(QtGui.QPen(self.palette().shadow().color(), self.outlinePenWidth))
            p.setBrush(self.palette().base())
            p.drawEllipse(baseRect)
        elif bs == self.StylePie:
            p.setPen(QtGui.QPen(self.palette().base().color(), self.outlinePenWidth))
            p.setBrush(self.palette().base())
            p.drawEllipse(baseRect)
        elif bs == self.StyleLine:
            p.setPen(QtGui.QPen(self.palette().base().color(), self.outlinePenWidth))
            p.setBrush(Qt.Qt.NoBrush)
            p.drawEllipse(
                baseRect.adjusted(self.outlinePenWidth / 2, self.outlinePenWidth / 2, -self.outlinePenWidth / 2,
                                  -self.outlinePenWidth / 2))

    def drawValue(self, p, baseRect, value, arcLength):
        # nothing to draw
        if value == self.min:
            return

        # for Line style
        if self.barStyle == self.StyleLine:
            p.setPen(QtGui.QPen(self.palette().highlight().color(), self.dataPenWidth))
            p.setBrush(Qt.Qt.NoBrush)
            p.drawArc(baseRect.adjusted(self.outlinePenWidth / 2, self.outlinePenWidth / 2, -self.outlinePenWidth / 2,
                                        -self.outlinePenWidth / 2),
                      self.nullPosition * 16,
                      -arcLength * 16)
            return

        # for Pie and Donut styles
        dataPath = QtGui.QPainterPath()
        dataPath.setFillRule(Qt.Qt.WindingFill)

        # pie segment outer
        dataPath.moveTo(baseRect.center())
        dataPath.arcTo(baseRect, self.nullPosition, -arcLength)
        dataPath.lineTo(baseRect.center())

        p.setBrush(self.palette().highlight())
        p.setPen(QtGui.QPen(self.palette().shadow().color(), self.dataPenWidth))
        p.drawPath(dataPath)

    def calculateInnerRect(self, baseRect, outerRadius):
        # for Line style
        if self.barStyle == self.StyleLine:
            innerRadius = outerRadius - self.outlinePenWidth
        else:  # for Pie and Donut styles
            innerRadius = outerRadius * self.donutThicknessRatio

        delta = (outerRadius - innerRadius) / 2.
        innerRect = QtCore.QRectF(delta, delta, innerRadius, innerRadius)
        return innerRect, innerRadius

    def drawInnerBackground(self, p, innerRect):
        if self.barStyle == self.StyleDonut:
            p.setBrush(self.palette().alternateBase())

            cmod = p.compositionMode()
            p.setCompositionMode(QtGui.QPainter.CompositionMode_Source)

            p.drawEllipse(innerRect)

            p.setCompositionMode(cmod)

    def drawText(self, p, innerRect, innerRadius, value):
        if not self.format:
            return

        text = self.valueToText(value)

        # !!! to revise
        f = self.font()
        # f.setPixelSize(innerRadius * max(0.05, (0.35 - self.decimals * 0.08)))
        f.setPixelSize(innerRadius * 3.5 / len(text))
        p.setFont(f)

        textRect = innerRect
        p.setPen(self.palette().text().color())
        p.drawText(textRect, Qt.Qt.AlignCenter, text)


    def valueToText(self, value):
        textToDraw = self.format

        format_string = '{' + ':.{}f'.format(self.decimals) + '}'

        if self.updateFlags & self.UF_VALUE:
            textToDraw = textToDraw.replace("%v", format_string.format(value))

        if self.updateFlags & self.UF_PERCENT:
            percent = (value - self.min) / (self.max - self.min) * 100.0
            textToDraw = textToDraw.replace("%p", format_string.format(percent))

        if self.updateFlags & self.UF_MAX:
            m = self.max - self.min + 1
            textToDraw = textToDraw.replace("%m", format_string.format(m))

        return textToDraw

    def valueFormatChanged(self):
        self.updateFlags = 0
        if "%v" in self.format:
            self.updateFlags |= self.UF_VALUE

        if "%p" in self.format:
            self.updateFlags |= self.UF_PERCENT

        if "%m" in self.format:
            self.updateFlags |= self.UF_MAX

        self.update()

    def rebuildDataBrushIfNeeded(self):
        if self.rebuildBrush:
            self.rebuildBrush = False

            dataBrush = QtGui.QConicalGradient()
            dataBrush.setCenter(0.5, 0.5)
            dataBrush.setCoordinateMode(QtGui.QGradient.StretchToDeviceMode)

            for pos, color in self.gradientData:
                dataBrush.setColorAt(1.0 - pos, color)

            # angle
            dataBrush.setAngle(self.nullPosition)

            p = self.palette()
            p.setBrush(QtGui.QPalette.Highlight, dataBrush)
            self.setPalette(p)



class QRoundTimer(QRoundProgressBar):
    """Clase creada para implementar el cronometro que pueda desbordar el valor, ejemplo que teniendo un valor maximo
    de 100, si tienes 101, el valor quedaria como 1.
    """

    UF_TIME = 8
    MILISECONDS = 3
    MICROSECONS = 6

    def __init__(self):
        super(QRoundTimer, self).__init__()
        self.actual_time: datetime.timedelta = datetime.timedelta(seconds=40, microseconds=655446)
        self.value = datetime.timedelta(seconds=0)

    def setValue(self, val):
        if isinstance(val, datetime.timedelta):
            super(QRoundTimer, self).setValue(val.microseconds / 10 ** 6)  # microseconds, in the decimals will change it
            self.actual_time = val
        else:
            super(QRoundTimer, self).setValue(val % self.max)

    def valueFormatChanged(self):
        self.updateFlags = 0
        if "%v" in self.format:
            self.updateFlags |= self.UF_VALUE

        if "%p" in self.format:
            self.updateFlags |= self.UF_PERCENT

        if "%m" in self.format:
            self.updateFlags |= self.UF_MAX

        if "%t" in self.format:
            self.updateFlags |= self.UF_TIME

        self.update()

    def valueToText(self, value):
        textToDraw = self.format

        format_string = '{' + ':.{}f'.format(self.decimals) + '}'

        if self.updateFlags & self.UF_VALUE:
            textToDraw = textToDraw.replace("%v", format_string.format(value))

        if self.updateFlags & self.UF_PERCENT:
            percent = (value - self.min) / (self.max - self.min) * 100.0
            textToDraw = textToDraw.replace("%p", format_string.format(percent))

        if self.updateFlags & self.UF_MAX:
            m = self.max - self.min + 1
            textToDraw = textToDraw.replace("%m", format_string.format(m))

        if self.updateFlags & self.UF_TIME:
            # TODO reworkear esto
            actual_seconds = self.actual_time.seconds
            hours, remainder = divmod(actual_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if actual_seconds < 3600:
                format_string = ("{:02}:" + format_string).format(minutes,
                                                                  seconds + self.actual_time.microseconds / (10 ** 6))
            else:
                format_string = ("{:02}{:02}:" + format_string).format(hours, minutes,
                                                                       seconds + self.actual_time.microseconds / (
                                                                                   10 ** 6))
            #m = self.actual_time.microseconds / (10 ** 6)
            textToDraw = textToDraw.replace("%t", format_string)

        return textToDraw


class __TstWidget(QWidget):
    """ Clase para probar el QRoundProgressBar, no utilizar. Solo basarse en esta"""

    def __init__(self, parent=None):
        super(type(self), self).__init__(parent)

        self.bar = QRoundTimer()
        # self.bar.setFixedSize(200, 200)

        self.bar.setDataPenWidth(2)  # es la anchura de las barras exteriores
        self.bar.setOutlinePenWidth(2)  # ??
        self.bar.setDonutThicknessRatio(0.75)  # Solo en los PIE y DONUT, es la anchura de la barra de progreso.
        self.bar.setDecimals(
            0)  # le das el numero de decimales si no hay formato no hace nada. Si es 0 es sin decimales
        # self.bar.setFormat('%v | %p %')
        self.bar.setFormat('%v')  # Le das formato al texto, sin texto no hay formato.
        self.bar.resetFormat()  # ResetFormat a ""
        self.bar.setNullPosition(90)  # ??
        self.bar.setBarStyle(QRoundProgressBar.StyleDonut)
        # self.bar.setDataColors([(0., QtGui.QColor.fromRgb(255,0,0)), (0.5, QtGui.QColor.fromRgb(255,255,0)), (1., QtGui.QColor.fromRgb(0,255,0))])
        self.bar.setDataColors([(0, QtGui.QColor.fromRgb(100, 100, 0))])
        # Metodo para darle un color, se le pasa una lista, con tuplas dentro.
        # El primer valor es el principio, y el segundo es el color, si hay varios hace un efecto de gradiente

        self.bar.setRange(0, 60)  # Minimo y maximo.
        self.bar.setValue(40)  # Valor actual

        lay = QVBoxLayout()
        lay.addWidget(self.bar)
        self.setLayout(lay)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = __TstWidget()
    window.show()
    app.exec_()
