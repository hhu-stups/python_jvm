# -*- coding: utf-8 -*-
# Mapping from/to C/Python
# C-level       python-level     comment
#
# jstring       Objectref        '(java/lang/String)'
# const jchar*  POINTER(c_char)  c_char_p before..
# jchar         c_char
# jsize         c_int
# jshort        c_int
# jint          c_int
# jboolean      c_int            NULL==None;0==False;1==True
# jbyte         c_int
# jlong         c_long
# jfloat        c_float
# jdouble       c_double
# jchar         c_char/c_wchar
# jclass        Classref         JClass before (and maybe still somewhere ;) )
# jobject       Objectref
# jobjectArray  Arrayref
# va_list       Stack
# jXArray  Arrayref
# *jboolean     <c_boolean_Array>
# *jbyte        <c_byte_Array>
# *jchar        <c_char_Array>
# *jshort       <c_short_Array>
# *jint         <c_int_Array>
# *jlong        <c_long_Array>
# *jfloat       <c_float_Array>
# *jdouble      <c_double_Array>
# FIXME: "random" segmentation faults, use create_string_buffer insted of c_char_p
import py, native
import interp
from test_interp import RunTests
from native import env_ptr, current_classloader, FieldID, MethodID
from ctypes import cdll, c_int, c_float, c_void_p, CFUNCTYPE, pointer, c_char_p,POINTER, py_object, Structure, c_char, c_wchar, c_long, c_float, c_double, create_string_buffer, Union
from objmodel import Objectref, Classref, Arrayref, Stack
from helper import make_String, unpack_string

path = str("/usr/lib/libtest_native.so")
clib = cdll.LoadLibrary(path)

class TestNative(RunTests):
    def test_it(self):
        clib.quitschibo.restype = POINTER(c_int)
        result = clib.quitschibo(pointer(c_int(1)))
        #print result.contents.value
        #print result[2]
        result = clib.quitschibo((c_int*3)(1,2,3))
        #print result[2]
        result = (c_int*3)(4,5,6)
        #print result[0]
        #print result[1]
        #print result[2]
        assert result[0] == 4
        clib.test_blubby(result)
        #print "after change: ",result[0]
        #print "after change: ",result[1]
        #print "after change: ",result[2]
        assert result[0] == 41
        #for i in result:
        #    print i

    def test_astr(self):
        class mystr(Structure):
            _fields_ = [("x", c_int),("y", c_int),]
        clib.a_str_method.restype = mystr
        result = clib.a_str_method(c_int(3), c_int(5))
        assert result.x==3
        assert result.y==5

    def test_aunion(self):
        class myunion(Union):
            _fields_ = [("z", c_int),
                       ("b", c_int),
                       ("c", c_char),
                       ("s", c_int),
                       ("i", c_int),
                       ("j", c_long),
                       ("f", c_float),
                       ("d", c_double),
                       ("l", py_object)]
        clib.a_union_method.restype = POINTER(myunion)
        result = clib.a_union_method(c_int(3))
        assert result.contents.i == 3

    def test_GetVersion(self):
        clib.test_GetVersion.restype = c_int
        result = clib.test_GetVersion(env_ptr)
        assert result == 1

    def test_GetStringUTFChars(self):
        py.test.skip("uses c_char_p -> random segfaults")
        self.loader = self.ClassLoader([])
        string = make_String("Hello World", self.loader)
        clib.test_GetStringUTFChars.restype = c_char_p
        result = clib.test_GetStringUTFChars(env_ptr, None, py_object(string))
        assert result == "Hello World"

    def test_NewString(self):
        native.current_classloader = self.ClassLoader([])
        clib.test_NewString.restype = py_object 
        result = clib.test_NewString(env_ptr, c_char_p("N00b"),c_int(len("N00b")))
        assert isinstance(result, Objectref)
        assert result.jcls.__name__ == "java/lang/String"
        assert unpack_string(result) == "N00b"

    def test_GetStringLength(self):
        self.loader = self.ClassLoader([])
        string = make_String("foo", self.loader)
        clib.test_GetStringLength.restype = c_int
        result = clib.test_GetStringLength(env_ptr, py_object(string))
        assert result == 3

    def test_GetStringChars(self):
        py.test.skip("uses c_char_p -> random segfaults")
        self.loader = self.ClassLoader([])
        string = make_String("bar", self.loader)
        clib.test_GetStringChars.restype = c_char_p
        result = clib.test_GetStringChars(env_ptr, py_object(string), None)
        assert result == "bar"

    def test_ReleaseStringChars(self):
        self.loader = self.ClassLoader([])
        string  = make_String("Baam", self.loader)
        clib.test_ReleaseStringChars(env_ptr, py_object(string), c_char_p("Baam"))

    def test_NewStringUTF(self):
        native.current_classloader = self.ClassLoader([])
        clib.test_NewStringUTF.restype = py_object
        result = clib.test_NewStringUTF(env_ptr, c_char_p("Narf"))
        assert isinstance(result, Objectref)
        assert result.jcls.__name__ == "java/lang/String"
        assert unpack_string(result) == "Narf"

    def test_GetStringUTFLength(self):
        interp.interp_lock.acquire() # XXX
        self.loader = self.ClassLoader([])
        string = make_String("Hatschi", self.loader)
        clib.test_GetStringUTFLength.restype = c_int
        result = clib.test_GetStringUTFLength(env_ptr, py_object(string))
        interp.interp_lock.release() # XXX
        assert result == 7

    def test_ReleaseStringUTFChars(self):
        interp.interp_lock.acquire() # XXX
        self.loader = self.ClassLoader([])
        string = make_String("HA!", self.loader)
        clib.test_ReleaseStringUTFChars(env_ptr, py_object(string), c_char_p("HA!"))
        interp.interp_lock.release() # XXX

    def test_GetFieldID(self):
        jcls = self.getclass('''
        class Test_GetField {
            public int x;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"),True, jcls, self.loader)
        clib.test_pyobject.restype = py_object
        result = clib.test_pyobject(py_object(clsref))
        assert isinstance(result, Classref)
        assert clsref == result
        assert result.class_type == jcls 
        # confusing names clsref.jcls != jcls :)
        clib.test_GetFieldID.restype = py_object
        clsref = Classref(self.loader.getclass("java/lang/Class"),True, jcls, self.loader)
        result = clib.test_GetFieldID(env_ptr, py_object(clsref), c_char_p("x"), c_char_p("I"))
        assert isinstance(result, FieldID)
        assert result.name == "x"
        assert result.sig == "I"

    def test_GetStaticFieldID(self):
        jcls = self.getclass('''
        class Test_GetStaticFieldID {
            static int x;
        }
        ''')
        clib.test_GetStaticFieldID.restype = py_object
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_GetStaticFieldID(env_ptr, py_object(clsref), c_char_p("x"), c_char_p("I"))
        assert isinstance(result, FieldID)
        assert result.name == "x"
        assert result.sig == "I"

    def test_CallStaticMethod(self):
        jcls = self.getclass('''
        class Test_StaticCall {
            public static void v(){}
            public static Test_StaticCall tsc(){return new Test_StaticCall();}
            public static boolean b(){return true;}
            public static byte by(){return 22;}
            public static char c(){return 'Q';}
            public static short s(){return 444;}
            public static int i(){return 7777;}
            public static long l(){return 55555;}
            public static float f(){return 1.0f;}
            public static double d(){return 2.0;}
            }
        ''')
        native.current_classloader = self.loader 
        methodID = MethodID("v", "()V")
        clib.test_CallStaticVoidMethodV.restype = c_void_p
        clsref =Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        clib.test_CallStaticVoidMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))

        native.current_classloader = self.loader
        methodID = MethodID("tsc", "()LTest_StaticCall;")
        clib.test_CallStaticObjectMethodV.restype = py_object
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_CallStaticObjectMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))
        assert isinstance(result, Objectref)
        assert result.jcls == jcls

        native.current_classloader = self.loader
        methodID = MethodID("b", "()Z")
        clib.test_CallStaticBooleanMethodV.restype = c_int
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_CallStaticBooleanMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))
        assert result == True

        native.current_classloader = self.loader
        methodID = MethodID("by", "()B")
        clib.test_CallStaticByteMethodV.restype = c_int
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_CallStaticByteMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))
        assert result == 22

        #native.current_classloader = self.loader
        #methodID = MethodID("c", "()C")
        #clib.test_CallStaticCharMethodV.restype = c_char
        #result = clib.test_CallStaticCharMethodV(env_ptr, py_object( Objectref(jcls)), py_object(methodID), py_object(Stack()))
        #assert result == 'Q'

        native.current_classloader = self.loader
        methodID = MethodID("s", "()S")
        clib.test_CallStaticShortMethodV.restype = c_int
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_CallStaticShortMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))
        assert result == 444

        native.current_classloader = self.loader
        methodID = MethodID("i", "()I")
        clib.test_CallStaticIntMethodV.restype = c_int
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_CallStaticIntMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))
        assert result == 7777

        native.current_classloader = self.loader
        methodID = MethodID("l", "()J")
        clib.test_CallStaticLongMethodV.restype = c_long
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_CallStaticLongMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))
        assert result == 55555

        native.current_classloader = self.loader
        methodID = MethodID("f", "()F")
        clib.test_CallStaticFloatMethodV.restype = c_float
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_CallStaticFloatMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))
        assert result == 1.0

        native.current_classloader = self.loader
        methodID = MethodID("d", "()D")
        clib.test_CallStaticDoubleMethodV.restype = c_double
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_CallStaticDoubleMethodV(env_ptr, py_object(clsref), py_object(methodID), py_object(Stack()))
        assert result == 2.0


    def test_GetStaticField(self):
        jcls2 = self.getclass('''
        class Dummy {
        }
        ''')
        jcls = self.getclass('''
        class Test_GetStaticField {
            static Dummy dum = new Dummy();
            static boolean bool = true;
            static byte bye = 23;
            static char carl = 'C';
            static short sho = 55;
            static int ini = 41;
            static long longer = 666;
            static float fly = 5.5f;
            static double duo = 44.0;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)

        fid = FieldID("dum","LDummy;")
        clib.test_GetStaticObjectField.restype = py_object
        result = clib.test_GetStaticObjectField(env_ptr, py_object(clsref), py_object(fid))
        assert isinstance(result, Objectref)
        assert result.jcls.__name__ == "Dummy"


        fid = FieldID("bool","Z")
        clib.test_GetStaticBooleanField.restype = c_int
        result = clib.test_GetStaticBooleanField(env_ptr, py_object(clsref), py_object(fid))
        assert result == True

        fid = FieldID("bye","Z")
        clib.test_GetStaticByteField.restype = c_int
        result = clib.test_GetStaticByteField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 23

        fid = FieldID("sho","S")
        clib.test_GetStaticShortField.restype = c_int
        result = clib.test_GetStaticShortField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 55

        fid = FieldID("carl","C")
        clib.test_GetStaticCharField.restype = c_wchar
        result = clib.test_GetStaticCharField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 'C'

        fid = FieldID("ini","I")
        clib.test_GetStaticIntField.restype = c_int
        result = clib.test_GetStaticIntField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 41

        fid = FieldID("longer","J")
        clib.test_GetStaticLongField.restype = c_long
        result = clib.test_GetStaticLongField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 666

        fid = FieldID("fly","F")
        clib.test_GetStaticFloatField.restype = c_float
        result = clib.test_GetStaticFloatField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 5.5

        fid = FieldID("duo","D")
        clib.test_GetStaticDoubleField.restype = c_double
        result = clib.test_GetStaticDoubleField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 44.0

    def test_SetStaticField(self):
        jcls2 = self.getclass('''
        class Dummy {
        }
        ''')
        jcls = self.getclass('''
        class Test_GetStaticField {
            static Dummy dum;
            static boolean bool;
            static byte bye;
            static char carl;
            static short sho;
            static int ini;
            static long longer;
            static float fly;
            static double duo;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        objref2 = Objectref(jcls2, True)

        fid = FieldID("dum","LDummy;")
        clib.test_SetStaticObjectField(env_ptr, py_object(clsref), py_object(fid), py_object(objref2))
        clib.test_GetStaticObjectField.restype = py_object
        result = clib.test_GetStaticObjectField(env_ptr, py_object(clsref), py_object(fid))
        assert isinstance(result, Objectref)
        assert result.jcls.__name__ == "Dummy"


        fid = FieldID("bool","Z")
        clib.test_SetStaticBooleanField(env_ptr, py_object(clsref), py_object(fid), c_int(True))
        clib.test_GetStaticBooleanField.restype = c_int
        result = clib.test_GetStaticBooleanField(env_ptr, py_object(clsref), py_object(fid))
        assert result == True # 1==true

        fid = FieldID("bye","B")
        clib.test_SetStaticByteField(env_ptr, py_object(clsref), py_object(fid), c_int(23))
        clib.test_GetStaticByteField.restype = c_int
        result = clib.test_GetStaticByteField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 23

        fid = FieldID("sho","S")
        clib.test_SetStaticShortField(env_ptr, py_object(clsref), py_object(fid), c_int(55))
        clib.test_GetStaticShortField.restype = c_int
        result = clib.test_GetStaticShortField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 55

        fid = FieldID("ini","I")
        clib.test_SetStaticIntField(env_ptr, py_object(clsref), py_object(fid), c_int(41))
        clib.test_GetStaticIntField.restype = c_int
        result = clib.test_GetStaticIntField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 41

        fid = FieldID("longer","J")
        clib.test_SetStaticLongField(env_ptr, py_object(clsref), py_object(fid), c_long(666))
        clib.test_GetStaticLongField.restype = c_long
        result = clib.test_GetStaticLongField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 666

        fid = FieldID("fly","F")
        clib.test_SetStaticFloatField(env_ptr, py_object(clsref), py_object(fid), c_float(5.5))
        clib.test_GetStaticFloatField.restype = c_float
        result = clib.test_GetStaticFloatField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 5.5

        fid = FieldID("duo","D")
        clib.test_SetStaticDoubleField(env_ptr, py_object(clsref), py_object(fid), c_double(44.0))
        clib.test_GetStaticDoubleField.restype = c_double
        result = clib.test_GetStaticDoubleField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 44.0

    def test_GetMethodID(self):
        jcls = self.getclass('''
        class Test_GetMethod {
            public int x(){return 41;}
        }
        ''')
        clib.test_GetMethodID.restype = py_object
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        result = clib.test_GetMethodID(env_ptr, py_object(clsref), c_char_p("x"), c_char_p("()I"))
        assert isinstance(result, MethodID)
        assert result.name == "x"
        assert result.sig == "()I"

    def test_Get_Set_Object_Field_Routines(self):
        jclsA = self.getclass('''
        class Klazz {}
        ''')
        jclsB = self.getclass('''
        class Test_GetField {
            public Klazz obj;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jclsB, self.loader)
        fieldID = FieldID("obj","LKlazz;")
        value = Objectref(jclsA, True)
        clib.test_SetObjectField(env_ptr, py_object(clsref), py_object(fieldID), py_object(value))
        clib.test_GetObjectField.restype = py_object
        result = clib.test_GetObjectField(env_ptr, py_object(clsref), py_object(fieldID))
        assert result == value

    def test_Get_Set_Boolean_Field_Routines(self):
        jcls = self.getclass('''
        class Test_GetField {
            public boolean bool;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        fieldID = FieldID("bool","Z")
        value = True
        clib.test_SetBooleanField(env_ptr, py_object(clsref), py_object(fieldID), c_int(value))
        clib.test_GetBooleanField.restype = c_int
        result = clib.test_GetBooleanField(env_ptr, py_object(clsref), py_object(fieldID))
        assert result

    def test_Get_Set_Byte_Field_Routines(self):
        jcls = self.getclass('''
        class Test_GetField {
            public byte by;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        fieldID = FieldID("by","Z")
        value = 41
        clib.test_SetByteField(env_ptr, py_object(clsref), py_object(fieldID), c_int(value))
        clib.test_GetByteField.restype = c_int
        result = clib.test_GetByteField(env_ptr, py_object(clsref), py_object(fieldID))
        assert result == value

    def test_Get_Set_Short_Field_Routines(self):
        jcls = self.getclass('''
        class Test_GetField {
            public short s;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        fieldID = FieldID("s","S")
        value = 41
        clib.test_SetShortField(env_ptr, py_object(clsref), py_object(fieldID), c_int(value))
        clib.test_GetShortField.restype = c_int
        result = clib.test_GetShortField(env_ptr, py_object(clsref), py_object(fieldID))
        assert result == value

    def test_Get_Set_Int_Field_Routines(self):
        jcls = self.getclass('''
        class Test_GetField {
            public int igor;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        fieldID = FieldID("igor","I")
        value = 41
        clib.test_SetIntField(env_ptr, py_object(clsref), py_object(fieldID), c_int(value))
        clib.test_GetIntField.restype = c_int
        result = clib.test_GetIntField(env_ptr, py_object(clsref), py_object(fieldID))
        assert result == value

    def test_Get_Set_Long_Field_Routines(self):
        jcls = self.getclass('''
        class Test_GetField {
            public long lenny;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        fieldID = FieldID("lenny","J")
        value = 4711
        clib.test_SetLongField(env_ptr, py_object(clsref), py_object(fieldID), c_long(value))
        clib.test_GetLongField.restype = c_long
        result = clib.test_GetLongField(env_ptr, py_object(clsref), py_object(fieldID))
        assert result == value

    def test_Get_Set_Float_Field_Routines(self):
        jcls = self.getclass('''
        class Test_GetField {
            public float fry;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        fieldID = FieldID("fry","F")
        value = 5.5
        clib.test_SetFloatField(env_ptr, py_object(clsref), py_object(fieldID), c_float(value))
        clib.test_GetFloatField.restype = c_float
        result = clib.test_GetFloatField(env_ptr, py_object(clsref), py_object(fieldID))
        assert result == value # FIXME: lose of precition

    def test_Get_Set_Double_Field_Routines(self):
        jcls = self.getclass('''
        class Test_GetField {
            public double donald;
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        fieldID = FieldID("donald","D")
        value = 1.9
        clib.test_SetDoubleField(env_ptr, py_object(clsref), py_object(fieldID), c_double(value))
        clib.test_GetDoubleField.restype = c_double
        result = clib.test_GetDoubleField(env_ptr, py_object(clsref), py_object(fieldID))
        assert result == value # FIXME: lose of precition too

    def test_CallVoidMethodV(self):
        jcls = self.getclass('''
        class Klazz {
            public int i1;
            public void change_i(int i2){i1 = i2;}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("change_i", "(I)V")
        args = Stack()
        args.push(7)
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallVoidMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        fieldID = FieldID("i1","I")
        clib.test_GetIntField.restype = c_int
        result = clib.test_GetIntField(env_ptr, py_object(objref), py_object(fieldID))
        assert result == 7

    def test_CallObjectMethodV(self):
        jclsA = self.getclass('''
        class Glazz {}
        ''')
        jclsB = self.getclass('''
        class Klazz {
            public Glazz gups;
            public Glazz change_obj(Glazz baam){gups = baam;return gups;}
        }
        ''')
        objref = Objectref(jclsB, True)
        objref2 = Objectref(jclsA, True)
        methodID = MethodID("change_obj", "(LGlazz;)LGlazz;")
        args = Stack()
        args.push(objref2)
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallObjectMethodV.restype = py_object
        result = clib.test_CallObjectMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result == objref2

    def test_CallBooleanMethodV(self):
        jcls = self.getclass('''
        class Klazz {
            public boolean p_eq_np(boolean b){return b;}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("p_eq_np", "(Z)Z")
        args = Stack()
        args.push(True)
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallBooleanMethodV.restype = c_int
        result = clib.test_CallBooleanMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result==True

    def test_CallByteMethodV(self):
        jcls = self.getclass('''
        class Klazz {
            public byte num(){return 41;}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("num", "()B")
        args = Stack()
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallByteMethodV.restype = c_int
        result = clib.test_CallByteMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result==41

    def test_CallShortMethodV(self):
        jcls = self.getclass('''
        class Klazz {
            public short num(){return 41;}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("num", "()S")
        args = Stack()
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallShortMethodV.restype = c_int
        result = clib.test_CallShortMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result==41

    def test_CallIntMethodV(self):
        jcls = self.getclass('''
        class Klazz {
            public int num(){return 41;}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("num", "()I")
        args = Stack()
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallIntMethodV.restype = c_int
        result = clib.test_CallIntMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result==41

    def test_CallLongMethodV(self):
        jcls = self.getclass('''
        class Klazz {
            public long num(){return 41;}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("num", "()J")
        args = Stack()
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallLongMethodV.restype = c_long
        result = clib.test_CallLongMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result==41

    def test_CallFloatMethodV(self):
        jcls = self.getclass('''
        class Klazz {
            public float num(){return 41f;}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("num", "()F")
        args = Stack()
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallFloatMethodV.restype = c_float
        result = clib.test_CallFloatMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result==41.0

    def test_CallDoubleMethodV(self):
        jcls = self.getclass('''
        class Klazz {
            public double num(){return 41;}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("num", "()D")
        args = Stack()
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallDoubleMethodV.restype = c_double
        result = clib.test_CallDoubleMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result==41.0

    def test_CallCharMethodV(self):
        py.test.skip("in-progress: test_CallCharMethodV")
        # cleanup the char--int repr. inside this vm before fixing this test
        jcls = self.getclass('''
        class Klazz {
            public char letter(){return 'A';}
        }
        ''')
        objref = Objectref(jcls, True)
        methodID = MethodID("letter", "()C")
        args = Stack()
        args.push(objref) #thisref
        native.current_classloader = self.loader
        clib.test_CallCharMethodV.restype = c_char
        result = clib.test_CallCharMethodV(env_ptr, py_object(objref), py_object(methodID), py_object(args))
        assert result=='A'

    def test_Get_Set_Char_Field_Routines(self):
        jcls = self.getclass('''
        class Test_GetField {
            public char c;
        }
        ''')
        objref = Objectref(jcls, True)
        fieldID = FieldID("c","C")
        value = 'X'
        clib.test_SetCharField(env_ptr, py_object(objref), py_object(fieldID), c_char(value))
        clib.test_GetCharField.restype = c_char
        result = clib.test_GetCharField(env_ptr, py_object(objref), py_object(fieldID))
        assert result == value

    def test_GetStringCritical(self):
        py.test.skip("in-progress: test_GetStringCritical")
        clib.test_GetStringCritical.restype = c_char_p
        result = clib.test_GetStringCritical(env_ptr, c_char_p("bar"), None)
        assert result == "bar"

    def test_ReleaseStringCritical(self):
        py.test.skip("in-progress: test_ReleaseStringCritical")
        clib.test_ReleaseStringCritical(env_ptr, c_char_p("HA!"), c_char_p("HA!"))

    def test_GetStringRegion(self):
        self.loader = self.ClassLoader([])
        string = make_String("Hello World", self.loader)
        lenght = c_int(5)
        start = c_int(6)
        result = (c_char*5)(' ',' ',' ',' ',' ')
        clib.test_GetStringRegion(env_ptr, py_object(string), start, lenght, result)
        exp = "World"
        for i in range(len(exp)):
            assert result[i] == exp[i]

    def test_GetStringUTFRegion(self):
        self.loader = self.ClassLoader([])
        string = make_String("Hello World", self.loader)
        lenght = c_int(5)
        start = c_int(6)
        result = (c_char*5)(' ',' ',' ',' ',' ')
        clib.test_GetStringUTFRegion(env_ptr, py_object(string), start, lenght, result)
        exp = "World"
        for i in range(len(exp)):
            assert result[i] == exp[i]


    def test_Get_SetXArrayRegion(self):
        loader = self.ClassLoader([])#XXX
        buff = (c_int*2)(False, False)
        pyarr = Arrayref([True, False, True], False, loader.getclass("[Z"))
        assert buff[0] == False
        assert buff[1] == False
        clib.test_GetBooleanArrayRegion(env_ptr, py_object(pyarr), c_int(1), c_int(2), buff)
        assert buff[0] == False
        assert buff[1] == True
        buff = (c_int*2)(True, True)
        assert pyarr.arrayref == [True, False, True]
        clib.test_SetBooleanArrayRegion(env_ptr, py_object(pyarr), c_int(1), c_int(2), buff)
        assert pyarr.arrayref == [True, True, True]

        buff = (c_int*2)(3, 1)
        pyarr = Arrayref([40, 41, 42], 0, loader.getclass("[B"))
        assert buff[0] == 3
        assert buff[1] == 1
        clib.test_GetByteArrayRegion(env_ptr, py_object(pyarr), c_int(1), c_int(2), buff)
        assert buff[0] == 41
        assert buff[1] == 42

        buff = (c_int*2)(4, 2)
        pyarr = Arrayref([43, 44, 45], 0, loader.getclass("[S"))
        assert buff[0] == 4
        assert buff[1] == 2
        clib.test_GetShortArrayRegion(env_ptr, py_object(pyarr), c_int(1), c_int(2), buff)
        assert buff[0] == 44
        assert buff[1] == 45

        buff = (c_int*2)(5, 3)
        pyarr = Arrayref([44, 45, 47], 0, loader.getclass("[I"))
        assert buff[0] == 5
        assert buff[1] == 3
        clib.test_GetIntArrayRegion(env_ptr, py_object(pyarr), c_int(1), c_int(2), buff)
        assert buff[0] == 45
        assert buff[1] == 47

        buff = (c_long*2)(6, 7)
        pyarr = Arrayref([66, 67, 68], 0, loader.getclass("[J"))
        assert buff[0] == 6
        assert buff[1] == 7
        clib.test_GetLongArrayRegion(env_ptr, py_object(pyarr), c_int(1), c_int(2), buff)
        assert buff[0] == 67
        assert buff[1] == 68

        buff = (c_float*2)(4.0, 5.0)
        pyarr = Arrayref([1.0, 2.0, 3.0], 0, loader.getclass("[F"))
        assert buff[0] == 4.0
        assert buff[1] == 5.0
        clib.test_GetFloatArrayRegion(env_ptr, py_object(pyarr), c_int(1), c_int(2), buff)
        assert buff[0] == 2.0
        assert buff[1] == 3.0

        buff = (c_double*2)(41.0, 51.0)
        pyarr = Arrayref([11.0, 21.0, 31.0], 0, loader.getclass("[D"))
        assert buff[0] == 41.0
        assert buff[1] == 51.0
        clib.test_GetDoubleArrayRegion(env_ptr, py_object(pyarr), c_int(1), c_int(2), buff)
        assert buff[0] == 21.0
        assert buff[1] == 31.0


    def test_ArrayStuff(self):
        jcls = self.getclass('''
        class Klazz {
        }
        ''')
        clib.test_NewObjectArray.restype = py_object
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        array = clib.test_NewObjectArray(env_ptr, c_int(3), py_object(clsref), py_object(Objectref(jcls)))
        assert isinstance(array, Arrayref)

        clib.test_GetArrayLength.restype.restype = c_int
        result = clib.test_GetArrayLength(env_ptr, py_object(array))
        assert result == 3

        clib.test_GetObjectArrayElement.restype = py_object
        result = clib.test_GetObjectArrayElement(env_ptr, py_object(array), c_int(2))
        assert isinstance(result, Objectref)

        clib.test_SetObjectArrayElement.restype = c_void_p
        clib.test_SetObjectArrayElement(env_ptr, py_object(array), c_int(2), py_object(Objectref(jcls)))

        clib.test_GetObjectArrayElement.restype = py_object
        result2 = clib.test_GetObjectArrayElement(env_ptr, py_object(array), c_int(2))
        assert not result == result2

        clib.test_NewBooleanArray.restype = py_object
        bool_array = clib.test_NewBooleanArray(env_ptr, c_int(4))
        assert isinstance(bool_array, Arrayref)
        assert bool_array.arrayref == [False, False, False, False]

        clib.test_NewByteArray.restype = py_object
        byte_array = clib.test_NewByteArray(env_ptr, c_int(4))
        assert isinstance(byte_array, Arrayref)
        assert byte_array.arrayref == [0, 0, 0, 0]

        clib.test_NewShortArray.restype = py_object
        short_array = clib.test_NewShortArray(env_ptr, c_int(4))
        assert isinstance(short_array, Arrayref)
        assert short_array.arrayref == [0, 0, 0, 0]

        clib.test_NewIntArray.restype = py_object
        int_array = clib.test_NewIntArray(env_ptr, c_int(4))
        assert isinstance(int_array, Arrayref)
        assert int_array.arrayref == [0, 0, 0, 0]

        clib.test_NewLongArray.restype = py_object
        long_array = clib.test_NewLongArray(env_ptr, c_int(4))
        assert isinstance(long_array, Arrayref)
        assert long_array.arrayref == [0, 0, 0, 0]

        clib.test_NewFloatArray.restype = py_object
        float_array = clib.test_NewFloatArray(env_ptr, c_int(5))
        assert isinstance(long_array, Arrayref)
        assert float_array.arrayref == [0.0, 0.0, 0.0, 0.0, 0.0]

        clib.test_NewDoubleArray.restype = py_object
        double_array = clib.test_NewDoubleArray(env_ptr, c_int(6))
        assert isinstance(long_array, Arrayref)
        assert double_array.arrayref == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        clib.test_NewCharArray.restype = py_object
        char_array = clib.test_NewCharArray(env_ptr, c_int(3))
        assert isinstance(char_array, Arrayref)
        assert char_array.arrayref == ['\x00', '\x00', '\x00']

    def test_GetXArrayElements(self):
        clib.test_NewIntArray.restype = py_object
        int_array = clib.test_NewIntArray(env_ptr, c_int(2))
        assert isinstance(int_array, Arrayref)
        assert int_array.arrayref == [0, 0]
        clib.test_GetIntArrayElements.restype = c_int*2
        result = clib.test_GetIntArrayElements(env_ptr, py_object(int_array), c_int(False))
        for i in result:
            print i

    def test_GetSuperclass(self):
        jclsA = self.getclass('''
        class Glazz {}
        ''')
        jclsB = self.getclass('''
        interface Face{}
        ''',"Face")
        jclsC = self.getclass('''
        class Klazz extends Glazz implements Face {}
        ''')
        clsrefA = Classref(self.loader.getclass("java/lang/Class"), True, jclsA, self.loader)
        clsrefB = Classref(self.loader.getclass("java/lang/Class"), True, jclsB, self.loader)
        clsrefC = Classref(self.loader.getclass("java/lang/Class"), True, jclsC, self.loader)
        clib.test_GetSuperclass.restype = py_object
        result = clib.test_GetSuperclass(env_ptr, py_object(clsrefA))
        assert isinstance(result, Classref)
        assert result.class_type.__name__ == "java/lang/Object"
        result = clib.test_GetSuperclass(env_ptr, py_object(result))
        assert result == None
        result = clib.test_GetSuperclass(env_ptr, py_object(clsrefB))
        assert result == None
        result = clib.test_GetSuperclass(env_ptr, py_object(clsrefC))
        assert isinstance(result, Classref)
        assert result.class_type.__name__ == "Glazz"

    def test_IsAssignableFrom(self):
        jclsA = self.getclass('''
        class Glazz {}
        ''')
        jclsB = self.getclass('''
        interface Face{}
        ''',"Face")
        jclsC = self.getclass('''
        class Klazz extends Glazz implements Face {}
        ''')
        clsrefA = Classref(self.loader.getclass("java/lang/Class"), True, jclsA, self.loader)
        clsrefB = Classref(self.loader.getclass("java/lang/Class"), True, jclsB, self.loader)
        clsrefC = Classref(self.loader.getclass("java/lang/Class"), True, jclsC, self.loader)
        clib.test_IsAssignableFrom.restype = c_int
        result = clib.test_IsAssignableFrom(env_ptr, py_object(clsrefA), py_object(clsrefB))
        assert result == False
        result = clib.test_IsAssignableFrom(env_ptr, py_object(clsrefA), py_object(clsrefC))
        assert result == False
        result = clib.test_IsAssignableFrom(env_ptr, py_object(clsrefB), py_object(clsrefA))
        assert result == False
        result = clib.test_IsAssignableFrom(env_ptr, py_object(clsrefB), py_object(clsrefC))
        assert result == False
        result = clib.test_IsAssignableFrom(env_ptr, py_object(clsrefC), py_object(clsrefC))
        assert result == True
        result = clib.test_IsAssignableFrom(env_ptr, py_object(clsrefC), py_object(clsrefA))
        assert result == True
        result = clib.test_IsAssignableFrom(env_ptr, py_object(clsrefC), py_object(clsrefB))
        assert result == True

    def test_object_operations(self):
        jcls = self.getclass('''
        class Klazz 
        {
            static int i = 1;
            Klazz(){i=2;}
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        clib.test_AllocObject.restype = py_object
        result = clib.test_AllocObject(env_ptr, py_object(clsref))
        assert isinstance(result, Objectref)
        assert result.jcls.__name__ == jcls.__name__
        clib.test_GetObjectClass.restype = py_object
        result = clib.test_GetObjectClass(env_ptr, py_object(result))
        assert isinstance(result, Classref)
        assert result.class_type.__name__ == jcls.__name__
        jclsA = self.getclass('''
        interface Blub{}
        ''', "Blub")
        jclsB = self.getclass('''
        class Casti {}
        ''')
        jclsC = self.getclass('''
        class Bla extends Casti implements Blub{}
        ''')
        clsrefA = Classref(self.loader.getclass("java/lang/Class"), True, jclsA, self.loader)
        clsrefB = Classref(self.loader.getclass("java/lang/Class"), True, jclsB, self.loader)
        clsrefC = Classref(self.loader.getclass("java/lang/Class"), True, jclsC, self.loader)
        objref = Objectref(jclsB)
        objref2 = Objectref(jclsC)
        clib.test_IsInstanceOf.restype = c_int
        result = clib.test_IsInstanceOf(env_ptr, py_object(objref), py_object(clsrefA))
        assert result == False
        result = clib.test_IsInstanceOf(env_ptr, py_object(objref), py_object(clsrefB))
        assert result == True
        result = clib.test_IsInstanceOf(env_ptr, py_object(objref), py_object(clsrefC))
        assert result == False
        result = clib.test_IsInstanceOf(env_ptr, py_object(objref2), py_object(clsrefA))
        assert result == True
        result = clib.test_IsInstanceOf(env_ptr, py_object(objref2), py_object(clsrefB))
        assert result == True
        result = clib.test_IsInstanceOf(env_ptr, py_object(objref2), py_object(clsrefC))
        assert result == True
        clib.test_IsSameObject.restype = c_int
        objref1 = Objectref(jclsB)
        objref2 = Objectref(jclsB)
        objref3 = objref2
        result = clib.test_IsSameObject(env_ptr, py_object(objref1), py_object(objref2))
        assert result == False
        result = clib.test_IsSameObject(env_ptr, py_object(objref3), py_object(objref2))
        assert result == True

    def test_nonvirtual_call(self):
        jcls = self.getclass('''
        class Klazz
        {
            static int in = 1;
            public void vmethod(int i){in=i;}
            public boolean bmethod(boolean b){return !b;}
            public byte bymethod(byte by){return (byte)(by*2);}
            public short smethod(short s){return (short)(s*3);}
            public char cmethod(char c){return c;}
            public int imethod(int i){return i+10;}
            public long lmethod(long l){return l+1;}
            public float fmethod(float f){return f + 1.0f;}
            public double dmethod(double d){return d + 1.0;}
            public Klazz omethod(Klazz k){return k;}
        }
        ''')
        clsref = Classref(self.loader.getclass("java/lang/Class"), True, jcls, self.loader)
        objref = Objectref(jcls)

        fid = FieldID("in","I")
        clib.test_GetStaticIntField.restype = c_int
        result = clib.test_GetStaticIntField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 1
        methodId = MethodID("vmethod", "(I)V")
        args = Stack()
        args.push(41)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualVoidMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        result = clib.test_GetStaticIntField(env_ptr, py_object(clsref), py_object(fid))
        assert result == 41

        methodId = MethodID("omethod", "(LKlazz;)LKlazz;")
        args = Stack()
        args.push(objref)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualObjectMethodV.restype = py_object
        result = clib.test_CallNonvirtualObjectMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        assert result == objref

        methodId = MethodID("bmethod", "(Z)Z")
        args = Stack()
        args.push(True)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualBooleanMethodV.restype = c_int
        result = clib.test_CallNonvirtualBooleanMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        assert result == False

        methodId = MethodID("bymethod", "(B)B")
        args = Stack()
        args.push(10)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualByteMethodV.restype = c_int
        result = clib.test_CallNonvirtualByteMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        assert result == 20

        #methodId = MethodID("cmethod", "(C)C")
        #args = Stack()
        #args.push('B')
        #args.push(objref) # this
        #native.current_classloader = self.loader
        #clib.test_CallNonvirtualCharMethodV.restype = c_char
        #result = clib.test_CallNonvirtualCharMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        #assert result == 'B'

        methodId = MethodID("smethod", "(S)S")
        args = Stack()
        args.push(11)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualShortMethodV.restype = c_int
        result = clib.test_CallNonvirtualShortMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        assert result == 33

        methodId = MethodID("imethod", "(I)I")
        args = Stack()
        args.push(31)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualIntMethodV.restype = c_int
        result = clib.test_CallNonvirtualIntMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        assert result == 41

        methodId = MethodID("lmethod", "(J)J")
        args = Stack()
        args.push(40)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualLongMethodV.restype = c_long
        result = clib.test_CallNonvirtualLongMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        assert result == 41

        methodId = MethodID("fmethod", "(F)F")
        args = Stack()
        args.push(40.0)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualFloatMethodV.restype = c_float
        result = clib.test_CallNonvirtualFloatMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        assert result == 41.0

        methodId = MethodID("dmethod", "(D)D")
        args = Stack()
        args.push(40.0)
        args.push(objref) # this
        native.current_classloader = self.loader
        clib.test_CallNonvirtualDoubleMethodV.restype = c_double
        result = clib.test_CallNonvirtualDoubleMethodV(env_ptr, py_object(objref), py_object(clsref), py_object(methodId), py_object(args))
        assert result == 41.0
