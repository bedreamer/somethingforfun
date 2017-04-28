# -*- coding: UTF-8 -*-
__author__ = 'lijie'
import os
import struct
import sys
import re

# surface description flags
DDSF_CAPS = 0x00000001
DDSF_HEIGHT = 0x00000002
DDSF_WIDTH = 0x00000004
DDSF_PITCH = 0x00000008
DDSF_PIXELFORMAT = 0x00001000
DDSF_MIPMAPCOUNT = 0x00020000
DDSF_LINEARSIZE = 0x00080000
DDSF_DEPTH = 0x00800000

# pixel format flags
DDSF_ALPHAPIXELS = 0x00000001
DDSF_FOURCC = 0x00000004
DDSF_RGB = 0x00000040
DDSF_RGBA = 0x00000041

# dwCaps1 flags
DDSF_COMPLEX = 0x00000008
DDSF_TEXTURE = 0x00001000
DDSF_MIPMAP = 0x00400000

# dwCaps2 flags
DDSF_CUBEMAP = 0x00000200
DDSF_CUBEMAP_POSITIVEX = 0x00000400
DDSF_CUBEMAP_NEGATIVEX = 0x00000800
DDSF_CUBEMAP_POSITIVEY = 0x00001000
DDSF_CUBEMAP_NEGATIVEY = 0x00002000
DDSF_CUBEMAP_POSITIVEZ = 0x00004000
DDSF_CUBEMAP_NEGATIVEZ = 0x00008000
DDSF_CUBEMAP_ALL_FACES = 0x0000FC00
DDSF_VOLUME = 0x00200000


class FileLoader(object):
    def __init__(self):
        pass

    def load_val(self, f, size, format):
        data = f.read(size)
        return struct.unpack(format, data)[0]

    def load_vals(self, f, size, format):
        data = f.read(size)
        return struct.unpack(format, data)


class DDPIXELFORMAT(FileLoader):
    def __init__(self, f):
        super(DDPIXELFORMAT, self).__init__()
        self.dwSize = self.load_val(f, 4, 'I')
        self.dwFlags = self.load_val(f, 4, 'I')
        self.dwFourCC = self.load_val(f, 4, '4s')
        self.dwRGBBitCount = self.load_val(f, 4, 'I')
        self.dwRBitMask = self.load_val(f, 4, 'I')
        self.dwGBitMask = self.load_val(f, 4, 'I')
        self.dwBBitMask = self.load_val(f, 4, 'I')
        self.dwRGBAlphaBitMask = self.load_val(f, 4, 'I')

    def __repr__(self):
        s = '  {\n'
        for name, value in vars(self).items():
            s = s + '    %s=%s\n'  % (name, value)
        return s + '    }'

class DDCAPS2(FileLoader):
    def __init__(self, f):
        super(DDCAPS2, self).__init__()
        self.dwCaps1 = self.load_val(f, 4, 'I')
        self.dwCaps2 = self.load_val(f, 4, 'I')
        self.Reserved = self.load_vals(f, 4 * 2, 'I' * 2)

    def __repr__(self):
        s = '  {\n'
        for name, value in vars(self).items():
            s = s + '    %s=%s\n'  % (name, value)
        return s + '    }'

class DDSURFACEDESC2(FileLoader):
    def __init__(self, f):
        super(DDSURFACEDESC2, self).__init__()
        self.dwSize = self.load_val(f, 4, 'I')
        self.dwFlags = self.load_val(f, 4, 'I')
        self.dwHeight = self.load_val(f, 4, 'I')
        self.dwWidth = self.load_val(f, 4, 'I')
        self.dwPitchOrLinearSize = self.load_val(f, 4, 'I')
        self.dwDepth = self.load_val(f, 4, 'I')
        self.dwMipMapCount = self.load_val(f, 4, 'I')
        self.dwReserved1 = self.load_vals(f, 4 * 11, 'I' * 11)
        self.ddpfPixelFormat = DDPIXELFORMAT(f)
        self.ddsCaps = DDCAPS2(f)
        self.dwReserved2 = self.load_val(f, 4, 'I')

    def __repr__(self):
        s = '  {\n'
        for name, value in vars(self).items():
            s = s + '    %s=%s\n'  % (name, value)
        return s + '  }'


class DDSTexture:
    def __init__(self, width, height, depth, size, pixels):
        self.width = width
        self.height = height
        self.depth = depth
        self.size = size
        self.pixels = pixels
        
        self.mimpmap = []

    def __repr__(self):
        s = 'DDSFile {\n'
        for name, value in vars(self).items():
            if name != 'pixels':
                s = s + '  %s=%s\n'  % (name, value)
            elif len(self.pixels) < 64:
                s = s + '  %s=%s\n'  % (name, value.encode('hex'))
            else:
                s = s + '  pixels=%d bytes\n'  % len(self.pixels)
        return s + '}'


class DDSFile(FileLoader):
    def __init__(self, path):
        f = open(path, 'r')

        super(DDSFile, self).__init__()

        self.magic = self.load_val(f, 4, '4s')        
        self.ddsd = DDSURFACEDESC2(f)

        self.m_type = 'TextureFlat'
        if self.ddsd.ddsCaps.dwCaps2 & DDSF_CUBEMAP != 0:
            self.m_type = 'TextureCubemap'
        if self.ddsd.ddsCaps.dwCaps2 & DDSF_VOLUME != 0 and self.ddsd.dwDepth > 0:
            self.m_type = 'Texture3D'
        
        if self.ddsd.ddpfPixelFormat.dwFlags & DDSF_FOURCC != 0:
            if self.ddsd.ddpfPixelFormat.dwFourCC == 'DXT1':
                self.m_format = 'GL_COMPRESSED_RGBA_S3TC_DXT1_EXT'
                self.m_components = 3
            elif self.ddsd.ddpfPixelFormat.dwFourCC == 'DXT3': 
                self.m_format = 'GL_COMPRESSED_RGBA_S3TC_DXT3_EXT'
                self.m_components = 4
            elif self.ddsd.ddpfPixelFormat.dwFourCC == 'DXT5':         
                self.m_format = 'GL_COMPRESSED_RGBA_S3TC_DXT5_EXT'
                self.m_components = 4
            else:
                raise TypeError('unkown dw FourCC')
        elif self.ddsd.ddpfPixelFormat.dwRGBBitCount == 32:
            self.m_format = 'GL_BGRA_EXT | GL_RGBA'
            self.m_components = 4
        elif self.ddsd.ddpfPixelFormat.dwRGBBitCount == 24:
            self.m_format = 'GL_RGB | GL_BGR_EXT'
            self.m_components = 3
        elif self.ddsd.ddpfPixelFormat.dwRGBBitCount == 8:
            self.m_format = 'GL_LUMINANCE'
            self.m_components = 1
        else:
            raise TypeError('unkown ddsh.ddspf.dwRGBBitCount!!')
            
        self.imgs = []

        if self.ddsd.dwDepth == 0:
            self.ddsd.dwDepth = 1
        
        biggest = 0
        if self.m_type == 'TextureCubemap':
            biggest = 6
        else:
            biggest = 1
        i = 0
        width = self.ddsd.dwWidth
        height = self.ddsd.dwHeight
        depth = self.ddsd.dwDepth
        while i < biggest:
            if self.is_compressed() is True:
                if self.m_format == 'GL_COMPRESSED_RGBA_S3TC_DXT1_EXT':
                    scale = 8
                else:
                    scale = 16
                size = ((width + 3) / 4) * ((height + 3) / 4) * scale;
            else:
                size = width * height * self.m_components;
            size = size * depth
            print size
            pixels = f.read(size)
            img = DDSTexture(width, height, depth, size, pixels)
            self.imgs.append( img )
            i = i + 1
            
            w = width >> 1
            if w <= 0:
                w = 1
            h = height >> 1
            if h <= 0:
                h = 1
            d = depth >> 1
            if d <= 0:
                d = 1
            if self.ddsd.dwMipMapCount > 0:
                nummipmaps = self.ddsd.dwMipMapCount - 1
            else:
                nummipmaps = 0

            j = 0
            while j < nummipmaps and ( w > 0 or h > 0 ):
                j = j + 1
                if self.is_compressed() is True:
                    if self.m_format == 'GL_COMPRESSED_RGBA_S3TC_DXT1_EXT':
                        scale = 8
                    else:
                        scale = 16
                    size = ((w + 3) / 4) * ((h + 3) / 4) * scale;
                else:
                    size = w * h * self.m_components;
                size = size * d
                pixels = f.read(size)
                mimpmap = DDSTexture(w, h, d, size, pixels)
                img.mimpmap.append(mimpmap)
                
                w = w >> 1
                if w <= 0:
                    w = 1
                h = h >> 1
                if h <= 0:
                    h = 1
                d = d >> 1
                if d <= 0:
                    d = 1

        f.close()

    def is_compressed(self):
        g = [
            'GL_COMPRESSED_RGBA_S3TC_DXT1_EXT',
            'GL_COMPRESSED_RGBA_S3TC_DXT3_EXT',
            'GL_COMPRESSED_RGBA_S3TC_DXT5_EXT'
        ]
        if self.m_format in g:
            return True

        return False

    def __repr__(self):
        s = 'DDSFile {\n'
        for name, value in vars(self).items():
            s = s + '  %s=%s\n'  % (name, value)
        return s + '}'

r = re.compile('.+\.dds')
for f in os.listdir('/home/kirk/Desktop/Resource/Model'):
    if re.match(r, f) is None:
        continue
    p  = '/home/kirk/Desktop/Resource/Model/' + f
    print p
    print DDSFile(p)
    print 
    print


