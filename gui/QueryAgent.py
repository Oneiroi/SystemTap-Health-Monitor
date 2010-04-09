#!/usr/bin/python
# systemtap health monitor
# Copyright (C) 2010 Aaron Luchko
#
# This file is part of systemtap, and is free software.  You can
# redistribute it and/or modify it under the terms of the GNU General
# Public License (GPL); either version 2, or (at your option) any
# later version.

import MetricTypeWindow
import Metrics
import AppWindow
import pygtk, gtk


from time import sleep
import threading
import time
import MySQLdb

# The roll of this class is to keep the MetricTypeWindows supplied with the current list of Metrics and their current values.
class QueryAgent(threading.Thread):
    def __init__ (self, appWindow):
        threading.Thread.__init__(self)
        self.setup = False
        self.appWindow = appWindow
        self.mtws = {} # list of MetricTypeWindows, 1 for each MetricType
        self.quit = False
        self.stopthread = threading.Event()
        self.lastTime = 0

    def update_metrics(self):
        print "update_metrics "+str(time.time())
        if (not self.setup): # create in this thread to be safe
            self.connection = MySQLdb.connect(host="localhost", user="health", passwd="password", db="health")
            self.setup = True
            # start with the previous to last sample
            lastTimeCursor = self.connection.cursor()
            lastTimeCursor.execute("select max(time) from metric_value where time < (select max(time) from metric_value)")
            self.lastTime = lastTimeCursor.fetchone()[0]
        typeCursor = self.connection.cursor()

        # we don't want the mtws list to change from under us
        mt_id_list = "(" #  yeah, only works for 1
        self.appWindow.lock.acquire()
        for mtw_id in self.appWindow.mtws:
            mt_id_list = mt_id_list + str(mtw_id)
        self.appWindow.lock.release()
        mt_id_list = mt_id_list + ")"
        mt_id_list = "(1,2)"
        # Every metric and it's most recent value since our last check
        metricCursor = self.connection.cursor()
        metricCursor.execute("select m.id, m.metric_type_id, m.name, m.mean, m.num_samples, m.m2, mv.value FROM metric m, metric_value mv WHERE m.id=mv.metric_id and m.num_samples > 1 AND mv.time > " + str(self.lastTime) + " AND mv.time = (select max(time) FROM metric_value WHERE metric_value.metric_id=m.id) GROUP BY m.id ORDER BY m.metric_type_id")
        print("select m.id, m.metric_type_id, m.name, m.mean, m.num_samples, m.m2, mv.value FROM metric m, metric_value mv WHERE m.id=mv.metric_id and m.num_samples > 1 AND mv.time > " + str(self.lastTime) + " AND mv.time = (select max(time) FROM metric_value WHERE metric_value.metric_id=m.id) GROUP BY m.id ORDER BY m.metric_type_id")

        # hrm, might miss a sample
        lastTimeCursor = self.connection.cursor()
        lastTimeCursor.execute("select max(time) from metric_value")
        self.lastTime = lastTimeCursor.fetchone()[0]


        mt_id = -1
        mtw = -1

        gtk.gdk.threads_enter()
        self.appWindow.lock.acquire()

        for metricRow in metricCursor:
            if not mt_id == metricRow[1]: # switch to new metricType
                print "new mtw "+str(metricRow[1])
                if not mtw == -1: # update the display of the last metricTypeWindow
                    mtw.purgeOldMetrics()
                    mtw.update()                    
                mt_id = metricRow[1]

                # it's possible the mtw has been closed since we got it
                if mt_id in self.appWindow.mtws:
                    mtw = self.appWindow.mtws[mt_id]
                else:
                    mtw = -1

            if mtw == -1:
                continue
            #mtw.lock.acquire()
           # gtk.gdk.threads_enter()
#            mtw = self.mtws[metricRow[1]]
            # lock so none other messes around with metricList
            # The metric could either have never been added or could have been removed
            if metricRow[0] not in mtw.metricList:
                metric = Metrics.Metric(metricRow[0], mtw.metricType, metricRow[2], metricRow[3], metricRow[4], metricRow[5])

                mtw.addMetric(metric)


            mtw.updateMetric(metricRow[0], metricRow[6])

            #gtk.gdk.threads_leave()
            #mtw.lock.release()
        if not mtw == -1:
            mtw.purgeOldMetrics()
            mtw.update() # update the display of the last mtw

        self.appWindow.lock.release()

        gtk.gdk.threads_leave()

    def run(self):
        while not self.stopthread.isSet() and not self.appWindow.stopthread.isSet():
            self.update_metrics()
            sleep(1)

    def stop(self):
        self.stopthread.set()
