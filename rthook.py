# -*- coding: utf-8 -*-
"""
Created on Sun Mar 20 14:28:10 2016

@author: Ronan
"""
print("HERE###################")
# Setup PyQt's v2 APIs
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl",
             "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)