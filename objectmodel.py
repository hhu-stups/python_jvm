# -*- coding: utf-8 -*-
# The classes in this module are the interpreter/JVM intern
# representation of instances and Stack
# This module also contains helper classes like TypeMap

#from rpython.rlib.rarithmetic import r_singlefloat, r_longlong

# when this is created in "new"
# a Object must not be created directly.
# Every ObjectRef contains a copy of the
# instancevariables of its class
class Objectref(object):
    def __init__(self, jcls, init = False):
        self.jcls = jcls
        self.is_null = not init
        self.fields = TypedMap()
        self.init_fields(self.jcls)
        self.owner_thread = None # this thread holds the lock on this obj
        self.lock_count = 0
        self.wait_set = [] #waiting to be notifyed

    # on init: copy every field defined in the class
    # to his own typed map.
    def init_fields(self, cls):
        self.fields.set_int_map(cls.fields.int_map.copy())
        self.fields.set_long_map(cls.fields.long_map.copy())
        self.fields.set_float_map(cls.fields.float_map.copy())
        self.fields.set_double_map(cls.fields.double_map.copy())
        self.fields.set_ref_map(cls.fields.ref_map.copy())


# special case:
# It is the responsibility of the JVM to determine
# the classloader of a Class (hooks.py: See GNU CP VM.getClassloader)
# And it is also the responsibility of the JVM to determine
# the Name/Type of a Instance of the Class class.
# may be created by vmobject_getClass_helper
class Classref(Objectref):
    def __init__(self, jcls, init = False, class_type = None, classLoader = None):
        Objectref.__init__(self, jcls, init)
        self.class_type = class_type
        self.classLoader = classLoader # null(None) if Bootstrap


class ClassLoaderref(Objectref):
    def __init__(self, jcls, init = False, class_loader = None):
        Objectref.__init__(self, jcls, init)
        self.class_loader = class_loader

# Array ref Wrapper
# TODO: change names for readability: e.g. aref
# TODO: implement Clonable and Serializable
class Arrayref(Objectref):
    def __init__(self, aref, defaultitem, jacls):
        assert isinstance(jacls, JClass)
        Objectref.__init__(self, jacls, True)
        self.arrayref = aref
        assert isinstance(aref, list)#elements or Arrayref
        self.defaultitem = defaultitem
        # init of the Arrayref:
        # e.g for jni newObjectArray
        # e.g a String[] array with all elem. set to "" insted of null
        if isinstance(self.defaultitem, Objectref):
            for i in range(len(self.arrayref)):
                self.arrayref[i] = self.defaultitem

# this Stack is typed for later RPython use.
class Stack(object):
    def __init__(self):
        self.stackhistory = []
        self.astack = []
        self.dstack = []
        self.fstack = []
        self.istack = []
        self.lstack = []
        self.i = 0
        #self.cstack = []

    def print_stack(self):
        print "a:",self.astack
        print "d:",self.dstack
        print "f:",self.fstack
        print "i:",self.istack
        print "l:",self.lstack
        #print "c:",self.cstack
        print "history:", self.stackhistory

    def clone(self):
        clone = Stack()
        self.copy_list(clone.astack, self.astack)
        self.copy_list(clone.dstack, self.dstack)
        self.copy_list(clone.fstack, self.fstack)
        self.copy_list(clone.istack, self.istack)
        self.copy_list(clone.lstack, self.lstack)
        #self.copy_list(clone.cstack, self.cstack)
        self.copy_list(clone.stackhistory, self.stackhistory)
        return clone

    def copy_list(self, copy, orig):
        for i in orig:
            copy.append(i)

    def push(self, value):
        if isinstance(value, int):
            self.stackhistory.append("int")
            self.istack.append(value)
        elif isinstance(value, r_singlefloat):
            self.stackhistory.append("float")
            self.fstack.append(value)
        elif isinstance(value, r_longlong):
            self.stackhistory.append("long")
            self.lstack.append(value)
        elif isinstance(value, float): # python float is c-double ;)
            self.stackhistory.append("double")
            self.dstack.append(value)
        elif isinstance(value, str) and len(value)==1:
            self.stackhistory.append("char")
            value = ord(value)
            self.istack.append(value)
        else:
            if value == "./":
                print self.i
                self.i = self.i+1
                print value
            self.stackhistory.append("ref")
            self.astack.append(value)
            #if isinstance(value, unicode):
            #    print "VAL:",value
            #    raise Exception("AAAA!!")
            #print self.astack
        #print "after PUSH:",self
        #self.print_stack()

    def pop(self):
        #print "before POP",self
        #self.print_stack()
        last = self.stackhistory.pop()
        if last == "int":
            assert isinstance(self.istack[-1],int)
            return self.istack.pop()
        elif last == "float":
            assert isinstance(self.fstack[-1], r_singlefloat)
            return self.fstack.pop()
        elif last == "ref":
            return self.astack.pop()
        elif last == "char":
            #assert  isinstance(self.cstack[-1], str) and len(self.cstack[-1])==1
            return self.istack.pop()
        elif last == "long":
            return self.lstack.pop()
        elif last == "double":
            assert isinstance(self.dstack[-1],float)
            return self.dstack.pop()
        else:
            raise Exception("illegal stack operation")

# this map is typed for later RPython use.
# It is used in every ObjectRef object
class TypedMap(object):
    def __init__(self):
       # self.char_map = {}
        self.int_map = {}
        self.float_map = {}
        self.double_map = {}
        self.long_map = {}
        self.ref_map = {}

    def print_map(self):
        print "i:", self.int_map
        print "f:", self.float_map
        print "d:", self.double_map
        print "j:", self.long_map
        print "l:", self.ref_map
        #print "c:", self.char_map

    def has_key(self, name, type):
        try:
            if type == "int":
                self.int_map[name]
                return True
            elif type == "boolean":
                self.int_map[name]
                return True
            elif type == "byte":
                self.int_map[name]
                return True
            elif type=="short":
                self.int_map[name]
                return True
            elif type == "char":
                self.int_map[name]
                return True
            elif type == "float":
                self.float_map[name]
                return True
            elif type == "double":
                self.double_map[name]
                return True
            elif type == "long":
                self.long_map[name]
                return True
            elif type.startswith("ref") or type.startswith("array"):
                self.ref_map[name]
                return True
            else:
                raise Exception("unknown type(%r)"%(type))
        except(KeyError):
            return False

    #def set_char_map(self, map):
    #    self.char_map = map

    def set_int_map(self, map):
        self.int_map = map

    def set_ref_map(self, map):
        self.ref_map = map

    def set_float_map(self, map):
        self.float_map = map

    def set_double_map(self, map):
        self.double_map = map

    def set_long_map(self, map):
        self.long_map = map

    def set(self, key, value, type):
        if type == "int" or type == "boolean" or type == "byte" or type=="short":
            self.int_map[key] = value
        elif type == "char":
            #if isinstance(value, int):
            #    value = chr(value)
            #self.char_map[key] = value
            if isinstance(value, str):
                value = ord(value)
            self.int_map[key] = value
        elif type.startswith("ref") or type.startswith("array"):
            self.ref_map[key] = value
        elif type == "float":
            self.float_map[key] = r_singlefloat(value)
        elif type == "double":
            self.double_map[key] = value
        elif type == "long":
            self.long_map[key] = r_longlong(value)
        else:
            raise Exception("unknown type(%r) or wrong key(%r)"%(type,key))

    def get(self, key, type):
        #self.print_map()
        if type == "int" or type == "boolean" or type == "byte" or type=="short":
            assert isinstance(self.int_map[key],int)
            return self.int_map[key]
        elif type == "char":
            #return self.char_map[key]
            return self.int_map[key]
        elif type.startswith("ref") or type.startswith("array"):
            # there are still sp. cases like JInteger
            #assert isinstance(self.ref_map[key], Objectref) or  isinstance(self.ref_map[key], Arrayref) or self.ref_map[key]==None
            return self.ref_map[key]
        elif type == "float":
            assert isinstance(self.float_map[key], r_singlefloat)
            return self.float_map[key]
        elif type == "double":
            assert isinstance(self.double_map[key], float)
            return self.double_map[key]
        elif type == "long":
            assert isinstance(self.long_map[key], r_longlong)
            return self.long_map[key]
        raise Exception("unknown type(%r) or wrong key(%r)"%(type,key))

class JException(Exception):
    def __init__(self, objref):
        self.objref = objref

class JObject(object):
    __slots__ = []
    fields = {}
    static_fields = {}
    def __init__(self, stack=None):
        pass
    __init__.jdescr = '()V'

    def getClass(self, args):
        return self.jcls
    getClass.jdescr = '()Ljava/lang/Class;'

# FIXME: Lookup uses that JObject is not a JClass
# TODO: move to objmodel
# This could also represent an Interface
class JClass(object):
    def __init__(self, clsname, scls, cls):
        self.__name__ = clsname
        self.supercls = scls # eg. <class 'javaclasses.JObject'>
        self.methods = {} # maps name -> methodinfo
        self.fields = TypedMap()
        self.static_fields = TypedMap()
        self.cls = cls # classfile.ClassFile
        if not isinstance(self, JArrayClass):
            self.is_interface = not not(cls.access_flags & 0x0200)
            self.is_public = not not(cls.access_flags & 0x0001)
            self.is_final = not not(cls.access_flags & 0x0002)
            self.is_super = not not(cls.access_flags & 0x0020)
            self.is_abstract = not not(cls.access_flags & 0x0400)

# special case: ;-)
# This Ref represent int.class oder Boolean.TYPE ....ect....
class JPrimitiveClass(JClass):
    def __init__(self, clsname, scls, cls):
        JClass.__init__(self, clsname, scls, cls)

class JArrayClass(JClass):
    def __init__(self, clsname, scls, cls):
        JClass.__init__(self, clsname, scls, cls)