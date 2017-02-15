#!/usr/bin/python
# -*- coding:utf8 -*-
import urllib2
import ConfigParser
import logging 
import platform

def create(loginfo):
                str=platform.system()
                if (str=="Windows"):
                    logfile='D:\\release\\logs\\common.log'
                else:
                    logfile='/opt/logs/release/common.log'
                logger = None
                logger = logging.getLogger()
                hdlr = logging.FileHandler(logfile)
                formatter = logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")
                hdlr.setFormatter(formatter)
                logger.addHandler(hdlr)
                logger.setLevel(logging.DEBUG)
                logging.info(loginfo)
                logger.removeHandler (hdlr)