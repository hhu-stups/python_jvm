# -*- coding: utf-8 -*-
import new, sys, os, types, native, thread

#import classfile, classloader, javaclasses

from classloader import JClass, descriptor # eg. for putfield
from helper import make_String, throw_NullPointerException, throw_ArithmeticException, throw_ArrayIndexOutOfBoundsException, throw_ClassCastException
from hooks import HOOKS, vmobject_getClass_helper
from objectmodel import TypedMap, Objectref, Classref, Arrayref, Stack, JObject, JException, JArrayClass
from native import current_classloader, env_ptr # for jni


from ctypes import py_object, c_int, c_float, c_long, c_double, c_char
from rpython.rlib.rarithmetic import r_singlefloat, r_longlong
from rpython.rlib.objectmodel import instantiate

# for threading:
interp_lock = thread.allocate_lock()
opcodes_count = 0
OPCODES_MAX = 2**8


# JVMS: 4.4.4 
# cast int (n) to IEEE 754 float (num)
# TODO: NaN infinety
def float_parse(n):
    if(n>>31)==0:
        s = 1
    else:
        s = -1
    e = n>>23 & 0xff
    if e==0:
        m = n & 0x7fffff << 1
    else:
        m = (n & 0x7fffff) | 0x800000
    num = s*m*2**(e-150)
    return r_singlefloat(num)

# JVMS: 4.4.5
def parse_double(n):
    if(n>>63)==0:
     s = 1
    else:
        s = -1
    e = n>>52 & 0x7ff
    if e==0:
        m = n & 0xfffffffffffff << 1
    else:
        m = (n & 0xfffffffffffff) | 0x10000000000000
    num = s*m*2**(e-1075)
    return num 

def intmask(n):  # mask to a 32-bit int
    n = n & 0xFFFFFFFF
    if n >= 0x80000000:
        n -= 0x100000000
    return int(n)

def shortmask(n):
    n = n & 0xFFFF
    if n >= 0x8000:
        n -= 0x10000
    return int(n)

def signedbytemask(n):
    n = n & 0xFF
    if n >= 0x80:
        n -= 0x100
    return int(n)

def cast_char(c):
    if isinstance(c, int):
        return unichr(c)
    return c

# adds to the AbstractClassLoader just one method
# which is able to run Frames
class ClassLoader(classloader.AbstractClassLoader):

    def __init__(self, path):
        classloader.AbstractClassLoader.__init__(self, path)
        # XXX: do not use classref. maybe a problem even if only intern
        self.called_classes = Arrayref([],None, self.getclass("[Ljava.lang.Class;")) # needed for e.g stackwalker hook
        self.extern_libs = {}

    # This method is called by the invoke-virtual, 
    # -special, -staticmethods (or native.py/JNI) and at the jvm-start
    # It executes the bytecode by using a Frame
    # TODO: refactor this method
    def invoke_method(self, cls, method, descr, args):
        # remember caller
        native_args = args.clone()
        classname, supercls = self.parse_parameter(cls)
        jcls = JClass(classname, supercls, cls)
        self.called_classes.arrayref.insert(0,Classref(self.getclass("java/lang/Class"), True, jcls, self))

        const = cls.constant_pool
        classNameIndex = const[cls.this_class].name_index
        self.currentclsName = clsName = const[classNameIndex]
        self.currentmethodName = methodName = const[method.name_index]

        argcount = len(descr) - 1 # one elem. is the return value
        int_locals = {}
        ref_locals = {}
        float_locals = {}
        double_locals = {}
        long_locals = {}
        i = 0
        # safe "this" reference (invisible in descr)
        if not (method.access_flags & method.ACC_STATIC):
            arg = args.pop()
            ref_locals[i] = arg
            i = i + 1 
        #assert len(args) == argcount
        #char_locals = {}
        # index index in the descr list, used to get this obejct
        # i index in the stacks, used to handle 2x values
        #args.print_stack()
        for index in range(argcount):
            arg = args.pop()

            if descr[index] == "int" or descr[index]=="boolean" or descr[index] == "short" or descr[index]=="byte":
                int_locals[i] = arg
                assert isinstance(arg,int)
            elif descr[index] == "char":
                #print arg
                #char_locals[i] = arg
                #if isinstance(arg, str):
                arg = ord(arg)
                int_locals[i] = arg
            elif descr[index] == "float":
                float_locals[i] = r_singlefloat(arg)
            elif descr[index] == "long":
                long_locals[i] = r_longlong(arg)
                i = i+1              # long needs two stack places
            elif descr[index] == "double":
                double_locals[i] = arg
                i = i+1               # doubles reserve two places
                assert isinstance(arg,float) #python float ==c double
            else:
                ref_locals[i] = arg
                assert not isinstance(arg,r_singlefloat)
                assert not isinstance(arg,int)
                assert not isinstance(arg,float)
                assert not isinstance(arg,r_longlong)
            i = i + 1

        locals = TypedMap()
        #locals.set_char_map(char_locals)
        locals.set_int_map(int_locals)
        locals.set_ref_map(ref_locals)
        locals.set_float_map(float_locals)
        locals.set_double_map(double_locals)
        locals.set_long_map(long_locals)

        if method.access_flags & method.ACC_SYNCHRONIZED:
            if not (method.access_flags & method.ACC_STATIC):
                monitor = ref_locals[0]
                from java_threading import monitorenter
                monitorenter(self, monitor)
            #else:
            #    raise NotImplemented("STATIC SYNCHRONIZED METHODS")


        # hook test
        #print "invoking methodname:",methodName,str(descr)
        # print "invoking class:",clsName
        #if methodName == "<init>" and clsName == "java/lang/String":
        #    print locals.print_map()
        #    print locals.get(0,"ref").jcls.__name__
        #    raise Exception("A")
        #print
        #if methodName == "getProperty":
        #    arrayr=locals.get(1,"ref").fields.get(unicode("value"),"array")
        #    print arrayr.arrayref
        #    print "locals:",locals.print_map()
        # if hook:run it
        if (clsName, methodName) in HOOKS:
            # use gnucp native File-impl. if posix
            if not (os.name == "posix" and clsName == "java/io/VMFile"):
                hook_method = HOOKS[(clsName,methodName)]
                return hook_method(locals, self, cls, method)
        # if native, call native method
        if (method.access_flags & method.ACC_NATIVE):
            return self.call_native(clsName, methodName, descr, native_args, jcls, method)
        # else run bytecode
        self.called_classes.arrayref.insert(0,Classref(self.getclass("java/lang/Class"), True, jcls, self))
        # create Frame
        frame = Frame(self, cls, method)
        frame.set_locals(locals)
        #try:
        re = frame.run()

        if method.access_flags & method.ACC_SYNCHRONIZED:
            if not (method.access_flags & method.ACC_STATIC):
                monitor = ref_locals[0]
                from java_threading import monitorexit
                monitorexit(monitor)
            #else:
            #    raise NotImplemented("STATIC SYNCHRONIZED METHODS")

        #print "leaving methodname:",methodName
        #print "leaving class:",clsName
        self.called_classes.arrayref.pop()
        return re
        #except JException, je: 
        #print "exception in methodname:",methodName
        #print "exception in class:",clsName
        #    self.called_classes.arrayref.pop()
        #    return je

    def init_static(self, pycls, method):
        frame = Frame(self, pycls, method)
        frame.run()

    def arg_to_ctype(self, arg):
        if arg == None:
            return None
        elif arg == "int" or arg == "byte" or arg == "short" or arg =="boolean":
            return c_int
        elif arg == "char":
            return c_char
        elif arg == "float":
            return c_float
        elif arg == "long":
            return c_long
        elif arg == "double":
            return c_double
        else:
            return py_object

    def call_native(self, clsName, methodName, descr, args, jcls, method):
        native.current_classloader = self # set global var of native.py
        real_method_name = "Java_"+ clsName.replace("_","_1").replace(";","_2").replace("[","_3").replace("/","_")+"_"+methodName.replace("_","_1").replace(";","_2").replace("[","_3")
        cfunction = None
        for lib in self.extern_libs.values():
            try:
                cfunction = eval("lib."+real_method_name)
                break
            except AttributeError:
                continue
        assert not cfunction == None

        # last arg is return value
        cfunction.restype = self.arg_to_ctype(descr.pop())
        if not (method.access_flags & method.ACC_STATIC):
            objref = args.pop()
        else:
            objref = Classref(self.getclass("java/lang/Class"), True, jcls, self) # TODO: this is a classref
        string = "cfunction(env_ptr, py_object(objref)"
        for i in range(len(descr)):
            ctype = self.arg_to_ctype(descr[i])
            string += ", "+str(ctype.__name__)+"(args.pop())"
        string += ")"
        #print real_method_name
        #print self.extern_libs
        #print cfunction
        #print "desc",descr
        #print "loc", args
        #print objref
        #print string
        # set our "exception-memory" to none
        native.exception_after_native_call = None
        result = eval(string) # execute native call
        #print result
        # the native call has created an Exception
        if native.exception_after_native_call:
            # this exception will be handled by the caller
            jexception = native.exception_after_native_call
            raise jexception
        #print "JNI RES:",result
        return result

# FIXME use r_singlefloat and r_long_long
# javaclasses > print has problems with this types
DESCR_CAST = {'byte': signedbytemask,
              'char': cast_char,
              'double': float,
              'float': float,#r_singlefloat,
              'int': intmask,
              'long': long,#r_longlong,
              'short': shortmask,
              'boolean': bool,
              }

# FIXME: Frame and interpreter are mixed :(
# After every methodcall, a Stackframe is created
# It executes every Java-Bytecode until a return opcode occurs
class Frame(object):
    intmask = staticmethod(intmask)
    instantiate = staticmethod(instantiate) ## XXX for javaclasses.py
    DESCR_CAST = DESCR_CAST
    DESCR_UNCAST = {'char': ord}

    def __init__(self, loader, cls, method):
        self.loader = loader
        self.cls = cls
        self.const = cls.constant_pool
        self.method = method
        self.co = cls.getattr(method, 'Code', classfile.Code_attribute) # XXX maybe not Rpython
        self.stack = Stack()
        self.locals = TypedMap()

    def run(self):
        global opcodes_count
        global OPCODES_MAX
        global interp_lock
        m_nam = unicode(self.const[self.method.name_index])
        cls_inf = self.const[self.cls.this_class]
        #print "\t", self.const[cls_inf.name_index],":",m_nam
        self.next_instr = 0
        try:
            while True:
                opcodes_count = opcodes_count +1
                if opcodes_count==OPCODES_MAX:
                    opcodes_count = 0 # reset for next thread in que
                    import java_threading 
                    if not java_threading.currentVMThread == "main_no_init":
                        java_threading.currentVMThread.STATE =make_String("WAITING", self.loader)
                    temp = java_threading.currentVMThread
                    #print "inperp:", java_threading.currentVMThread
                    interp_lock.release()
                    
                    # if there is an other thread it will get the
                    # exc. control here!
                    interp_lock.acquire()
                    #TODO: do something if currentVMThread.isInterrupted = True
                    java_threading.currentVMThread = temp
                    if not java_threading.currentVMThread == "main_no_init":
                        java_threading.currentVMThread.STATE =make_String("RUNNABLE", self.loader)
                last_instr = self.next_instr
                num = self.nextbyte()
                opimpl = getattr(self, 'opcode_0x%02x' % (num,)) # XXX not Rpython
                import java_threading
                #print '\t', java_threading.currentVMThread, ":", self.next_instr-1,": ",opimpl.__doc__
                #self.stack.print_stack()
                #print "\t", self.const[cls_inf.name_index],":",m_nam
                try:
                    if opimpl():
                        # this block is only visited after an
                        # jump-opcode
                        self.next_instr = last_instr + 1
                        offset = self.nextsignedword()
                        if num in WIDE_TARGET:
                            offset = (offset << 16) | self.nextword()
                        self.next_instr = last_instr + offset
                except JException, je:
                    #print je.objref.jcls.__name__
                    #print "\t", self.const[cls_inf.name_index],":",m_nam
                    self.handle_exception(je.objref)
        except Return, r:
            return r.retval

    def set_locals(self, locals):
        self.locals = locals

    def nextbyte(self):
        index = self.next_instr
        self.next_instr = index + 1
        return ord(self.co.code[index])

    def nextsignedbyte(self):
        return signedbytemask(self.nextbyte())

    def nextword(self):
        index = self.next_instr
        self.next_instr = index + 2
        return (ord(self.co.code[index]) << 8) | ord(self.co.code[index + 1])

    def nextdoubleword(self):
        index = self.next_instr
        self.next_instr = index + 4
        return (ord(self.co.code[index]) << 24) | (ord(self.co.code[index + 1]) << 16) | (ord(self.co.code[index + 2]) << 8) | ord(self.co.code[index + 3])

    def nextsignedword(self):
        return shortmask(self.nextword())

    def opcode_0x00(self):
        "nop"

    # JVMS: Push null (== None)
    def opcode_0x01(self):
        "aconst_null"
        self.stack.push(None)

    def opcode_0x02(self):
        "iconst_m1"
        self.stack.push(-1)

    def opcode_0x03(self):
        "iconst_0"
        self.stack.push(0)

    def opcode_0x04(self):
        "iconst_1"
        self.stack.push(1)

    def opcode_0x05(self):
        "iconst_2"
        self.stack.push(2)

    def opcode_0x06(self):
        "iconst_3"
        self.stack.push(3)

    def opcode_0x07(self):
        "iconst_4"
        self.stack.push(4)

    def opcode_0x08(self):
        "iconst_5"
        self.stack.push(5)

    def opcode_0x09(self):
        "lconst_0"
        self.stack.push(r_longlong(0))

    def opcode_0x0a(self):
        "lconst_1"
        self.stack.push(r_longlong(1))

    def opcode_0x0b(self):
        "fconst_0"
        self.stack.push(r_singlefloat(0.0))

    def opcode_0x0c(self):
        "fconst_1"
        self.stack.push(r_singlefloat(1.0))

    def opcode_0x0d(self):
        "fconst_2"
        self.stack.push(r_singlefloat(2.0))

    def opcode_0x0e(self):
        "dconst_0"
        self.stack.push(0.0)

    def opcode_0x0f(self):
        "dconst_1"
        self.stack.push(1.0)

    def opcode_0x10(self):
        "bipush"
        self.stack.push(self.nextsignedbyte())

    # JVMS: Push short
    def opcode_0x11(self):
        "sipush"
        self.stack.push(self.nextsignedword())

    def opcode_0x12(self):
        "ldc"
        index = self.nextbyte()
        const = self.const[index]
        if isinstance(const, classfile.CONSTANT_String_info):
            string = self.const[const.string_index]
            objectref = make_String(string, self.loader)
            self.stack.push(objectref)
        elif isinstance(const, classfile.CONSTANT_Float):
            self.stack.push(float_parse(const.bytes)) ### TODO: floatmask
        #maybe this is only used in ldc_w
        elif isinstance(const, classfile.CONSTANT_Class_info):
            name = self.const[const.name_index]
            jcls = self.loader.getclass(name)
            objectref = vmobject_getClass_helper(jcls, self.loader)
            self.stack.push(objectref)
        else:# XXX other types?
            self.stack.push(intmask(const.bytes))

    def opcode_0x13(self):
        "ldc_w"
        index = self.nextword()
        const = self.const[index]
        if isinstance(const, classfile.CONSTANT_String_info):
            string = self.const[const.string_index]
            objectref = make_String(string, self.loader)
            #print objectref
            self.stack.push(objectref)
        elif isinstance(const, classfile.CONSTANT_Float):
            self.stack.push(float_parse(const.bytes)) ### TODO: floatmask
        elif isinstance(const, classfile.CONSTANT_Class_info):
            name = self.const[const.name_index]
            jcls = self.loader.getclass(name, self.method)# for inner-classes
            objectref = vmobject_getClass_helper(jcls, self.loader)
            self.stack.push(objectref)
        else:# XXX other types?
            self.stack.push(intmask(const.bytes))
        #raise NotImplementedError("ldc_w")

    def opcode_0x14(self):
        "ldc2_w"
        indexbyte1 = self.nextbyte()
        indexbyte2 = self.nextbyte()
        index = (indexbyte1 << 8) | indexbyte2
        const = self.const[index]
        if isinstance(const, classfile.CONSTANT_Double):
            int_value =(const.high_bytes << 32) | const.low_bytes
            self.stack.push(parse_double(int_value))
        elif isinstance(const, classfile.CONSTANT_Long_Info):
            value =(const.high_bytes << 32) | const.low_bytes
            self.stack.push(r_longlong(value))
        else:
            raise Exception("unknown constant type")

    def opcode_0x15(self):
        "iload"
        loc = self.nextbyte()
        self.stack.push(self.locals.get(loc,"int"))

    def opcode_0x16(self):
        "lload"
        loc = self.nextbyte()
        self.stack.push(self.locals.get(loc,"long"))

    def opcode_0x17(self):
        "fload"
        loc = self.nextbyte()
        self.stack.push(self.locals.get(loc,"float"))

    def opcode_0x18(self):
        "dload"
        loc = self.nextbyte()
        self.stack.push(self.locals.get(loc,"double"))

    # JVMS: Load reference from local variable
    def opcode_0x19(self):
        "aload"
        loc = self.nextbyte()
        self.stack.push(self.locals.get(loc,"ref"))

    def opcode_0x1a(self):
        "iload_0"
        self.stack.push(self.locals.get(0,"int"))

    def opcode_0x1b(self):
        "iload_1"
        self.stack.push(self.locals.get(1,"int"))

    def opcode_0x1c(self):
        "iload_2"
        self.stack.push(self.locals.get(2,"int"))

    def opcode_0x1d(self):
        "iload_3"
        self.stack.push(self.locals.get(3,"int"))

    def opcode_0x1e(self):
        "lload_0"
        self.stack.push(self.locals.get(0,"long"))

    def opcode_0x1f(self):
        "lload_1"
        self.stack.push(self.locals.get(1,"long"))

    def opcode_0x20(self):
        "lload_2"
        self.stack.push(self.locals.get(2,"long"))

    def opcode_0x21(self):
        "lload_3"
        self.stack.push(self.locals.get(3,"long"))

    def opcode_0x22(self):
        "fload_0"
        self.stack.push(self.locals.get(0,"float"))

    def opcode_0x23(self):
        "fload_1"
        self.stack.push(self.locals.get(1,"float"))

    def opcode_0x24(self):
        "fload_2"
        self.stack.push(self.locals.get(2,"float"))

    def opcode_0x25(self):
        "fload_3"
        self.stack.push(self.locals.get(3,"float"))

    def opcode_0x26(self):
        "dload_0"
        self.stack.push(self.locals.get(0,"double"))

    def opcode_0x27(self):
        "dload_1"
        self.stack.push(self.locals.get(1,"double"))

    def opcode_0x28(self):
        "dload_2"
        self.stack.push(self.locals.get(2,"double"))

    def opcode_0x29(self):
        "dload_3"
        self.stack.push(self.locals.get(3,"double"))

    # JVMS: Load reference from local variable
    def opcode_0x2a(self):
        "aload_0"
        self.stack.push(self.locals.get(0,"ref"))

    def opcode_0x2b(self):
        "aload_1"
        self.stack.push(self.locals.get(1,"ref"))

    def opcode_0x2c(self):
        "aload_2"
        self.stack.push(self.locals.get(2,"ref"))

    def opcode_0x2d(self):
        "aload_3"
        self.stack.push(self.locals.get(3,"ref"))

    # JVMS: Load int from array
    def opcode_0x2e(self):
        "iaload"
        index = self.stack.pop()
        array = self.stack.pop()
        if array==None:
            throw_NullPointerException(self.loader)
        if not index < len(array.arrayref):
            throw_ArrayIndexOutOfBoundsException(self.loader, index)
        self.stack.push(array.arrayref[index])

    def opcode_0x2f(self):
        "laload"
        index = self.stack.pop()
        array = self.stack.pop()
        if array==None:
            throw_NullPointerException(self.loader)
        if not index < len(array.arrayref):
            throw_ArrayIndexOutOfBoundsException(self.loader, index)
        self.stack.push(array.arrayref[index])

    def opcode_0x30(self):
        "faload"
        index = self.stack.pop()
        array = self.stack.pop()
        if array==None:
            throw_NullPointerException(self.loader)
        if not index < len(array.arrayref):
            throw_ArrayIndexOutOfBoundsException(self.loader, index)
        self.stack.push(array.arrayref[index])

    def opcode_0x31(self):
        "daload"
        index = self.stack.pop()
        array = self.stack.pop()
        if array==None:
            throw_NullPointerException(self.loader)
        if not index < len(array.arrayref):
            throw_ArrayIndexOutOfBoundsException(self.loader, index)
        self.stack.push(array.arrayref[index])

    def opcode_0x32(self):
        "aaload"
        index = self.stack.pop()
        array = self.stack.pop()
        if array==None:
            throw_NullPointerException(self.loader)
        if not index < len(array.arrayref):
            throw_ArrayIndexOutOfBoundsException(self.loader, index)
        #print "aa",array.arrayref[index].jcls.__name__
        #array.arrayref[index].fields.print_map()
        self.stack.push(array.arrayref[index])

    # JVMS: Load byte or boolean from array
    def opcode_0x33(self):
        "baload"
        index = self.stack.pop()
        array = self.stack.pop()
        self.stack.push(array.arrayref[index])

    def opcode_0x34(self):
        "caload"
        index = self.stack.pop()
        array = self.stack.pop()
        #print "CA:",index
        self.stack.push(self.DESCR_UNCAST['char'](array.arrayref[index]))

    def opcode_0x35(self):
        "saload"
        index = self.stack.pop()
        array = self.stack.pop()
        self.stack.push(array.arrayref[index])

    def opcode_0x36(self):
        "istore"
        loc = self.nextbyte()
        self.locals.set(loc, self.stack.pop(), "int")

    def opcode_0x37(self):
        "lstore"
        loc = self.nextbyte()
        self.locals.set(loc, self.stack.pop(), "long")

    def opcode_0x38(self):
        "fstore"
        loc = self.nextbyte()
        self.locals.set(loc, self.stack.pop(), "float")

    def opcode_0x39(self):
        "dstore"
        loc = self.nextbyte()
        self.locals.set(loc, self.stack.pop(), "double")

    def opcode_0x3a(self):
        "astore"
        loc = self.nextbyte()
        self.locals.set(loc, self.stack.pop(), "ref")

    def opcode_0x3b(self):
        "istore_0"
        self.locals.set(0, self.stack.pop(), "int")

    def opcode_0x3c(self):
        "istore_1"
        self.locals.set(1, self.stack.pop(), "int")

    def opcode_0x3d(self):
        "istore_2"
        self.locals.set(2, self.stack.pop(), "int")

    def opcode_0x3e(self):
        "istore_3"
        self.locals.set(3, self.stack.pop(), "int")

    def opcode_0x3f(self):
        "lstore_0"
        self.locals.set(0, self.stack.pop(), "long")

    def opcode_0x40(self):
        "lstore_1"
        self.locals.set(1, self.stack.pop(), "long")

    def opcode_0x41(self):
        "lstore_2"
        self.locals.set(2, self.stack.pop(), "long")

    def opcode_0x42(self):
        "lstore_3"
        self.locals.set(3, self.stack.pop(), "long")

    def opcode_0x43(self):
        "fstore_0"
        self.locals.set(0, self.stack.pop(), "float")

    def opcode_0x44(self):
        "fstore_1"
        self.locals.set(1, self.stack.pop(), "float")

    def opcode_0x45(self):
        "fstore_2"
        self.locals.set(2, self.stack.pop(), "float")

    def opcode_0x46(self):
        "fstore_3"
        self.locals.set(3, self.stack.pop(), "float")

    def opcode_0x47(self):
        "dstore_0"
        self.locals.set(0, self.stack.pop(), "double")

    def opcode_0x48(self):
        "dstore_1"
        self.locals.set(1, self.stack.pop(), "double")

    def opcode_0x49(self):
        "dstore_2"
        self.locals.set(2, self.stack.pop(), "double")

    def opcode_0x4a(self):
        "dstore_3"
        self.locals.set(3, self.stack.pop(), "double")

    def opcode_0x4b(self):
        "astore_0"
        self.locals.set(0, self.stack.pop(), "ref")

    def opcode_0x4c(self):
        "astore_1"
        self.locals.set(1, self.stack.pop(), "ref")

    def opcode_0x4d(self):
        "astore_2"
        self.locals.set(2, self.stack.pop(), "ref")

    def opcode_0x4e(self):
        "astore_3"
        self.locals.set(3, self.stack.pop(), "ref")

    # JVMS: Store into int array
    def opcode_0x4f(self):
        "iastore"
        value = self.stack.pop()
        index = self.stack.pop()
        array = self.stack.pop()
        array.arrayref[index] = value

    def opcode_0x50(self):
        "lastore"
        value = self.stack.pop()
        index = self.stack.pop()
        array = self.stack.pop()
        array.arrayref[index] = value

    def opcode_0x51(self):
        "fastore"
        value = self.stack.pop()
        index = self.stack.pop()
        array = self.stack.pop()
        array.arrayref[index] = value

    def opcode_0x52(self):
        "dastore"
        value = self.stack.pop()
        index = self.stack.pop()
        array = self.stack.pop()
        array.arrayref[index] = value

    # JVMS: Store into reference array
    def opcode_0x53(self):
        "aastore"
        value = self.stack.pop()
        index = self.stack.pop()
        array = self.stack.pop()
        array.arrayref[index] = value


    def opcode_0x54(self):
        "bastore"
        value = self.stack.pop()
        index = self.stack.pop()
        array = self.stack.pop()
        array.arrayref[index] = value

    def opcode_0x55(self):
        "castore"
        value = self.stack.pop()
        index = self.stack.pop()
        array = self.stack.pop()
        array.arrayref[index] = self.DESCR_CAST['char'](value)

    def opcode_0x56(self):
        "sastore"
        value = self.stack.pop()
        index = self.stack.pop()
        array = self.stack.pop()
        array.arrayref[index] = value

    # This 6 methods are the only ones which access
    # istack, astack..., directly
    # FIXME: no direct use
    def opcode_0x57(self):
        "pop"
        value = self.stack.pop()
        assert not isinstance(value,float)
        assert not isinstance(value,r_longlong)

    # XXX Not Tested yet
    def opcode_0x58(self):
        "pop2"
        value = self.stack.pop()
        # is "value" a category 2 value? 
        # value is not a long and not a double
        if not isinstance(value,float) and not isinstance(value,r_longlong):
            self.stack.pop()


    def opcode_0x59(self):
        "dup"
        last_stack = self.stack.stackhistory[-1]
        if last_stack == "int":
            self.stack.push(self.stack.istack[-1]) 
            return
        elif last_stack == "ref":
            self.stack.push(self.stack.astack[-1]) 
            return
        elif last_stack == "float":
            self.stack.push(self.stack.fstack[-1]) 
            return
        elif last_satck == "long" or last_satck == "double":
            raise Exception("category 2 value on stack")
        else:
            raise Exception("unknown type on stack")

    def opcode_0x5a(self):
        "dup_x1"
        value1 = self.stack.pop()
        value2 = self.stack.pop()
        self.stack.push(value1)
        self.stack.push(value2)
        self.stack.push(value1)

    # Not tested yet
    def opcode_0x5b(self):
        "dup_x2"
        # value1 = self.stack.pop()
        # value2 = self.stack.pop()
        # if not isinstance(value1,float) and not isinstance(value1,r_longlong) and not isinstance(value2,float) and not isinstance(value2,r_longlong):
        #       value3 = self.stack.pop()
        #       self.stack.push(value1)
        #       self.stack.push(value3)
        #       self.stack.push(value2)
        #       self.stack.push(value1)
        # elif not isinstance(value1,float) and not isinstance(value1,r_longlong) and (isinstance(value2,float) or isinstance(value2,r_longlong)):
        #       self.stack.push(value1)
        #       self.stack.push(value2)
        #       self.stack.push(value1)
        # else:
        #       raise Exception("unexpected or unknown type on stack")
        raise NotImplementedError("dup_x2")

    def opcode_0x5c(self):
        "dup2"
        value1 = self.stack.pop()
        if not isinstance(value1,float) and not isinstance(value1,r_longlong):
            value2 = self.stack.pop()
            assert not isinstance(value2,float) and not isinstance(value2,r_longlong)
            self.stack.push(value2)
            self.stack.push(value1)
            self.stack.push(value2)
            self.stack.push(value1)
        elif isinstance(value1,float) or isinstance(value1,r_longlong):
            self.stack.push(value1)
            self.stack.push(value1)
        else:
            raise Exception("unexpected or unknown type on stack")

    # Not tested yet
    def opcode_0x5d(self):
        "dup2_x1"
        # value1 = self.stack.pop()
        # value2 = self.stack.pop()
        # if not isinstance(value1,float) and not isinstance(value1,r_longlong) and not isinstance(value2,float) and not isinstance(value1,r_longlong):
        #       value3 = self.stack.pop()
        #       assert not isinstance(value3,float) and not isinstance(value3,r_longlong)
        #       self.stack.push(value2)
        #       self.stack.push(value1)
        #       self.stack.push(value3)
        #       self.stack.push(value2)
        #       self.stack.push(value1)
        # elif (isinstance(value1,float) or isinstance(value1,r_longlong)) and not isinstance(value2,float) and not isinstance(value2,r_longlong):
        #       self.stack.push(value1)
        #       self.stack.push(value2)
        #       self.stack.push(value1)
        # else:
        #       raise Exception("unexpected or unknown type on stack")
        raise NotImplementedError("dup2_x1")

    # Not tested yet
    def opcode_0x5e(self):
        "dup2_x2"
        # value1 = self.stack.pop()
        # value2 = self.stack.pop()
        # if not isinstance(value1,float) and not isinstance(value1,r_longlong) and not isinstance(value2,float) and not isinstance(value2,r_longlong):
        #       value3 = self.stack.pop()
        #       if not isinstance(value3,float) and not isinstance(value3,r_longlong):
        #               value4 = self.stack.pop()
        #               assert not isinstance(value4,float) and not isinstance(value4,r_longlong)
        #               self.stack.push(value2)
        #               self.stack.push(value1)
        #               self.stack.push(value4)
        #               self.stack.push(value3)
        #               self.stack.push(value2)
        #               self.stack.push(value1)
        #       elif isinstance(value3,float) or isinstance(value3,r_longlong):
        #               self.stack.push(value2)
        #               self.stack.push(value1)
        #               self.stack.push(value3)
        #               self.stack.push(value2)
        #               self.stack.push(value1)
        #       else:
        #               raise Exception("unexpected or unknown type on stack
        # elif (isinstance(value1,float) or isinstance(value1,r_longlong)) and not isinstance(value2,float) and not isinstance(value2,r_longlong):
        #       value3 = self.stack.pop()
        #       assert not isinstance(value3,float) and not isinstance(value3,r_longlong)
        #       self.stack.push(value1)
        #       self.stack.push(value3)
        #       self.stack.push(value2)
        #       self.stack.push(value1)
        # elif (isinstance(value1,float) or isinstance(value1,r_longlong)) and (isinstance(value2,float) or isinstance(value2,r_longlong)):
        #       self.stack.push(value1)
        #       self.stack.push(value2)
        #       self.stack.push(value1)
        # else:
        #       raise Exception("unexpected or unknown type on stack
        raise NotImplementedError("dup2_x2")

    # Not tested yet
    def opcode_0x5f(self):
        "swap"
        # value1 = self.stack.pop()
        # value2 = self.stack.pop()
        # self.stack.push(value1)
        # self.stack.push(value2)
        raise NotImplementedError("swap")

    def opcode_0x60(self):
        "iadd"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(self.intmask(value1 + value2))

    def opcode_0x61(self):
        "ladd"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 + value2)

    def opcode_0x62(self):
        "fadd"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(r_singlefloat(float(value1) + float(value2)))

    def opcode_0x63(self):
        "dadd"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 + value2)

    def opcode_0x64(self):
        "isub"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(self.intmask(value1 - value2))

    def opcode_0x65(self):
        "lsub"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 - value2)

    def opcode_0x66(self):
        "fsub"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(r_singlefloat(float(value1) - float(value2)))

    def opcode_0x67(self):
        "dsub"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 - value2)

    def opcode_0x68(self):
        "imul"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(self.intmask(value1 * value2))

    def opcode_0x69(self):
        "lmul"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 * value2)

    def opcode_0x6a(self):
        "fmul"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(r_singlefloat(float(value1) * float(value2)))

    def opcode_0x6b(self):
        "dmul"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 * value2)

    def opcode_0x6c(self):
        "idiv"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value2==0:
            throw_ArithmeticException(self.loader)
        self.stack.push(intmask(value1 / value2))

    def opcode_0x6d(self):
        "ldiv"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value2==0:
            throw_ArithmeticException(self.loader)
        self.stack.push(value1 / value2)

    def opcode_0x6e(self):
        "fdiv"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if float(value2)==0:
            throw_ArithmeticException(self.loader)
        self.stack.push(r_singlefloat(float(value1) / float(value2)))

    def opcode_0x6f(self):
        "ddiv"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value2==0:
            throw_ArithmeticException(self.loader)
        self.stack.push(value1 / value2)

    def opcode_0x70(self):
        "irem"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value2==0:
            throw_ArithmeticException(self.loader)
        self.stack.push(intmask(value1 % value2))

    def opcode_0x71(self):
        "lrem"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value2==0:
            throw_ArithmeticException(self.loader)
        self.stack.push(value1 % value2)

    def opcode_0x72(self):
        "frem"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if float(value2)==0:
            throw_ArithmeticException(self.loader)
        self.stack.push(r_singlefloat(float(value1) % float(value2)))

    def opcode_0x73(self):
        "drem"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value2==0:
            throw_ArithmeticException(self.loader)
        self.stack.push(value1 % value2)

    def opcode_0x74(self):
        "ineg"
        value = self.stack.pop()
        self.stack.push(intmask(-value))

    def opcode_0x75(self):
        "lneg"
        value = self.stack.pop()
        self.stack.push(-value)

    def opcode_0x76(self):
        "fneg"
        value = self.stack.pop()
        self.stack.push(r_singlefloat(-float(value)))

    def opcode_0x77(self):
        "dneg"
        value = self.stack.pop()
        self.stack.push(-value)

    def opcode_0x78(self):
        "ishl"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(intmask(value1 << value2))

    def opcode_0x79(self):
        "lshl"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 << value2)

    def opcode_0x7a(self):
        "ishr"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        #value1 = value1 & 31
        self.stack.push(intmask(value1 >> value2))

    # TODO: be sure that this is right..
    def opcode_0x7b(self):
        "lshr"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        #value1 = value1 & 31
        self.stack.push(value1 >> value2)

    # logic shift (zero extention)
    def opcode_0x7c(self):
        "iushr"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        s = value2 & 0x1f
        if value1 >0:
            result = (value1 >> s)
        else:
            x = 0
            for i in range(32-s):
                x |= (1 << i)
            result = (value1 >> s) & x
        #print result
        self.stack.push(result)

    def opcode_0x7d(self):
        "lushr"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        s = value2 & 0x3f
        if value1 >0:
            result = (value1 >> s)
        else:
            x = 0
            for i in range(64-s): # XXX
                x |= (1 << i)
            result = (value1 >> s) & x
        self.stack.push(result)

    def opcode_0x7e(self):
        "iand"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 & value2)

    def opcode_0x7f(self):
        "land"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 & value2)

    def opcode_0x80(self):
        "ior"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 | value2)

    def opcode_0x81(self):
        "lor"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 | value2)

    def opcode_0x82(self):
        "ixor"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 ^ value2)

    def opcode_0x83(self):
        "lxor"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        self.stack.push(value1 ^ value2)

    def opcode_0x84(self):
        "iinc"
        index = self.nextbyte()
        const = self.nextsignedbyte()
        value = self.locals.get(index, "int") + const
        self.locals.set(index, value, "int")

    #JVMS: 0x85 - 0x93 casting bytecodes
    def opcode_0x85(self):
        "i2l"
        value = self.stack.pop()
        assert isinstance(value,int)
        self.stack.push(r_longlong(value))

    def opcode_0x86(self):
        "i2f"
        value = self.stack.pop()
        assert isinstance(value,int)
        self.stack.push(r_singlefloat(value))

    def opcode_0x87(self):
        "i2d"
        value = self.stack.pop()
        assert isinstance(value,int)
        self.stack.push(float(value))

    def opcode_0x88(self):
        "l2i"
        value = self.stack.pop()
        self.stack.push(intmask(int(value)))

    def opcode_0x89(self):
        "l2f"
        value = self.stack.pop()
        self.stack.push(r_singlefloat(value))

    def opcode_0x8a(self):
        "l2d"
        value = self.stack.pop()
        self.stack.push(float(value))

    def opcode_0x8b(self):
        "f2i"
        value = self.stack.pop()
        self.stack.push(intmask(int(value.__float__())))

    def opcode_0x8c(self):
        "f2l"
        value = self.stack.pop()
        self.stack.push(r_longlong(value.__float__()))

    def opcode_0x8d(self):
        "f2d"
        value = self.stack.pop()
        self.stack.push(float(value.__float__()))

    def opcode_0x8e(self):
        "d2i"
        value = self.stack.pop()
        self.stack.push(intmask(int(value)))

    def opcode_0x8f(self):
        "d2l"
        value = self.stack.pop()
        self.stack.push(r_longlong(value))

    def opcode_0x90(self):
        "d2f"
        value = self.stack.pop()
        self.stack.push(r_singlefloat(value))

    def opcode_0x91(self):
        "i2b"
        value = self.stack.pop()
        self.stack.push(signedbytemask(value))

    def opcode_0x92(self):
        "i2c"
        # JVMS 3.3.1:
        # int: from -2**31 to 2**31-1
        # char: from 0 to 2**16-1
        value = self.stack.pop()
        if value>(2**16-1): # overflow
            value = value - (2**16)
        self.stack.push(value)

    def opcode_0x93(self):
        "i2s"
        value = self.stack.pop()
        self.stack.push(shortmask(value))

    def opcode_0x94(self):
        "lcmp"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value1>value2:
            self.stack.push(1)
        elif value1==value2:
            self.stack.push(0)
        elif value1<value2:
            self.stack.push(-1)

    # TODO: handled NaN ?
    def opcode_0x95(self):
        "fcmpl"
        value2 = float(self.stack.pop())
        value1 = float(self.stack.pop())
        if value1>value2:
            self.stack.push(1)
        elif value1==value2:
            self.stack.push(0)
        elif value1<value2:
            self.stack.push(-1)
        else:# at least one of value1 or value2 is NaN
            self.stack.push(-1)

    def opcode_0x96(self):
        "fcmpg"
        value2 = float(self.stack.pop())
        value1 = float(self.stack.pop())
        if value1>value2:
            self.stack.push(1)
        elif value1==value2:
            self.stack.push(0)
        elif value1<value2:
            self.stack.push(-1)
        else:# at least one of value1 or value2 is NaN
            self.stack.push(1)

    def opcode_0x97(self):
        "dcmpl"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value1>value2:
            self.stack.push(1)
        elif value1==value2:
            self.stack.push(0)
        elif value1<value2:
            self.stack.push(-1)
        else:# at least one of value1 or value2 is NaN
            self.stack.push(-1)

    def opcode_0x98(self):
        "dcmpg"
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        if value1>value2:
            self.stack.push(1)
        elif value1==value2:
            self.stack.push(0)
        elif value1<value2:
            self.stack.push(-1)
        else:# at least one of value1 or value2 is NaN
            self.stack.push(1)

    def opcode_0x99(self):
        "ifeq"
        self.nextsignedword()
        value = self.stack.pop()
        return value == 0

    def opcode_0x9a(self):
        "ifne"
        self.nextsignedword()
        value = self.stack.pop()
        return value != 0

    def opcode_0x9b(self):
        "iflt"
        self.nextsignedword()
        value = self.stack.pop()
        return value < 0

    def opcode_0x9c(self):
        "ifge"
        self.nextsignedword()
        value = self.stack.pop()
        return value >= 0

    def opcode_0x9d(self):
        "ifgt"
        self.nextsignedword()
        value = self.stack.pop()
        return value > 0

    def opcode_0x9e(self):
        "ifle"
        self.nextsignedword()
        value = self.stack.pop()
        return value <= 0

    def opcode_0x9f(self):
        "if_icmpeq"
        self.nextsignedword()
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        return value1 == value2

    def opcode_0xa0(self):
        "if_icmpne"
        self.nextsignedword()
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        return value1 != value2

    def opcode_0xa1(self):
        "if_icmplt"
        self.nextsignedword()
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        return value1 < value2

    def opcode_0xa2(self):
        "if_icmpge"
        self.nextsignedword()
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        return value1 >= value2

    def opcode_0xa3(self):
        "if_icmpgt"
        self.nextsignedword()
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        return value1 > value2

    def opcode_0xa4(self):
        "if_icmple"
        self.nextsignedword()
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        return value1 <= value2

    def opcode_0xa5(self):
        "if_acmpeq"
        self.nextsignedword()
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        return value1 == value2

    def opcode_0xa6(self):
        "if_acmpne"
        self.nextsignedword()
        value2 = self.stack.pop()
        value1 = self.stack.pop()
        return value1 != value2

    def opcode_0xa7(self):
        "goto"
        return True

    # for Exceptionhandling, to reach the finally block
    def opcode_0xa8(self):
        "jsr"
        offset = self.nextsignedword()
        self.stack.push(self.next_instr) #remember entrypoint of sub
        # instruction lenght + next bytecode length
        self.next_instr =  self.next_instr + offset-3 

    def opcode_0xa9(self):
        "ret"
        index  = self.nextbyte()
        offset = self.locals.get(index, "ref")
        self.next_instr = offset # return to entrypoint(by jsr)

    def opcode_0xaa(self):
        "tableswitch"
        opcode_addr = self.next_instr -1 #address of the tableswitch opcode
        while not self.next_instr % 4==0:
            self.nextbyte()
        index = self.stack.pop()
        default = self.nextdoubleword()
        low = self.nextdoubleword()
        high = self.nextdoubleword()
        assert low <= high
        if index > high or index < low:
            self.next_instr = opcode_addr + default
        else:
            offset1 = ord(self.co.code[self.next_instr+(index - low)*4])
            offset2 = ord(self.co.code[self.next_instr+(index - low)*4+1])
            offset3 = ord(self.co.code[self.next_instr+(index - low)*4+2])
            offset4 = ord(self.co.code[self.next_instr+(index - low)*4+3])
            offset = offset1 << 24 | offset2 << 16 | offset3 << 8| offset4
            self.next_instr = opcode_addr + offset 

    def opcode_0xab(self):
        "lookupswitch"
        opcode_addr = self.next_instr -1 #address of the tableswitch opcode
        while not self.next_instr % 4==0:
            self.nextbyte()
        default = self.nextdoubleword()
        npairs  = self.nextdoubleword()
        assert npairs >= 0
        key = self.stack.pop()
        # TODO: search quicker the linear
        for i in range(npairs):
            match1 = ord(self.co.code[self.next_instr+i*8])
            match2 = ord(self.co.code[self.next_instr+i*8+1])
            match3 = ord(self.co.code[self.next_instr+i*8+2])
            match4 = ord(self.co.code[self.next_instr+i*8+3])
            match = match1 << 24 | match2 << 16 | match3 << 8 | match4
            if key == match:
                offset1 = ord(self.co.code[self.next_instr+i*8+4])
                offset2 = ord(self.co.code[self.next_instr+i*8+5])
                offset3 = ord(self.co.code[self.next_instr+i*8+6])
                offset4 = ord(self.co.code[self.next_instr+i*8+7])
                offset = offset1 << 24 | offset2 << 16 | offset3 << 8 | offset4
                self.next_instr = opcode_addr + offset 
                return
            else:
                continue
        self.next_instr = opcode_addr + default

    def opcode_0xac(self):
        "ireturn"
        raise Return(self.stack.pop())

    def opcode_0xad(self):
        "lreturn"
        raise Return(self.stack.pop())

    def opcode_0xae(self):
        "freturn"
        raise Return(self.stack.pop())

    def opcode_0xaf(self):
        "dreturn"
        raise Return(self.stack.pop())

    def opcode_0xb0(self):
        "areturn"
        raise Return(self.stack.pop())

    def opcode_0xb1(self):
        "return"
        raise Return(None)

    def opcode_0xb2(self):
        "getstatic"
        index = self.nextword()
        fieldref = self.const[index]
        classref = self.const[fieldref.class_index]
        cls = self.loader.getclass(self.const[classref.name_index])
        nametyperef = self.const[fieldref.name_and_type_index]
        name = self.const[nametyperef.name_index]
        descr = descriptor(self.const[nametyperef.descriptor_index])
        # TODO: lookup in supercls
        #print name,cls.__name__
        #print "decr:",descr
        if isinstance(cls, JClass):
            # supercls lookup
            # while not cls.__name__ == "java/lang/Object":
            while not cls == None:
                if cls.static_fields.has_key(unicode(name), descr):
                    # get it and stop lookup at the first match
                    value = cls.static_fields.get(unicode(name),descr)
                    break
                cls = cls.supercls
        else: # for javaclasses.py
            value = getattr(cls, name) # XXX not Rpython
        #print "value:",value
        self.stack.push(value)

    def opcode_0xb3(self):
        "putstatic"
        index = self.nextword()
        fieldref = self.const[index]
        classref = self.const[fieldref.class_index]
        cls = self.loader.getclass(self.const[classref.name_index])
        nametyperef = self.const[fieldref.name_and_type_index]
        name = self.const[nametyperef.name_index]
        descr = descriptor(self.const[nametyperef.descriptor_index])
        value = self.stack.pop()
        #print name, cls.__name__
        if isinstance(cls, JClass):
            # supercls lookup
            #while not cls.__name__ == "java/lang/Object":
            while not cls == None:
                if cls.static_fields.has_key(unicode(name), descr):
                    # set it and stop lookup at the first match
                    cls.static_fields.set(unicode(name), value, descr)
                    break
                cls = cls.supercls
        else: # javaclasses.JavaIoPrintStream
            assert isinstance(cls, javaclasses.JavaIoPrintStream)
            setattr(cls,name,value) # XXX not Rpython

    def opcode_0xb4(self):
        "getfield"
        index = self.nextword()
        fieldref = self.const[index]
        nametyperef = self.const[fieldref.name_and_type_index]
        name = self.const[nametyperef.name_index]
        descr = descriptor(self.const[nametyperef.descriptor_index])
        objectref = self.stack.pop()
        if objectref==None:
            throw_NullPointerException(self.loader)
        #print
        #print "objref:", objectref
        #print objectref.jcls.__name__,":"
        #print objectref.fields.print_map()
        #print "keyname:",name
        #print "super:",objectref.jcls.supercls.__name__
        value = objectref.fields.get(unicode(name), descr)
        #print "value:",value
        self.stack.push(value)

    def opcode_0xb5(self):
        "putfield"
        index = self.nextword()
        fieldref = self.const[index]
        nametyperef = self.const[fieldref.name_and_type_index]
        name = self.const[nametyperef.name_index]
        descr = descriptor(self.const[nametyperef.descriptor_index])
        value = self.stack.pop()
        objectref = self.stack.pop()
        #print
        #print objectref.jcls.__name__,":"
        objectref.fields.set(unicode(name), value, descr)

    def prepare_invoke(self):
        index = self.nextword()
        methodref = self.const[index]
        nametyperef = self.const[methodref.name_and_type_index]
        name = self.const[nametyperef.name_index]
        type = self.const[nametyperef.descriptor_index]
        descr = classloader.descriptor(type)
        classref = self.const[methodref.class_index]
        cls = self.loader.getclass(self.const[classref.name_index])
        argcount = len(descr) - 1
        args = Stack()
        for i in range(argcount):
            try:
                args.push(self.DESCR_CAST[descr[argcount-i-1]](self.stack.pop()))
            except KeyError:
                args.push(self.stack.pop()) # no number (or chr)
        real_name = classloader.encode_name(name, descr)
        return cls, methodref, name, args, descr[-1], real_name

    def push_result(self, rettype, result):
        if rettype is not None:
            if rettype=="long":
                self.stack.push(r_longlong(result))
            elif rettype=="float":
                self.stack.push(r_singlefloat(result))
            else:
                self.stack.push(result)

    def opcode_0xb6(self):
        "invokevirtual"
        cls, methodref, name, args, rettype, real_name = self.prepare_invoke()
        objectref = self.stack.pop()
        result = self.invokevirtual(cls, objectref, name, real_name, args)
        self.push_result(rettype, result)

    def opcode_0xb7(self):
        "invokespecial"
        cls, methodref, name, args, rettype, real_name = self.prepare_invoke()
        objectref = self.stack.pop()
        result = self.invokespecial(cls, objectref, name, real_name, args)
        self.push_result(rettype, result)

    def opcode_0xb8(self):
        "invokestatic"
        cls, methodref, name, args, rettype, real_name = self.prepare_invoke()
        result = self.invokestatic(cls, name, real_name, args)
        self.push_result(rettype, result)

    def opcode_0xb9(self):
        "invokeinterface"
        cls, methodref, name, args, rettype, real_name = self.prepare_invoke()
        count = self.nextbyte()
        zero  = self.nextbyte()
        assert count != 0 # not used (historical)
        assert zero == 0
        objectref = self.stack.pop()
        result = self.invokeinterface(cls, objectref, name, real_name, args)
        self.push_result(rettype, result)

    def opcode_0xbb(self):
        "new"
        index = self.nextword()
        classref = self.const[index]
        jcls = self.loader.getclass(self.const[classref.name_index])
        # TODO: no special case for non-JClasses
        if isinstance(jcls, JClass):
            self.stack.push(Objectref(jcls, True))
        else:
            self.stack.push(self.instantiate(jcls))


    def newarray(self, type_char, defaultitem, count, *counts):
        if len(counts) == 0:#basecase of recursion
            if isinstance(defaultitem, JClass):
                result = []
                # no init, ref is null
                for i in range(count):
                    result.append(Objectref(defaultitem, False))
            else:
                result = [defaultitem] * count
        else:
            result = []
            for i in range(count):
                result.append(self.newarray(type_char, defaultitem, *counts))

        # returning form recursion...
        if isinstance(defaultitem, JClass):
            array_cls_name = "["*(len(counts)+1)+"L"+defaultitem.__name__+";"
            return Arrayref(result,defaultitem, self.loader.getclass(array_cls_name))
        else:
            t = type_char
            assert t=='Z' or t=='S' or t=='B' or t=='I' or t=='J' or t=='F' or t=='D' or t=='C'
            array_cls_name = "["*(len(counts)+1)+type_char
            #if len(counts) == 0:
                #return Arrayref(result,defaultitem, self.loader.getPrimArrayClass(type_char))
            #else:
            return Arrayref(result,defaultitem, self.loader.getclass(array_cls_name))

    def opcode_0xbc(self):
        "newarray"
        typecode = self.nextbyte()
        count = self.stack.pop()
        self.stack.push(self.newarray(CHAR_BY_TYPECODE[typecode], DEFAULT_BY_TYPECODE[typecode], count))

    def opcode_0xbd(self):
        "anewarray"
        typeindex = self.nextword()
        count = self.stack.pop()
        typename = self.const[self.const[typeindex].name_index]
        # part of a multidim. array
        if typename.startswith('['):
            index = 0
            for c in typename:
                if c != '[':
                    break
                index = index +1
            self.stack.push(self.newarray(typename[index:], typename, count))
        # single dim. of ref. array
        else:
            jcls = self.loader.getclass(typename)
            #print "anewarray:",cls.__name__
            self.stack.push(self.newarray(None, jcls, count))

    def opcode_0xbe(self):
        "arraylength"
        array = self.stack.pop()
        if array==None:
            throw_NullPointerException(self.loader)
        self.stack.push(len(array.arrayref))

    # TODO: implementation not finished
    def opcode_0xbf(self):
        "athrow"
        objectref = self.stack.pop()
        #print "athrow:",objectref.jcls.__name__
        # TODO: assert objref isinstance throwable
        raise JException(objectref)

    # TODO: if synchronized do "something" :)
    def handle_exception(self, objectref):
        #print "handle exception:", objectref.jcls.__name__
        #clsnind = self.const[self.cls.this_class].name_index
        #print "inside methodname:",self.const[self.method.name_index]
        #print "inside class:",self.const[clsnind]
        if objectref==None: # somebody has thrown null
            #special case: 
            #raising here again would complicated the interp. loop
            jcls = self.loader.getclass("java/lang/NullPointerException")
            string = make_String("null", self.loader)
            objectref = Objectref(jcls, True)
            objectref.fields.set("detailMessage", string, "ref")
        assert self.co.exception_table_length>=0

        # search for exceptionhandles (catch blocks)
        for i in range(self.co.exception_table_length):
            exception = self.co.exception_table[i]
            if exception.catch_type==0:
                # JVMS Page 123 and 7.13 (finally)
                # or end of synchronized block
                if self.next_instr-1>=exception.start_pc and self.next_instr-1<exception.end_pc:
                    #handler found
                    self.next_instr = exception.handler_pc
                    self.stack.push(objectref)
                    return
            else:
                cls_info = self.const[exception.catch_type]
                type_name = self.const[cls_info.name_index]
                if objectref.jcls.__name__ == type_name and self.next_instr-1>=exception.start_pc and self.next_instr-1<exception.end_pc:
                    # handler found
                    self.next_instr = exception.handler_pc
                    self.stack.push(objectref)
                    return

        # check if this is a RunntimeException
        # This exceptions can (maybe) not found in the method-sig
        tempcls = objectref.jcls
        while not tempcls.__name__ == "java/lang/Throwable":
            if tempcls.__name__ == "java/lang/RuntimeException":
                # no exceptionhandlers in this class
                # the next frame must handle that
                raise JException(objectref)
            tempcls = tempcls.supercls

        # no exceptionshandlers (catch blocks) in this method
        # find the exceptions which are thrown by this method
        attr = self.cls.getattr(self.method, 'Exceptions', classfile.Exceptions_attribute)
        for i in range(attr.number_of_exceptions):
            excep_index = attr.exceptions_index_table[i]
            cls_info = self.const[excep_index]
            excep_name = self.const[cls_info.name_index]
            # exception thrown by this method

            # lookup of superclasses
            tempcls = objectref.jcls
            # TODO: throw new Thowable();
            while not tempcls.__name__ == "java/lang/Throwable":
                if tempcls.__name__ == excep_name:
                    # no exceptionhandlers in this class
                    # the next frame must handle that
                    raise JException(objectref)
                tempcls = tempcls.supercls
        raise Exception("Exception Handling Error-no catch and no throws!")

    def opcode_0xc0(self):
        "checkcast"
        index = self.nextword()
        classref = self.const[index]
        # XXX missing: array or interface
        # FIXME: is using astack directly
        cls = self.loader.getclass(self.const[classref.name_index])
        objectref = self.stack.astack[-1]
        self.checkcast(objectref, cls)

    # TODO: arraytpye
    def checkcast(self, objectref, cls):
        if objectref is None:
            return
        elif objectref.jcls == cls:
            return
        # check interfaces
        for iface_num in objectref.jcls.cls.interfaces:
            cls_info = objectref.jcls.cls.constant_pool[iface_num]
            if_name= objectref.jcls.cls.constant_pool[cls_info.name_index]
            if if_name == cls.__name__:
                return
        # Lookup of superclasses
        if not objectref.jcls.__name__ == "java/lang/Object":
            obj2 = Objectref(objectref.jcls.supercls) #FIXME when sp. cases are done
            return self.checkcast(obj2, cls)
        clsname1 = objectref.jcls.__name__.replace("/",".")
        clsname2 = cls.__name__.replace("/",".")
        throw_ClassCastException(self.loader, clsname1, clsname2)

    def opcode_0xc1(self):
        "instanceof"
        index = self.nextword()
        classref = self.const[index]
        # XXX missing: array or interface
        jcls = self.loader.getclass(self.const[classref.name_index])
        objectref = self.stack.pop()
        self.stack.push(self.instanceof(objectref, jcls))


    def opcode_0xc2(self):
        "monitorenter"
        from java_threading import monitorenter
        objectref = self.stack.pop()
        monitorenter(self.loader, objectref)

    def opcode_0xc3(self):
        "monitorexit"
        from java_threading import monitorexit
        objectref = self.stack.pop()
        monitorexit(objectref)


    # TODO: arraytype #maybe done?
    def instanceof(self, objectref, cls):
        if objectref == None:
            return False # null is never ref. of any class
        if isinstance(objectref, Arrayref):
            assert isinstance(objectref.jcls, JArrayClass)
            assert isinstance(cls, JClass)
            #print "cls:",cls.__name__ 
            #print "obj:",objectref.jcls.__name__ 
            if (cls.__name__ == objectref.jcls.__name__ or
                cls.__name__ == "java/lang/Object"): # all arrays are Objects
                return True
            return False
        if isinstance(objectref, Objectref) and objectref.jcls==cls:
            return True
        for iface_num in objectref.jcls.cls.interfaces:
            cls_info = objectref.jcls.cls.constant_pool[iface_num]
            if_name= objectref.jcls.cls.constant_pool[cls_info.name_index]
            if if_name == cls.__name__:
                return True
        # Lookup of superclasses
        if not objectref.jcls.__name__ == "java/lang/Object":
            obj2 = Objectref(objectref.jcls.supercls) #FIXME when sp. cases are done
            return self.instanceof(obj2, cls)
        # XXX a class form javaclasses
        # TODO: remove this when hooks are implemented
        return objectref==cls 

    def opcode_0xc4(self):
        "wide"
        opcode = self.nextbyte()
        index = self.nextword()
        if opcode == 21: #iload
            self.stack.push(self.locals.get(index, "int"))
        elif opcode == 22: #lload
            self.stack.push(self.locals.get(index, "long"))
        elif opcode == 23: #fload
            self.stack.push(self.locals.get(index, "float"))
        elif opcode == 24: #dload
            self.stack.push(self.locals.get(index, "double"))
        elif opcode == 25: #aload
            self.stack.push(self.locals.get(index, "ref"))
        elif opcode == 54: #istore
            self.locals.set(index, self.stack.pop(), "int")
        elif opcode == 55: #lstore
            self.locals.set(index, self.stack.pop(), "long")
        elif opcode == 56: #fstore
            self.locals.set(index, self.stack.pop(), "float")
        elif opcode == 57: #dstore
            self.locals.set(index, self.stack.pop(), "double")
        elif opcode == 58: #astore
            self.locals.set(index, self.stack.pop(), "ref")
        elif opcode == 129: #ret
            # offset = self.locals.get(index, "int")
            # self.next_instr = self.next_instr + offset -1
            raise NotImplementedError("ret")
        else: #iinc
            assert opcode== 132
            const = self.nextword()
            value = self.locals.get(index, "int") + const
            self.locals.set(index, value, "int")

    def opcode_0xc5(self):
        "multianewarray"
        typeindex = self.nextword()
        dimensions = self.nextbyte()
        assert dimensions >= 1
        typename = self.const[self.const[typeindex].name_index]
        assert typename.startswith('[' * dimensions)
        descr = classloader.descriptor(typename[dimensions:])
        defaultitem = classloader.DEFAULT_BY_DESCR.get(descr, None)
        if defaultitem == None:# no primitive type: Objectinstance
            defaultitem = self.loader.getclass(typename[dimensions+1:-1])
            assert isinstance(defaultitem, JClass)
        # TODO: check counts >0
        counts = [self.stack.pop() for i in range(dimensions)]
        counts.reverse()
        self.stack.push(self.newarray(typename[dimensions:], defaultitem, *counts))

    def opcode_0xc6(self):
        "ifnull"
        self.nextsignedword()
        value = self.stack.pop()
        if isinstance(value, Objectref):
            return value.is_null
        return value == None

    def opcode_0xc7(self):
        "ifnonnull"
        self.nextsignedword()
        value = self.stack.pop()
        if isinstance(value, Objectref):
            return not value.is_null
        return value != None

    def opcode_0xc8(self):
        "goto_w"
        return True

    # for Exception handling
    # TODO: offset of type returnAddress
    def opcode_0xc9(self):
        "jsr_w"
        # offset = self.nextsignedword()
        # offset = (offset << 16) | self.nextword()
        # self.stack.push(offset)
        raise NotImplementedError("jsr_w")

    # FIXME: java.lang.String insted of str
    # XXX str dont throws exceptions
    def invokevirtual(self, jcls, objectref, name, real_name, args):
        if objectref==None:
            throw_NullPointerException(self.loader)
        if isinstance(objectref, str):  # special-casing
            #print "string..."
            if name == 'length':
                return len(objectref)
            if real_name == classloader.encode_name(u'compareTo', (u'reference:java/lang/Object', 'int')):
                arg = args.pop()
                if not isinstance(arg[0], str):
                    raise TypeError
                return cmp(objectref, arg)
        #elif isinstance(objectref, unicode): # XXX dirty Bugfix
        #    #print "unicode..."
        #    if real_name=="toString_reference_java__lang__String":
        #        return make_String(objectref, self.loader)

        #print objectref
        #print "jcls:",jcls.__name__
        #print real_name
        #if name =="getProperty":
        #    clsnind = self.const[self.cls.this_class].name_index
        #    print "inside methodname:",self.const[self.method.name_index]
        #    print "inside class:",self.const[clsnind]
        #    print args.print_stack()
        if isinstance(objectref, Objectref) and isinstance(objectref.jcls, JClass):
            #if isinstance(objectref, Classref):
            #    print "a classref:", objectref
            args.push(objectref)
            cls = objectref.jcls
            #print "lookup:", real_name, cls.__name__
            while(True): #Do-While-Loop: method lookup
                try:
                    #print real_name
                    method = cls.methods[unicode(real_name)]
                    break
                except KeyError:
                    if isinstance(cls.supercls, JClass):
                        cls = cls.supercls
                        continue
                    else:
                        raise Exception("method not found: %s in %s",real_name, objectref.jcls.__name__)

            const = cls.cls.constant_pool
            descr = descriptor(const[method.descriptor_index])
            retval = self.loader.invoke_method(cls.cls, method, descr, args)
        else:
            #print "special..."
            #print real_name
            # there can be no python method with the name print
            # so the name is _print
            if(real_name[0:6] == 'print_'):
                real_name = '_'+real_name
            javaclasses.aloader = self.loader
            retval = getattr(objectref, real_name)(args)
        #if isinstance(retval,JException):
        #    self.handle_exception(retval.objref)
        #else:
        return retval

    def invokeinterface(self, cls, objectref, name, real_name, args):
        return self.invokevirtual(cls, objectref, name, real_name, args)

    def invokespecial(self, jcls, objectref, name, real_name, args):
        #if name == "<init>" and cls is object:
        #    return object.__init__(objectref, *args)
        #if name == "<init>" and cls is int:
        #    return int(*args)
        if isinstance(jcls, JClass):
            args.push(objectref)
            cls = jcls
            while(True): #Do-While-Loop: method lookup
                try:
                    method = cls.methods[unicode(real_name)]
                    break
                except KeyError:
                    if isinstance(cls.supercls, JClass):
                        cls = cls.supercls
                        continue
                    else:
                        raise Exception("method not found")

            const = cls.cls.constant_pool
            descr = descriptor(const[method.descriptor_index])
            retval = self.loader.invoke_method(cls.cls, method, descr, args)
        else: # special case
            retval = getattr(jcls, real_name)(objectref, args)
        #if isinstance(retval,JException):
        #    self.handle_exception(retval.objref)
        #else:
        return retval

    def invokestatic(self, jcls, name, real_name, args):
        if isinstance(jcls, JClass):
            cls = jcls
            while(True): #Do-While-Loop: method lookup
                try:
                    method = cls.methods[unicode(real_name)]
                    break
                except KeyError:
                    if isinstance(cls.supercls, JClass):
                        cls = cls.supercls
                        continue
                    else:
                        raise Exception("method not found")

            const = cls.cls.constant_pool
            descr = descriptor(const[method.descriptor_index])
            retval = self.loader.invoke_method(cls.cls, method, descr, args)
        else:
            retval = getattr(jcls, real_name)(args)
        #if isinstance(retval,JException):
        #    self.handle_exception(retval.objref)
        #else:
        return retval

WIDE_TARGET = {0xc8: "goto_w",
               }

DEFAULT_BY_TYPECODE = {4: False, # boolean
                       5: '\x00',# char
                       6: 0.0,   # float
                       7: 0.0,   # double
                       8: 0,     # byte
                       9: 0,     # short
                       10: 0,    # int
                       11: 0,    # long
                       }

CHAR_BY_TYPECODE =    {4: 'Z', # boolean
                       5: 'C',# char
                       6: 'F',   # float
                       7: 'D',   # double
                       8: 'B',     # byte
                       9: 'S',     # short
                       10: 'I',    # int
                       11: 'J',    # long
                       }

class Dummy:
    pass

# raised when a return opcode is reached
class Return(Exception):
    def __init__(self, retval):
        self.retval = retval