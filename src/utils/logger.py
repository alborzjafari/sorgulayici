import os
import sys
import pathlib
import platform
from os import listdir
from os.path import isfile, join
from datetime import datetime, date
import traceback

class Logger:
  logFileCreated = False
  logFileName = "" # Defalt name is only date string
  logDirPath = "/var/log/"
  if platform.system() == 'Windows':
    logDirPath = pathlib.Path(sys.executable).parent.resolve()
  dateFormat = "%d-%m-%Y"
  logLevel = 0

  @staticmethod
  def setLogDir(logDir):
      print("First Log DIRRRRRRRR:", Logger.logDirPath)
      Logger.logDirPath = join(Logger.logDirPath, logDir)
      print("Last Log DIRRRRRRRR:", Logger.logDirPath)

  @staticmethod
  def setLogFileName(logFileName):
      Logger.logFileName = logFileName

  @staticmethod
  def createLogFile():
      if not Logger.logFileCreated:
          today = date.today()
          logFileName = Logger.logFileName + "_" +\
                        today.strftime(Logger.dateFormat) + ".txt"
          pathlib.Path(Logger.logDirPath).mkdir(parents=True, exist_ok=True)
          logFilePath = join(Logger.logDirPath, logFileName)
          Logger.logFile = open(logFilePath, 'a')
          Logger.logFileCreated = True
          Logger.checkLogFileLifeTime()

  @staticmethod
  def getFileLifeTime(logFile):
      firstPos = logFile.find('_') + 1
      if firstPos:
        dateStr = logFile[firstPos : firstPos + 10]
      else:
        return None
      print(logFile + " :: " + dateStr)
      try:
        logDateobj = datetime.strptime(dateStr, Logger.dateFormat)
        timeDiff = datetime.now() - logDateobj
      except:
        return None

      return timeDiff


  @staticmethod
  def checkLogFileLifeTime():
      logFiles = [f for f in listdir(Logger.logDirPath) if isfile(join(Logger.logDirPath, f))]
      for logFile in logFiles:
          fileDatediff = Logger.getFileLifeTime(logFile)
          if fileDatediff != None and fileDatediff.days >= 2:
              fileToDelete = join(Logger.logDirPath, logFile)
              os.remove(fileToDelete)

  @staticmethod
  def setLogFileName(logFileName):
      Logger.logFileName = logFileName

  @staticmethod
  def setLogLevel(level):
    """
    level: 0: Errors only, 1: all
    """
    Logger.logLevel = level

  @staticmethod
  def log(operation="", error=""):
    """
    :param operation: Current operation as string.
    :param error: Current error as string.
    """

    if Logger.logLevel == 0 and not error:
      return

    Logger.createLogFile()

    date_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log = '[' + date_string + '] '
    if error:
      log += 'Err:[' + error + ']'
    if operation:
      log += 'Opr:[' + operation + ']'
    log += '\n'
    Logger.logFile.write(log)
    Logger.logFile.flush()


if __name__ == '__main__':
  Logger.setLogLevel(1)
  Logger.log(operation="ops")
  Logger.log(error="err")