# -*- coding: utf-8 -*-
# The class in this module emulates System.out.print/println
# for testing reasons. It puts the method inside
# the bootstrap Classloader classloader.py on a
# prebuild phase.
# It is not used on a JVM-Startup via java.py.

aloader = None #XXXX must be set before make_String funtion call
from helper import unpack_string
from objectmodel import JObject, Classref, Objectref,JPrimitiveClass

class JavaIoPrintStream(JObject):
    output = None

    def __init__(self, stack=None):
        pass
    __init__.jdescr = '(Ljava/io/OutputStream;Z)V'
    # TODO: fix /x00 error here
    def println(self, stack):
        assert not self.output == None
        if stack.stackhistory == []:
            print >> self.output, ""
            return # this is:  System.out.println() //no arg
        string = stack.pop()
        if isinstance(string, bool):
            if string:
                string = 'true'
            else:
                string = 'false'
        elif isinstance(string, Classref):
            if isinstance(string.class_type, JPrimitiveClass):
                string = string.class_type.__name__
            else:
                assert string.jcls.__name__ == "java/lang/Class"
                string = "class "+ string.class_type.__name__.replace("/",".")
        elif isinstance(string, Objectref):
            if string.jcls.__name__ == "java/lang/String":
                string = unpack_string(string)
            elif string.jcls.__name__ == "java/lang/Byte" or string.jcls.__name__ == "java/lang/Short" or string.jcls.__name__ == "java/lang/Integer":
                integer = string.fields.get(unicode("value"), "int")
                string = str(integer)
            elif string.jcls.__name__ == "java/lang/Boolean":
                boolean = string.fields.get(unicode("value"), "int")
                if boolean==0:
                    string = str("false")
                else:
                    string = str("true")
            elif string.jcls.__name__ == "java/lang/Character":
                character = string.fields.get(unicode("value"), "char")
                string = str(character)
            elif string.jcls.__name__ == "java/lang/Long":
                long_val = string.fields.get(unicode("value"), "long")
                string = str(long_val)
            elif string.jcls.__name__ == "java/lang/Float":
                f_val = string.fields.get(unicode("value"), "float")
                string = str(float(f_val))
            elif string.jcls.__name__ == "java/lang/Double":
                d_val = string.fields.get(unicode("value"), "double")
                string = str(d_val)
            elif string.jcls.__name__ == "java/lang/Thread$State":
                string = string.fields.get(unicode("name"), "ref")
                string = unpack_string(string)
            #else:
            #    print string.jcls.__name__
            # TODO: call toString method
        elif string is None:
            string = "null"
        print >> self.output, string
        #print "PYPYJVM DEBUG: ", string
    println.jdescr = ('(Ljava/lang/String;)V',
                      '(I)V',
                      '(Z)V',
                      '(C)V',
                      '(F)V',
                      '(D)V',
                      '(J)V',
                      '(Ljava/lang/Object;)V',
                      '()V',
                      # XXX likely more
                      )
    def _print(self, stack):
        string = stack.pop()
        if isinstance(string, Objectref):
            if string.jcls.__name__ == "java/lang/String":
                string = unpack_string(string)
        self.output.write(string)
    _print.jdescr = ('(C)V',
                     '(Ljava/lang/String;)V',)

CLASSES = {#'java/lang/Object': JObject,
           #'java/lang/System': JavaLangSystem,
           #'java/lang/String': str,
           #'java/lang/Integer': JInteger,
           #'java/lang/Comparable': JComparable,
           #'java/lang/StringBuilder': JavaLangStringBuilder,
           'java/io/PrintStream': JavaIoPrintStream,
           #'java/lang/Exception':JavaException,
           #'java/lang/reflect/Constructor':JavaConstructor,
           #'java/lang/reflect/Method':JavaMethod,
           #'java/lang/reflect/Field':JavaField,
           #'java/lang/VMThrowable':JavaThrowable,
           #'java/lang/Thread':JavaThread,
           #'java/lang/Class':JavaClass,
           #'java/lang/ClassLoader':JavaClassLoader,
           }

#class JInteger(JObject):
    #__slots__ = ['j_intval']

    #def __init__(self, stack =None):
        #if stack:
            #intval = stack.pop()
            #self.j_intval = int(intval)
    #__init__.jdescr = '(I)V', '(Ljava/lang/String;)V'

    #def parseInt(stack):
        #str = stack.pop()
        #assert str.jcls.__name__ == "java/lang/String"
        #char_list = str.fields.get(unicode("value"),"array").arrayref
        ## unpack char array to string
        #str = ""
        #for char in char_list:
            #str += char
        #return int(str)
    #parseInt.jdescr = '(Ljava/lang/String;)I'
    #parseInt = staticmethod(parseInt)

    #def toString(self, stack):
        #objref = make_String(str(self.j_intval), aloader)
        #return objref
    #toString.jdescr = '()Ljava/lang/String;'

#class JavaLangSystem(JObject):
    #out = JavaIoPrintStream()
    #def loadLibrary(str):
        #pass
    #loadLibrary.jdescr = ('(Ljava/lang/String;)V', )
    #loadLibrary = staticmethod(loadLibrary)

#class JComparable(object):
    #"interface"

#class JavaLangStringBuilder(JObject):
    #__slots__ = "buffer"

    #def __init__(self, stack):
        #from StringIO import StringIO
        #self.buffer = StringIO()
        #if not stack.stackhistory == []:
            #args = stack.pop()
            #if isinstance(args, Objectref):
                #assert args.jcls.__name__ == "java/lang/String"
                #stri =unpack_string(args)
                #self.buffer.write(stri)
            #else:
                ##print args.jcls.__name__
                #assert len(args) == 1
                #arg = args[0]
                #assert isinstance(arg, str) # XXX there is also int and CharSequence
                #self.buffer.write(arg)
    #__init__.jdescr = ('()V', '(Ljava/lang/String;)V', )

    #def append(self, stack):
        #obj = stack.pop()
        #if isinstance(obj, Objectref):
            #assert obj.jcls.__name__ == "java/lang/String"
            #obj =unpack_string(obj)
        #elif not isinstance(obj, str):
            #obj = chr(obj)# XXX there are many more
        #self.buffer.write(obj)
        #return self
    #append.jdescr = ('(Ljava/lang/String;)Ljava/lang/StringBuilder;','(Ljava/lang/Object;)Ljava/lang/StringBuilder;' )

    #def toString(self, stack):
        #objref = make_String(self.buffer.getvalue(), aloader)
        #return objref
    #toString.jdescr = ('()Ljava/lang/String;', )

#class JavaException(object):
#    def __init__(self, errstring):
#        self.errstring = errstring
#    __init__.jdescr = ('()V', '(Ljava/lang/String;)V', )

#TODO: Implement this VM Hooks
#class JavaConstructor(object):
    #def __init__(self):
        #raise NotImplementedError("JavaConstructor")

#class JavaMethod(object):
    #def __init__(self):
        #raise NotImplementedError("JavaMethod")

#class JavaField(object):
    #def __init__(self):
        #raise NotImplementedError("JavaField")

#class JavaThrowable(object):
    #def __init__(self):
        #raise NotImplementedError("JavaThrowable")

#class JavaThread(object):
    #def __init__(self):
        #raise NotImplementedError("JavaThread")

## maybe inherit from JCLass
#class JavaClass(object):
    #def __init__(self):
        #raise NotImplementedError("JavaClass")

## maybe inherit form ClassLoader
#class JavaClassLoader(object):
    #def __init__(self):
        #raise NotImplementedError("JavaClassLoader")
