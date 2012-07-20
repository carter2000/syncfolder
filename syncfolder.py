#-*- coding: utf-8 -*-

import filecmp
import os
import shutil
import sys

class SyncData:
    OP_ASK = 0
    OP_YA = 1
    OP_NA = 2
    def __init__(self):
        self.deleted = []
        self.untracked = []
        self.delop = self.OP_ASK
        self.syncop = self.OP_ASK
        self.lastesttime = 0

g_syncdata = SyncData()

TIPS = "('y', 'n', 'ya', 'na')"

def sync(srcpath, dstpath):
    if not os.path.exists(srcpath) or not os.path.exists(dstpath):
        return
    if os.path.isdir(srcpath) != os.path.isdir(dstpath):
        return
    srcpath = os.path.abspath(srcpath)
    dstpath = os.path.abspath(dstpath)

    if os.path.isdir(srcpath):
        syndir(srcpath, dstpath)
    else:
        syncfile(srcpath, dstpath)

    for (srcdir, dstdir, namelist) in g_syncdata.untracked:
        for name in namelist:
            syncuntracked(srcdir, dstdir, name)

    for (srcdir, dstdir, namelist) in g_syncdata.deleted:
        for name in namelist:
            syncdeleted(srcdir, dstdir, name)

def syndir(srcpath, dstpath):
    (srcdirs, srcfiles) = splitfiledir(srcpath)
    (dstdirs, dstfiles) = splitfiledir(dstpath)
    syncfiles(srcpath, dstpath, srcfiles, dstfiles)
    syndirs(srcpath, dstpath, srcdirs, dstdirs)

def syndirs(srcpath, dstpath, srcdirs, dstdirs):
    tracked = intersection(srcdirs, dstdirs)
    untracked = difference(srcdirs, dstdirs)
    deleted = difference(dstdirs, srcdirs)
    for name in tracked:
        syndir(os.path.join(srcpath, name), os.path.join(dstpath, name))
    g_syncdata.untracked.append((srcpath, dstpath, untracked))
    g_syncdata.deleted.append((srcpath, dstpath, deleted))

def syncfile(srcfile, dstfile):
    print("updated: " + dstfile)
    shutil.copyfile(srcfile, dstfile)

def syncfiles(srcpath, dstpath, srcfiles, dstfiles):
    tracked = intersection(srcfiles, dstfiles)
    for filename in tracked:
        dstfile = os.path.join(dstpath, filename)
        dstatime = os.path.getatime(dstfile)
        dstmtime = os.path.getmtime(dstfile)
        dstctime = os.path.getctime(dstfile)
        dsttime = max(dstatime, dstmtime, dstctime)
        if dsttime > g_syncdata.lastesttime:
            g_syncdata.lastesttime = dsttime
        srcfile = os.path.join(srcpath, filename)
        if not filecmp.cmp(srcfile, dstfile):
            syncfile(srcfile, dstfile)
    deleted = difference(dstfiles, srcfiles)
    untracked = difference(srcfiles, dstfiles)
    g_syncdata.deleted.append((srcpath, dstpath, deleted))
    g_syncdata.untracked.append((srcpath, dstpath, untracked))

def syncuntracked(srcpath, dstpath, name):
    srcfull = os.path.join(srcpath, name)
    dstfull = os.path.join(dstpath, name)
    if os.path.isdir(srcfull):
        syncuntrackeddir(srcfull, dstfull)
    else:
        syncuntrackedfile(srcfull, dstfull)

def syncuntrackeddir(srcdir, dstdir):
    for name in os.listdir(srcdir):
        syncuntracked(srcdir, dstdir, name)

def syncuntrackedfile(srcfile, dstfile):
    if g_syncdata.syncop == SyncData.OP_NA:
        return
    srcatime = os.path.getatime(srcfile)
    srcmtime = os.path.getmtime(srcfile)
    srcctime = os.path.getctime(srcfile)
    srctime = max(srcatime, srcmtime, srcctime)
    if srctime <= g_syncdata.lastesttime:
        return
    op = "y"
    if g_syncdata.syncop == SyncData.OP_ASK:
        op = input("sync: " + srcfile + TIPS + "?").lower()
        if op == "ya":
            g_syncdata.syncop = SyncData.OP_YA
        elif op == "na":
            g_syncdata.syncop = SyncData.OP_NA
    if op == "y" or op == "ya":
        fixupdir(dstfile)
        syncfile(srcfile, dstfile)

def syncdeleted(srcpath, dstpath, name):
    srcfull = os.path.join(srcpath, name)
    dstfull = os.path.join(dstpath, name)
    if os.path.isdir(dstfull):
        syncdeleteddir(srcfull, dstfull)
    else:
        syncdeletedfile(srcfull, dstfull)

def syncdeleteddir(srcdir, dstdir):
    for name in os.listdir(dstdir):
        syncdeleted(srcdir, dstdir, name)
    if os.listdir(dstdir) == []:
        print("delete dir: " + dstdir)
        os.removedirs(dstdir)

def syncdeletedfile(srcfile, dstfile):
    if g_syncdata.delop == SyncData.OP_NA:
        return
    op = "y"
    if g_syncdata.delop == SyncData.OP_ASK:
        op = input("deleted: " + dstfile + TIPS + "?").lower()
        if op == "ya":
            g_syncdata.delop = SyncData.OP_YA
        elif op == "na":
            g_syncdata.delop = SyncData.OP_NA
    if op == "y" or op == "ya":
        print("delete file: " + dstfile)
        os.remove(dstfile)

def intersection(list1, list2):
    return filter(lambda x : x in list2, list1)

def difference(list1, list2):
    return filter(lambda x : x not in list2, list1)

def splitfiledir(srcdir):
    dirs = []
    files = []
    if os.path.exists(srcdir):
        for child in os.listdir(srcdir):
            if os.path.isdir(os.path.join(srcdir, child)):
                dirs.append(child)
            else:
                files.append(child)
    return (dirs, files)

def fixupdir(path):
    if os.path.exists(path):
        return
    (parent, _) = os.path.split(path)
    if os.path.exists(parent) and os.path.isdir(parent):
        return
    fixupdir(parent)
    print("create dir: " + parent)
    os.makedirs(parent)

if __name__ == "__main__":
    sync(sys.argv[1], sys.argv[2])
