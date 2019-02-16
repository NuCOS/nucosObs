# -*- coding: utf-8 -*-
"""
backbonelogger
--------------

.. module:: backbonelogger
   :platform: Unix, Windows
   :synopsis: provides logging

log levels:

========  ===========
ERROR     'ERROR'
WARNING   'WARNING'
INFO      'INFO'
DEBUG     'DEBUG'
========  ===========

Created 2016/2017

@author: oliver, johannes
"""

import logging
import sys
import os
log_filename = "./out.log"

class Logger():
    """
    This brings advanced logging from the python batteries::

        logger = Logger('clientLogger')
        logger.format(
            [], '[%(asctime)-15s] %(name)-8s %(levelname)-7s  -- %(message)s')
        logger.level("DEBUG")

    format can receive items, that are not necessary::

         logger.format(
             ["clientip","user"], '[%(asctime)-15s] %(name)-8s %(levelname)-7s %(clientip)s %(user)s -- %(message)s')

    a basic logger format would be::

        "%(levelname)s:%(name)s:%(message)s"

    """

    def __init__(self, name, path=os.path.dirname(__file__)):
        self.logger = logging.getLogger(name=name)
        self.items = []
        self.path = path
        self.formatter = None
        self.format(
            ["orig"],
            '[%(asctime)-15s] %(orig)-12s %(levelname)-7s -- %(message)s')
        self.deb = "DEBUG"
        self.inf = "INFO"
        self.war = "WARNING"
        self.err = "ERROR"
        self.cri = "CRITICAL"
        self.level(self.war)

    def getLogger(self):
        return self

    def format(self, items, FORMAT):
        """
        :param items: [] list type item argument(s)
        :param FORMAT: '[%(asctime)-15s] %(name)-8s %(levelname)-7s  -- %(message)s' format string e.g. with four variables
        """
        if self.logger.handlers:
            return
        self.items = items
        handler = logging.StreamHandler()
        filehandler = logging.FileHandler(log_filename)
        self.formatter = logging.Formatter(FORMAT)
        handler.setFormatter(self.formatter)
        filehandler.setFormatter(self.formatter)
        self.logger.addHandler(handler)
        self.logger.addHandler(filehandler)

    def level(self, loglevel):
        numeric_level = getattr(logging, loglevel.upper(), None)
        if isinstance(numeric_level, int):
            self.logger.setLevel(numeric_level)
        else:
            raise ValueError('Invalid log level: %s' % loglevel)

    def log(self, *msgs, **logdict):
        """
        more robust version, since missing arguments in the logdict are handled correctly

        log levels:

        ========  ===========  =================================================
        CRITICAL  'CRITICAL'   the program may be unable to continue running
        ERROR     'ERROR'      show a serious problem
        WARNING   'WARNING'    indicate something unexpected to happen
        INFO      'INFO'       confirm that things are working
        DEBUG     'DEBUG'      show detailed information
        ========  ===========  =================================================

        Most commonly used like this (inside class and function)::

            self.cn = self.__class__.__name__
            message = "message1"

            log(lvl="INFO", msg=message, orig=self.cn)

            >> [2018-08-14 16:33:45,488] Class_name.fun_name DEBUG   -- message1

        """
        # if logger.isEnabledFor(self.DEBUG):
        # this is to put a special output level in the Logger class

        if not msgs:
            msg = logdict.pop('msg')
        else:
            msg = msgs[0]
        for i in self.items:
            if i not in logdict.keys():
                logdict.update({i: ""})
        if 'lvl' in logdict.keys():
            lvl = logdict['lvl']
            numeric_level = getattr(logging, lvl.upper(), None)
            if not isinstance(numeric_level, int):
                raise ValueError('Invalid log level: %s' % lvl)
        else:
            numeric_level = self.inf

        # adds the function name of the function calling log()
        if "orig" in logdict.keys():
            logdict["orig"] = f"{logdict['orig']}.{sys._getframe(1).f_code.co_name}"

        self.logger.log(numeric_level, msg, extra=logdict)



