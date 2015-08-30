# -*- coding: utf-8 -*-
# this module contains helpermethods
# some helpers are in used in interp.py hooks.py and native.py
from objectmodel import Objectref, Arrayref, JException

# linear lookup:
# returns a method_info obj if the method with the name m_name and
# the descriptor m_desc can be found in jcls
def find_method(jcls, m_name, m_desc):
    method = None
    for i in  range(jcls.cls.methods_count):
        name_index = jcls.cls.methods[i].name_index
        name = jcls.cls.constant_pool[name_index]
        if name== m_name:
            d_index = jcls.cls.methods[i].descriptor_index
            des = jcls.cls.constant_pool[d_index]
            if des== m_desc:
                method = jcls.cls.methods[i]
                break
    return method

# create a string by hand
# TODO: rename py_str_to_javaString
def make_String(string, loader):
        objectref = Objectref(loader.getclass("java/lang/String"), True)
        objectref.fields.set(unicode("count"), len(string), "int")
        objectref.fields.set(unicode("offset"), 0, "int")
        char_array = []
        for c in string:
            char_array.append(c)
        array = Arrayref(char_array, '\x00', loader.getclass("[C"))
        objectref.fields.set(unicode("value"), array, "array")
        return objectref

# TODO: rename javaString_to_py_str
def unpack_string(string):
    char_list = string.fields.get(unicode("value"),"array").arrayref
    # unpack char array to python-string
    str = ""
    for char in char_list:
        str += char
    return str

def throw_ArithmeticException(loader):
    ename = "java/lang/ArithmeticException"
    throw_RuntimeException(loader, ename, "/ by zero")

def throw_ArrayIndexOutOfBoundsException(loader, index):
    ename = "java/lang/ArrayIndexOutOfBoundsException"
    throw_RuntimeException(loader, ename, str(index))

def throw_NullPointerException(loader):
    ename = "java/lang/NullPointerException"
    throw_RuntimeException(loader, ename, "null")

# XXX is NOT a runntimeexception. This is just "quick and dirty"
def throw_InterruptedException(loader, method_name):
    ename = "java/lang/InterruptedException"
    throw_RuntimeException(loader, ename, method_name+" interrupted")

def throw_ClassCastException(loader, clsname1, clsname2):
    ename = "java/lang/ClassCastException"
    emsg = clsname1 +" cannot be cast to "+clsname2
    throw_RuntimeException(loader, ename, emsg)

def throw_RuntimeException(loader, ename, emsg):
    jcls = loader.getclass(ename)
    string = make_String(emsg, loader)
    objref = Objectref(jcls, True)
    objref.fields.set("detailMessage", string, "ref")
    raise JException(objref)