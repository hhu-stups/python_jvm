# -*- coding: utf-8 -*-
import math # for math hooks
import time # for currentTimeMillis
import thread # # for start Threads
#import classfile # for parsing of inner classes eg in getDeclaredClasses
#import java_threading

from java_threading import vmdata_VMThread
from ctypes import * # loading extern libs XXX maybe not RPython
from classloader import descriptor
from objectmodel import Stack, Objectref, Classref, ClassLoaderref, Arrayref, JPrimitiveClass, JArrayClass, JException
from helper import make_String, unpack_string, find_method
from helper import throw_NullPointerException, throw_ArithmeticException, throw_ArrayIndexOutOfBoundsException, throw_ClassCastException, throw_InterruptedException



# Hook Methods:

def invoke_setProperty(loader, acls, method, descr, objref, str1, str2):
    args = Stack()
    key = make_String(str1, loader)
    value = make_String(str2, loader)
    args.push(value)
    args.push(key)
    args.push(objref)
    loader.invoke_method(acls, method, descr, args)

def VMClass_isInterface(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    assert isinstance(classref, Classref)
    return check_interface(classref)

def VMClass_getName(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    assert isinstance(classref, Classref)
    string = classref.class_type.__name__.replace("/",".")
    return make_String(string, loader)

def VMClass_getSuperclass(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    assert isinstance(classref, Classref)
    name = classref.class_type.__name__
    if name == "java/lang/Object":
        return None
    elif check_primitive(name):
        return None
    elif check_interface(classref):
        return None
    return vmobject_getClass_helper(classref.class_type.supercls, loader)
    #return Classref(loader.getclass("java/lang/Class"), True, classref.class_type.supercls, loader)

def VMClass_getInterfaces(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    assert isinstance(classref, Classref)
    lst = []
    cls = classref.class_type.cls
    if check_primitive(classref.class_type.__name__):
        return Arrayref([], None, loader.getclass("[Ljava/lang/Class;"))
    for i in range(cls.interfaces_count):
        cls_info = cls.constant_pool[cls.interfaces[i]]
        name = cls.constant_pool[cls_info.name_index]
        jcls = loader.getclass(name)
        #iface =Classref(loader.getclass("java/lang/Class"),False,jcls,loader)
        iface = vmobject_getClass_helper(jcls, loader)
        lst.append(iface)
    cls_array = Arrayref(lst, None, loader.getclass("[Ljava/lang/Class;"))
    return cls_array


def VMClass_getDeclaredClasses(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    boolean = locals.get(1, "boolean")
    assert isinstance(classref, Classref)
    lst = []
    cls = classref.class_type.cls
    const = cls.constant_pool
    # search for inner classes
    for i in range(cls.attributes_count):
        name_index = cls.attributes[i].attribute_name_index
        if const[name_index] == "InnerClasses":
            attr = cls.getattr(cls, 'InnerClasses', classfile.InnerClasses_attribute)
            assert isinstance(attr, classfile.InnerClasses_attribute)
            for j in range(attr.number_of_classes):
                inner = const[attr.classes[j].inner_class_info_index]
                inner_name = const[inner.name_index]
                #outer = const[attr.classes[j].outer_class_info_index]
                #outer_name = const[outer.name_index]
                #const[attr.classes[j].inner_name_index]
                jcls = loader.getclass(inner_name)
                #icls = Classref(loader.getclass("java/lang/Class"),False,jcls,loader)
                icls = vmobject_getClass_helper(jcls, loader)
                if boolean: 
                    if attr.classes[j].inner_class_access_flags&0x001 != 0x001: # test: is public?
                        lst.append(icls)
                else:
                    lst.append(icls)
    cls_array = Arrayref(lst,None, loader.getclass("[Ljava/lang/Class;"))
    return cls_array

def VMClass_getDeclaredFields(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    boolean = locals.get(1, "boolean") #TODO: if true: skip non public fields
    assert isinstance(classref, Classref)
    field_cls = loader.getclass("java/lang/reflect/Field")
    vmfield_cls = loader.getclass("java/lang/reflect/VMField")
    lst = []
    cls = classref.class_type.cls
    const = cls.constant_pool
    for i in range(cls.fields_count):
        #for j in range(cls.fields[i].attributes_count):
        #    attr = cls.fields[i].attributes[j]
        
        # filter public fields
        if boolean and cls.fields[i].access_flags & 0x1 != 0x01:
            continue

        # build the filed class 
        objref = Objectref(field_cls, True)
        vmfield_objref = Objectref(vmfield_cls, True)
        string = make_String(const[cls.fields[i].name_index], loader)
        vmfield_objref.fields.set(u'name', string,"ref")
        vmfield_objref.fields.set(u'clazz', classref, "ref")
        # XXX extra attr
        vmfield_objref.fields.set(u'id', id(vmfield_objref), "long")
        objref.fields.set(u'f', vmfield_objref, "ref")
        
        lst.append(objref)
    field_array = Arrayref(lst,None, loader.getclass("[Ljava/lang/reflect/Field;"))
    return field_array

def VMClass_getDeclareMethods(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    boolean = locals.get(1, "boolean") #TODO: if true: skip non public fields
    assert isinstance(classref, Classref)
    method_cls = loader.getclass("java/lang/reflect/Method")
    vmmethod_cls = loader.getclass("java/lang/reflect/VMMethod")
    lst = []
    cls = classref.class_type.cls
    const = cls.constant_pool
    for i in range(cls.methods_count):
        #for j in range(cls.methods[i].attributes_count):
        #    attr = cls.methods[i].attributes[j]

        # build the method class 
        objref = Objectref(method_cls, True)
        vmmethod_objref = Objectref(vmmethod_cls, True)
        name = const[cls.methods[i].name_index]
        if name == "<init>": #FIXME: maybe only the std. constructor
            continue
        string = make_String(name, loader)
        
        vmmethod_objref.fields.set(u'name', string,"ref")
        vmmethod_objref.fields.set(u'clazz', classref, "ref")
        # XXX: extra attr.
        method_info = cls.methods[i]
        vmmethod_objref.fields.set(u'method_info', method_info, "ref")
        descriptor  = const[cls.methods[i].descriptor_index]
        vmmethod_objref.fields.set(u'descriptor', descriptor, "ref")
        exc_lst = []
        for attr in cls.methods[i].attributes:
            if const[attr.attribute_name_index] == "Exceptions":
                attr = cls.getattr(cls.methods[i], 'Exceptions', classfile.Exceptions_attribute)
                for k in range(attr.number_of_exceptions):
                    excep_index = attr.exceptions_index_table[k]
                    cls_info = const[excep_index]
                    excep_name = const[cls_info.name_index]
                    exc_lst.append(excep_name)
        vmmethod_objref.fields.set(u'exceptions', exc_lst, "ref")
        
        objref.fields.set(u'm', vmmethod_objref, "ref")
        lst.append(objref)
    method_array = Arrayref(lst,None, loader.getclass("[Ljava/lang/reflect/Method;"))
    return method_array

def VMClass_getDeclaredConstructors(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    boolean = locals.get(1, "boolean") #TODO: if true: skip non public fields
    assert isinstance(classref, Classref)
    constr_jcls = loader.getclass("java/lang/reflect/Constructor")
    vmconstr_jcls = loader.getclass("java/lang/reflect/VMConstructor")
    lst = []
    cls = classref.class_type.cls
    const = cls.constant_pool
    for i in range(cls.methods_count):

        # build the method class 
        objref = Objectref(constr_jcls, True)
        vmconstr_objref = Objectref(vmconstr_jcls, True)
        name = const[cls.methods[i].name_index]
        if name != "<init>": #FIXME: maybe only the std. constructor
            continue
        string = make_String(name, loader)
        
        vmconstr_objref.fields.set(u'name', string,"ref")
        vmconstr_objref.fields.set(u'clazz', classref, "ref")

        # XXX: extra attr.
        method_info = cls.methods[i]
        vmconstr_objref.fields.set(u'method_info', method_info, "ref")
        exc_lst = []
        for attr in cls.methods[i].attributes:
            if const[attr.attribute_name_index] == "Exceptions":
                attr = cls.getattr(cls.methods[i], 'Exceptions', classfile.Exceptions_attribute)
                for k in range(attr.number_of_exceptions):
                    excep_index = attr.exceptions_index_table[k]
                    cls_info = const[excep_index]
                    excep_name = const[cls_info.name_index]
                    exc_lst.append(excep_name)
        vmconstr_objref.fields.set(u'exceptions', exc_lst, "ref")
        objref.fields.set(u'cons', vmconstr_objref, "ref")
        lst.append(objref)

    constr_cls_array = Arrayref(lst, None, loader.getclass("[Ljava/lang/reflect/Constructor;"))
    return constr_cls_array


def VMClass_getClassLoader(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    # null(None) if Bootsstrap: set by vmobject_getClass_helper
    return classref.classLoader

# BUG: if clsLoader is not the Bootstrap clsLoader
def VMClass_forName(locals, loader, cls, method):
    string = unpack_string(locals.get(0, "ref"))
    # classname sperated by poins insted of slashs!
    string = string.replace(".","/")
    boolean = locals.get(1, "boolean")
    clsLoader = locals.get(2, "ref")
    jcls = loader.getclass(string) # FIXME: use clsLoader
    #return Classref(loader.getclass("java/lang/Class"), boolean, jcls, clsLoader)
    return vmobject_getClass_helper(jcls, clsLoader)


def VMClass_isArray(locals, loader, cls, method):
    clsref = locals.get(0, "ref")
    return isinstance(clsref.class_type, JArrayClass)

def VMClass_initialize(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClass_loadArrayClass(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClass_throwException(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClass_isInstance(locals, loader, cls, method):
    classref = locals.get(0, "ref")
    objectref = locals.get(1, "ref")
    assert isinstance(classref, Classref)
    assert isinstance(objectref, Objectref)
    # lookup:
    name = classref.class_type.__name__
    cls = objectref.jcls
    while True: #do-Wihle loop
        if cls.__name__ == name:
            return True
        elif cls.__name__ == "java/lang/Object":
            if name == "java/lang/Object":
                return True
            else:
                return False
        cls = cls.supercls

def VMClass_isAssignableForm(locals, loader, cls, method):
    clsref = locals.get(0, "ref") # this
    clsref2 = locals.get(1, "ref")
    if clsref2==None:
        throw_NullPointerException(loader)
    cls = clsref2.class_type
    # lookup
    while True: # Do -While loop
        if clsref.class_type.__name__ == cls.__name__:
            return True
        if cls.__name__ == "java/lang/Object":
            return False
        cls = cls.supercls


def VMClass_isPrimitive(locals, loader, cls, method):
    cls = locals.get(0, "ref")
    name = cls.class_type.__name__
    return check_primitive(name)

def VMClass_getComponentType(locals, loader, cls, method):
    clsref = locals.get(0, "ref")
    if isinstance(clsref.class_type, JArrayClass):
        name = clsref.class_type.__name__
        index = 0
        for c in name:  # skip '[*'
            if not c == '[':
                break
            index = index +1
        if name[index] == 'L':
            jcls = loader.getclass(name[index+1:-1]) # skip 'L' and ';'
        else: #primitive class
            jcls = loader.getPrimClass(name[index:])
        return vmobject_getClass_helper(jcls, loader)
    else: # no Array-class
        return None

def VMClass_getModifiers(locals, loader, cls, method):
    clsref = locals.get(0, "ref")
    bool_skip_public = locals.get(1, "int")#TODO
    result = clsref.class_type.cls.access_flags
    return result

def VMClass_getDeclaringClass(locals, loader, cls, method):
    clsref = locals.get(0, "ref")
    name = ""
    for c in clsref.class_type.__name__:
        if c=="$":
            break
        name = name + c
    jcls = loader.getclass(name) 
    return vmobject_getClass_helper(jcls, loader)

def VMClass_isSynthetic(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClass_isAnnotation(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClass_isEnum(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# Use default impl. for now
#def VMClass_getSimpleName(locals, loader, cls, method):
#    raise NotImplemented("Hook Method")

def VMClass_getCanonicalName(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClass_getEnclosingClass(locals, loader, cls, method):
    clsref = locals.get(0, "ref")
    name = clsref.class_type.__name__
    name2 = ""
    for c in name:
        if c== '$':
            break
        name2 = name2 + c
    if not name == name2:
        jcls = loader.getclass(name2) 
        return vmobject_getClass_helper(jcls, loader)
    else:
        return None


def VMClass_getEnclosingConstructor(locals, loader, cls, method):
    clsref = locals.get(0, "ref") # maybe an inner class
    name = clsref.class_type.__name__
    name2 = ""
    index = 0
    for c in name:
        index = index +1
        if c== '$':
            break
        name2 = name2 + c
    if not name == name2:
        if not name[index].isdigit():
            return None# local class
        jcls = loader.getclass(name2) #name2: name of outer class
        outer_clsref = vmobject_getClass_helper(jcls, loader)
        constr_cls = loader.getclass("java/lang/reflect/Constructor")
        vmconstr_cls = loader.getclass("java/lang/reflect/VMConstructor")
        objref = Objectref(constr_cls, True)
        vmconstr_objref = Objectref(vmconstr_cls, True)
        method_info = clsref.class_type.enclosingMethod_info
        const = outer_clsref.class_type.cls.constant_pool
        name = const[method_info.name_index] 
        if name!="<init>": # only a method but no construcor
            return None
        string = make_String(name, loader)
        vmconstr_objref.fields.set(u'name', string,"ref")
        vmconstr_objref.fields.set(u'clazz', outer_clsref, "ref")
        
        # XXX: extra attr.
        vmconstr_objref.fields.set(u'method_info', method_info, "ref")
        descriptor  = const[method_info.descriptor_index]
        vmconstr_objref.fields.set(u'descriptor', descriptor, "ref")
        exc_lst = []
        for attr in method_info.attributes:
            if const[attr.attribute_name_index] == "Exceptions":
                attr = cls.getattr(method_info, 'Exceptions', classfile.Exceptions_attribute)
                for k in range(attr.number_of_exceptions):
                    excep_index = attr.exceptions_index_table[k]
                    cls_info = const[excep_index]
                    excep_name = const[cls_info.name_index]
                    exc_lst.append(excep_name)
        vmconstr_objref.fields.set(u'exceptions', exc_lst, "ref")
        objref.fields.set(u'cons', vmconstr_objref, "ref")
        return objref
    return None # no inner class => no enclosing constructor

def VMClass_getEnclosingMethod(locals, loader, cls, method):
    clsref = locals.get(0, "ref") # maybe an inner class
    name = clsref.class_type.__name__
    name2 = ""
    index = 0
    for c in name:
        index = index +1
        if c== '$':
            break
        name2 = name2 + c
    if not name == name2:
        if not name[index].isdigit():
            return None # no local class
        jcls = loader.getclass(name2) #name2: name of outer clas
        outer_clsref = vmobject_getClass_helper(jcls, loader)
        method_cls = loader.getclass("java/lang/reflect/Method")
        vmmethod_cls = loader.getclass("java/lang/reflect/VMMethod")
        #########################
        objref = Objectref(method_cls, True)
        vmmethod_objref = Objectref(vmmethod_cls, True)
        method_info = clsref.class_type.enclosingMethod_info
        const = outer_clsref.class_type.cls.constant_pool
        name = const[method_info.name_index]
        string = make_String(name, loader)
        vmmethod_objref.fields.set(u'name', string,"ref")
        vmmethod_objref.fields.set(u'clazz', outer_clsref, "ref")
        
        # XXX: extra attr.
        vmmethod_objref.fields.set(u'method_info', method_info, "ref")
        descriptor  = const[method_info.descriptor_index]
        vmmethod_objref.fields.set(u'descriptor', descriptor, "ref")
        exc_lst = []
        for attr in method_info.attributes:
            if const[attr.attribute_name_index] == "Exceptions":
                attr = cls.getattr(method_info, 'Exceptions', classfile.Exceptions_attribute)
                for k in range(attr.number_of_exceptions):
                    excep_index = attr.exceptions_index_table[k]
                    cls_info = const[excep_index]
                    excep_name = const[cls_info.name_index]
                    exc_lst.append(excep_name)
        vmmethod_objref.fields.set(u'exceptions', exc_lst, "ref")
        objref.fields.set(u'm', vmmethod_objref, "ref")
        return objref
    return None # no inner class => no enclosing method

def VMClass_getClassSignature(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClass_isAnonymousClass(locals, loader, cls, method):
    clsref = locals.get(0, "ref")
    name = clsref.class_type.__name__
    index = 0
    for c in name:
        if c== '$':
            break
        index = index +1
    num = name[index+1:]
    if not num == "":
        assert isinstance(int(num),int) # e.g. ClassName$42: int(num)==42
        return True
    return False

def VMClass_isLocalClass(locals, loader, cls, method):
    clsref = locals.get(0, "ref")
    name = clsref.class_type.__name__
    index =0 
    for c in name:
        index = index +1
        if c=="$":
            # local classes have a number after there $
            if name[index].isdigit():
                return True
            else:
                return False # inner but not local
    return False # no inner class


def VMClass_isMemberClass(locals, loader, cls, method):
    clsref = locals.get(0, "ref")
    return "$" in clsref.class_type.__name__

def VMObject_getClass(locals, loader, cls, method):
    objectref = locals.get(0, "ref")
    return vmobject_getClass_helper(objectref.jcls, loader)


# for every instance of a class there is only one java.lang.Class class
# X a = new X(); X b = new X();
# a.getClass()==b.getClass() //true
def vmobject_getClass_helper(jcls, loader):
    if isinstance(loader, ClassLoaderref):
        loader = loader.class_loader
    try:
        return loader.class_cache[jcls.__name__]
    except KeyError:
        if isinstance(loader, ClassLoaderref): # no Bootstarploader!
            clsref = Classref(loader.getclass("java/lang/Class"), True, jcls, loader)
        else: # Bootsstraploader
            clsref = Classref(loader.getclass("java/lang/Class"), True, jcls, None)
        loader.class_cache[jcls.__name__] = clsref
        return clsref
        
def VMObject_clone(locals, loader, cls, method):
    objectref = locals.get(0, "ref")
    copy = Objectref(objectref.jcls)
    copy.fields.set_int_map(objectref.fields.int_map.copy())
    copy.fields.set_long_map(objectref.fields.long_map.copy())
    copy.fields.set_float_map(objectref.fields.float_map.copy())
    copy.fields.set_double_map(objectref.fields.double_map.copy())
    copy.fields.set_ref_map(objectref.fields.ref_map.copy())
    return copy


def VMObject_notify(locals, loader, cls, method):
    objref = locals.get(0, "ref")
    if not len(objref.wait_set) == 0:
        objref.wait_set.pop(0)


def VMObject_notifyAll(locals, loader, cls, method):
    objref = locals.get(0, "ref")
    objref.wait_set = []
    #print objref.fields.get('vmdata', "ref")
    #print "notifyAll:",objref.wait_set

def VMObject_wait(locals, loader, cls, method):
    objref = locals.get(0, "ref")
    ms = locals.get(1, "long")
    ns = locals.get(3, "int")
    if objref.jcls.__name__ == "java/lang/VMThread":
        import java_threading
        from interp import interp_lock
        if ms*1000+ns ==0: # special case : eg. join()
            objref.wait_set.append(java_threading.currentVMThread)

            # JVMSpec 8.14: release lock on objref
            remember_lock_count = objref.lock_count
            objref.lock_count = 0
            old_owner = objref.owner_thread
            objref.owner_thread = None

            while not objref.wait_set.count(java_threading.currentVMThread)==0:
                if not java_threading.currentVMThread == "main_no_init":
                    java_threading.currentVMThread.STATE =make_String("BLOCKED", loader)
                temp = java_threading.currentVMThread
                interp_lock.release()
                # if there is an other thread it will get the
                # exc. control here!
                interp_lock.acquire()
                java_threading.currentVMThread = temp
                if not java_threading.currentVMThread == "main_no_init":
                    java_threading.currentVMThread.STATE =make_String("RUNNABLE", loader)
                cvmt = java_threading.currentVMThread
                if not cvmt=="main_no_init" and cvmt.isInterrupted:
                    # TODO: maybe add: objref.owner_thread = old_owner ???
                    cvmt.isInterrupted = False
                    java_threading.currentVMThread = cvmt
                    throw_InterruptedException(loader, "sleep")
            # JVMSpec 8.14: restore look
            objref.lock_count = remember_lock_count
            objref.owner_thread = old_owner
            assert java_threading.currentVMThread == objref.owner_thread
        else:
            t0= time.time()
            t1= t0
            #TODO: set state to waiting
            from interp import interp_lock
            import java_threading
            while not (t1-t0)*1000000>ms*1000+ns:
                if not java_threading.currentVMThread == "main_no_init":
                    java_threading.currentVMThread.STATE =make_String("TIMED_WAITING", loader)
                temp = java_threading.currentVMThread
                interp_lock.release()
                interp_lock.acquire()
                java_threading.currentVMThread = temp
                if not java_threading.currentVMThread == "main_no_init":
                    java_threading.currentVMThread.STATE =make_String("RUNNABLE", loader)
                t1=time.time()
                cvmt = java_threading.currentVMThread
                if not cvmt=="main_no_init" and cvmt.isInterrupted:
                    cvmt.isInterrupted = False
                    java_threading.currentVMThread = cvmt
                    throw_InterruptedException(loader, "sleep")
    else:
        raise NotImplemented("Hook Method")

def VMClassLoader_defineClass(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoader_resolveClass(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoader_loadClass(locals, loader, cls, method):
    string = locals.get(0, "ref")
    assert string.jcls.__name__ == "java/lang/String"
    str = unpack_string(string)
    jcls = loader.getclass(string)
    #clsref = Classref(loader.getclass("java/lang/Class"), True, jcls, loader)
    clsref = vmobject_getClass_helper(jcls, loader)
    return clsref

def VMClassLoader_getPrimitiveClass(locals, loader, cls, method):
    char = locals.get(0, "char")
    char = chr(char)
    return get_primitive_class_helper(char, loader)

def get_primitive_class_helper(char, loader):
    jcls = loader.getPrimClass(char)
    return vmobject_getClass_helper(jcls, loader)

def VMClassLoader_getResource(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoader_getResources(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoader_getPackage(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoader_getPackages(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

#def VMClassLoader_defaultAssertionStatus(locals, loader, cls, method):
#    raise NotImplemented("Hook Method")

def VMClassLoader_packageAssertionStatus(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoader_classAssertionStatus(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoader_getSystemClassLoader(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# FIXME: dont workes if src = dest (?)
# TODO: Throw Exceptions
def VMSystem_arraycopy(locals, loader, cls, method):
    src = locals.get(0, "ref")
    srcStart = locals.get(1, "int")
    dest  = locals.get(2, "ref")
    destStart = locals.get(3, "int")
    le = locals.get(4, "int") 
    dest.arrayref[destStart:destStart+le] = src.arrayref[srcStart:srcStart+le]

# uses python hash
def VMSystem_identityHashCode(locals, loader, cls, method):
    objref = locals.get(0, "ref")
    return hash(objref)

def VMSystem_setIn(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMSystem_setOut(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMSystem_setErr(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMSystem_currentTimeMillis(locals, loader, cls, method):
    return long(time.time() * 1000)

def VMSystem_getenv(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMSystem_makeStandardInputStream(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMSystem_makeStandardOutputStream(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMSystem_makeStandardErrorStream(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# TODO: Store Vm exec state
def VMThrowable_fillInStackTrace(locals, loader, cls, method):
    objectref = locals.get(0, "ref")
    #print objectref.jcls.__name__
    return None # null means not supported

def VMThrowable_getStackTrace(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMCompiler_compileClass(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMCompiler_compileClasses(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMCompiler_command(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMCompiler_enable(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMCompiler_disable(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDouble_doubleToRawLongBits(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDouble_longBitsToDouble(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDouble_toString(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDouble_initIDs(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDouble_parseDouble(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFloat_floatToRawIntBits(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFloat_intBitsToFloat(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMProcess_nativeSpawn(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMProcess_nativeReap(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMProcess_nativeKill(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_availableProcessors(locals, loader, cls, method):
    import multiprocessing
    return multiprocessing.cpu_count()

def VMRuntime_freeMemory(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_totalMemory(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_maxMemory(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_gc(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_runFinalization(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_runFinalizationForExit(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_traceInstructions(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_traceMethodCalls(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_runFinalizersOnExit(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_exit(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntime_nativeLoad(locals, loader, cls, method):
    string = locals.get(0, "ref")
    assert string.jcls.__name__ == "java/lang/String"
    str = unpack_string(string)
    classLoader = locals.get(1, "ref")
    assert isinstance(classLoader, ClassLoaderref)
    classLoader.class_loader.extern_libs[str] = cdll.LoadLibrary("/usr/lib/classpath/"+str)
    #classLoader.class_loader.extern_libs[str] = cdll.LoadLibrary("/usr/local/classpath/lib/classpath/"+str)
    return 41 # TODO return zero for failure, do nothing if allready loaded

def VMRuntime_mapLibraryName(locals, loader, cls, method):
    string = locals.get(0, "ref")
    assert string.jcls.__name__ == "java/lang/String"
    str = unpack_string(string)
    # TODO support WIndows (.dll)
    linuxlib = "lib"+str+".so"
    return make_String(linuxlib, loader)

def VMThread_start(locals, loader, cls, method):
    vmthread_objref = locals.get(0, "ref") #this
    stack_size = locals.get(1, "long") #TODO: dont ignore that
    method_info = find_method(vmthread_objref.jcls, "run", "()V")
    descr = [u'reference:java/lang/Thread']
    args = Stack()
    args.push(vmthread_objref) #this
    thread = vmdata_VMThread(loader, vmthread_objref, method_info, descr, args)
    vmthread_objref.fields.set("vmdata",thread,"ref")
    thread.start()
    #thread.start_new_thread(java_threading.start_thread,)
    #java_threading.start_thread(loader, thread_objref, method_info, descr, args)

def VMThread_interrupt(locals, loader, cls, method):
    vmthread_objref = locals.get(0, "ref") #this
    vmdata = vmthread_objref.fields.get("vmdata","ref")
    assert isinstance(vmdata, vmdata_VMThread)
    vmdata.isInterrupted = True

def VMThread_isInterrupted(locals, loader, cls, method):
    vmthread_objref = locals.get(0, "ref") #this
    vmdata = vmthread_objref.fields.get("vmdata","ref")
    assert isinstance(vmdata, vmdata_VMThread)
    return vmdata.isInterrupted

def VMThread_suspend(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThread_resume(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThread_nativeSetPriority(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThread_nativeStop(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

#TODO: set state after task switch
def VMThread_getState(locals, loader, cls, method):
    this = locals.get(0,"ref")
    if this.jcls.__name__=="java/lang/VMThread":
        vmthread = this.fields.get("vmdata", "ref")
        assert not vmthread==None
        return vmthread.STATE
    raise NotImplemented("Hook Method")

#TODO: must be the current Thread
# this constructs a main thread.
# maybe this must be moved to an seperated Method some day
def VMThread_currentThread(locals, loader, cls, method):
    # FIXME: wrong thread_id 0 insted of one
    import java_threading 
    if java_threading.currentVMThread=="main_no_init":
        thread_ref = java_threading.give_main_thread(loader)
    else:
        vm_thread = java_threading.currentVMThread.vmthread_objref
        thread_ref = vm_thread.fields.get("thread","ref")
    #g= thread_ref.fields.get("group","ref")
    #print "tg:",g
    return thread_ref

def VMThread_yield(locals, loader, cls, method):
    import java_threading, interp 
    if not java_threading.currentVMThread == "main_no_init":
        java_threading.currentVMThread.STATE =make_String("WAITING", loader)
    temp = java_threading.currentVMThread
    interp.interp_lock.release()
    # if there is an other thread it will get the
    # exc. control here!
    interp.interp_lock.acquire()
    java_threading.currentVMThread = temp
    if not java_threading.currentVMThread == "main_no_init":
        java_threading.currentVMThread.STATE =make_String("RUNNABLE", loader)

def VMThread_interrupted(locals, loader, cls, method):
    import java_threading 
    cvmt = java_threading.currentVMThread
    result = cvmt.isInterrupted
    cvmt.isInterrupted = False
    return result

def VMThread_countStackFrame(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# where does that come from?
# FIXME:MAYBE buggy
def VMStackWalker_getClassLoader(locals, loader, cls, method):
    return ClassLoaderref(loader.getclass("java/lang/ClassLoader"), True, loader)

# TODO: this is wrong. it musst return an arra of classes of the callstack
def VMStackWalker_getClassContext(locals, loader, cls, method):
    classref = loader.called_classes
    assert isinstance(classref, Classref)
    return classref

def VMStackWalker_getCallingClass(locals, loader, cls, method):
    try:
        classref = loader.called_classes.arrayref[1]
        assert isinstance(classref, Classref)
        return classref
    except IndexError:
        return None

def VMStackWalker_getCallingClassLoader(locals, loader, cls, method):
    try:
        classref = loader.called_classes.arrayref[1]
        assert isinstance(classref, Classref)
        return ClassLoaderref(loader.getclass("java/lang/ClassLoader"), True, classref.classLoader)
    except IndexError:
        return None

def VMSystemProperties_preInit(locals, loader, cls, method):
    #TODO: add Systemproperties
    # call setProperty(String,String) by hand
    objectref = locals.get(0,"ref")
    assert objectref.jcls.__name__ == "java/util/Properties"
    acls = objectref.jcls.cls
    const = acls.constant_pool
    classNameIndex = const[acls.this_class].name_index
    clsName = const[classNameIndex]
    assert clsName == "java/util/Properties"
    real_name = "setProperty_reference_java__lang__String___reference_java__lang__String___reference_java__lang__Object"
    method_info = objectref.jcls.methods[unicode(real_name)]
    descr = descriptor(const[method_info.descriptor_index])
    invoke_setProperty(loader, acls, method_info, descr, objectref,"java.vm.name", "NoName")
    invoke_setProperty(loader, acls, method_info, descr, objectref,"java.vm.version", "1")
    invoke_setProperty(loader, acls, method_info, descr, objectref,"java.io.tmpdir", "/tmp") #Default temp file patp XXX Windows
    invoke_setProperty(loader, acls, method_info, descr, objectref,"os.name", "Linux") #XXX WIndows
    invoke_setProperty(loader, acls, method_info, descr, objectref,"file.separator", "/") #XXX WIndows
    invoke_setProperty(loader, acls, method_info, descr, objectref,"path.separator", ":") #XXX WIndows
    invoke_setProperty(loader, acls, method_info, descr, objectref,"line.separator", "\n") #XXX WIndows

def VMSystemProperties_postInit(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# replaced gnu/classpath by sun/misc
def Unsafe_objectFieldOffset(locals, loader, cls, method):
    fieldref  = locals.get(1,"ref")
    vmfieldref = fieldref.fields.get(u"f","ref")
    return vmfieldref.fields.get(u"id","long")

# replaced gnu/classpath by sun/misc
def Unsafe_compareAndSwap(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# replaced gnu/classpath by sun/misc
def Unsafe_put(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# replaced gnu/classpath by sun/misc
def Unsafe_get(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# replaced gnu/classpath by sun/misc
def Unsafe_arrayBaseOffset(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

# replaced gnu/classpath by sun/misc
def Unsafe_park(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMath_sin(locals, loader, cls, method):
    return math.sin(locals.get(0, "double"))

def VMMath_cos(locals, loader, cls, method):
    return math.cos(locals.get(0, "double"))

def VMMath_tan(locals, loader, cls, method):
    return math.tan(locals.get(0, "double"))

def VMMath_asin(locals, loader, cls, method):
    return math.asin(locals.get(0, "double"))

def VMMath_acos(locals, loader, cls, method):
    return math.acos(locals.get(0, "double"))

def VMMath_atan(locals, loader, cls, method):
    return math.atan(locals.get(0, "double"))

def VMMath_atan2(locals, loader, cls, method):
    #doubles need two stackpos
    return math.atan2(locals.get(0, "double"), locals.get(2, "double"))

def VMMath_exp(locals, loader, cls, method):
    return math.exp(locals.get(0, "double"))

def VMMath_log(locals, loader, cls, method):
    return math.log(locals.get(0, "double"))

def VMMath_sqrt(locals, loader, cls, method):
    return math.sqrt(locals.get(0, "double"))

def VMMath_pow(locals, loader, cls, method):
    #doubles need two stackpos
    return math.pow(locals.get(0, "double"), locals.get(2, "double"))

def VMMath_floor(locals, loader, cls, method):
    return math.floor(locals.get(0, "double"))

def VMMath_ceil(locals, loader, cls, method):
    return math.ceil(locals.get(0, "double"))

def VMMath_cosh(locals, loader, cls, method):
    return math.cosh(locals.get(0, "double"))

def VMMath_sinh(locals, loader, cls, method):
    return math.sinh(locals.get(0, "double"))

def VMMath_tanh(locals, loader, cls, method):
    return math.tanh(locals.get(0, "double"))

def VMMath_log10(locals, loader, cls, method):
    return math.log10(locals.get(0, "double"))

def VMMath_hypot(locals, loader, cls, method):
    return math.hypot(locals.get(0, "double"), locals.get(2, "double"))

def VMMath_log1p(locals, loader, cls, method):
    return math.log1p(locals.get(0, "double"))

def VMMath_expm1(locals, loader, cls, method):
    return math.exp(locals.get(0, "double")-1.0)

def VMMath_IEEEremainder(locals, loader, cls, method):
    return math.fmod(locals.get(0, "double"), locals.get(2, "double"))

def VMMath_cbrt(locals, loader, cls, method):
    return math.pow(locals.get(0, "double"),1.0/3)

def VMMath_rint(locals, loader, cls, method):
    value = locals.get(0, "double")
    min = math.floor(value)
    max = math.ceil(value)
    if value-min == 0 and value-max==0:
        return value
    value = value - min
    if value<0.5:
        return min
    else:
        return max

def VMFile_lastModified(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_setReadOnly(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_create(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_list(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_renameTo(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_length(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_exists(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_delete(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_setLastModified(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_mkdir(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_isFile(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_canWrite(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_canRead(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_isDirectory(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_canWriteDirectory(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_listRoots(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_isHidden(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_getName(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMFile_getCanonicalForm(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMAccessController_pushContext(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMAccessController_popContext(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMAccessController_getContext(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMAccessController_getStack(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInetAddress_getLocalHostname(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInetAddress_lookupInaddrAny(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInetAddress_getHostByAddr(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInetAddress_getHostByName(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDirectByteBuffer_init(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDirectByteBuffer_allocate(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDirectByteBuffer_free(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDirectByteBuffer_get(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDirectByteBuffer_put(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDirectByteBuffer_adjustAddress(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMDirectByteBuffer_shiftDown(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMChannels_createStream(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMChannels_newInputStream(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMChannels_newOutputStream(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInstrumentationImpl_isRedefineClassesSupported(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInstrumentationImpl_redefineClasses(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInstrumentationImpl_getAllLoadedClass(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInstrumentationImpl_getInitiatedClass(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMInstrumentationImpl_getObjectSize(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntimeMXBeanImpl_getInputArguments(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntimeMXBeanImpl_getName(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMRuntimeMXBeanImpl_getStartTime(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoadingMXBeanImpl_getLoadedClassCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoadingMXBeanImpl_getUnloadedClassCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoadingMXBeanImpl_isVerbose(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMClassLoadingMXBeanImpl_setVerbose(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_findDeadlockedThreads(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_findMonitorDeadlockedThreads(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getAllThreads(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getAllThreadIds(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getAllThreadIds(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getCurrentThreadCpuTime(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getCurrentThreadUserTime(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getDaemonThreadCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getLockInfo(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getMonitorInfo(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getPeakThreadCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_resetPeakThreadCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getThreadCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getThreadCpuTime(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getThreadUserTime(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getThreadInfoForId(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMThreadMXBeanImpl_getTotalStartedThreadCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryMXBeanImpl_getHeapMemoryUsage(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryMXBeanImpl_getNonHeapMemoryUsage(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryMXBeanImpl_getObjectPendingFinalizationCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryMXBeanImpl_isVerbose(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryMXBeanImpl_setVerbose(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMCompilationMXBeanImpl_getTotalCompilationTime(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getCollectionUsage(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getCollectionUsageThreshold(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getCollectionUsageThresholdCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getMemoryManagerNames(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getPeakUsage(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getType(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getUsage(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getUsageThreshold(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_getUsageThresholdCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_isValid(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_resetPeakUsage(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_setCollectionUsageThreshold(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryPoolMXBeanImpl_setUsageThreshold(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryManagerMXBeanImpl_getMemoryPoolNames(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMMemoryManagerMXBeanImpl_isValid(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMGarbageCollectorMXBeanImpl_getCollectionCount(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMGarbageCollectorMXBeanImpl_getCollectionTime(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMManagementFactory_getMemoryPoolNames(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMManagementFactory_getMemoryManagerNames(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMManagementFactory_getGarbageCollectorNames(locals, loader, cls, method):
    raise NotImplemented("Hook Method")

def VMField_setInt(locals, loader, cls, method):
    vmfield_set_helper(locals, "int")

def VMField_setByte(locals, loader, cls, method):
    vmfield_set_helper(locals, "byte")

def VMField_setShort(locals, loader, cls, method):
    vmfield_set_helper(locals, "short")

def VMField_setLong(locals, loader, cls, method):
    vmfield_set_helper(locals, "long")

def VMField_setFloat(locals, loader, cls, method):
    vmfield_set_helper(locals, "float")

def VMField_setDouble(locals, loader, cls, method):
    vmfield_set_helper(locals, "double")

def VMField_setBoolean(locals, loader, cls, method):
    vmfield_set_helper(locals, "boolean")

def VMField_setChar(locals, loader, cls, method):
    vmfield_set_helper(locals, "char")

def VMField_set(locals, loader, cls, method):
    vmfield_set_helper(locals, "ref")

def VMField_getInt(locals, loader, cls, method):
    return vmfield_get_helper(locals, "int")

def VMField_getByte(locals, loader, cls, method):
    return vmfield_get_helper(locals, "byte")

def VMField_getShort(locals, loader, cls, method):
    return vmfield_get_helper(locals, "short")

def VMField_getLong(locals, loader, cls, method):
    return vmfield_get_helper(locals, "long")

def VMField_getFloat(locals, loader, cls, method):
    return vmfield_get_helper(locals, "float")

def VMField_getDouble(locals, loader, cls, method):
    return vmfield_get_helper(locals, "double")

def VMField_getBoolean(locals, loader, cls, method):
    return vmfield_get_helper(locals, "boolean")

def VMField_getChar(locals, loader, cls, method):
    return vmfield_get_helper(locals, "char")

def VMField_get(locals, loader, cls, method):
    return vmfield_get_helper(locals, "ref")

def VMField_getType(locals, loader, cls, method):
    this = locals.get(0, "ref")
    clazz = this.fields.get('clazz', "ref")
    name = unpack_string(this.fields.get('name', "ref"))
    const = clazz.class_type.cls.constant_pool
    for i in range(clazz.class_type.cls.fields_count):
        f = clazz.class_type.cls.fields[i]
        fname = const[f.name_index]
        descr = const[f.descriptor_index]
        if fname==name:
            break
    if descr.startswith("L"):
        cls_name = descr[1:-1]
        return vmobject_getClass_helper(loader.getclass(cls_name), loader)
    else:
        prim_cls = get_primitive_class_helper(descr, loader)
        return prim_cls

def VMField_getModifiersInternal(locals, loader, cls, method):
    this = locals.get(0, "ref")
    clazz = this.fields.get('clazz', "ref")
    name = unpack_string(this.fields.get('name', "ref"))
    const = clazz.class_type.cls.constant_pool
    for i in range(clazz.class_type.cls.fields_count):
        f = clazz.class_type.cls.fields[i]
        fname = const[f.name_index]
        flags = f.access_flags
        if fname==name:
            break
    return flags

def VMMethod_getParameterTypes(locals, loader, cls, method):
    this = locals.get(0, "ref")
    descriptor = this.fields.get('descriptor', "ref")
    lst = []
    parseing_ref = False
    ref_name = ""
    array_dim = 0
    # TODO: write only one parse method
    for char in descriptor:
        # End of args
        if char==")":
            break
        #parse array-class
        if char=="[":
            array_dim = array_dim +1
        #parse references:
        if char==";":
            parseing_ref = False
            if not array_dim == 0:
                jcls = loader.getclass("["*array_dim + ref_name)
                array_dim = 0
            else:
                jcls = loader.getclass(ref_name)
            ref_name= ""
            cls = vmobject_getClass_helper(jcls, loader)
            lst.append(cls)
        if parseing_ref:
            ref_name += char
            continue
        if char=='L':
            parseing_ref = True
        if char=='B'or char == 'C' or char == 'D' or char == 'F' or char == 'I' or char == 'J' or char == 'S' or char == 'Z' or char == 'V':
            if not array_dim == 0:
                jcls = loader.getclass("["*array_dim + char)
                array_dim = 0
                cls = vmobject_getClass_helper(jcls, loader)
            else:
                cls = get_primitive_class_helper(char , loader)
            lst.append(cls)
    cls_array = Arrayref(lst,None, loader.getclass("[Ljava.lang.Class;"))
    return cls_array


def VMMethod_getExceptionTypes(locals, loader, cls, method):
    this = locals.get(0, "ref")
    exc_lst = this.fields.get('exceptions', "ref")
    lst = []
    for ref_name in exc_lst:
        jcls = loader.getclass(ref_name)
        cls = vmobject_getClass_helper(jcls, loader)
        lst.append(cls)
    cls_array = Arrayref(lst,None, loader.getclass("[Ljava.lang.Class;"))
    return cls_array

# TODO: throws IllegalAccessException, InvocationTargetException
def VMMethod_invoke(locals, loader, cls, method):
    this = locals.get(0, "ref")
    method = this.fields.get('method_info', "ref")
    objref = locals.get(1, "ref")
    objref_args_array = locals.get(2, "ref")
    args  = unwrapp_args_helper(objref_args_array)
    const = objref.jcls.cls.constant_pool
    descr = descriptor(const[method.descriptor_index])
    args.push(objref)
    result = loader.invoke_method(objref.jcls.cls, method, descr, args)
    return wrapp_result(result, descr, loader)

def wrapp_result(value, descr, loader):
    if descr[-1]=="byte":
        jcls = loader.getclass("java/lang/Byte")
        objref = Objectref(jcls, True)
        objref.fields.set('value', value, "int")
        return objref
    elif descr[-1]=="short":
        jcls = loader.getclass("java/lang/Short")
        objref = Objectref(jcls, True)
        objref.fields.set('value', value, "int")
        return objref
    elif descr[-1]=="int":
        jcls = loader.getclass("java/lang/Integer")
        objref = Objectref(jcls, True)
        objref.fields.set('value', value, "int")
        return objref
    elif descr[-1]=="boolean":
        jcls = loader.getclass("java/lang/Boolean")
        objref = Objectref(jcls, True)
        objref.fields.set('value', value, "int")
        return objref
    elif descr[-1]=="char":
        jcls = loader.getclass("java/lang/Character")
        objref = Objectref(jcls, True)
        objref.fields.set('value', value, "char")
        return objref
    elif descr[-1]=="long":
        jcls = loader.getclass("java/lang/Long")
        objref = Objectref(jcls, True)
        objref.fields.set('value', value, "long")
        return objref
    elif descr[-1]=="float":
        jcls = loader.getclass("java/lang/Float")
        objref = Objectref(jcls, True)
        objref.fields.set('value', value, "float")
        return objref
    elif descr[-1]=="double":
        jcls = loader.getclass("java/lang/Double")
        objref = Objectref(jcls, True)
        objref.fields.set('value', value, "double")
        return objref
    return value

def unwrapp_args_helper(array):
    stack = Stack()
    lst = array.arrayref
    lst.reverse()
    for elem in lst:
        #XXX more...
        if elem.jcls.__name__ == "java/lang/Short" or elem.jcls.__name__ == "java/lang/Byte" or elem.jcls.__name__ == "java/lang/Integer" or elem.jcls.__name__ == "java/lang/Boolean":
            value = elem.fields.get('value', "int")
            stack.push(value)
        elif elem.jcls.__name__ == "java/lang/Character":
            value = elem.fields.get('value', "char")
            stack.push(value)
        elif elem.jcls.__name__ == "java/lang/Long":
            value = elem.fields.get('value', "long")
            stack.push(value)
        elif elem.jcls.__name__ == "java/lang/Float":
            value = elem.fields.get('value', "float")
            stack.push(value)
        elif elem.jcls.__name__ == "java/lang/Double":
            value = elem.fields.get('value', "double")
            stack.push(value)
        else:
            stack.push(elem)
    return stack
    
def VMMethod_getReturnType(locals, loader, cls, method):
    this = locals.get(0, "ref")
    descriptor = this.fields.get('descriptor', "ref")
    i = 0
    for c in descriptor:
        if descriptor[i] != ')':
            i = i+1
            continue
        char = descriptor[i+1:]
    if char=='B'or char == 'C' or char == 'D' or char == 'F' or char == 'I' or char == 'J' or char == 'S' or char == 'Z' or char == 'V':
            cls = get_primitive_class_helper(char , loader)
    else:
        ref_name = char[1:-1]
        jcls = loader.getclass(ref_name)
        cls = vmobject_getClass_helper(jcls, loader)
    return cls

def VMMethod_getModifiersInternal(locals, loader, cls, method):
    this = locals.get(0, "ref")
    method_info = this.fields.get('method_info', "ref")
    return method_info.access_flags

def VMConstructor_getParameterTypes(locals, loader, cls, method):
    this = locals.get(0, "ref")
    method_info = this.fields.get('method_info', "ref")
    clazz = this.fields.get('clazz', "ref")
    const = clazz.class_type.cls.constant_pool
    descriptor = const[method_info.descriptor_index]
    lst = []
    parseing_ref = False
    ref_name = ""
    array_dim = 0
    # TODO: write only one parse method
    for char in descriptor:
        # End of args
        if char==")":
            break
        #parse array-class
        if char=="[":
            array_dim = array_dim +1
        #parse references:
        if char==";":
            parseing_ref = False
            if not array_dim == 0:
                jcls = loader.getclass("["*array_dim + ref_name)
                array_dim = 0
            else:
                jcls = loader.getclass(ref_name)
            ref_name= ""
            cls = vmobject_getClass_helper(jcls, loader)
            lst.append(cls)
        if parseing_ref:
            ref_name += char
            continue
        if char=='L':
            parseing_ref = True
        if char=='B'or char == 'C' or char == 'D' or char == 'F' or char == 'I' or char == 'J' or char == 'S' or char == 'Z' or char == 'V':
            if not array_dim == 0:
                jcls = loader.getclass("["*array_dim + char)
                array_dim = 0
                cls = vmobject_getClass_helper(jcls, loader)
            else:
                cls = get_primitive_class_helper(char , loader)
            lst.append(cls)
    cls_array = Arrayref(lst,None, loader.getclass("[Ljava.lang.Class;"))
    return cls_array


def VMConstructor_getExceptionTypes(locals, loader, cls, method):
    this = locals.get(0, "ref")
    excp_lst = this.fields.get('exceptions', "ref")
    lst = []
    for e in excp_lst:
        jcls = loader.getclass(e)
        cls = vmobject_getClass_helper(jcls, loader)
        lst.append(cls)
    cls_array = Arrayref(lst,None, loader.getclass("[Ljava.lang.Class;"))
    return cls_array

def VMConstructor_getModifiersInternal(locals, loader, cls, method):
    this = locals.get(0, "ref")
    method_info = this.fields.get(u'method_info', "ref")
    return method_info.access_flags

def VMConstructor_construct(locals, loader, cls, method):
    this = locals.get(0, "ref")
    objref_args_array = locals.get(1, "ref")
    clazz = this.fields.get('clazz', "ref")
    method_info = this.fields.get(u'method_info', "ref")
    objref = Objectref(clazz.class_type, True) # new this
    # TODO: call constructor
    args  = unwrapp_args_helper(objref_args_array)
    const = clazz.class_type.cls.constant_pool
    descr = descriptor(const[method_info.descriptor_index])
    args.push(objref)
    #try:
    loader.invoke_method(objref.jcls.cls, method_info, descr, args)
    #except Exception:
    #    jcls = loader.getclass("java/lang/reflect/InvocationTargetException")
    #    objref = Objectref(jcls, True)
    #    raise JException(objref)
    return objref

#TODO: Test me!
def VMConstructor_getSignature(locals, loader, cls, method):
    this = locals.get(0, "ref")
    clazz = this.fields.get('clazz', "ref")
    method_info = this.fields.get(u'method_info', "ref")
    const = clazz.class_type.cls.constant_pool
    descr = const[method_info.descriptor_index]
    return make_String(descr, loader)

def vmfield_set_helper(locals, _type):
    this = locals.get(0, "ref")
    objectref = locals.get(1, "ref")
    value = locals.get(2, _type)
    clazz = this.fields.get('clazz', "ref") 
    if not objectref.jcls.__name__ == clazz.class_type.__name__:
        pass #TODO: throw IllegalAccessException
    name = this.fields.get('name', "ref")
    string = unpack_string(name)
    # check if private
    f_info = find_field_info(clazz.class_type.cls, string)
    is_private = f_info.access_flags & 0x2 == 0x2
    # TODO: find calling class
    try:
        objectref.fields.set(string, value, _type)
    except KeyError:
        pass #TODO: throw IllegalAccessException

# TODO: IllegalAccessException, IllegalArgumentException
# NullPointerException, ExceptionInInitializerError
def vmfield_get_helper(locals, _type):
    this = locals.get(0, "ref")
    objectref = locals.get(1, "ref")
    clazz = this.fields.get('clazz', "ref")
    name = this.fields.get('name', "ref")
    string = unpack_string(name)
    if objectref==None:
        try:
            result = clazz.class_type.static_fields.get(string, _type)
        except KeyError:
            pass #TODO: exception if not static
        return result
    elif not objectref.jcls.__name__ == clazz.class_type.__name__:
        pass #TODO: throw IllegalAccessException
    try:
        result = objectref.fields.get(string, _type)
    except KeyError:
        pass #TODO: throw IllegalAccessException
    return result

def find_field_info(cls, name):
    for i in range(cls.fields_count):
        f = cls.fields[i]
        fname = cls.constant_pool[f.name_index]
        if fname==name:
            return f
    return None # not found

def check_primitive(name):
    if name == "boolean":
        return True
    elif name == "byte":
        return True
    elif name == "short":
        return True
    elif name == "int":
        return True
    elif name == "char":
        return True
    elif name == "long":
        return True
    elif name == "float":
        return True
    elif name == "double":
        return True
    elif name == "void":
        return True
    return False

def check_interface(classref):
    if classref.class_type.cls.access_flags == 0x0200 or classref.class_type.cls.access_flags == 0x0600:
        return True
    return False


HOOKS = {
    ("java/lang/reflect/VMConstructor","getSignature"):VMConstructor_getSignature,("java/lang/reflect/VMConstructor","construct"):VMConstructor_construct,
    ("java/lang/reflect/VMConstructor","getExceptionTypes"):VMConstructor_getExceptionTypes,
    ("java/lang/reflect/VMConstructor","getModifiersInternal"):VMConstructor_getModifiersInternal,
            ("java/lang/reflect/VMConstructor", "getParameterTypes"):VMConstructor_getParameterTypes,
            ("java/lang/reflect/VMMethod","invoke"):VMMethod_invoke,
            ("java/lang/reflect/VMMethod","getExceptionTypes"):VMMethod_getExceptionTypes,
            ("java/lang/reflect/VMMethod", "getReturnType"):VMMethod_getReturnType,
            ("java/lang/reflect/VMMethod", "getModifiersInternal"):VMMethod_getModifiersInternal,
            ("java/lang/reflect/VMMethod", "getParameterTypes"):VMMethod_getParameterTypes,
            ("java/lang/reflect/VMField", "getModifiersInternal"):VMField_getModifiersInternal,
            ("java/lang/reflect/VMField", "getType"):VMField_getType,
            ("java/lang/reflect/VMField", "setInt"):VMField_setInt,
            ("java/lang/reflect/VMField", "setByte"):VMField_setByte,
            ("java/lang/reflect/VMField", "setShort"):VMField_setShort,
            ("java/lang/reflect/VMField", "setLong"):VMField_setLong,
            ("java/lang/reflect/VMField", "setFloat"):VMField_setFloat,
            ("java/lang/reflect/VMField", "setDouble"):VMField_setDouble,
            ("java/lang/reflect/VMField", "setBoolean"):VMField_setBoolean,
            ("java/lang/reflect/VMField", "setChar"):VMField_setChar,
            ("java/lang/reflect/VMField", "set"):VMField_set,
            ("java/lang/reflect/VMField", "getInt"):VMField_getInt,
            ("java/lang/reflect/VMField", "getByte"):VMField_getByte,
            ("java/lang/reflect/VMField", "getShort"):VMField_getShort,
            ("java/lang/reflect/VMField", "getLong"):VMField_getLong,
            ("java/lang/reflect/VMField", "getFloat"):VMField_getFloat,
            ("java/lang/reflect/VMField", "getDouble"):VMField_getDouble,
            ("java/lang/reflect/VMField", "getBoolean"):VMField_getBoolean,
            ("java/lang/reflect/VMField", "getChar"):VMField_getChar,
            ("java/lang/reflect/VMField", "get"):VMField_get,
            ("java/lang/VMClass", "isInterface"):VMClass_isInterface,
            ("java/lang/VMClass", "getName"):VMClass_getName,
            ("java/lang/VMClass", "getSuperclass"):VMClass_getSuperclass,
            ("java/lang/VMClass", "getInterfaces"):VMClass_getInterfaces,
            ("java/lang/VMClass", "getDeclaredClasses"):VMClass_getDeclaredClasses,
            ("java/lang/VMClass", "getDeclaredFields"):VMClass_getDeclaredFields,
            ("java/lang/VMClass", "getDeclaredMethods"):VMClass_getDeclareMethods,
            ("java/lang/VMClass", "getDeclaredConstructors"):VMClass_getDeclaredConstructors,
            ("java/lang/VMClass", "getClassLoader"):VMClass_getClassLoader,
            ("java/lang/VMClass", "forName"):VMClass_forName,
            ("java/lang/VMClass", "isArray"):VMClass_isArray,
            ("java/lang/VMClass", "initialize"):VMClass_initialize,
            ("java/lang/VMClass", "loadArrayClass"):VMClass_loadArrayClass,
            ("java/lang/VMClass", "throwException"):VMClass_throwException,
            ("java/lang/VMClass", "isInstance"):VMClass_isInstance,
            ("java/lang/VMClass", "isAssignableFrom"):VMClass_isAssignableForm,
            ("java/lang/VMClass", "isPrimitive"):VMClass_isPrimitive,
            ("java/lang/VMClass", "getComponentType"):VMClass_getComponentType,
            ("java/lang/VMClass", "getModifiers"):VMClass_getModifiers,
            ("java/lang/VMClass", "getDeclaringClass"):VMClass_getDeclaringClass,
            ("java/lang/VMClass", "isSynthetic"):VMClass_isSynthetic,
            ("java/lang/VMClass", "isAnnotation"):VMClass_isAnnotation,
            ("java/lang/VMClass", "isEnum"):VMClass_isEnum,
            #("java/lang/VMClass", "getSimpleName"):VMClass_getSimpleName,
            ("java/lang/VMClass", "getCanonicalName"):VMClass_getCanonicalName,
            ("java/lang/VMClass", "getEnclosingClass"):VMClass_getEnclosingClass,
            ("java/lang/VMClass", "getEnclosingConstructor"):VMClass_getEnclosingConstructor,
            ("java/lang/VMClass", "getEnclosingMethod"):VMClass_getEnclosingMethod,
            ("java/lang/VMClass", "getClassSignature"):VMClass_getClassSignature,
            ("java/lang/VMClass", "isAnonymousClass"):VMClass_isAnonymousClass,
            ("java/lang/VMClass", "isLocalClass"):VMClass_isLocalClass,
            ("java/lang/VMClass", "isMemberClass"):VMClass_isMemberClass,
            ("java/lang/VMObject","getClass"):VMObject_getClass,
            ("java/lang/VMObject","clone"):VMObject_clone,
            ("java/lang/VMObject","notify"):VMObject_notify,
            ("java/lang/VMObject","notifyAll"):VMObject_notifyAll,
            ("java/lang/VMObject","wait"):VMObject_wait,
            ("java/lang/VMClassLoader","defineClass"):VMClassLoader_defineClass,
            ("java/lang/VMClassLoader","resolveClass"):VMClassLoader_resolveClass,
            ("java/lang/VMClassLoader","loadClass"):VMClassLoader_loadClass,
            ("java/lang/VMClassLoader","getPrimitiveClass"):VMClassLoader_getPrimitiveClass,
            #("java/lang/VMClassLoader","getResource"):VMClassLoader_getResource,
            #("java/lang/VMClassLoader","getResources"):VMClassLoader_getResources,
            ("java/lang/VMClassLoader","getPackage"):VMClassLoader_getPackage,
            ("java/lang/VMClassLoader","getPackages"):VMClassLoader_getPackages,
            #("java/lang/VMClassLoader","defaultAssertionStatus"):VMClassLoader_defaultAssertionStatus,
            ("java/lang/VMClassLoader","packageAssertionStatus"):VMClassLoader_packageAssertionStatus,
            ("java/lang/VMClassLoader","classAssertionStatus"):VMClassLoader_classAssertionStatus,
            ("java/lang/VMClassLoader","getSystemClassLoader"):VMClassLoader_getSystemClassLoader,
            ("java/lang/VMSystem","arraycopy"):VMSystem_arraycopy,
            ("java/lang/VMSystem","identityHashCode"):VMSystem_identityHashCode,
            ("java/lang/VMSystem","setIn"):VMSystem_setIn,
            ("java/lang/VMSystem","setOut"):VMSystem_setOut,
            ("java/lang/VMSystem","setErr"):VMSystem_setErr,
            ("java/lang/VMSystem","currentTimeMillis"):VMSystem_currentTimeMillis,
            ("java/lang/VMSystem","getenv"):VMSystem_getenv,
            #("java/lang/VMSystem","makeStandardInputStream"):VMSystem_makeStandardInputStream,
            #("java/lang/VMSystem","makeStandardOutputStream"):VMSystem_makeStandardOutputStream,
            #("java/lang/VMSystem","makeStandardErrorStream"):VMSystem_makeStandardErrorStream,
            ("java/lang/VMThrowable","fillInStackTrace"):VMThrowable_fillInStackTrace,
            ("java/lang/VMThrowable","getStackTrace"):VMThrowable_getStackTrace,
            ("java/lang/VMCompiler","compileClass"):VMCompiler_compileClass,
            ("java/lang/VMCompiler","compileClasses"):VMCompiler_compileClasses,
            ("java/lang/VMCompiler","command"):VMCompiler_command,
            ("java/lang/VMCompiler","enable"):VMCompiler_enable,
            ("java/lang/VMCompiler","disable"):VMCompiler_disable,
            #("java/lang/VMDouble","doubleToRawLongBits"):VMDouble_doubleToRawLongBits,
            #("java/lang/VMDouble","longBitsToDouble"):VMDouble_longBitsToDouble,
            #("java/lang/VMDouble","toString"):VMDouble_toString,
            #("java/lang/VMDouble","initIDs"):VMDouble_initIDs,
            #("java/lang/VMDouble","parseDouble"):VMDouble_parseDouble,
            #("java/lang/VMFloat","floatToRawIntBits"):VMFloat_floatToRawIntBits,
            #("java/lang/VMFloat","intBitsToFloat"):VMFloat_intBitsToFloat,
            ("java/lang/VMProcess","nativeSpawn"):VMProcess_nativeSpawn,
            ("java/lang/VMProcess","nativeReap"):VMProcess_nativeReap,
            ("java/lang/VMProcess","nativeKill"):VMProcess_nativeKill,
            ("java/lang/VMRuntime", "availableProcessors"):VMRuntime_availableProcessors,
            ("java/lang/VMRuntime", "freeMemory"):VMRuntime_freeMemory,
            ("java/lang/VMRuntime", "totalMemory"):VMRuntime_totalMemory,
            ("java/lang/VMRuntime", "maxMemory"):VMRuntime_maxMemory,
            ("java/lang/VMRuntime", "gc"):VMRuntime_gc,
            ("java/lang/VMRuntime", "runFinalization"):VMRuntime_runFinalization,
            ("java/lang/VMRuntime", "runFinalizationForExit"):VMRuntime_runFinalizationForExit,
            ("java/lang/VMRuntime", "traceInstructions"):VMRuntime_traceInstructions,
            ("java/lang/VMRuntime", "traceMethodCalls"):VMRuntime_traceMethodCalls,
            ("java/lang/VMRuntime", "runFinalizersOnExit"):VMRuntime_runFinalizersOnExit,
            ("java/lang/VMRuntime", "exit"):VMRuntime_exit,
            ("java/lang/VMRuntime", "nativeLoad"):VMRuntime_nativeLoad,
            ("java/lang/VMRuntime", "mapLibraryName"):VMRuntime_mapLibraryName,
            ("java/lang/VMThread", "start"):VMThread_start,
            ("java/lang/VMThread", "interrupt"):VMThread_interrupt,
            ("java/lang/VMThread", "isInterrupted"):VMThread_isInterrupted,
            ("java/lang/VMThread", "suspend"):VMThread_suspend,
            ("java/lang/VMThread", "resume"):VMThread_resume,
            ("java/lang/VMThread", "nativeSetPriority"):VMThread_nativeSetPriority,
            ("java/lang/VMThread", "nativeStop"):VMThread_nativeStop,
            ("java/lang/VMThread", "getState"):VMThread_getState,
            ("java/lang/VMThread", "currentThread"):VMThread_currentThread,
            ("java/lang/VMThread", "yield"):VMThread_yield,
            ("java/lang/VMThread", "interrupted"):VMThread_interrupted,
            ("java/lang/VMThread", "countStackFrame"):VMThread_countStackFrame,
            ("gnu/classpath/VMStackWalker", "getClassContext"):VMStackWalker_getClassContext,
            ("gnu/classpath/VMStackWalker", "getCallingClass"):VMStackWalker_getCallingClass,
            ("gnu/classpath/VMStackWalker", "getCallingClassLoader"):VMStackWalker_getCallingClassLoader,
            ("gnu/classpath/VMSystemProperties","preInit"):VMSystemProperties_preInit,
            #("gnu/classpath/VMSystemProperties","postInit"):VMSystemProperties_postInit,
            # replaced gnu/classpath by sun/misc
            # I assume that this is an error in gcp
            ("sun/misc/Unsafe","objectFieldOffset"): Unsafe_objectFieldOffset,
            ("sun/misc/Unsafe","compareAndSwap"): Unsafe_compareAndSwap,
            ("sun/misc/Unsafe","put"): Unsafe_put,
            ("sun/misc/Unsafe","get"): Unsafe_get,
            ("sun/misc/Unsafe","arrayBaseOffset"): Unsafe_arrayBaseOffset,
            ("sun/misc/Unsafe","park"): Unsafe_park,
            ("java/lang/VMMath","sin"):VMMath_sin,
            ("java/lang/VMMath","cos"):VMMath_cos,
            ("java/lang/VMMath","tan"):VMMath_tan,
            ("java/lang/VMMath","acos"):VMMath_acos,
            ("java/lang/VMMath","asin"):VMMath_asin,
            ("java/lang/VMMath","atan"):VMMath_atan,
            ("java/lang/VMMath","atan2"):VMMath_atan2,
            ("java/lang/VMMath","exp"):VMMath_exp,
            ("java/lang/VMMath","log"):VMMath_log,
            ("java/lang/VMMath","pow"):VMMath_pow,
            ("java/lang/VMMath","sqrt"):VMMath_sqrt,
            ("java/lang/VMMath","ceil"):VMMath_ceil,
            ("java/lang/VMMath","floor"):VMMath_floor,
            ("java/lang/VMMath","sinh"):VMMath_sinh,
            ("java/lang/VMMath","cosh"):VMMath_cosh,
            ("java/lang/VMMath","tanh"):VMMath_tanh,
            ("java/lang/VMMath","log10"):VMMath_log10,
            ("java/lang/VMMath","hypot"):VMMath_hypot,
            ("java/lang/VMMath","log1p"):VMMath_log1p,
            ("java/lang/VMMath","expm1"):VMMath_expm1,
            ("java/lang/VMMath","IEEEremainder"):VMMath_IEEEremainder,
            ("java/lang/VMMath","cbrt"):VMMath_cbrt,
            ("java/lang/VMMath","rint"):VMMath_rint,
            ("java/io/VMFile", "lastModified"):VMFile_lastModified,
            ("java/io/VMFile", "setReadOnly"):VMFile_setReadOnly,
            ("java/io/VMFile", "create"):VMFile_create,
            ("java/io/VMFile", "_list"):VMFile_list,
            ("java/io/VMFile", "renameTo"):VMFile_renameTo,
            ("java/io/VMFile", "length"):VMFile_length,
            ("java/io/VMFile", "exists"):VMFile_exists,
            ("java/io/VMFile", "delete"):VMFile_delete,
            ("java/io/VMFile", "setLastModified"):VMFile_setLastModified,
            ("java/io/VMFile", "mkdir"):VMFile_mkdir,
            ("java/io/VMFile", "isFile"):VMFile_isFile,
            ("java/io/VMFile", "canWrite"):VMFile_canWrite,
            ("java/io/VMFile", "canRead"):VMFile_canRead,
            ("java/io/VMFile", "isDirectory"):VMFile_isDirectory,
            ("java/io/VMFile", "canWriteDirectory"):VMFile_canWriteDirectory,
            ("java/io/VMFile", "listRoots"):VMFile_listRoots,
            ("java/io/VMFile", "isHidden"):VMFile_isHidden,
            ("java/io/VMFile", "getName"):VMFile_getName,
            ("java/io/VMFile", "getCanonicalForm"):VMFile_getCanonicalForm,
            #("java/security/VMAccessController","pushContext"): VMAccessController_pushContext,
            #("java/security/VMAccessController","popContext"): VMAccessController_popContext,
            #("java/security/VMAccessController","getContext"): VMAccessController_getContext,
            #("java/security/VMAccessController","getStack"): VMAccessController_getStack,
            ("java/net/VMInetAddress","getLocalHostname"): VMInetAddress_getLocalHostname,
            ("java/net/VMInetAddress","lookupInaddrAny"): VMInetAddress_lookupInaddrAny,
            ("java/net/VMInetAddress","getHostByAddr"): VMInetAddress_getHostByAddr,
            ("java/net/VMInetAddress","getHostByName"): VMInetAddress_getHostByName,
            ("java/nio/VMDirectByteBuffer","init"): VMDirectByteBuffer_init,
            ("java/nio/VMDirectByteBuffer","allocate"): VMDirectByteBuffer_allocate,
            ("java/nio/VMDirectByteBuffer","free"): VMDirectByteBuffer_free,
            ("java/nio/VMDirectByteBuffer","get"): VMDirectByteBuffer_get,
            ("java/nio/VMDirectByteBuffer","put"): VMDirectByteBuffer_put,
            ("java/nio/VMDirectByteBuffer","adjustAddress"): VMDirectByteBuffer_adjustAddress,
            ("java/nio/VMDirectByteBuffer","shiftDown"): VMDirectByteBuffer_shiftDown,
            ("java/nio/channels/VMChannels","createStream"): VMChannels_createStream,
            ("java/nio/channels/VMChannels","newInputStream"): VMChannels_newInputStream,
            ("java/nio/channels/VMChannels","newOutputStream"): VMChannels_newOutputStream,
            ("gnu/java/lang/VMInstrumentationImpl","isRedefineClassesSupported"): VMInstrumentationImpl_isRedefineClassesSupported,
            ("gnu/java/lang/VMInstrumentationImpl","redefineClasses"): VMInstrumentationImpl_redefineClasses,
            ("gnu/java/lang/VMInstrumentationImpl","getAllLoadedClass"): VMInstrumentationImpl_getAllLoadedClass,
            ("gnu/java/lang/VMInstrumentationImpl","getInitiatedClass"): VMInstrumentationImpl_getInitiatedClass,
            ("gnu/java/lang/VMInstrumentationImpl","getObjectSize"): VMInstrumentationImpl_getObjectSize,
            ("gnu/java/lang/management/VMRuntimeMXBeanImpl","getInputArguments"): VMRuntimeMXBeanImpl_getInputArguments,
            ("gnu/java/lang/management/VMRuntimeMXBeanImpl","getName"): VMRuntimeMXBeanImpl_getName,
            ("gnu/java/lang/management/VMRuntimeMXBeanImpl","getStartTime"): VMRuntimeMXBeanImpl_getStartTime,
            ("gnu/java/lang/management/VMClassLoadingMXBeanImpl","getLoadedClassCount"): VMClassLoadingMXBeanImpl_getLoadedClassCount,
            ("gnu/java/lang/management/VMClassLoadingMXBeanImpl","getUnloadedClassCount"): VMClassLoadingMXBeanImpl_getUnloadedClassCount,
            ("gnu/java/lang/management/VMClassLoadingMXBeanImpl","isVerbose"): VMClassLoadingMXBeanImpl_isVerbose,
            ("gnu/java/lang/management/VMClassLoadingMXBeanImpl","setVerbose"): VMClassLoadingMXBeanImpl_setVerbose,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","findDeadlockedThreads"): VMThreadMXBeanImpl_findDeadlockedThreads,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","findMonitorDeadlockedThreads"): VMThreadMXBeanImpl_findMonitorDeadlockedThreads,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getAllThreads"): VMThreadMXBeanImpl_getAllThreads,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getAllThreadIds"): VMThreadMXBeanImpl_getAllThreadIds,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getAllThreadIds"): VMThreadMXBeanImpl_getAllThreadIds,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getCurrentThreadCpuTime"): VMThreadMXBeanImpl_getCurrentThreadCpuTime,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getCurrentThreadUserTime"): VMThreadMXBeanImpl_getCurrentThreadUserTime,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getDaemonThreadCount"): VMThreadMXBeanImpl_getDaemonThreadCount,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getLockInfo"): VMThreadMXBeanImpl_getLockInfo,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getMonitorInfo"): VMThreadMXBeanImpl_getMonitorInfo,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getPeakThreadCount"): VMThreadMXBeanImpl_getPeakThreadCount,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","resetPeakThreadCount"): VMThreadMXBeanImpl_resetPeakThreadCount,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getThreadCount"): VMThreadMXBeanImpl_getThreadCount,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getThreadCpuTime"): VMThreadMXBeanImpl_getThreadCpuTime,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getThreadUserTime"): VMThreadMXBeanImpl_getThreadUserTime,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getThreadInfoForId"): VMThreadMXBeanImpl_getThreadInfoForId,
            ("gnu/java/lang/management/VMThreadMXBeanImpl","getTotalStartedThreadCount"): VMThreadMXBeanImpl_getTotalStartedThreadCount,
            ("gnu/java/lang/management/VMMemoryMXBeanImpl","getHeapMemoryUsage"): VMMemoryMXBeanImpl_getHeapMemoryUsage,
            ("gnu/java/lang/management/VMMemoryMXBeanImpl","getNonHeapMemoryUsage"): VMMemoryMXBeanImpl_getNonHeapMemoryUsage,
            ("gnu/java/lang/management/VMMemoryMXBeanImpl","getObjectPendingFinalizationCount"): VMMemoryMXBeanImpl_getObjectPendingFinalizationCount,
            ("gnu/java/lang/management/VMMemoryMXBeanImpl","isVerbose"): VMMemoryMXBeanImpl_isVerbose,
            ("gnu/java/lang/management/VMMemoryMXBeanImpl","setVerbose"): VMMemoryMXBeanImpl_setVerbose,
            ("gnu/java/lang/management/VMCompilationMXBeanImpl","getTotalCompilationTime"): VMCompilationMXBeanImpl_getTotalCompilationTime,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getCollectionUsage"): VMMemoryPoolMXBeanImpl_getCollectionUsage,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getCollectionUsageThreshold"): VMMemoryPoolMXBeanImpl_getCollectionUsageThreshold,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getCollectionUsageThresholdCount"): VMMemoryPoolMXBeanImpl_getCollectionUsageThresholdCount,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getMemoryManagerNames"): VMMemoryPoolMXBeanImpl_getMemoryManagerNames,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getPeakUsage"): VMMemoryPoolMXBeanImpl_getPeakUsage,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getType"): VMMemoryPoolMXBeanImpl_getType,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getUsage"): VMMemoryPoolMXBeanImpl_getUsage,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getUsageThreshold"): VMMemoryPoolMXBeanImpl_getUsageThreshold,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","getUsageThresholdCount"): VMMemoryPoolMXBeanImpl_getUsageThresholdCount,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","isValid"): VMMemoryPoolMXBeanImpl_isValid,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","resetPeakUsage"): VMMemoryPoolMXBeanImpl_resetPeakUsage,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","setCollectionUsageThreshold"): VMMemoryPoolMXBeanImpl_setCollectionUsageThreshold,
            ("gnu/java/lang/management/VMMemoryPoolMXBeanImpl","setUsageThreshold"): VMMemoryPoolMXBeanImpl_setUsageThreshold,
            ("gnu/java/lang/management/VMMemoryManagerMXBeanImpl","getMemoryPoolNames"): VMMemoryManagerMXBeanImpl_getMemoryPoolNames,
            ("gnu/java/lang/management/VMMemoryManagerMXBeanImpl","isValid"): VMMemoryManagerMXBeanImpl_isValid,
            ("gnu/java/lang/management/VMGarbageCollectorMXBeanImpl","getCollectionCount"): VMGarbageCollectorMXBeanImpl_getCollectionCount,
            ("gnu/java/lang/management/VMGarbageCollectorMXBeanImpl","getCollectionTime"): VMGarbageCollectorMXBeanImpl_getCollectionTime,
            ("java/lang/management/VMManagementFactory","getMemoryPoolNames"): VMManagementFactory_getMemoryPoolNames,
            ("java/lang/management/VMManagementFactory","getMemoryManagerNames"): VMManagementFactory_getMemoryManagerNames,
            ("java/lang/management/VMManagementFactory","getGarbageCollectorNames"): VMManagementFactory_getGarbageCollectorNames,
            }
#def hook(classname, methodname, result, args=None):
#    def wrapper(function):
#        allhooks[(classname, methodname)] = function
#    return wrapper


#@hook("java/lang/VMMath", "sin", "double", ["double"])
#def implementation(value):
#    return math.sin(value)
