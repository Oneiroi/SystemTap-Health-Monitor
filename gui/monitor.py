#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import sys, string
import MetricTypeWindow, Metrics, QueryAgent
import gobject
gobject.threads_init()
 
def main():
    # And of course, our main loop.
    gtk.main()
    # Control returns here when main_quit() is called
    return 0         

if __name__ =="__main__":
    metricWindow = MetricTypeWindow.MetricTypeWindow("usage")
 #   mt = Metrics.MetricType(1,"usage", 0, 100, 0)
#    metricWindow.addMetricType(mt)
#    metric = Metrics.Metric(1, mt, "firefox", 50, 20, 25)
 #   metricWindow.addMetric(metric)
    print "FOO"
    queryAgent = QueryAgent.QueryAgent(metricWindow)
    queryAgent.start()
    main()
    queryAgent.quit = True