# -*- coding: utf-8 -*-
"""
The Python PDF Toolkit
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE.txt for details.

@author: Ronan Paixão
"""

# Setup PyQt's v2 APIs
import sip
API_NAMES = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl",
             "QVariant"]
API_VERSION = 2
for name in API_NAMES:
    sip.setapi(name, API_VERSION)