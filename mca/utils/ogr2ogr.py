import os
import shutil
import glob
import re
import sys
import time
import subprocess
from subprocess import Popen, PIPE
from mca.model.meta import *
import traceback

# --- wxPython threadsafe  ---
import threading
import wx
from wx.lib.pubsub import Publisher


def cleanTemporaryFiles(path):
    # os.rmdir doesn't work if the folder isn't empty
    shutil.rmtree(path)


class Postgresql_2_shp(threading.Thread):

    def __init__(self, path_2_shp, schema, table, callback):
        threading.Thread.__init__(self) # init Worker Thread Class
        self._stop = threading.Event()

        self.callback = callback
        self.path_2_shp = path_2_shp
        self.schema = schema
        self.table = table

        self.start() # start the thread

    def stop(self):
        self._stop.set()

    def run(self):
        #psql_pass = dict(PGPASSWORD = password)
        try:
            #su_process = Popen("pgsql2shp -u "+user+" "+"-h "+host+" "+"-f "+self.path_2_shp+" "+database+" "+self.schema+"."+self.table, shell=True, env=psql_pass, stdout=PIPE, stderr=PIPE)
            #su_process.wait()
            subprocess.check_call(["pgsql2shp", "-u", user, "-h", host, "-f", self.path_2_shp, database, self.schema+"."+self.table])
            wx.CallAfter(Publisher().sendMessage, self.callback, self.table)
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the conversion from sql to shp")
            self.stop()


class Populate(threading.Thread):

    def __init__(self, shp, s_srs, t_srs, table, callback):
        threading.Thread.__init__(self) # init Worker Thread Class
        self._stop = threading.Event()

        self.callback = callback
        self.shp = str(shp)
        self.s_srs = str(s_srs)
        self.t_srs = str(t_srs)
        self.table = str(table)

        self.basePath = '/tmp/%s/' %time.time()
        os.mkdir(self.basePath)

        self.start() # start the thread

    def stop(self):
        self._stop.set()

    def run(self):
        self.baseShp = self.shp.strip('shp')
        self.baseReproj = self.basePath + self.table + '.'
        self.reproj = self.baseReproj + 'shp'
        self.sql = self.baseReproj + 'sql'

        if self.s_srs != self.t_srs:
            wx.CallAfter(Publisher().sendMessage, "consoleAppend", "Reprojecting file...")
            self.reproject()
        else:
            wx.CallAfter(Publisher().sendMessage, "consoleAppend", "Not reprojected since input srs is the same than the output srs")
            for filename in glob.glob(self.baseShp+'*'):
                filenameReproj = filename.replace(self.baseShp, self.baseReproj)
                shutil.copy(filename, filenameReproj)

        if not self._stop.isSet():
            wx.CallAfter(Publisher().sendMessage, "consoleAppend", "Converting file to sql...")
            self.shp_2_sql()

        if not self._stop.isSet():
            wx.CallAfter(Publisher().sendMessage, "consoleAppend", "Loading file to the database...")
            self.sql_2_postgresql()

        if not self._stop.isSet():
            wx.CallAfter(Publisher().sendMessage, self.callback, self.basePath)

    def reproject(self):
        s_srs = "EPSG:" + self.s_srs
        t_srs = "EPSG:" + self.t_srs
        # if the input srs is the same than the output srs -> we don't reproject'
        try:
            subprocess.check_call(["ogr2ogr","-s_srs", s_srs, "-t_srs", t_srs, "-a_srs", t_srs, "-f", "ESRI Shapefile", self.reproj, self.shp])
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the reprojection")
            self.stop()

    # TODO Test Encoding
    def shp_2_sql(self, encoding='LATIN1'):
        try:
            subprocess.check_call(["sh", "-c", "shp2pgsql -s "+self.t_srs+" "+"-W"+" "+encoding+" "+self.reproj+" "+self.table+" > "+self.sql])
        except:
            encoding = 'UTF-8'
            try:
                subprocess.check_call(["sh", "-c", "shp2pgsql -s "+self.t_srs+" "+"-W"+" "+encoding+" "+self.reproj+" "+self.table+" > "+self.sql])
            except:
                print traceback.print_exc()
                wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the conversion of the shapefile to sql")
                self.stop()

    def sql_2_postgresql(self):
        try:
            subprocess.check_call(["psql", "-U", user, "-d", database, "-h", host, "-f", self.sql])
        except:
            print traceback.print_exc()
            wx.CallAfter(Publisher().sendMessage, "catchError", "An error occured during the data loading")
            self.stop()

