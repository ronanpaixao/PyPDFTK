# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 16:06:03 2016

@author: Ronan Paixão
"""
from PIL import Image
from cStringIO import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

img_modes = {'/DeviceRGB': 'RGB', '/DefaultRGB': 'RGB',
             '/DeviceCMYK': 'CMYK', '/DefaultCMYK': 'CMYK',
             '/DeviceGray': 'L', '/DefaultGray': 'L',
             '/Indexed': 'P'}

import PyPDF2 as pdf

def extract_images(page):
    # Image information on PDF Reference Manual, pg 340
    imgs = []
    for img_name, img_indir_obj in p['/Resources']['/XObject'].items():
        img_obj = img_indir_obj.getObject()
        print(img_name, img_obj['/Subtype'])
        if img_obj.get('/Subtype', '') == '/Image' and img_obj.get('/Filter', '') == '/FlateDecode':
            color_space = img_obj['/ColorSpace']
            if isinstance(color_space, pdf.generic.ArrayObject) and color_space[0] == '/Indexed':
                color_space, base, hival, lookup = [v.getObject() for v in color_space] # pg 262
            print("Image: {}bpc, w={}, h={}, len={}, colorspace={}".format(
                img_obj['/BitsPerComponent'], img_obj['/Width'],
                img_obj['/Height'], len(img_obj.getData()), color_space))
            img_mode = img_modes[color_space]
            img_size = (img_obj['/Width'], img_obj['/Height'])
            img_buffer = StringIO()
            img_buffer.write(img_obj.getData())
            img = Image.frombytes(img_mode, img_size, img_obj.getData())
            if color_space == '/Indexed':
                img.putpalette(lookup.getData())
                img = img.convert('RGB')
            imgs.append(img)
    return imgs

def image_to_pdf(image_filename, page_size_cm):
    tmp = StringIO()
    image_reader = ImageReader(image_filename)
    size_pdf = [s/2.54*72 for s in page_size_cm] # cm->in->1/72" (PDF unit)
    output_pdf = canvas.Canvas(tmp, pagesize=size_pdf)
    output_pdf.drawImage(image_reader, 0, 0, *size_pdf, mask='auto')
    output_pdf.showPage()
    output_pdf.save()
    tmp.seek(0)
    return tmp
