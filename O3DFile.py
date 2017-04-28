# -*- coding: UTF-8 -*-
__author__ = 'lijie'
import os
import struct
import sys
from DDSFile import *

class O3DTypeBase(object):
    def __init__(self, f):
        self.f = f

    def read(self, n):
        return self.f.read(n)

    def read_uchar(self):
        data = self.read(1)
        return struct.unpack('B', data)

    def read_float(self):
        return self.read_floats(1)

    def read_floats(self, n):
        data = self.read(4 * n)
        return struct.unpack('f' * n, data)

    def read_word(self):
        return self.read_words(1)

    def read_words(self, n):
        data = self.read(2 * n)
        return struct.unpack('H' * n, data)

    def read_dword(self):
        return self.read_dwords(1)

    def read_dwords(self, n):
        data = self.read(4 * n)
        return struct.unpack('I' * n, data)

    def read_string(self, n):
        data = self.read(4 * n)
        return struct.unpack('%ds', data)


class O3D_String(O3DTypeBase):
    def __init__(self, f, name, n):
        super(O3D_String).__init__(self, f)
        self.name = name
        self.v = self.read_string(n)

    def __repr__(self):
        return self.v


class O3D_Float(O3DTypeBase):
    def __init__(self, f, name):
        super(O3D_Float).__init__(self, f)
        self.name = name
        self.v = self.read_float()

    def __repr__(self):
        return "%.5f" % self.v


class O3D_Word(O3DTypeBase):
    def __init__(self, f, name):
        super(O3D_Word).__init__(self, f)
        self.name = name
        self.v = self.read_word()

    def __repr__(self):
        return "%d" % self.v


class O3D_Uchar(O3DTypeBase):
    def __init__(self, f, name):
        super(O3D_Uchar).__init__(self, f)
        self.name = name
        self.v = self.read_uchar()

    def __repr__(self):
        return "%d" % self.v


class O3D_Dword(O3DTypeBase):
    def __init__(self, f, name):
        super(O3D_Dword).__init__(f)
        self.name = name
        self.v = self.read_dword()

    def __repr__(self):
        return "%d" % self.v


class O3D_D3DXVECTOR3(O3DTypeBase):
    def __init__(self, f, name):
        super(O3D_D3DXVECTOR3).__init__(f)
        self.f = f
        self.name = name
        self.v = [
            O3D_Float(f, 'x'),
            O3D_Float(f, 'y'),
            O3D_Float(f, 'z')
        ]

    def __repr__(self):
        return '%s:(x:%s, y:%s, z:%s)' % (self.name, self.v[0], self.v[1], self.v[2])


class O3D_D3DCOLORVALUE(O3DTypeBase):
    def __init__(self, f, name):
        super(O3D_D3DCOLORVALUE).__init__(f)
        self.f = f
        self.name = name
        self.v = [
            O3D_Float(f, 'r'),
            O3D_Float(f, 'g'),
            O3D_Float(f, 'b'),
            O3D_Float(f, 'a')
        ]

    def __repr__(self):
        return '%s:(r:%s, g:%s, b:%s, a:%s)' % (self.name, self.v[0], self.v[1], self.v[2], self.v[3])


class O3D_D3DMATERIAL9(O3DTypeBase):
    def __init__(self, f, name):
        super(O3D_D3DMATERIAL9).__init__(f)
        self.f = f
        self.name = name
        self.v = (
            O3D_D3DCOLORVALUE(f, 'Diffuse'),
            O3D_D3DCOLORVALUE(f, 'Ambient'),
            O3D_D3DCOLORVALUE(f, 'Specular'),
            O3D_D3DCOLORVALUE(f, 'Emissive'),
            O3D_Float(f, 'Power')
        )

    def __repr__(self):
        return '%s:(r:%s, g:%s, b:%s, a:%s)' % (self.name, self.v[0], self.v[1], self.v[2], self.v[3], self.v[4])


class O3DFile:
    def __init__(self, path):
        self.path = path
        self.load()

    def load_vectex(self, f):
        pass

    def load_face(self, f):
        pass

    def load_val(self, f, size, format):
        data = f.read(size)
        return struct.unpack(format, data)[0]

    def load_vals(self, f, size, format):
        data = f.read(size)
        return struct.unpack(format, data)

    def auto_load(self):
        f = open(self.path, 'r')
        self.file_name_len = O3D_Uchar(f, 'file_name_len')
        self.file_name = O3D_String(f, 'file_name', self.file_name_len)
        f.close()

    def load(self):
        f = open(self.path, 'r')
        self.file_name_len = self.load_val(f, 1, "B")
        self.file_name = self.load_val(f, self.file_name_len, "%ds"%self.file_name_len)
        self.nversion = self.load_val(f, 4, "I")
        self.serial_id = self.load_val(f, 4, "I")

        self.v_force1 = self.load_vals(f, 4 * 3, "fff")
        self.v_force2 = self.load_vals(f, 4 * 3, "fff")

        if self.nversion < 20:
            f.close()
            return

        if self.nversion >= 22:
            self.v_force3 = self.load_vals(f, 4 * 3, "fff")
            self.v_force4 = self.load_vals(f, 4 * 3, "fff")
        else:
            self.v_force3 = None
            self.v_force4 = None

        self.fscrlu = self.load_val(f, 4, "f")
        self.fscrlv = self.load_val(f, 4, "f")

        self.pad1 = self.load_val(f, 16, '16s')

        self.vBBMin = self.load_vals(f, 4 * 3, "fff")
        self.vBBMax = self.load_vals(f, 4 * 3, "fff")

        self.perslerp = self.load_val(f, 4, "f")
        self.nmaxframe = self.load_val(f, 4, "I")

        self.nmaxevent = self.load_val(f, 4, "I")
        if self.nmaxevent > 0:
            i = 0
            self.vevent = []
            while i < self.nmaxevent:
                v = self.load_vals(f, 4 * 3, "fff")
                self.vevent.append(v)
                i = i + 1
        else:
            self.vevent = None

        self.ntemp = self.load_val(f, 4, "I")
        if self.ntemp:
            self.loadGMobj(f)

        f.close()

    def loadGMobj(self, f):
        self.vBBMin = self.load_vals(f, 4 * 3, "fff")
        self.vBBMax = self.load_vals(f, 4 * 3, "fff")
        self.bopacity = self.load_val(f, 4, "I")
        self.bbump = self.load_val(f, 4, "I")
        self.brigid = self.load_val(f, 4, "I")
        self.pad2 = self.load_val(f, 28, "28s")
        self.nmaxvetexlist = self.load_val(f, 4, 'I')
        self.nmaxvb = self.load_val(f, 4, 'I')
        self.nmaxfacelist = self.load_val(f, 4, 'I')
        self.nmaxib = self.load_val(f, 4, 'I')
        n = 0
        self.pvertexlist = []
        while n < self.nmaxvetexlist:
            n = n + 1
            x = self.load_vals(f, 4 * 3 , "fff")
            self.pvertexlist.append(x)
        n = 0
        self.m_pVB  = []
        while n < self.nmaxvb:
            n = n + 1
            x = self.load_vals(f, 4 * 3 * 2 + 4 * 2, "ffffffff")
            self.m_pVB.append(x)

        self.pIB = self.load_vals(f, 2 * self.nmaxib, 'H' * self.nmaxib)
        self.pIIB = self.load_vals(f, 2 * self.nmaxvb, 'H' * self.nmaxvb)
        self.nPhysiqueVertex = self.load_val(f, 4 , 'I')
        if self.nPhysiqueVertex > 0:
            self.pPhysiqueVertex = self.load_vals(f, 4 * self.nmaxvetexlist, 'I'*self.nmaxvetexlist)
        else:
            self.pPhysiqueVertex = None
        
        self.dds = []

        self.bIsMaterial = self.load_val(f, 4, 'I')
        if self.bIsMaterial:
            self.m_nMaxMaterial = self.load_val(f, 4, 'I')
            if self.m_nMaxMaterial == 0:
                self.m_nMaxMaterial = 1
            n = 0
            self.m_MaterialAry = []
            while n < self.m_nMaxMaterial:
                n = n + 1
                x = self.load_vals(f, 16 * 4 + 4, 'f' * (4 * 4 + 1))
                name_len =self.load_val(f, 4, 'I')
                sz_file = self.load_val(f, name_len, '%ds' % name_len)
                self.m_MaterialAry.append((sz_file, x))
                if sz_file != '\x00':
                    if '\x00' in sz_file:
                        file = sz_file[:len(sz_file)-1]
                    print file, file.encode('hex')
                    dds = DDSFile(file)
                    self.dds.append(dds)
        else:
            self.m_MaterialAry = []
            self.m_nMaxMaterial = 0


    def __repr__(self):
        print 'file path: ', self.path
        print 'file name len: ', self.file_name_len
        # file_name must be < than 64
        print 'file name:', self.file_name, self.file_name.encode('hex')
        print "file version: %08X, %d" % (self.nversion, self.nversion)
        if self.nversion >= 20:
            print "file serial id: %08X, %d" % (self.serial_id, self.serial_id)
            print 'self.v_force1, self.v_force2', self.v_force1, self.v_force2
            print 'self.v_force3, self.v_force4', self.v_force3, self.v_force4
            print 'self.fscrlu, self.fscrlv', self.fscrlu, self.fscrlv
            print 'self.pad1', self.pad1
            print 'self.vBBMin, self.vBBMax', self.vBBMin, self.vBBMax
            print 'self.perslerp', self.perslerp
            print 'self.nmaxframe', self.nmaxframe
            print 'self.nmaxevent', self.nmaxevent
            print 'self.vevent', self.vevent
            print 'self.ntemp', self.ntemp
            if self.ntemp > 0:
                print 'vBBMin', self.vBBMin
                print 'vBBMax', self.vBBMax
                print 'bopacity', self.bopacity
                print 'bbump', self.bbump
                print 'brigid', self.brigid
                print 'pad2', self.pad2
                print 'nmaxvetexlist', self.nmaxvetexlist
                print 'nmaxvb', self.nmaxvb
                print 'nmaxfacelist', self.nmaxfacelist
                print 'nmaxib', self.nmaxib
                print 'self.pvertexlist', len(self.pvertexlist), self.pvertexlist
                print 'self.m_pVB', len(self.m_pVB), self.m_pVB
                print 'self.pIB', len(self.pIB), self.pIB
                print 'self.pIIB', len(self.pIIB), self.pIIB
                print 'self.pPhysiqueVertex', self.pPhysiqueVertex
                print 'self.bIsMaterial', self.bIsMaterial
                print 'self.m_nMaxMaterial', self.m_nMaxMaterial
                print 'self.m_MaterialAry', self.m_MaterialAry


        return ''


'''
o3ddir_root = '/Users/lijie/Desktop/V18客户端/V18客户端/Model'
for f in os.listdir(o3ddir_root):
    if f.find('.o3d') >= 0:
        o3d = O3DFile(o3ddir_root + '/' + f)
        print o3d
        print
        print
        break
'''
