# -*- coding: utf-8 -*-
import new, sys, os, types, py
#import classfile, javaclasses #FIXME: import only what is needed.
from objectmodel import TypedMap, JObject, JClass, JArrayClass, JPrimitiveClass

from rpython.tool.sourcetools import func_with_new_name

class AbstractClassLoader(object):
    # set the search path and add the standard classes
    # e.g Object, String.... to the map
    def __init__(self, path):
        self.path = path
        self.path.append('/usr/local/classpath/share/classpath/')
        self.path.append("./examples/") # only for testing the vm
        # Cache for loaded classes
        self.classes = {}
        # There is only one classinstanze per class
        # string->java.lang.Class
        # This dict ONLY contains Instances of java.lang.Class
        self.class_cache = {} 
        for name, cls in javaclasses.CLASSES.items():
            initialize_prebuilt(cls)
            self.classes[name] = cls

    # If there is not already a pycls with name <name> than
    # search for the classfile with the name <name> in
    # every known <path> and parse the file if found.
    # After that the class is wrapped to a pythonclass
    def getclass(self, name, enclosingMethod_info=None):
        try:
            return self.classes[name]
        except KeyError:
            #print "classloader.getclass name:",name
            if name.startswith("["):
                jcls = JArrayClass(name, self.getclass("java/lang/Object"), cls=None)
                self.classes[name] = jcls
                return jcls
            for dir in self.path:
                try:
                    f = open(os.path.join(dir, '%s.class' % (unicode(name),)), 'rb')
                except IOError:
                    continue
                cls = classfile.ClassFile(f)
                f.close()
                classname, supercls = self.parse_parameter(cls)
                jcls = JClass(classname, supercls, cls)
                if "$" in name: # inner class
                    jcls.enclosingMethod_info = enclosingMethod_info
                self.classes[name] = jcls
                self.init_class(jcls, cls)
                return jcls
            #TODO: throw ClassNotFoundException
            raise IOError("Java class file not found: %r" % (name,))

    def getPrimClass(self, char):
        jscls = self.getclass("java/lang/Object")
        if   char == 'B':
            jcls = JPrimitiveClass("byte", None, jscls.cls)
        elif char == 'C':
            jcls = JPrimitiveClass("char", None, jscls.cls)
        elif char == 'D':
            jcls = JPrimitiveClass("double", None, jscls.cls)
        elif char == 'F':
            jcls = JPrimitiveClass("float", None, jscls.cls)
        elif char == 'I':
            jcls = JPrimitiveClass("int", None, jscls.cls)
        elif char == 'J':
            jcls = JPrimitiveClass("long", None, jscls.cls)
        elif char == 'S':
            jcls = JPrimitiveClass("short", None, jscls.cls)
        elif char == 'Z':
            jcls = JPrimitiveClass("boolean", None, jscls.cls)
        elif char == 'V':
            jcls = JPrimitiveClass("void", None, jscls.cls)#XXX
        else:
            raise Exception("Unknown Type for primitive Class")
        return jcls

    #def getPrimArrayClass(self, char):
    #    assert char=='Z' or char=='S' or char=='B' or char=='I' or char=='J' or char=='F' or char=='D' or char=='C'
    #    jscls = self.getclass("java/lang/Object")
    #    return JArrayClass(char, jscls, cls=None)

    def parse_parameter(self, cls):
        classref = cls.constant_pool[cls.this_class]
        classname = str(cls.constant_pool[classref.name_index])
        superref = cls.constant_pool[cls.super_class]
        if superref == None:
            assert classname == "java/lang/Object"
            supercls = None
        else:
            supername = cls.constant_pool[superref.name_index]
            supercls = self.getclass(supername) # parsing of superclass
        return classname, supercls

    # implemented in a subclass
    def init_static(self, pycls, method):
        pass

    def init_class(self, pycls, cls):
        self.add_fields(pycls, cls, add_static=True)
        # add supercls fields
        jcls = pycls.supercls
        while not jcls == None:
            self.add_fields(pycls, jcls.cls, add_static=False)
            #self.take_static_init_from_super(pycls, jcls)
            jcls = jcls.supercls

        for method in cls.methods:
            const = cls.constant_pool
            mname = cls.constant_pool[method.name_index]
            descr = descriptor(const[method.descriptor_index])
            name = encode_name(mname, descr)
            assert name not in pycls.methods, (
                "duplicate name %r in %r" % (name, pycls))
            pycls.methods[unicode(name)] = method
        if unicode('<clinit>_None') in pycls.methods:
            #print "init of:", pycls.__name__
            self.init_static(pycls.cls, pycls.methods[unicode('<clinit>_None')])
            #print "++++++++++", pycls.__name__ , "+++++++++"
            #pycls.static_fields.print_map()
            #print "++++++++++", pycls.__name__ , "+++++++++"

    def add_fields(self, pycls, cls, add_static):
        for field in cls.fields:
            name, defaultitem, descr = self.parse_field(cls, field)
            if not (field.access_flags& 0x0008) == 0:
                #assert name not in pycls.static_fields, (
                #    "duplicate name %r in %r" % (name, pycls))
                if add_static:
                    pycls.static_fields.set(unicode(name), defaultitem, descr)
                #print "Classloader: added (static) ",name
            else:
                #assert name not in pycls.fields, (
                #    "duplicate name %r in %r" % (name, pycls))
                pycls.fields.set(unicode(name), defaultitem, descr)
                #print pycls.__name__," Classloader: added ",name

    # the static fields of the super class have been init.
    # the superclass must know that too
    #def take_static_init_from_super(self, pycls, super_cls):
        #print pycls.__name__,super_cls.__name__
    #    for sfield in super_cls.cls.fields:
    #        if not (sfield.access_flags& 0x0008) == 0: #static field
    #            name, defaultitem, descr = self.parse_field(super_cls.cls, sfield)
    #            value = super_cls.static_fields.get(unicode(name), descr)
    #            pycls.static_fields.set(unicode(name), value, descr)

    def parse_field(self, cls, field):
        const = cls.constant_pool
        name = const[field.name_index]
        descr = descriptor(const[field.descriptor_index])
        #name = encode_name(name, descr) - not encoded for now
        defaultitem = DEFAULT_BY_DESCR.get(descr, None) ### xxx maybe to interp ?
        return name, defaultitem, descr

def checkname(name):
    assert not name.startswith('__') or name in REMAPPED_NAMES, (
        "Java name confusing for Python: %r" % (name,))
    return REMAP_NAMES.get(name, escape_dollar(name))

def escape_dollar(name):
    if '$' in name:
        name = '__' + name.replace('$', '__')
    return name

REMAP_NAMES = {'<init>': '__init__',
               }
REMAPPED_NAMES = dict.fromkeys(REMAP_NAMES.values())

#def native_java_method(*args):
#    raise NotImplementedError("native Java method")
#
#def abstract_method(*args):
#    raise NotImplementedError("abstract method")


def parse_descriptor(s, i):
    if   s[i] == 'B': return 'byte',     i+1
    elif s[i] == 'C': return 'char',     i+1
    elif s[i] == 'D': return 'double',   i+1
    elif s[i] == 'F': return 'float',    i+1
    elif s[i] == 'I': return 'int',      i+1
    elif s[i] == 'J': return 'long',     i+1
    elif s[i] == 'S': return 'short',    i+1
    elif s[i] == 'Z': return 'boolean',  i+1
    elif s[i] == 'V': return None,       i+1
    elif s[i] == 'L':           # instance
        j = s.find(';', i+1)
        return 'reference:' + s[i+1:j],  j+1
    elif s[i] == '[':
        res, i = parse_descriptor(s, i+1)
        return 'array:' + res, i
    elif s[i] == '(':
        res = []
        i += 1
        while s[i] != ')':
            arg, i = parse_descriptor(s, i)
            res.append(arg)
        arg, i = parse_descriptor(s, i+1)
        res.append(arg)
        return res, i
    else:
        raise AssertionError(repr(s[i]))

def descriptor(s):
    res, i = parse_descriptor(s, 0)
    assert i == len(s)
    return res


def mangle_descriptor(s):
    mangled = "_%s" % ( "___".join(unicode(x).replace(":", "_").replace("/", "__") for x in s),)
    return mangled


def encode_name(name, descr):
    mangled = u"%s%s" % (checkname(name), escape_dollar(mangle_descriptor(descr)))
    encoded = mangled.encode("utf-7").replace("+", "_").replace("-", "_")
    #print "encode_name(%r, %r) resulted in %r" % (name, descr, encoded)
    return encoded


DEFAULT_BY_DESCR    = {"boolean": False,
                       "char":    '\x00',
                       "float":   0.0,
                       "double":  0.0,
                       "byte":    0,
                       "short":   0,
                       "int":     0,
                       "long":    0,
                       }


def initialize_prebuilt(cls):
    if cls is str:
        return
    if '_JREADY_' in cls.__dict__:
        return
    for key, value in cls.__dict__.items():
        wrap_result = None
        if isinstance(value, staticmethod):
            value = value.__get__(42)
            wrap_result = staticmethod
        if isinstance(value, types.FunctionType):
            if hasattr(value, 'jdescr'): # XXX not Rpython
                jdescr = value.jdescr
                if isinstance(jdescr, str):
                    jdescr = (jdescr,)
                for s in jdescr:
                    real_name = encode_name(key, descriptor(s))
                    #print "class and real name:",cls, real_name
                    assert real_name not in cls.__dict__
                    newfunction = func_with_new_name(value, real_name)
                    if wrap_result:
                        newfunction = wrap_result(newfunction)
                    setattr(cls, real_name, newfunction)
    cls._JREADY_ = True
