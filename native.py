# -*- coding: utf-8 -*-
# This module implements the JNI Env Functions which make
# it possible to native(C/C++)-Code to interact with the JVM

from objectmodel import Objectref, Arrayref, Classref, Stack, JException
from helper import make_String, unpack_string
from classloader import descriptor
from ctypes import cdll
from _ctypes import PyObj_FromPtr
from ctypes import Structure, Union
from ctypes import c_int, c_float, c_byte, c_void_p, CFUNCTYPE, pointer, addressof, c_char_p,POINTER, py_object, c_char, c_wchar, c_long, c_float, c_double, cast

# FIXME: this is the classloader which calles the native method
# this variable is set by the classloader itself before every native-method
# -call
current_classloader = None

# TODO: this is no good design
# if there is an exception on the java side or via throw on c side
# it is remeberd here. This variable should only be read/wrote in 
# call_native method inside the interpreter
exception_after_native_call = None

class FieldID(object):
    def __init__(self, name , sig):
        self.name = name
        self.sig = sig

class MethodID(object):
    def __init__(self, name, sig):
        self.name = name
        self.sig = sig

class jvalues(Union):
    _fields_ = [("z", c_int),
                ("b", c_int),
                ("c", c_char),
                ("s", c_int),
                ("i", c_int),
                ("j", c_long),
                ("f", c_float),
                ("d", c_double),
                ("l", py_object)]

class LocalRefFrame(object):
    refs = []

# TODO: Implement me
GlobalRefs = []
LocalRefFrames = []
WeakGlobalRef = []

class JNINativeInterface(Structure):
    _fields_ = [
    ("reserved0", c_void_p),
    ("reserved1", c_void_p),
    ("reserved2", c_void_p),
    ("reserved3", c_void_p),
    ("GetVersion", CFUNCTYPE(c_int, c_void_p)),
    ("DefineClass", CFUNCTYPE(py_object, c_void_p, c_char_p, POINTER(py_object))),
    ("FindClass", CFUNCTYPE(py_object, c_void_p, c_char_p)),
    ("FromReflectedMethod", CFUNCTYPE(py_object, c_void_p, py_object)), 
    ("FromReflectedField", CFUNCTYPE(py_object, c_void_p, py_object)),
    ("ToReflectedMethod", CFUNCTYPE(py_object, c_void_p, py_object, py_object)), 
    ("GetSuperclass", CFUNCTYPE(py_object, c_void_p, py_object)),
    ("IsAssignableFrom", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("ToReflectedField", CFUNCTYPE(py_object, c_void_p, py_object, py_object)),
    ("Throw", CFUNCTYPE(c_int, c_void_p, py_object)),
    ("ThrowNew", CFUNCTYPE(c_int, c_void_p, py_object, c_char_p)), 
    ("ExceptionOccurred", CFUNCTYPE(py_object, c_void_p)),
    ("ExceptionDescribe", CFUNCTYPE(c_void_p, c_void_p)),
    ("ExceptionClear", CFUNCTYPE(c_void_p, c_void_p)),
    ("FatalError", CFUNCTYPE(c_void_p, c_void_p, c_char_p)),
    ("PushLocalFrame", CFUNCTYPE(c_int, c_void_p, c_int)),
    ("PopLocalFrame", CFUNCTYPE(py_object, c_void_p, py_object)),
    ("NewGlobalRef", CFUNCTYPE(py_object, c_void_p, py_object)),
    ("DeleteGlobalRef", CFUNCTYPE(c_void_p, c_void_p, py_object)),
    ("DeleteLocalRef", CFUNCTYPE(c_void_p, c_void_p, py_object)),
    ("IsSameObject", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("NewLocalRef", CFUNCTYPE(py_object, c_void_p, py_object)),
    ("EnsureLocalCapacity", CFUNCTYPE(c_int, c_void_p, c_int)),
    ("AllocObject", CFUNCTYPE(py_object, c_void_p, py_object)),
    ("NewObject", c_void_p),
    ("NewObjectV", CFUNCTYPE(py_object, c_void_p, py_object, py_object)),
    ("NewObjectA", CFUNCTYPE(py_object, c_void_p, py_object, py_object, POINTER(jvalues))), 
    ("GetObjectClass", CFUNCTYPE(py_object, c_void_p, py_object)),
    ("IsInstanceOf", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("GetMethodID", CFUNCTYPE(py_object, c_void_p, py_object, c_char_p, c_char_p)),
    ("CallObjectMethod", c_void_p),
    ("CallObjectMethodV", CFUNCTYPE(py_object, c_void_p, py_object, py_object, py_object)),
    ("CallObjectMethodA", CFUNCTYPE(py_object, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallBooleanMethod", c_void_p), 
    ("CallBooleanMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)),
    ("CallBooleanMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallByteMethod", c_void_p),
    ("CallByteMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)),
    ("CallByteMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallCharMethod", c_void_p), 
    ("CallCharMethodV", CFUNCTYPE(c_char, c_void_p, py_object, py_object, py_object)),
    ("CallCharMethodA", CFUNCTYPE(c_char, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallShortMethod", c_void_p),
    ("CallShortMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)),
    ("CallShortMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallIntMethod", c_void_p), 
    ("CallIntMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)),
    ("CallIntMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallLongMethod", c_void_p),
    ("CallLongMethodV", CFUNCTYPE(c_long, c_void_p, py_object, py_object, py_object)),
    ("CallLongMethodA", CFUNCTYPE(c_long, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallFloatMethod", c_void_p),
    ("CallFloatMethodV", CFUNCTYPE(c_float, c_void_p, py_object, py_object, py_object)),
    ("CallFloatMethodA", CFUNCTYPE(c_float, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallDoubleMethod", c_void_p),
    ("CallDoubleMethodV", CFUNCTYPE(c_double, c_void_p, py_object, py_object, py_object)),
    ("CallDoubleMethodA", CFUNCTYPE(c_double, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallVoidMethod", c_void_p), 
    ("CallVoidMethodV", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object)),
    ("CallVoidMethodA", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallNonvirtualObjectMethod", c_void_p),
    ("CallNonvirtualObjectMethodV", CFUNCTYPE(py_object, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualObjectMethodA", CFUNCTYPE(py_object, c_void_p, py_object, py_object, py_object, POINTER(jvalues))),
    ("CallNonvirtualBooleanMethod", c_void_p),
    ("CallNonvirtualBooleanMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualBooleanMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, POINTER(jvalues))),
    ("CallNonvirtualByteMethod", c_void_p),
    ("CallNonvirtualByteMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualByteMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, POINTER(jvalues))),
    ("CallNonvirtualCharMethod", c_void_p), 
    ("CallNonvirtualCharMethodV", CFUNCTYPE(c_char, c_void_p, py_object, py_object, py_object, py_object)), 
    ("CallNonvirtualCharMethodA", CFUNCTYPE(c_char, c_void_p, py_object, py_object, py_object, POINTER(jvalues))), 
    ("CallNonvirtualShortMethod", c_void_p), 
    ("CallNonvirtualShortMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualShortMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, POINTER(jvalues))),
    ("CallNonvirtualIntMethod", c_void_p),
    ("CallNonvirtualIntMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualIntMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, POINTER(jvalues))),
    ("CallNonvirtualLongMethod", c_void_p), 
    ("CallNonvirtualLongMethodV", CFUNCTYPE(c_long, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualLongMethodA", CFUNCTYPE(c_long, c_void_p, py_object, py_object, py_object, POINTER(jvalues))),
    ("CallNonvirtualFloatMethod", c_void_p),
    ("CallNonvirtualFloatMethodV", CFUNCTYPE(c_float, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualFloatMethodA", CFUNCTYPE(c_float, c_void_p, py_object, py_object, py_object, POINTER(jvalues))), 
    ("CallNonvirtualDoubleMethod", c_void_p), 
    ("CallNonvirtualDoubleMethodV", CFUNCTYPE(c_double, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualDoubleMethodA", CFUNCTYPE(c_double, c_void_p, py_object, py_object, py_object, POINTER(jvalues))), 
    ("CallNonvirtualVoidMethod", c_void_p), 
    ("CallNonvirtualVoidMethodV", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object, py_object)),
    ("CallNonvirtualVoidMethodA", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object, POINTER(jvalues))), 
    ("GetFieldID", CFUNCTYPE(py_object, c_void_p, py_object, c_char_p, c_char_p)),
    ("GetObjectField", CFUNCTYPE(py_object, c_void_p, py_object, py_object)),
    ("GetBooleanField", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("GetByteField", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("GetCharField", CFUNCTYPE(c_char, c_void_p, py_object, py_object)),
    ("GetShortField", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("GetIntField", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("GetLongField", CFUNCTYPE(c_long, c_void_p, py_object, py_object)), 
    ("GetFloatField", CFUNCTYPE(c_float, c_void_p, py_object, py_object)),
    ("GetDoubleField", CFUNCTYPE(c_double, c_void_p, py_object, py_object)),
    ("SetObjectField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object)),
    ("SetBooleanField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)),
    ("SetByteField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)),
    ("SetCharField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_char)), 
    ("SetShortField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)),
    ("SetIntField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)), 
    ("SetLongField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_long)),
    ("SetFloatField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_float)),
    ("SetDoubleField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_double)),
    ("GetStaticMethodID", CFUNCTYPE(py_object, c_void_p, py_object, c_char_p, c_char_p)),
    ("CallStaticObjectMethod", c_void_p), 
    ("CallStaticObjectMethodV", CFUNCTYPE(py_object, c_void_p, py_object, py_object, py_object)), 
    ("CallStaticObjectMethodA", CFUNCTYPE(py_object, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallStaticBooleanMethod", c_void_p),
    ("CallStaticBooleanMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)),
    ("CallStaticBooleanMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallStaticByteMethod", c_void_p), 
    ("CallStaticByteMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)),
    ("CallStaticByteMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallStaticCharMethod", c_void_p), 
    ("CallStaticCharMethodV", CFUNCTYPE(c_char, c_void_p, py_object, py_object, py_object)),
    ("CallStaticCharMethodA", CFUNCTYPE(c_char, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallStaticShortMethod", c_void_p),
    ("CallStaticShortMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)), 
    ("CallStaticShortMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))), 
    ("CallStaticIntMethod", c_void_p),
    ("CallStaticIntMethodV", CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)),
    ("CallStaticIntMethodA", CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallStaticLongMethod", c_void_p), 
    ("CallStaticLongMethodV", CFUNCTYPE(c_long, c_void_p, py_object, py_object, py_object)),
    ("CallStaticLongMethodA", CFUNCTYPE(c_long, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallStaticFloatMethod", c_void_p),
    ("CallStaticFloatMethodV",  CFUNCTYPE(c_float, c_void_p, py_object, py_object, py_object)),
    ("CallStaticFloatMethodA", CFUNCTYPE(c_float, c_void_p, py_object, py_object, POINTER(jvalues))),
    ("CallStaticDoubleMethod", c_void_p), 
    ("CallStaticDoubleMethodV", CFUNCTYPE(c_double, c_void_p, py_object, py_object, py_object)), 
    ("CallStaticDoubleMethodA", CFUNCTYPE(c_double, c_void_p, py_object, py_object, POINTER(jvalues))), 
    ("CallStaticVoidMethod", c_void_p), 
    ("CallStaticVoidMethodV", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object)),
    ("CallStaticVoidMethodA", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, POINTER(jvalues))), 
    ("GetStaticFieldID", CFUNCTYPE(py_object, c_void_p, py_object, c_char_p, c_char_p)),
    ("GetStaticObjectField", CFUNCTYPE(py_object, c_void_p, py_object, py_object)),
    ("GetStaticBooleanField", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("GetStaticByteField", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("GetStaticCharField", CFUNCTYPE(c_wchar, c_void_p, py_object, py_object)),
    ("GetStaticShortField", CFUNCTYPE(c_int, c_void_p, py_object, py_object)), 
    ("GetStaticIntField", CFUNCTYPE(c_int, c_void_p, py_object, py_object)),
    ("GetStaticLongField", CFUNCTYPE(c_long, c_void_p, py_object, py_object)),
    ("GetStaticFloatField", CFUNCTYPE(c_float, c_void_p, py_object, py_object)),
    ("GetStaticDoubleField", CFUNCTYPE(c_double, c_void_p, py_object, py_object)),
    ("SetStaticObjectField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object)),
    ("SetStaticBooleanField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)),
    ("SetStaticByteField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)),
    ("SetStaticCharField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_char)),
    ("SetStaticShortField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)), 
    ("SetStaticIntField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)),
    ("SetStaticLongField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_long)), 
    ("SetStaticFloatField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_float)),
    ("SetStaticDoubleField", CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_double)), 
    ("NewString", CFUNCTYPE(py_object, c_void_p, c_char_p, c_int)), 
    ("GetStringLength", CFUNCTYPE(c_int, c_void_p, py_object)), 
    ("GetStringChars", c_void_p), 
    ("ReleaseStringChars", CFUNCTYPE(c_void_p, c_void_p, py_object, c_char_p)), 
    ("NewStringUTF", CFUNCTYPE(py_object, c_void_p, c_char_p)), 
    ("GetStringUTFLength", CFUNCTYPE(c_int, c_void_p, py_object)), 
    ("GetStringUTFChars", c_void_p), 
    ("ReleaseStringUTFChars", CFUNCTYPE(c_void_p, c_void_p, py_object, c_char_p)),
    ("GetArrayLength", CFUNCTYPE(c_int, c_void_p, py_object)), 
    ("NewObjectArray", CFUNCTYPE(py_object, c_void_p, c_int, py_object, c_void_p)),
    ("GetObjectArrayElement", CFUNCTYPE(py_object, c_void_p, py_object, c_int)), 
    ("SetObjectArrayElement", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, py_object)),
    ("NewBooleanArray", CFUNCTYPE(py_object, c_void_p, c_int)), 
    ("NewByteArray", CFUNCTYPE(py_object, c_void_p, c_int)),
    ("NewCharArray", CFUNCTYPE(py_object, c_void_p, c_int)),
    ("NewShortArray", CFUNCTYPE(py_object, c_void_p, c_int)),
    ("NewIntArray", CFUNCTYPE(py_object, c_void_p, c_int)),
    ("NewLongArray", CFUNCTYPE(py_object, c_void_p, c_int)),
    ("NewFloatArray", CFUNCTYPE(py_object, c_void_p, c_int)), 
    ("NewDoubleArray", CFUNCTYPE(py_object, c_void_p, c_int)),
    ("GetBooleanArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)), 
    ("GetByteArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)),
    ("GetCharArrayElements", c_void_p), 
    ("GetShortArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)),
    ("GetIntArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)), 
    ("GetLongArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)),
    ("GetFloatArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)), 
    ("GetDoubleArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)), 
    ("ReleaseBooleanArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_int), c_int)), 
    ("ReleaseByteArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_int), c_int)),
    ("ReleaseCharArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_char), c_int)), 
    ("ReleaseShortArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_int), c_int)),
    ("ReleaseIntArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_int), c_int)), 
    ("ReleaseLongArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_long), c_int)),
    ("ReleaseFloatArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_float), c_int)),
    ("ReleaseDoubleArrayElements", CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_double), c_int)),
    ("GetBooleanArrayRegion",CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))),
    ("GetByteArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))),
    ("GetCharArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_char))),
    ("GetShortArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))),
    ("GetIntArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))),
    ("GetLongArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_long))), 
    ("GetFloatArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_float))),
    ("GetDoubleArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_double))), 
    ("SetBooleanArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))),
    ("SetByteArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_byte))), 
    ("SetCharArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_char))),
    ("SetShortArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))), 
    ("SetIntArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))),
    ("SetLongArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_long))), 
    ("SetFloatArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_float))),
    ("SetDoubleArrayRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_double))), 
    ("RegisterNatives", CFUNCTYPE(c_int, c_void_p, py_object, c_void_p, c_int)),
    ("UnregisterNatives", CFUNCTYPE(c_int, c_void_p, py_object)),
    ("MonitorEnter", CFUNCTYPE(c_int, c_void_p, py_object)),
    ("MonitorExit", CFUNCTYPE(c_int, c_void_p, py_object)),
    ("GetJavaVM", CFUNCTYPE(c_int, c_void_p, c_void_p)),
#JNI 1.2 functions
    ("GetStringRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_char))),
    ("GetStringUTFRegion", CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER((c_char)))), 
    ("GetPrimitiveArrayCritical", c_void_p), 
    ("ReleasePrimitiveArrayCritical", c_void_p),
    ("GetStringCritical", CFUNCTYPE(c_char_p, c_void_p, c_char_p, c_int)), 
    ("ReleaseStringCritical", CFUNCTYPE(c_void_p, c_void_p, py_object, c_char_p)), 
    ("NewWeakGlobalRef", CFUNCTYPE(py_object, c_void_p, py_object)),
    ("DeleteWeakGlobalRef", CFUNCTYPE(c_void_p, c_void_p, py_object)), 
    ("ExceptionCheck", CFUNCTYPE(c_int, c_void_p)),
    ("NewDirectByteBuffer", c_void_p), 
    ("GetDirectBufferAddress", c_void_p),
    ("GetDirectBufferCapacity", c_void_p), 
    ("GetObjectRefType", c_void_p)]

# some consts 
jni_version = 1

# takes a String with a method-signatur and
# returns a list with the letters which describe
# the type of the args. E.g Byte=B Object=L
def method_sig_to_type_list(method_sig_str):
    arg_list = []
    skip_until_semi = False
    for i in list(method_sig_str.replace("(","")):
        if i==")":
            break
        elif i=="L" and not skip_until_semi:
            arg_list.append(i)
            skip_until_semi = True
        elif i==";" and skip_until_semi:
            skip_until_semi = False
        elif not skip_until_semi:
            arg_list.append(i)
    return arg_list

# helper function which puts the varargs from
# a c-side funtion into a stack object.
# This args can come from  e.g CallMethodX or NewObjectA..
# TODO: check if the p_jvales have the right type
def jvalues_to_stack(p_jvalue, _methodID):
    arg_list = method_sig_to_type_list(_methodID.sig)
    stack = Stack()
    index = 0
    for arg in arg_list:
        if arg == "Z":
            stack.push(p_jvalue[index].z)
        elif arg == "B":
            stack.push(p_jvalue[index].b)
        elif arg == "C":
            stack.push(p_jvalue[index].c)
        elif arg == "S":
            stack.push(p_jvalue[index].s)
        elif arg == "I":
            stack.push(p_jvalue[index].i)
        elif arg == "J":
            stack.push(p_jvalue[index].j)
        elif arg == "F":
            stack.push(p_jvalue[index].f)
        elif arg == "D":
            stack.push(p_jvalue[index].d)
        elif arg == "L":
            stack.push(p_jvalue[index].l)
        else:
            raise Exception("parsing error in jvalues_to_stack")
        index = index + 1
    return stack

# the implementations:
def JNI_FindClass(_JNIEnv, _char):
    loader = current_classloader
    jcls = loader.getclass(_char)
    clsref = Classref(loader.getclass("java/lang/Class"), True, jcls, loader)
    return clsref

def JNI_GetVersion(_JNIEnv):
    # TODO: getVersion()
    return jni_version 

def JNI_DefineClass(_JNIEnv, _char, _py_obj_p):
    raise NotImplemented("Define Class")
    return None # object

# Causes a java.lang.Throwable object to be thrown.
# TODO: return negative value on failure.
def JNI_Throw(_JNIEnv, _jthrowable):
    global exception_after_native_call
    exception_after_native_call = JException(_jthrowable)
    return 0 #success

# Constructs an exception object from the specified class with the message specified by message and causes that exception to be thrown.
# TODO: return negative value on failure.
def JNI_ThrowNew(_JNIEnv, _jclass, p_char):
    loader = current_classloader
    stack = Stack()
    stack.push(make_String(p_char, loader))
    objref = Objectref(_jclass.class_type, True)
    stack.push(objref) #this
    cls = _jclass.class_type.cls
    const = cls.constant_pool
    method = None
    # search for String-Constructor
    for m in cls.methods:
        name = const[m.name_index]
        sig = const[m.descriptor_index]
        if "<init>" == name and "(Ljava/lang/String;)V" == sig:
            method = m
            break
    assert not method == None # wrong descr or name?
    descr = descriptor(const[method.descriptor_index])
    # call Constructor with the String p_char
    current_classloader.invoke_method(cls, method, descr, stack)
    # Exceptionobject created....
    global exception_after_native_call
    exception_after_native_call = JException(objref)
    return 0 #success


# Determines if an exception is being thrown. The exception stays being thrown until either the native code calls ExceptionClear(), or the Java code handles the exception.
def JNI_ExceptionOccurred(_JNIEnv):
    global exception_after_native_call
    if exception_after_native_call:
        return exception_after_native_call
    return None

# Prints an exception and a backtrace of the stack to a system error-reporting channel, such as stderr. This is a convenience routine provided for debugging.
def JNI_ExceptionDescribe(_JNIEnv):
    raise NotImplemented("ExceptionDescribe")

# Clears any exception that is currently being thrown. If no exception is currently being thrown, this routine has no effect.
def JNI_ExceptionClear(_JNIEnv):
    global exception_after_native_call
    exception_after_native_call = None 

# Raises a fatal error and does not expect the VM to recover. This function does not return.
def JNI_FatalError(_JNIEnv, p_char):
    raise NotImplemented("FatalError")

# We introduce a convenience function to check for pending exceptions without creating a local reference to the exception object.
def JNI_ExceptionCheck(_JNIEnv):
    global exception_after_native_call
    return not exception_after_native_call==None 

#If clazz represents any class other than the class Object, then this function returns the object that represents the superclass of the class specified by clazz. 
# If clazz specifies the class Object, or clazz represents an interface, this function returns NULL.
def JNI_GetSuperclass(_JNIEnv, _jclass):
    assert isinstance(_jclass, Classref)
    if _jclass.class_type.__name__ == "java/lang/Object" or _jclass.class_type.is_interface:
        return None
    else:
        jcls = _jclass.class_type.supercls
        loader = current_classloader
        return Classref(loader.getclass("java/lang/Class"), True, jcls, loader)

# Determines whether an object of clazz1 can be safely cast to clazz2.
# FIXME: two classes are identicale if they have the same names
def JNI_IsAssignableFrom(_JNIEnv, _jclass1, _jclass2):
    assert isinstance(_jclass1, Classref)
    assert isinstance(_jclass2, Classref)
    if _jclass1.class_type.cls == _jclass2.class_type.cls:
        return True
    for num in _jclass1.class_type.cls.interfaces:
        cls_info = _jclass1.class_type.cls.constant_pool[num]
        name = _jclass1.class_type.cls.constant_pool[cls_info.name_index]
        if name == _jclass2.class_type.__name__:
            return True
    acls = _jclass1.class_type
    while not acls.__name__ == "java/lang/Object":
        acls = acls.supercls
        if acls.__name__ == _jclass2.class_type.__name__:
            return True
    return False

# returns the field ID for an instance (nonstatic) field of a class. The field is specified by its name and signature. The Get<type>Field and Set<type>Field families of accessor functions use field IDs to retrieve object fields. 
def JNI_GetFieldID(_JNIEnv, _jclass, _char_p, _char_p2):
    assert isinstance(_jclass, Classref)
    assert _jclass.class_type.fields.has_key(_char_p, descriptor(_char_p2))
    jfieldid = FieldID(_char_p, _char_p2)
    return jfieldid

# This family of accessor routines returns the value of an instance (nonstatic) field of an object. The field to access is specified by a field ID obtained by calling GetFieldID().
def JNI_GetXField(_JNIEnv, _jobject, _jfieldID):
    assert isinstance(_jobject, Objectref)
    assert isinstance(_jfieldID, FieldID)
    result = _jobject.fields.get(unicode(_jfieldID.name), descriptor(_jfieldID.sig))
    if _jfieldID.sig == "C":
        result = chr(result) #char in java are ints
    return result


# This family of accessor routines sets the value of an instance (nonstatic) field of an object. The field to access is specified by a field ID obtained by calling GetFieldID().
def JNI_SetXField(_JNIEnv, _jobject, _jfieldID, X):
    _jobject.fields.set(unicode(_jfieldID.name), X, descriptor(_jfieldID.sig))


# Returns the number of elements in the array.
def JNI_GetArrayLength(_JNIEnv, _array):
    assert isinstance(_array, Arrayref)
    return len(_array.arrayref)

# Returns an element of an Object array.
def JNI_GetObjectArrayElement(_JNIEnv, _array, _jsize):
    assert isinstance(_array, Arrayref)
    assert isinstance(_jsize, int) # index
    return _array.arrayref[_jsize]

# Constructs a new array holding objects in class elementClass. All elements are initially set to initialElement
def JNI_NewObjectArray(_JNIEnv, _jsize, _jclass, _jobject):
    # convert a cpointer(c_void_p) to a py_object
    if _jobject:
        _jobject = PyObj_FromPtr(_jobject)
    else:
        _jobject = None
    #_jobject.fields.print_map()
    assert isinstance(_jsize, int)
    #if not isinstance(_jobject, Objectref):
    #    _jobject = Objectref(_jclass.class_type, True)
    return Arrayref([Objectref(_jclass.class_type)]*_jsize, _jobject, current_classloader.getclass("[Ljava.lang.Object;"))

# Sets an element of an Object array.
def JNI_SetObjectArrayElement(_JNIEnv, _array, _jsize, _jobject):
    assert isinstance(_jsize, int)
    assert isinstance(_array, Arrayref)
    _array.arrayref[_jsize] = _jobject

# A family of operations used to construct a new primitive array object
def JNI_NewXArray(default_item, type_char):
    def array_method(_JNIEnv, _jsize):
        assert isinstance(_jsize, int)
        return Arrayref([default_item]*_jsize, default_item, current_classloader.getclass("["+type_char))
    return array_method

# Constructs a new java.lang.String object from an array of Unicode characters.
def JNI_NewString(_JNIEnv, _jchar_p, _jsize):
    loader = current_classloader
    return make_String(_jchar_p, loader) # FIXME returns a UTF8 String

# Returns the length (the count of Unicode characters) of a Java string.
def JNI_GetStringLength(_JNIEnv, _jstring):
    assert isinstance(_jstring, Objectref)
    assert _jstring.jcls.__name__ == "java/lang/String"
    return len(unpack_string(_jstring))

# Returns a pointer to the array of Unicode characters of the string. This pointer is valid until ReleaseStringchars() is called. 
# If isCopy is not NULL, then *isCopy is set to JNI_TRUE if a copy is made; or it is set to JNI_FALSE if no copy is made.
#def JNI_GetStringChars(_JNIEnv, _jstring, _jboolean):
    #if not _jboolean == None:
        #_jboolean = c_int(False) # no copy has been made 
    #assert isinstance(_jstring, Objectref)
    #assert _jstring.jcls.__name__ == "java/lang/String"
    #return unpack_string(_jstring)

# Informs the VM that the native code no longer needs access to chars. The chars argument is a pointer obtained from string using GetStringChars().
def JNI_ReleaseStringChars(_JNIEnv, _jstring, _jchar_p):
    pass # XXX

# Constructs a new java.lang.String object from an array of characters in modified UTF-8 encoding.
def JNI_NewStringUTF(_JNIEnv, _jchar_p):
    loader = current_classloader
    return make_String(_jchar_p, loader)

# Returns the length in bytes of the modified UTF-8 representation of a string.
def JNI_GetStringUTFLength(_JNIEnv, _jstring):
    assert isinstance(_jstring, Objectref)
    assert _jstring.jcls.__name__ == "java/lang/String"
    return len(unpack_string(_jstring)) 

# Returns a pointer to an array of bytes representing the string in modified UTF-8 encoding. This array is valid until it is released by ReleaseStringUTFChars(). 
# If isCopy is not NULL, then *isCopy is set to JNI_TRUE if a copy is made; or it is set to JNI_FALSE if no copy is made.
#def JNI_GetStringUTFChars(_JNIEnv, _jstring, _jboolean):
    #if not _jboolean == None:
        #_jboolean = c_int(False) # no copy has been made 
    #assert isinstance(_jstring, Objectref)
    #assert _jstring.jcls.__name__ == "java/lang/String"
    #return unpack_string(_jstring)

# Informs the VM that the native code no longer needs access to utf. The utf argument is a pointer derived from string using GetStringUTFChars().
def JNI_ReleaseStringUTFChars(_JNIEnv, _jstring, _char_p):
    pass # XXX

# Copies len number of Unicode characters beginning at offset start to the given buffer buf. 
# Throws StringIndexOutOfBoundsException on index overflow.
def JNI_GetStringRegion(_JNIEnv, _jstring, _jsize1, _jsize2, _jchar_p):
    pystr = unpack_string(_jstring)
    if len(pystr[_jsize1:])> _jsize2:
        throw_native_exception("StringIndexOutOfBoundsException")
    else:
        result = pystr[_jsize1:_jsize1+_jsize2]
        #print _jchar_p
        for i in range(len(result)):
            _jchar_p[i] = result[i]
        _jchar_p[i+1] = '\0'

# Translates len number of Unicode characters beginning at offset start into modified UTF-8 encoding and place the result in the given buffer buf. 
# Throws StringIndexOutOfBoundsException on index overflow.
# FIXME: ignores unicode property
def JNI_GetStringUTFRegion(_JNIEnv, _jstring, _jsize1, _jsize2, _jchar_p):
    pystr = unpack_string(_jstring)
    if len(pystr[_jsize1:])> _jsize2:
        throw_native_exception("StringIndexOutOfBoundsException")
    else:
        result = pystr[_jsize1:_jsize1+_jsize2]
        for i in range(len(result)):
            _jchar_p[i] = str(result[i])
        _jchar_p[i+1] = '\0'

# If possible, the VM returns a pointer to string elements; otherwise, a copy is made
def JNI_GetStringCritical(_JNIEnv, _jstring, _jboolean):
    if not _jboolean == None:
        _jboolean = c_int(False) # no copy has been made 
    #print _jstring.value
    return _jstring

# Returns the method ID for an instance (nonstatic) method of a class or interface. The method may be defined in one of the clazz’s superclasses and inherited by clazz. The method is determined by its name and signature.
def JNI_GetMethodID(_JNIEnv, _jclass, _char_p1, _char_p2):
    return MethodID(_char_p1, _char_p2)

# The CallNonvirtual<type>Method families of routines and the Call<type>Method families of routines are different. Call<type>Method routines invoke the method based on the class of the object, while CallNonvirtual<type>Method routines invoke the method based on the class, designated by the clazz parameter, from which the method ID is obtained. The method ID must be obtained from the real class of the object or from one of its superclasses.
def JNI_CallNonvirtualXMethodV(_JNIEnv, _jobject, _jclass, _jmethodID, _va_list):
    return JNI_CallXMethodV(_JNIEnv, _jobject, _jmethodID, _va_list) # XXX

def JNI_CallNonvirtualXMethodA(_JNIEnv, _jobject, _jclass, _jmethodID, p_jvalue):
    stack = jvalues_to_stack(p_jvalue, _methodID)
    stack.push(_jobject)  ### maybe wrong
    return JNI_CallNonvirtualXMethodV(_JNIEnv, _jobject, _jclass, _jmethodID, stack)

def JNI_CallStaticXMethodA(_JNIEnv, _jclass, _methodID, p_jvalue):
    stack = jvalues_to_stack(p_jvalue, _methodID)
    return JNI_CallStaticXMethodV(_JNIEnv, _jclass, _methodID, stack)

def JNI_CallXMethodA(_JNIEnv, _jobject, _methodID, p_jvalue):
    stack = jvalues_to_stack(p_jvalue, _methodID)
    stack.push(_jobject) 
    #TODO: push the this ref is this the task of a JVM???
    return JNI_CallXMethodV(_JNIEnv, _jobject, _methodID, stack)


# This family of operations invokes a static method on a Java object, according to the specified method ID
# TODO: arg is a _jclass not an object
def JNI_CallStaticXMethodV(_JNIEnv, _jclass, _jmethodID, _va_list):
    objref = Objectref(_jclass.class_type)
    return JNI_CallXMethodV(_JNIEnv, objref, _jmethodID, _va_list)


# Programmers place all arguments to the method in an args argument of type va_list that immediately follows the methodID argument. The Call<type>MethodV routine accepts the arguments, and, in turn, passes them to the Java method that the programmer wishes to invoke.
def JNI_CallXMethodV(_JNIEnv, _jobject, _jmethodID, _va_list):
    assert not current_classloader == None
    assert isinstance(_jobject, Objectref) # FIXME: static call gives Classref as paramter
    assert isinstance(_jmethodID, MethodID)
    assert isinstance(_va_list, Stack)
    cls = _jobject.jcls.cls
    const = cls.constant_pool
    method = None
    for m in cls.methods:
        name = const[m.name_index]
        sig = const[m.descriptor_index]
        #print name, sig
        if _jmethodID.name== name and _jmethodID.sig == sig:
            method = m
            break
    assert not method == None # wrong descr or name?
    descr = descriptor(const[method.descriptor_index])
    try:
        X = current_classloader.invoke_method(cls, method, descr, _va_list)
    except JException, je:
        global exception_after_native_call
        # the execution of the java code has thrown an Excption
        # this Exception can not be handele here. It must be
        # handled via C-Code+Exception Clear or by the vm after the
        # native call in call_native in interp.py
        exception_after_native_call = je
    current_classloader == None# BUG ??
    return X

# Returns the field ID for a static field of a class. The field is specified by its name and signature. The GetStatic<type>Field and SetStatic<type>Field families of accessor functions use field IDs to retrieve static fields.
def JNI_GetStaticFieldID(_JNIEnv, _jclass, _char_p, _char_p2):
    assert isinstance(_jclass, Classref)
    assert _jclass.class_type.static_fields.has_key(_char_p, descriptor(_char_p2))
    jfieldid = FieldID(_char_p, _char_p2)
    return jfieldid

# This family of accessor routines returns the value of a static field of an object. The field to access is specified by a field ID, which is obtained by calling GetStaticFieldID().
def JNI_GetStaticXField(_JNIEnv, _jclass, _jfieldID):
    assert isinstance(_jclass, Classref)
    result = _jclass.class_type.static_fields.get(unicode(_jfieldID.name), descriptor(_jfieldID.sig))
    if _jfieldID.sig == "C":
        result = chr(result) # map java int to c char
    return result

# This family of accessor routines sets the value of a static field of an object. The field to access is specified by a field ID, which is obtained by calling GetStaticFieldID().
def JNI_SetStaticXField(_JNIEnv, _jclass, _jfieldID, X):
    assert isinstance(_jclass, Classref)
    _jclass.class_type.static_fields.set(unicode(_jfieldID.name), X, descriptor(_jfieldID.sig))

# Allocates a new Java object without invoking any of the constructors for the object. Returns a reference to the object. 
# The clazz argument must not refer to an array class.
def JNI_AllocObject(_JNIEnv, _jclass):
    assert isinstance(_jclass, Classref)
    return Objectref(_jclass.class_type, False) # ref is null

# Returns the class of an object.
def JNI_GetObjectClass(_JNIEnv, _jobject):
    assert isinstance(_jobject, Objectref)
    jcls = _jobject.jcls
    loader = current_classloader
    return Classref(loader.getclass("java/lang/Class"), True, jcls, loader)


# Tests whether an object is an instance of a class.
def JNI_IsInstanceOf(_JNIEnv, _jobject, _jclass):
    assert isinstance(_jclass, Classref)
    assert isinstance(_jobject, Objectref)
    if _jobject== None:
        return True
    if _jobject.jcls.cls == _jclass.class_type.cls:
        return True
    for num in _jobject.jcls.cls.interfaces:
        cls_info = _jobject.jcls.cls.constant_pool[num]
        name = _jobject.jcls.cls.constant_pool[cls_info.name_index]
        if name == _jclass.class_type.__name__:
            return True
    acls = _jobject.jcls
    while not acls.__name__ == "java/lang/Object":
        acls = acls.supercls
        if acls.__name__ == _jclass.class_type.__name__:
            return True
    return False

# Tests whether two references refer to the same Java object.
def JNI_IsSameObject(_JNIEnv, _jobject1, _jobject2):
    assert isinstance(_jobject1, Objectref)
    assert isinstance(_jobject2, Objectref)
    return _jobject1 == _jobject2

# A family of functions that informs the VM that the native code no longer needs access to elems. The elems argument is a pointer derived from array using the corresponding Get<PrimitiveType>ArrayElements() function. If necessary, this function copies back all changes made to elems to the original array.
def JNI_ReleaseXArrayElements(a_c_type):
    def method(_JNIEnv, _array, _nativetype_p, _jint):
        assert isinstance(_array, Arrayref)
        raise NotImplemented("ReleaseXArrayElements")
    return method

# A family of functions that returns the body of the primitive array
# todo:change getobjectarrayelements ?
# XXX: no RPython
def JNI_GetXArrayElements(a_c_type):
    def get_method(_JNIEnv, _array, _jboolean):
        assert isinstance(_array, Arrayref)
        length = len(_array.arrayref)
        assert isinstance(length, int)
        if length == 0:
            return None
        if not _jboolean == None:
            _jboolean = c_int(False) # no copy has been made 
        array_type = a_c_type * length
        string = "array_type(_array.arrayref[0]"
        for i in range(length-1):
            string += ", _array.arrayref["+str(i+1)+"]"
        string += ")"
        carray = eval(string)
        #print carray
        return cast(carray, c_void_p)
    return get_method

# A family of functions that copies a region of a primitive array into a buffer.
def JNI_GetXArrayRegion(_JNIEnv, _array, _jsize, _jsize2, _native_type_p):
    assert isinstance(_array, Arrayref)
    for i in range(_jsize2):
        _native_type_p[i] = _array.arrayref[_jsize+i]

# A family of functions that copies back a region of a primitive array from a buffer.
def JNI_SetXArrayRegion(_JNIEnv, _array, _jsize, _jsize2, _native_type_p):
    assert isinstance(_array, Arrayref)
    for i in range(_jsize2):
        _array.arrayref[_jsize+i] =_native_type_p[i]

#  A family of functions that informs the VM that the native code no longer needs access to elems. 
def JNI_ReleaseXArrayElement(_JNIEnv, _array, _native_type_p, _jint):
    pass

# Creates a new global reference to the object referred to by the obj argument.
def JNI_NewGlobalRef(_JNIEnv, _jobject):
    GlobalRefs.append(_jobject)
    return _jobject

# Deletes the global reference pointed to by globalRef.
def JNI_DeleteGlobalRef(_JNIEnv, _jobject):
    pass

# Deletes the local reference pointed to by localRef.
def JNI_DeleteLocalRef(_JNIEnv, _jobject):
    pass

# Ensures that at least a given number of local references can be created in the current thread. Returns 0 on success; otherwise returns a negative number and throws an OutOfMemoryError.
def JNI_EnsureLocalCapacity(_JNIEnv, _jint):
    return 0

# Creates a new local reference frame, in which at least a given number of local references can be created. Returns 0 on success, a negative number and a pending OutOfMemoryError on failure.
def JNI_PushLocalFrame(_JNIEnv, _jint):
    LocalRefFrames.append(LocalRefFrame())
    return 0

#Pops off the current local reference frame, frees all the local references, and returns a local reference in the previous local reference frame for the given result object.
def JNI_PopLocalFrame(_JNIEnv, _jobject):
    LocalRefFrames.pop()
    frame = LocalRefFrames[-1]
    frame.refs.append(_jobject)
    return _jobject

# Creates a new local reference that refers to the same object as ref.
def JNI_NewLocalRef(_JNIEnv, _jobject):
    frame = LocalRefFrames[-1]
    frame.refs.append(_jobject)
    return _jobject

# Creates a new weak global reference.
def JNI_NewWeakGlobalRef(_JNIEnv, _jobject):
    WeakGlobalRefs.append(_jobject)
    return _jobject

# Delete the VM resources needed for the given weak global reference.
def JNI_DeleteWeakGlobalRef(_JNIEnv, _jweak):
    pass

# Converts a java.lang.reflect.Method or java.lang.reflect.Constructor object to a method ID.
def JNI_FromReflectedMethod(_JNIEnv, _jobject):
    raise NotImplemented("FromReflectedMethod")

# Converts a java.lang.reflect.Field to a field ID.
def JNI_FromReflectedField(_JNIEnv, _jobject):
    raise NotImplemented("FromReflectedField")

# Converts a method ID derived from cls to a java.lang.reflect.Method or java.lang.reflect.Constructor object.
def JNI_ToReflectedMethod(_JNIEnv, _jclass, _jmethodID):
    raise NotImplemented("ToReflectedMethod")

# Converts a field ID derived from cls to a java.lang.reflect.Field object.
def JNI_ToReflectedField(_JNIEnv, _jclass, _jfieldID):
    raise NotImplemented("ToReflectedField")

# Returns the Java VM interface (used in the Invocation API) associated with the current thread. The result is placed at the location pointed to by the second argument, vm.
def JNI_GetJavaVM(_JNIEnv, _JavaVm):
    raise NotImplemented("GetJavaVM")

def JNI_NewObjectV(_JNIEnv, _jclass, _jmethodID, _va_list):
    raise NotImplemented("NewObjectV")

def JNI_NewObjectA(_JNIEnv, _jclass, _jmethodID, p_jvalue):
    stack = jvalues_to_stack(p_jvalue, _jmethodID)
    objref = Objectref(_jclass.class_type, True)
    stack.push(objref)
    cls = _jclass.class_type.cls
    const = cls.constant_pool
    method = None
    for m in cls.methods:
        name = const[m.name_index]
        sig = const[m.descriptor_index]
        #print name, sig
        if _jmethodID.name== name and _jmethodID.sig == sig:
            method = m
            break
    assert not method == None # wrong descr or name?
    descr = descriptor(const[method.descriptor_index])
    current_classloader.invoke_method(cls, method, descr, stack)
    return objref

# Enters the monitor associated with the underlying Java object referred to by obj.
def JNI_MonitorEnter(_JNIEnv, _jobject):
    raise NotImplemented("MonitorEnter")

def JNI_MonitorExit(_JNIEnv, _jobject):
    raise NotImplemented("MonitorExit")

def JNI_RegisterNatives(_JNIEnv, _jobject, _JNINativeMethod, _jint):
    raise NotImplemented("RegisterNatives")

def JNI_UnregisterNatives(_JNIEnv, _jclass):
    raise NotImplemented("UnregisterNatives")

jni_env = JNINativeInterface()
# setting implemented functions
#for tupel in jni_env._fields_:
#    if not tupel[1]==c_void_p:
#        Ftype = tupel[1]
#
#        command =str("jni_env."+tupel[0]+"= Ftype(JNI_"+tupel[0]+")")
#        eval(command)
#    else:
#        Ftype = None

Ftype = CFUNCTYPE(c_int, c_void_p, c_void_p)
jni_env.GetJavaVM = Ftype(JNI_GetJavaVM)
# Registering Native Methods
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, c_void_p, c_int)
jni_env.RegisterNatives = Ftype(JNI_RegisterNatives)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object)
jni_env.UnregisterNatives = Ftype(JNI_UnregisterNatives)
# Monitor Operations
Ftype = CFUNCTYPE(c_int, c_void_p, py_object)
jni_env.MonitorEnter = Ftype(JNI_MonitorEnter)
jni_env.MonitorExit = Ftype(JNI_MonitorExit)
# Reflection Support
Ftype = CFUNCTYPE(py_object, c_void_p, py_object)
jni_env.FromReflectedMethod = Ftype(JNI_FromReflectedMethod)
jni_env.FromReflectedField = Ftype(JNI_FromReflectedField)
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object)
jni_env.ToReflectedMethod = Ftype(JNI_ToReflectedMethod)
jni_env.ToReflectedField = Ftype(JNI_ToReflectedField)
# class operations
Ftype = CFUNCTYPE(py_object, c_void_p, py_object)
jni_env.GetSuperclass = Ftype(JNI_GetSuperclass)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object)
jni_env.IsAssignableFrom = Ftype(JNI_IsAssignableFrom)
# exceptions (TODO)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object)
jni_env.Throw = Ftype(JNI_Throw)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, c_char_p)
jni_env.ThrowNew = Ftype(JNI_ThrowNew)
Ftype = CFUNCTYPE(py_object, c_void_p)
jni_env.ExceptionOccurred = Ftype(JNI_ExceptionOccurred)
Ftype = CFUNCTYPE(c_void_p, c_void_p)
jni_env.ExceptionDescribe = Ftype(JNI_ExceptionDescribe)
jni_env.ExceptionClear = Ftype(JNI_ExceptionClear)
Ftype = CFUNCTYPE(c_void_p, c_void_p, c_char_p)
jni_env.FatalError = Ftype(JNI_FatalError)
Ftype = CFUNCTYPE(c_int, c_void_p)
jni_env.ExceptionCheck = Ftype(JNI_ExceptionCheck)
# Global and Local References
Ftype = CFUNCTYPE(py_object, c_void_p, py_object)
jni_env.NewGlobalRef = Ftype(JNI_NewGlobalRef)
jni_env.PopLocalFrame = Ftype(JNI_PopLocalFrame)
jni_env.NewLocalRef = Ftype(JNI_NewLocalRef)
jni_env.NewWeakGlobalRef = Ftype(JNI_NewWeakGlobalRef)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object)
jni_env.DeleteWeakGlobalRef = Ftype(JNI_DeleteWeakGlobalRef)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object)
jni_env.DeleteGlobalRef = Ftype(JNI_DeleteGlobalRef)
jni_env.DeleteLocalRef = Ftype(JNI_DeleteLocalRef)
Ftype = CFUNCTYPE(c_int, c_void_p, c_int)
jni_env.EnsureLocalCapacity = Ftype(JNI_EnsureLocalCapacity)
jni_env.PushLocalFrame = Ftype(JNI_PushLocalFrame)
# set static field
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object)
jni_env.SetStaticObjectField = Ftype(JNI_SetStaticXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)
jni_env.SetStaticBooleanField = Ftype(JNI_SetStaticXField)
jni_env.SetStaticByteField = Ftype(JNI_SetStaticXField)
jni_env.SetStaticShortField = Ftype(JNI_SetStaticXField)
jni_env.SetStaticIntField = Ftype(JNI_SetStaticXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_char)
jni_env.SetStaticCharField = Ftype(JNI_SetStaticXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_long)
jni_env.SetStaticLongField = Ftype(JNI_SetStaticXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_float)
jni_env.SetStaticFloatField = Ftype(JNI_SetStaticXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_double)
jni_env.SetStaticDoubleField = Ftype(JNI_SetStaticXField)
# get static field
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object)
jni_env.GetStaticObjectField = Ftype(JNI_GetStaticXField)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object)
jni_env.GetStaticIntField = Ftype(JNI_GetStaticXField)
jni_env.GetStaticBooleanField = Ftype(JNI_GetStaticXField)
jni_env.GetStaticByteField = Ftype(JNI_GetStaticXField)
jni_env.GetStaticShortField = Ftype(JNI_GetStaticXField)
Ftype = CFUNCTYPE(c_wchar, c_void_p, py_object, py_object)
jni_env.GetStaticCharField = Ftype(JNI_GetStaticXField)
Ftype = CFUNCTYPE(c_long, c_void_p, py_object, py_object)
jni_env.GetStaticLongField = Ftype(JNI_GetStaticXField)
Ftype = CFUNCTYPE(c_float, c_void_p, py_object, py_object)
jni_env.GetStaticFloatField = Ftype(JNI_GetStaticXField)
Ftype = CFUNCTYPE(c_double, c_void_p, py_object, py_object)
jni_env.GetStaticDoubleField = Ftype(JNI_GetStaticXField)
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, c_char_p, c_char_p)
jni_env.GetStaticFieldID = Ftype(JNI_GetStaticFieldID)

Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object, POINTER(jvalues))
jni_env.CallNonvirtualVoidMethodA = Ftype(JNI_CallNonvirtualXMethodA)
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object, py_object, POINTER(jvalues))
jni_env.CallNonvirtualObjectMethodA = Ftype(JNI_CallNonvirtualXMethodA)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, POINTER(jvalues))
jni_env.CallNonvirtualBooleanMethodA = Ftype(JNI_CallNonvirtualXMethodA)
jni_env.CallNonvirtualByteMethodA    = Ftype(JNI_CallNonvirtualXMethodA)
jni_env.CallNonvirtualShortMethodA   = Ftype(JNI_CallNonvirtualXMethodA)
jni_env.CallNonvirtualIntMethodA     = Ftype(JNI_CallNonvirtualXMethodA)
Ftype = CFUNCTYPE(c_char, c_void_p, py_object, py_object, py_object, POINTER(jvalues))
jni_env.CallNonvirtualCharMethodA    = Ftype(JNI_CallNonvirtualXMethodA)
Ftype = CFUNCTYPE(c_long, c_void_p, py_object, py_object, py_object, POINTER(jvalues))
jni_env.CallNonvirtualLongMethodA    = Ftype(JNI_CallNonvirtualXMethodA)
Ftype = CFUNCTYPE(c_float, c_void_p, py_object, py_object, py_object, POINTER(jvalues))
jni_env.CallNonvirtualFloatMethodA   = Ftype(JNI_CallNonvirtualXMethodA)
Ftype = CFUNCTYPE(c_double, c_void_p, py_object, py_object, py_object, POINTER(jvalues))
jni_env.CallNonvirtualDoubleMethodA  = Ftype(JNI_CallNonvirtualXMethodA)

Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object, POINTER(jvalues))
jni_env.CallStaticObjectMethodA = Ftype(JNI_CallStaticXMethodA)
jni_env.CallObjectMethodA       = Ftype(JNI_CallXMethodA)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, POINTER(jvalues))
jni_env.CallStaticVoidMethodA = Ftype(JNI_CallStaticXMethodA)
jni_env.CallVoidMethodA       = Ftype(JNI_CallXMethodA)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object, POINTER(jvalues))
jni_env.CallStaticBooleanMethodA = Ftype(JNI_CallStaticXMethodA)
jni_env.CallStaticByteMethodA    = Ftype(JNI_CallStaticXMethodA)
jni_env.CallStaticShortMethodA   = Ftype(JNI_CallStaticXMethodA)
jni_env.CallStaticIntMethodA     = Ftype(JNI_CallStaticXMethodA)
jni_env.CallBooleanMethodA      = Ftype(JNI_CallXMethodA)
jni_env.CallByteMethodA         = Ftype(JNI_CallXMethodA)
jni_env.CallShortMethodA        = Ftype(JNI_CallXMethodA)
jni_env.CallIntMethodA          = Ftype(JNI_CallXMethodA)
Ftype = CFUNCTYPE(c_char, c_void_p, py_object, py_object, POINTER(jvalues))
jni_env.CallStaticCharMethodA  = Ftype(JNI_CallStaticXMethodA)
jni_env.CallCharMethodA        = Ftype(JNI_CallXMethodA)
Ftype = CFUNCTYPE(c_long, c_void_p, py_object, py_object, POINTER(jvalues))
jni_env.CallStaticLongMethodA  = Ftype(JNI_CallStaticXMethodA)
jni_env.CallLongMethodA        = Ftype(JNI_CallXMethodA)
Ftype = CFUNCTYPE(c_float, c_void_p, py_object, py_object, POINTER(jvalues))
jni_env.CallStaticFloatMethodA = Ftype(JNI_CallStaticXMethodA)
jni_env.CallFloatMethodA       = Ftype(JNI_CallXMethodA)
Ftype = CFUNCTYPE(c_double, c_void_p, py_object, py_object, POINTER(jvalues))
jni_env.CallStaticDoubleMethodA = Ftype(JNI_CallStaticXMethodA)
jni_env.CallDoubleMethodA       = Ftype(JNI_CallXMethodA)
# call instance method / call static method
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object)
jni_env.CallVoidMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallStaticVoidMethodV = Ftype(JNI_CallStaticXMethodV)
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object, py_object)
jni_env.CallObjectMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallStaticObjectMethodV = Ftype(JNI_CallStaticXMethodV)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object)
jni_env.CallBooleanMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallByteMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallShortMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallIntMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallStaticBooleanMethodV = Ftype(JNI_CallStaticXMethodV)
jni_env.CallStaticByteMethodV = Ftype(JNI_CallStaticXMethodV)
jni_env.CallStaticShortMethodV = Ftype(JNI_CallStaticXMethodV)
jni_env.CallStaticIntMethodV = Ftype(JNI_CallStaticXMethodV)
Ftype = CFUNCTYPE(c_char, c_void_p, py_object, py_object, py_object)
jni_env.CallCharMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallStaticCharMethodV = Ftype(JNI_CallStaticXMethodV)
Ftype = CFUNCTYPE(c_long, c_void_p, py_object, py_object, py_object)
jni_env.CallLongMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallStaticLongMethodV = Ftype(JNI_CallStaticXMethodV)
Ftype = CFUNCTYPE(c_float, c_void_p, py_object, py_object, py_object)
jni_env.CallFloatMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallStaticFloatMethodV = Ftype(JNI_CallStaticXMethodV)
Ftype = CFUNCTYPE(c_double, c_void_p, py_object, py_object, py_object)
jni_env.CallDoubleMethodV = Ftype(JNI_CallXMethodV)
jni_env.CallStaticDoubleMethodV = Ftype(JNI_CallStaticXMethodV)
# method IDs
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, c_char_p, c_char_p)
jni_env.GetMethodID = Ftype(JNI_GetMethodID)
jni_env.GetStaticMethodID = Ftype(JNI_GetMethodID)
# get field
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object)
jni_env.GetObjectField = Ftype(JNI_GetXField)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object)
jni_env.GetBooleanField = Ftype(JNI_GetXField)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object)
jni_env.GetByteField = Ftype(JNI_GetXField)
Ftype = CFUNCTYPE(c_char, c_void_p, py_object, py_object)
jni_env.GetCharField = Ftype(JNI_GetXField)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object)
jni_env.GetShortField = Ftype(JNI_GetXField)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object)
jni_env.GetIntField = Ftype(JNI_GetXField)
Ftype = CFUNCTYPE(c_long, c_void_p, py_object, py_object)
jni_env.GetLongField = Ftype(JNI_GetXField)
Ftype = CFUNCTYPE(c_float, c_void_p, py_object, py_object)
jni_env.GetFloatField = Ftype(JNI_GetXField)
Ftype = CFUNCTYPE(c_double, c_void_p, py_object, py_object)
jni_env.GetDoubleField = Ftype(JNI_GetXField)
# set field
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object)
jni_env.SetObjectField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)
jni_env.SetBooleanField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)
jni_env.SetByteField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_char)
jni_env.SetCharField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)
jni_env.SetShortField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_int)
jni_env.SetIntField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_long)
jni_env.SetLongField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_float)
jni_env.SetFloatField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, c_double)
jni_env.SetDoubleField = Ftype(JNI_SetXField)
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, c_char_p, c_char_p)
jni_env.GetFieldID = Ftype(JNI_GetFieldID)
# string operations, version
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_char))
jni_env.GetStringRegion = Ftype(JNI_GetStringRegion)
jni_env.GetStringUTFRegion = Ftype(JNI_GetStringUTFRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_char_p)
jni_env.ReleaseStringUTFChars = Ftype(JNI_ReleaseStringUTFChars)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object)
jni_env.GetStringUTFLength = Ftype(JNI_GetStringUTFLength)
Ftype = CFUNCTYPE(py_object, c_void_p, c_char_p)
jni_env.NewStringUTF = Ftype(JNI_NewStringUTF)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_char_p)
jni_env.ReleaseStringChars = Ftype(JNI_ReleaseStringChars)
jni_env.ReleaseStringCritical = Ftype(JNI_ReleaseStringChars) # XXX
#Ftype = CFUNCTYPE(c_char_p, c_void_p, py_object, c_int)
#jni_env.GetStringChars = Ftype(JNI_GetStringChars)
Ftype = CFUNCTYPE(c_char_p, c_void_p, c_char_p, c_int)
jni_env.GetStringCritical = Ftype(JNI_GetStringCritical)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object)
jni_env.GetStringLength = Ftype(JNI_GetStringLength)
Ftype = CFUNCTYPE(py_object, c_void_p, c_char_p, c_int)
jni_env.NewString = Ftype(JNI_NewString)
Ftype = CFUNCTYPE(c_int, c_void_p)
jni_env.GetVersion = Ftype(JNI_GetVersion)
#Ftype = CFUNCTYPE(c_char_p, c_void_p, py_object, c_int)
#jni_env.GetStringUTFChars = Ftype(JNI_GetStringUTFChars)
Ftype = CFUNCTYPE(py_object, c_void_p, c_char_p)
jni_env.FindClass = Ftype(JNI_FindClass)
# Array operations
Ftype = CFUNCTYPE(py_object, c_void_p, c_int, py_object, c_void_p)
jni_env.NewObjectArray = Ftype(JNI_NewObjectArray)

Ftype = CFUNCTYPE(c_int, c_void_p, py_object)
jni_env.GetArrayLength = Ftype(JNI_GetArrayLength)
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, c_int)
jni_env.GetObjectArrayElement = Ftype(JNI_GetObjectArrayElement)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, py_object)
jni_env.SetObjectArrayElement = Ftype(JNI_SetObjectArrayElement)
Ftype = CFUNCTYPE(py_object, c_void_p, c_int)
jni_env.NewBooleanArray = Ftype(JNI_NewXArray(False,'Z'))
jni_env.NewByteArray = Ftype(JNI_NewXArray(0,'B'))
jni_env.NewCharArray = Ftype(JNI_NewXArray('\x00','C'))
jni_env.NewShortArray= Ftype(JNI_NewXArray(0,'S'))
jni_env.NewIntArray = Ftype(JNI_NewXArray(0,'I'))
jni_env.NewLongArray = Ftype(JNI_NewXArray(0,'J'))
jni_env.NewFloatArray = Ftype(JNI_NewXArray(0.0,'F'))
jni_env.NewDoubleArray = Ftype(JNI_NewXArray(0.0,'D'))
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))
jni_env.GetBooleanArrayRegion = Ftype(JNI_GetXArrayRegion)
jni_env.GetByteArrayRegion = Ftype(JNI_GetXArrayRegion)
jni_env.GetShortArrayRegion = Ftype(JNI_GetXArrayRegion)
jni_env.GetIntArrayRegion = Ftype(JNI_GetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_char))
jni_env.GetCharArrayRegion = Ftype(JNI_GetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_long))
jni_env.GetLongArrayRegion = Ftype(JNI_GetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_float))
jni_env.GetFloatArrayRegion = Ftype(JNI_GetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_double))
jni_env.GetDoubleArrayRegion = Ftype(JNI_GetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_int), c_int)
jni_env.ReleaseBooleanArrayElements = Ftype(JNI_ReleaseXArrayElements)
jni_env.ReleaseByteArrayElements = Ftype(JNI_ReleaseXArrayElements)
jni_env.ReleaseShortArrayElements = Ftype(JNI_ReleaseXArrayElements)
jni_env.ReleaseIntArrayElements = Ftype(JNI_ReleaseXArrayElements)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_char), c_int)
jni_env.ReleaseCharArrayElements = Ftype(JNI_ReleaseXArrayElements)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_long), c_int)
jni_env.ReleaseLongArrayElements = Ftype(JNI_ReleaseXArrayElements)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_float), c_int)
jni_env.ReleaseFloatArrayElements = Ftype(JNI_ReleaseXArrayElements)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, POINTER(c_double), c_int)
jni_env.ReleaseDoubleArrayElements = Ftype(JNI_ReleaseXArrayElements)

Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_int))
jni_env.SetBooleanArrayRegion = Ftype(JNI_SetXArrayRegion)
jni_env.SetShortArrayRegion = Ftype(JNI_SetXArrayRegion)
jni_env.SetIntArrayRegion = Ftype(JNI_SetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_byte))
jni_env.SetByteArrayRegion = Ftype(JNI_SetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_char))
jni_env.SetCharArrayRegion = Ftype(JNI_SetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_long))
jni_env.SetLongArrayRegion = Ftype(JNI_SetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_float))
jni_env.SetFloatArrayRegion = Ftype(JNI_SetXArrayRegion)
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int, c_int, POINTER(c_double))
jni_env.SetDoubleArrayRegion = Ftype(JNI_SetXArrayRegion)

Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)
jni_env.GetBooleanArrayElements = Ftype(JNI_GetXArrayElements(c_int))
jni_env.GetByteArrayElements  = Ftype(JNI_GetXArrayElements(c_int))
jni_env.GetShortArrayElements = Ftype(JNI_GetXArrayElements(c_int))
jni_env.GetIntArrayElements   = Ftype(JNI_GetXArrayElements(c_int))
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)
jni_env.GetLongArrayElements  = Ftype(JNI_GetXArrayElements(c_long))
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)
jni_env.GetFloatArrayElements = Ftype(JNI_GetXArrayElements(c_float))
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, c_int)
jni_env.GetDoubleArrayElements = Ftype(JNI_GetXArrayElements(c_double))
# object operations
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object)
jni_env.NewObjectV = Ftype(JNI_NewObjectV)
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object, POINTER(jvalues))
jni_env.NewObjectA = Ftype(JNI_NewObjectA)

Ftype = CFUNCTYPE(py_object, c_void_p, py_object)
jni_env.AllocObject = Ftype(JNI_AllocObject)
jni_env.GetObjectClass = Ftype(JNI_GetObjectClass)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object)
jni_env.IsInstanceOf = Ftype(JNI_IsInstanceOf)
jni_env.IsSameObject = Ftype(JNI_IsSameObject)
# call nonvirtual method
Ftype = CFUNCTYPE(c_void_p, c_void_p, py_object, py_object, py_object, py_object)
jni_env.CallNonvirtualVoidMethodV = Ftype(JNI_CallNonvirtualXMethodV)
Ftype = CFUNCTYPE(py_object, c_void_p, py_object, py_object, py_object, py_object)
jni_env.CallNonvirtualObjectMethodV = Ftype(JNI_CallNonvirtualXMethodV)
Ftype = CFUNCTYPE(c_int, c_void_p, py_object, py_object, py_object, py_object)
jni_env.CallNonvirtualBooleanMethodV = Ftype(JNI_CallNonvirtualXMethodV)
jni_env.CallNonvirtualByteMethodV = Ftype(JNI_CallNonvirtualXMethodV)
jni_env.CallNonvirtualShortMethodV = Ftype(JNI_CallNonvirtualXMethodV)
jni_env.CallNonvirtualIntMethodV = Ftype(JNI_CallNonvirtualXMethodV)
Ftype = CFUNCTYPE(c_char, c_void_p, py_object, py_object, py_object, py_object)
jni_env.CallNonvirtualCharMethodV = Ftype(JNI_CallNonvirtualXMethodV)
Ftype = CFUNCTYPE(c_long, c_void_p, py_object, py_object, py_object, py_object)
jni_env.CallNonvirtualLongMethodV = Ftype(JNI_CallNonvirtualXMethodV)
Ftype = CFUNCTYPE(c_float, c_void_p, py_object, py_object, py_object, py_object)
jni_env.CallNonvirtualFloatMethodV = Ftype(JNI_CallNonvirtualXMethodV)
Ftype = CFUNCTYPE(c_double, c_void_p, py_object, py_object, py_object, py_object)
jni_env.CallNonvirtualDoubleMethodV = Ftype(JNI_CallNonvirtualXMethodV)
# setting jni-enviroment pointer **JNIEnv
env_ptr = pointer(pointer(jni_env))
# setting var args functions on the c-side (crashs if ever libtest_native.so is terminated when jvm runs)
class helper_func(Structure):
    _fields_ = [
    ("args_length", CFUNCTYPE(c_int, py_object)),
    ("argtype_at_index", CFUNCTYPE(c_char, py_object, c_int))]

def JNI_HELPER_args_length(_methodID):
    arg_list = []
    for i in list(_methodID.sig.replace("(","")):
        if i==")":
            break
        arg_list.append(i)
    return len(arg_list)

def JNI_HELPER_argtype_at_index(_methodID, index):
    arg_list = []
    for i in list(_methodID.sig.replace("(","")):
        if i==")":
            break
        arg_list.append(i)
    return arg_list[index]


helper_funs = helper_func()
Ftype = CFUNCTYPE(c_int, py_object)
helper_funs.args_length = Ftype(JNI_HELPER_args_length)
Ftype = CFUNCTYPE(c_char, py_object, c_int)
helper_funs.argtype_at_index = Ftype(JNI_HELPER_argtype_at_index)

string = "libtest_native.so"
init_lib = cdll.LoadLibrary("/usr/lib/"+string)
init_lib.set_varargs(env_ptr, helper_funs)
