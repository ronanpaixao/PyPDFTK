# -*- coding: utf-8 -*-
"""
The Python PDF Toolkit
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE.txt for details.

Links:
PDF format: http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf
CCITT Group 4: https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-T.6-198811-I!!PDF-E&type=items
Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html

@author: Ronan Paixão, with some code from
    http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
"""
import struct
import base64

from PIL import Image
try:
    from cStringIO import StringIO as BytesIO
except ModuleNotFoundError:  # Py3
    from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO

import PyPDF2 as pdf


img_modes = {'/DeviceRGB': 'RGB', '/DefaultRGB': 'RGB',
             '/DeviceCMYK': 'CMYK', '/DefaultCMYK': 'CMYK',
             '/DeviceGray': 'L', '/DefaultGray': 'L',
             '/Indexed': 'P'}


def tiff_header_for_CCITT(width, height, img_size, CCITT_group=4):
    tiff_header_struct = '<' + '2s' + 'h' + 'l' + 'h' + 'hhll' * 8 + 'h'
    return struct.pack(tiff_header_struct,
                       b'II',  # Byte order indication: Little indian
                       42,  # Version number (always 42)
                       8,  # Offset to first IFD
                       8,  # Number of tags in IFD
                       256, 4, 1, width,  # ImageWidth, LONG, 1, width
                       257, 4, 1, height,  # ImageLength, LONG, 1, lenght
                       258, 3, 1, 1,  # BitsPerSample, SHORT, 1, 1
                       259, 3, 1, CCITT_group,  # Compression, SHORT, 1, 4 = CCITT Group 4 fax encoding
                       262, 3, 1, 0,  # Threshholding, SHORT, 1, 0 = WhiteIsZero
                       273, 4, 1, struct.calcsize(tiff_header_struct),  # StripOffsets, LONG, 1, len of header
                       278, 4, 1, height,  # RowsPerStrip, LONG, 1, lenght
                       279, 4, 1, img_size,  # StripByteCounts, LONG, 1, size of image
                       0  # last IFD
                       )


def extract_images(page, filename_prefix="IMG_", start_index=0):

    if '/XObject' not in page['/Resources']:
        return start_index
    xObject = page['/Resources']['/XObject'].getObject()

    i = start_index
    for obj in xObject:
        if xObject[obj]['/Subtype'] == '/Image':
            filt = xObject[obj]['/Filter']
            print("extracting {} to {}{:04}.xxx".format(filt, filename_prefix, i))
            size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
            color_space = xObject[obj]['/ColorSpace']
            if isinstance(color_space, pdf.generic.ArrayObject) and color_space[0] == '/Indexed':
                color_space, base, hival, lookup = [v.getObject() for v in color_space] # pg 262
            mode = img_modes[color_space]

            # xObject[obj].getData() does not work for DCTDecode, JPXDecode and
            # CCITTFaxDecode
            if '/FlateDecode' in filt:
                data = xObject[obj].getData()
            else:
                data = xObject[obj]._data  #   # for /FlateDecode only?

            if data.endswith(b'~>'):
                data = base64.a85decode(data, adobe=True)

            if isinstance(filt, list):
                while len(filt) > 1:
                    first_filter = filt.pop(0)
                    if first_filter == '/ASCII85Decode':
                        continue
                    else:
                        print("Unsupported filter:", first_filter)
                        return i
                filt = filt[0]

            if filt == '/FlateDecode':
                img = Image.frombytes(mode, size, data)
                if color_space == '/Indexed':
                    img.putpalette(lookup.getData())
                    img = img.convert('RGB')
                img.save("{}{:04}.png".format(filename_prefix, i))
            elif filt == '/DCTDecode':
                img = open("{}{:04}.jpg".format(filename_prefix, i), "wb")
                img.write(data)
                img.close()
            elif filt == '/JPXDecode':
                img = open("{}{:04}.jp2".format(filename_prefix, i), "wb")
                img.write(data)
                img.close()
#            The  CCITTFaxDecode filter decodes image data that has been encoded using
#            either Group 3 or Group 4 CCITT facsimile (fax) encoding. CCITT encoding is
#            designed to achieve efficient compression of monochrome (1 bit per pixel) image
#            data at relatively low resolutions, and so is useful only for bitmap image data, not
#            for color images, grayscale images, or general data.
#
#            K < 0 --- Pure two-dimensional encoding (Group 4)
#            K = 0 --- Pure one-dimensional encoding (Group 3, 1-D)
#            K > 0 --- Mixed one- and two-dimensional encoding (Group 3, 2-D)
            elif filt == '/CCITTFaxDecode':
                if xObject[obj]['/DecodeParms']['/K'] == -1:
                    CCITT_group = 4
                else:
                    CCITT_group = 3
                width = xObject[obj]['/Width']
                height = xObject[obj]['/Height']

                img_size = len(data)
                tiff_header = tiff_header_for_CCITT(width, height, img_size, CCITT_group)
                img_name = "{}{:04}.tiff".format(filename_prefix, i)
                with open(img_name, 'wb') as img_file:
                    img_file.write(tiff_header + data)
            i += 1

    return i


def image_to_pdf(image_filename, page_size_cm):
    tmp = BytesIO()
    image_reader = ImageReader(image_filename)
    size_pdf = [s/2.54*72 for s in page_size_cm] # cm->in->1/72" (PDF unit)
    output_pdf = canvas.Canvas(tmp, pagesize=size_pdf)
    output_pdf.drawImage(image_reader, 0, 0, *size_pdf, mask='auto')
    output_pdf.showPage()
    output_pdf.save()
    tmp.seek(0)
    return tmp
