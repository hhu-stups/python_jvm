// C side of the test_native.py file
// Compile und run it with:
// gcc -fPIC -Wall -g -c test_native.c -I/home/stupsi/pypy_kram/jvm/jvm/classpath/
// gcc -fPIC -Wall -g -c test_native.c -I/home/stupsi/pypy_kram/jvm/jvm/classpath-0.98/include
// gcc -shared -Wl,-soname,libtest_native.so -o libtest_native.so test_native.o -lc
// sudo cp libtest_native.so /usr/local/classpath/lib/classpath/ (for late use)
// or sudo cp libtest_native.so /usr/lib/ (to test this file)


#include <jni.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>



// most of the jni-env functions are implementet in python in native.py 
// with c-types. But some functions can't be implemented easyly because
// c-types dont support var-args and has problems with returning pointers.
// This functions are implemented here:

// set var args functions
struct helper_func{
    int (*args_length) (jmethodID);
    char (*argtype_at_index) (jmethodID, int);
}my_helpers;

// Nonvirtual calls
void myCallNonvirtualVoidMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    (*env)->CallNonvirtualVoidMethodA(env, obj, methodID, clazz, values);
}

jobject myCallNonvirtualObjectMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...) 
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualObjectMethodA(env, obj, clazz, methodID, values);
}

jboolean myCallNonvirtualBooleanMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualBooleanMethodA(env, obj, clazz, methodID, values);
}

jbyte myCallNonvirtualByteMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualByteMethodA(env, obj, clazz, methodID, values);
}

jchar myCallNonvirtualCharMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualCharMethodA(env, obj, clazz, methodID, values);
}

jshort myCallNonvirtualShortMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualShortMethodA(env, obj, clazz, methodID, values);
}

jint myCallNonvirtualIntMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualIntMethodA(env, obj, clazz, methodID, values);
}

jlong myCallNonvirtualLongMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualLongMethodA(env, obj, clazz, methodID, values);
}

jfloat myCallNonvirtualFloatMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualFloatMethodA(env, obj, clazz, methodID, values);
}

jdouble myCallNonvirtualDoubleMethod(JNIEnv *env, jobject obj, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallNonvirtualDoubleMethodA(env, obj, clazz, methodID, values);
}

// normal call

void myCallVoidMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    (*env)->CallVoidMethodA(env, obj, methodID, values);
}

jobject myCallObjectMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...) 
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallObjectMethodA(env, obj, methodID, values);
}

jboolean myCallBooleanMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallBooleanMethodA(env, obj, methodID, values);
}

jbyte myCallByteMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallByteMethodA(env, obj, methodID, values);
}

jchar myCallCharMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallCharMethodA(env, obj, methodID, values);
}

jshort myCallShortMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallShortMethodA(env, obj, methodID, values);
}

jint myCallIntMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallIntMethodA(env, obj, methodID, values);
}

jlong myCallLongMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallLongMethodA(env, obj, methodID, values);
}

jfloat myCallFloatMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallFloatMethodA(env, obj, methodID, values);
}

jdouble myCallDoubleMethod(JNIEnv *env, jobject obj, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallDoubleMethodA(env, obj, methodID, values);
}

// static method calls
void myCallStaticVoidMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    (*env)->CallStaticVoidMethodA(env, clazz, methodID, values);
}

jobject myCallStaticObjectMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...) 
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticObjectMethodA(env, clazz, methodID, values);
}

jboolean myCallStaticBooleanMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticBooleanMethodA(env, clazz, methodID, values);
}

jbyte myCallStaticByteMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticByteMethodA(env, clazz, methodID, values);
}

jchar myCallStaticCharMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticCharMethodA(env, clazz, methodID, values);
}

jshort myCallStaticShortMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticShortMethodA(env, clazz, methodID, values);
}

jint myCallStaticIntMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticIntMethodA(env, clazz, methodID, values);
}

jlong myCallStaticLongMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticLongMethodA(env, clazz, methodID, values);
}

jfloat myCallStaticFloatMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticFloatMethodA(env, clazz, methodID, values);
}

jdouble myCallStaticDoubleMethod(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->CallStaticDoubleMethodA(env, clazz, methodID, values);
}

jobject myNewObject(JNIEnv *env, jclass clazz, jmethodID methodID, ...)
{
    int arg_num = my_helpers.args_length(methodID);
    jvalue values[arg_num];
    va_list ap;
    va_start(ap, methodID);
    int i;
    for (i=0; i<arg_num; i++)
    {
        char c = my_helpers.argtype_at_index(methodID, i);
        switch(c)
        {
            case 'Z':
                values[i].z = va_arg(ap, int);
                break;
            case 'B':
                values[i].b = va_arg(ap, int);
                break;
            case 'C':
                values[i].c = va_arg(ap, int);
                break;
            case 'S':
                values[i].s = va_arg(ap, int);
                break;
            case 'I':
                values[i].i = va_arg(ap, int);
                break;
            case 'J':
                values[i].j = va_arg(ap, long);
                break;
            case 'F':
                values[i].f = va_arg(ap, double);
                break;
            case 'D':
                values[i].d = va_arg(ap, double);
                break;
            case 'L':
                values[i].l = va_arg(ap, jobject);
                break;
        }
    }
    va_end(ap);
    return (*env)->NewObjectA(env, clazz, methodID, values);
}

const char * myGetStringUTFChars(JNIEnv *env, jstring string, 
 jboolean *isCopy)
{
    jsize length = (*env)->GetStringUTFLength(env, string);
    char *buf = malloc(sizeof(jchar) *length+1); // len(jstring) + \0
    (*env)->GetStringUTFRegion(env, string, 0, length, buf);
    return buf;
}

const jchar * myGetStringChars(JNIEnv *env, jstring string,
 jboolean *isCopy)
{
    jsize length = (*env)->GetStringLength(env, string);
    jchar *buf = malloc(sizeof(jchar) *length+1); // len(jstring) + \0
    (*env)->GetStringRegion(env, string, 0, length, buf);
    return buf;
}

// void myReleaseStringUTFChars(JNIEnv *env, jstring string,
//  const char *utf)
// {
//     free(utf);
// }
// 
// void myReleaseStringChars(JNIEnv *env, jstring string, 
//  const jchar *chars)
// {
//     free(chars);
// }


void set_varargs(struct JNINativeInterface_** jni_niface, struct helper_func helperfunctions)
{
//     (*jni_niface)->ReleaseStringUTFChars = myReleaseStringUTFChars;
//     (*jni_niface)->ReleaseStringChars = myReleaseStringChars;
    (*jni_niface)->GetStringChars = myGetStringChars;
    (*jni_niface)->GetStringUTFChars = myGetStringUTFChars; 
    (*jni_niface)->CallVoidMethod = myCallVoidMethod;
    (*jni_niface)->CallObjectMethod = myCallObjectMethod;
    (*jni_niface)->CallBooleanMethod = myCallBooleanMethod;
    (*jni_niface)->CallByteMethod = myCallByteMethod;
    (*jni_niface)->CallCharMethod = myCallCharMethod;
    (*jni_niface)->CallShortMethod = myCallShortMethod;
    (*jni_niface)->CallIntMethod = myCallIntMethod;
    (*jni_niface)->CallLongMethod = myCallLongMethod;
    (*jni_niface)->CallFloatMethod = myCallFloatMethod;
    (*jni_niface)->CallDoubleMethod = myCallDoubleMethod;

    (*jni_niface)->CallStaticVoidMethod = myCallStaticVoidMethod;
    (*jni_niface)->CallStaticObjectMethod = myCallStaticObjectMethod;
    (*jni_niface)->CallStaticBooleanMethod = myCallStaticBooleanMethod;
    (*jni_niface)->CallStaticByteMethod = myCallStaticByteMethod;
    (*jni_niface)->CallStaticCharMethod = myCallStaticCharMethod;
    (*jni_niface)->CallStaticShortMethod = myCallStaticShortMethod;
    (*jni_niface)->CallStaticIntMethod = myCallStaticIntMethod;
    (*jni_niface)->CallStaticLongMethod = myCallStaticLongMethod;
    (*jni_niface)->CallStaticFloatMethod = myCallStaticFloatMethod;
    (*jni_niface)->CallStaticDoubleMethod = myCallStaticDoubleMethod;

    (*jni_niface)->CallNonvirtualVoidMethod = myCallNonvirtualVoidMethod;
    (*jni_niface)->CallNonvirtualObjectMethod = myCallNonvirtualObjectMethod;
    (*jni_niface)->CallNonvirtualBooleanMethod = myCallNonvirtualBooleanMethod;
    (*jni_niface)->CallNonvirtualByteMethod = myCallNonvirtualByteMethod;
    (*jni_niface)->CallNonvirtualCharMethod = myCallNonvirtualCharMethod;
    (*jni_niface)->CallNonvirtualShortMethod = myCallNonvirtualShortMethod;
    (*jni_niface)->CallNonvirtualIntMethod = myCallNonvirtualIntMethod;
    (*jni_niface)->CallNonvirtualLongMethod = myCallNonvirtualLongMethod;
    (*jni_niface)->CallNonvirtualFloatMethod = myCallNonvirtualFloatMethod;
    (*jni_niface)->CallNonvirtualDoubleMethod = myCallNonvirtualDoubleMethod;
    (*jni_niface)->NewObject = myNewObject;
    my_helpers = helperfunctions;
}

// JNI Tests...(missing prototypes header)
// This native-method implementations are used in test_jni.py

JNIEXPORT void JNICALL Java_Add_calc
  (JNIEnv *env, jobject this, jint num)
{
    jclass cls = (*env)->GetObjectClass(env, this);
    jfieldID fid = (*env)->GetFieldID(env, cls, "number", "I");
    jint i = (*env)->GetIntField(env, this, fid);
    printf("%i \n",num+i);
}

JNIEXPORT jint JNICALL Java_Fac_fun
  (JNIEnv *env, jobject this)
{
    jclass cls = (*env)->GetObjectClass(env, this);
    jfieldID fid = (*env)->GetFieldID(env, cls, "i", "I");
    jint i = (*env)->GetIntField(env, this, fid);
    int result = 1;
    int k;
    for(k=1; k<i; k++)
    {
        result *= k;
    }
    return result;
}

JNIEXPORT void JNICALL Java_Sum_cCode
  (JNIEnv *env, jobject this)
{
       jvalue values[2];
       values[0].i = (jint)3;
       values[1].i = (jint)4;
       jclass cls = (*env)->FindClass(env, "Sum");
       jmethodID method = (*env)->GetMethodID(env, cls, "set_it", "(II)V");
       (*env)->CallVoidMethodA(env, this, method, values);
}

JNIEXPORT void JNICALL Java_Va_nativeMethod
  (JNIEnv *env, jobject this)
{
       jclass cls = (*env)->FindClass(env, "Va");
       jmethodID method = (*env)->GetMethodID(env, cls, "method", "(II)V");
       (*env)->CallVoidMethod(env, this, method, 1, 2);
}

JNIEXPORT jint JNICALL Java_Va_nativeMethod2
  (JNIEnv *env, jobject this)
{
       jclass cls = (*env)->FindClass(env, "Va");
       jmethodID method = (*env)->GetMethodID(env, cls, "method2", "(II)I");
       return (*env)->CallIntMethod(env, this, method, 1, 2);
}

JNIEXPORT jint JNICALL
Java_StrLen_strlen( JNIEnv *env, jclass clazz, jstring s )
{
  if ( s == NULL )
  {
    jclass exc = (*env)->FindClass( env, "java/lang/NullPointerException" );
    if ( exc != NULL )
      (*env)->ThrowNew( env, exc, "(in C++ code)" );
    return -1;
  }
  const jbyte* str = (jbyte*)(*env)->GetStringUTFChars( env, s, NULL );
  if ( str == NULL )
    return -1;
  int len = strlen((char*)str);
  (*env)->ReleaseStringUTFChars( env, s, (char*)str );
  return (jint) len;
}

JNIEXPORT jint JNICALL 
 Java_IntArray_sumArray(JNIEnv *env, jobject obj, jintArray arr)
{
     jint buf[10];
     jint i, sum = 0;
     (*env)->GetIntArrayRegion(env, arr, 0, 10, buf);
     for (i = 0; i < 10; i++) {
         sum += buf[i];
     }
     return sum;
}

JNIEXPORT jobjectArray JNICALL 
 Java_ObjectArrayTest2_initObjArray(JNIEnv *env,
                                    jclass cls,
                                    int size)
{
     jobjectArray result;
     int i;
     jobject myObj;
     jmethodID methodID;
     jfieldID fieldID;
     jclass objCls = (*env)->FindClass(env, "A");

     if (objCls == NULL) {
         printf("objCls==Null\n");
         return NULL; /* exception thrown */
     }
     result = (*env)->NewObjectArray(env, size, objCls, NULL);
     if (result == NULL) {
         printf("result==Null\n");
         return NULL; /* out of memory error thrown */
     }

     for (i = 0; i < size; i++) {
        methodID = (*env)->GetMethodID(env, objCls, "<init>", "()V");
        myObj = (*env)->NewObject(env, objCls, methodID);
        fieldID = (*env)->GetFieldID(env, objCls, "x", "I");
        (*env)->SetIntField(env, myObj, fieldID, 41+i);
        (*env)->SetObjectArrayElement(env, result, i, myObj);
        (*env)->DeleteLocalRef(env, myObj);
     }
     return result;
}

// somewhere here is a bug :-)
// dosent return a array
// maybe a garbage collection problem of myObj?
JNIEXPORT jobjectArray JNICALL 
 Java_ObjectArrayTest3_initObjArray(JNIEnv *env,
                                    jclass cls,
                                    int size)
{
     jobjectArray result;
     jobject myObj;
     jmethodID methodID;
     jfieldID fieldID;
     jclass objCls = (*env)->FindClass(env, "A");

     if (objCls == NULL) {
         printf("objCls==Null\n");
         return NULL; /* exception thrown */
     }

     methodID = (*env)->GetMethodID(env, objCls, "<init>", "()V");
     myObj = (*env)->NewObject(env, objCls, methodID);
     fieldID = (*env)->GetFieldID(env, objCls, "x", "I");
     (*env)->SetIntField(env, myObj, fieldID, 41);
     result = (*env)->NewObjectArray(env, size, objCls, myObj);

     if (result == NULL) {
         printf("result==Null\n");
         return NULL; /* out of memory error thrown */
     }
     return result;
}

JNIEXPORT jobjectArray JNICALL 
 Java_ObjectArrayTest4_initObjArray(JNIEnv *env,
                                    jclass cls,
                                    int size)
{
     jclass objCls = (*env)->FindClass(env, "java/lang/String");
     if (objCls == NULL) {
         printf("objCls==Null\n");
         return NULL; /* exception thrown */
     }
     
     jmethodID methodID = (*env)->GetMethodID(env, objCls, "<init>", "(Ljava/lang/String;)V");
     jobject myObj = (*env)->NewObject(env, objCls, methodID, (*env)->NewStringUTF(env, "C"));
     jobjectArray result = (*env)->NewObjectArray(env, size, objCls, myObj);
     
     if (result == NULL) {
         printf("result==Null\n");
         return NULL; /* out of memory error thrown */
     }
     return result;
}

// from http://java.sun.com/developer/onlineTraining/Programming/JDCBook/jniexamp.html
JNIEXPORT jbyteArray JNICALL Java_ReadFile_loadFile
  (JNIEnv * env, jobject jobj, jstring name) {
    caddr_t m;
    jbyteArray jb;
    jboolean iscopy;
    struct stat finfo;
    const char *mfile = (*env)->GetStringUTFChars(
                env, name, &iscopy);
    int fd = open(mfile, O_RDONLY);

    if (fd == -1) {
      printf("Could not open %s\n", mfile);
    }
    lstat(mfile, &finfo);
    m = mmap((caddr_t) 0, finfo.st_size,
                PROT_READ, MAP_PRIVATE, fd, 0);
    if (m == (caddr_t)-1) {
      printf("Could not mmap %s\n", mfile);
      return(0);
    }
    jb=(*env)->NewByteArray(env, finfo.st_size);
    (*env)->SetByteArrayRegion(env, jb, 0, 
        finfo.st_size, (jbyte *)m);
    close(fd);
    (*env)->ReleaseStringUTFChars(env, name, mfile);
    return (jb);
}

JNIEXPORT jobjectArray JNICALL 
               Java_ArrayHandler_returnArray(JNIEnv *env, jobject jobj)
{

    jobjectArray ret;
    int i;

    char *message[5]= {"first", 
        "second", 
        "third", 
        "fourth", 
        "fifth"};

    ret= (jobjectArray)(*env)->NewObjectArray(env,5,
         (*env)->FindClass(env,"java/lang/String"),
         (*env)->NewStringUTF(env,""));

    for(i=0;i<5;i++) {
        (*env)->SetObjectArrayElement(env,
                ret,i,(*env)->NewStringUTF(env, message[i]));
    }
    return(ret);
}

JNIEXPORT void JNICALL Java_ArrayManipulation_manipulateArray
(JNIEnv *env, jobject jobj, jobjectArray elements, 
                            jobject lock){

  jobjectArray ret;
  int i,j;
  //jint arraysize;
  int asize;
  jclass cls;
  jmethodID mid;
  jfieldID fid;
  long localArrayCopy[3][3];
  long localMatrix[3]={4,4,4};

  for(i=0; i<3; i++) {
     jintArray oneDim= 
        (jintArray)(*env)->GetObjectArrayElement(env,
                             elements, i);
     jint *element=(*env)->GetIntArrayElements(env,oneDim, 0);
     for(j=0; j<3; j++) {
        localArrayCopy[i][j]= element[j];
     }
  }

// With the C copy of the array, 
// process the array with LAPACK, BLAS, etc.

  for (i=0;i<3;i++) {
    for (j=0; j<3 ; j++) {
      localArrayCopy[i][j]=
        localArrayCopy[i][j]*localMatrix[i];
     }
  }

// Create array to send back
  jintArray row= (jintArray)(*env)->NewIntArray(env,3);
  ret=(jobjectArray)(*env)->NewObjectArray(env,
        3, (*env)->GetObjectClass(env,row), 0);

  for(i=0;i<3;i++) {
    row= (jintArray)(*env)->NewIntArray(env,3);
    (*env)->SetIntArrayRegion(env,(jintArray)row,(
        jsize)0,3,(jint *)localArrayCopy[i]);
    (*env)->SetObjectArrayElement(env,ret,i,row);
  }

  cls=(*env)->GetObjectClass(env,jobj);
  mid=(*env)->GetMethodID(env,cls, "sendArrayResults", 
                            "([[I)V");
  if (mid == 0) {
    printf("Can't find method sendArrayResults\n");
    return;
  }

  (*env)->ExceptionClear(env);
  (*env)->MonitorEnter(env,lock);
  (*env)->CallVoidMethod(env,jobj, mid, ret);
  (*env)->MonitorExit(env,lock);
  if((*env)->ExceptionOccurred(env)) {
    printf("error occured copying array back\n");
    (*env)->ExceptionDescribe(env);
    (*env)->ExceptionClear(env);
  }
  fid=(*env)->GetFieldID(env,cls, "arraySize",  "I");
  if (fid == 0) {
    printf("Can't find field arraySize\n");
    return;
  }
  asize=(*env)->GetIntField(env,jobj,fid);
  if((*env)->ExceptionOccurred(env)) {
    (*env)->ExceptionClear(env);
  }
  return;
}

JNIEXPORT void JNICALL Java_NativeExc_evilMethod(JNIEnv *env, jclass jcls)
{
    jclass cls = (*env)->FindClass(env, "java/lang/Exception");
    (*env)->ThrowNew(env, cls, "ich bin eine native Exception");
}

JNIEXPORT void JNICALL Java_NativeExc_evilMethod2(JNIEnv *env, jclass jcls)
{
    jclass cls = (*env)->FindClass(env, "java/lang/Exception");
    jmethodID methodID = (*env)->GetMethodID(env, cls, "<init>", "()V");
    jobject myObj = (*env)->NewObject(env, cls, methodID);
    (*env)->Throw(env, myObj);
}


JNIEXPORT void JNICALL Java_NativeExc_evilMethod3(JNIEnv *env, jclass jcls)
{
    jthrowable thrown = (*env)->ExceptionOccurred(env);
    //if(thrown==NULL)
    //    printf("C: throw is null on c side \n");
    jclass cls = (*env)->FindClass(env, "NativeExc");
    jmethodID method = (*env)->GetStaticMethodID(env, cls, "method", "()V");
    (*env)->CallStaticVoidMethod(env, jcls, method);
    thrown = (*env)->ExceptionOccurred(env);
    if(thrown!=NULL)
    {
        //printf("C: throw is NOT null on c side \n");
        (*env)->ExceptionDescribe(env);
        (*env)->ExceptionClear(env);
    }
    return;
}

JNIEXPORT void JNICALL Java_NativeExc_evilMethod4(JNIEnv *env, jclass jcls)
{
    jclass cls = (*env)->FindClass(env, "NativeExc");
    jmethodID method = (*env)->GetStaticMethodID(env, cls, "method2", "()I");
    int i= 41;
    printf("i=%i\n",i);
    jint j = (*env)->CallStaticIntMethod(env, jcls, method);
    i = (int) j;
    printf("i=%i\n",i);
    jthrowable thrown = (*env)->ExceptionOccurred(env);
    if(thrown!=NULL)
    {
        //printf("C: throw is NOT null on c side \n");
        (*env)->ExceptionDescribe(env);
        (*env)->ExceptionClear(env);
    }
    return;
}

JNIEXPORT void JNICALL Java_NativeExc_evilMethod5(JNIEnv *env, jclass jcls)
{
    jclass cls = (*env)->FindClass(env, "NativeExc");
    jmethodID method2 = (*env)->GetStaticMethodID(env, cls, "method2", "()I");
    jmethodID method = (*env)->GetStaticMethodID(env, cls, "method", "()V");
    (*env)->CallStaticIntMethod(env, jcls, method);
    (*env)->CallStaticVoidMethod(env, jcls, method2);
    /*jthrowable thrown = (*env)->ExceptionOccurred(env);
    if(thrown!=NULL)
    {
        printf("C: throw is NOT null on c side \n");
        (*env)->ExceptionDescribe(env);
        (*env)->ExceptionClear(env);
    }*/
    return;
}

JNIEXPORT void JNICALL Java_NativeExc_nativeMethod(JNIEnv *env, jclass jcls)
{
    jclass cls = (*env)->FindClass(env, "NativeExc");
    jmethodID m = (*env)->GetStaticMethodID(env, cls, "callBack", "()V");
    (*env)->CallStaticVoidMethod(env, jcls, m);
    //after that there sould "wait" a Exception on the java side for us.
}

JNIEXPORT void JNICALL Java_NativeExc2_nativeMethod(JNIEnv *env, jclass jcls)
{
    jclass cls = (*env)->FindClass(env, "NativeException");
    (*env)->ThrowNew(env, cls, "thrown on C Side");
    //after that there sould "wait" a Exception on the java side for us.
}

JNIEXPORT void JNICALL Java_NativeExc3_nativeMethod(JNIEnv *env, jclass jcls)
{
    jclass cls = (*env)->FindClass(env, "NativeException");
    jmethodID methodID = (*env)->GetMethodID(env, cls, "<init>", "()V");
    jobject myObj = (*env)->NewObject(env, cls, methodID);
    (*env)->Throw(env, (jthrowable) myObj);
    //after that there sould "wait" a Exception on the java side for us.
}

JNIEXPORT jboolean JNICALL Java_NativeExc4_nativeMethod(JNIEnv *env, jclass jcls)
{
    jclass cls = (*env)->FindClass(env, "NativeException");
    (*env)->ThrowNew(env, cls, "thrown on C Side");
    //after that there sould "wait" a Exception on the java side for us.
    jthrowable throwi = (*env)->ExceptionOccurred(env);
    if(throwi!=0&&(*env)->ExceptionCheck(env))
    {
        (*env)->ExceptionClear(env);
        if(!(*env)->ExceptionCheck(env)) return JNI_TRUE;
    }
    return JNI_FALSE;
}

JNIEXPORT void JNICALL Java_CallMe_callit(JNIEnv *env, jclass jcls, jint value)
{
       jclass cls = (*env)->FindClass(env, "CallMe");
       jmethodID method = (*env)->GetStaticMethodID(env, cls, "callme", "(I)V");
       (*env)->CallStaticVoidMethod(env, jcls, method, value);
}

JNIEXPORT jobjectArray JNICALL
 Java_ObjectArrayTest_initInt2DArray(JNIEnv *env,
                                    jclass cls,
                                    int size)
{
     jobjectArray result;
     int i;
     jclass intArrCls = (*env)->FindClass(env, "[I");
     if (intArrCls == NULL) {
         return NULL; /* exception thrown */
     }
     result = (*env)->NewObjectArray(env, size, intArrCls,
                                     NULL);
     if (result == NULL) {
         return NULL; /* out of memory error thrown */
     }
     for (i = 0; i < size; i++) {
         jint tmp[256];  /* make sure it is large enough! */
         int j;
         jintArray iarr = (*env)->NewIntArray(env, size);
         if (iarr == NULL) {
             return NULL; /* out of memory error thrown */
         }
         for (j = 0; j < size; j++) {
             tmp[j] = i + j;
         }
         (*env)->SetIntArrayRegion(env, iarr, 0, size, tmp);
         (*env)->SetObjectArrayElement(env, result, i, iarr);
         (*env)->DeleteLocalRef(env, iarr);
     }
     return result;
 }

JNIEXPORT jstring JNICALL
Java_Prompt_getLine(JNIEnv *env, jobject obj, jstring prompt)
{
    char buf[128];
    const jbyte *str;
    str = (*env)->GetStringUTFChars(env, prompt, NULL);
    if (str == NULL) {
        return NULL; /* OutOfMemoryError already thrown */
    }
    printf("%s", str);
    (*env)->ReleaseStringUTFChars(env, prompt, str);
    /* We assume here that the user does not type more than
    * 127 characters */
    scanf("%s", buf);
    return (*env)->NewStringUTF(env, buf);
}

// end of native-method implementations(test-jni.py)


// some stupid tests
// TODO: delete them some day...

int* quitschibo(int* array)
{
    array[0] = 41;
    return array;
}

void test_blubby(int* array)
{
    array[0] = 41;
}

struct astr
{
   int x;
   int y;
};

typedef union myvalue
{
  jboolean z;
  jbyte    b;
  jchar    c;
  jshort   s;
  jint     i;
  jlong    j;
  jfloat   f;
  jdouble  d;
  jobject  l;
} myvalue;

struct astr a_str_method(int a, int b)
{
    struct astr str;
    str.x = a;
    str.y = b;
    return str;
}

myvalue* a_union_method(int in)
{
    myvalue values[4];
    values[0].i = in;
    return values; //FIXME: returns address of local var
}

// start of jni tests used in test_native.py:
// The following lines are just the tests for the jni-env. implementation.
// This is not the implementation, which is writen in python via ctypes.
// Every test-function calls its python function on the python site and
// returns its result. Some "void-functions" doing this via pointers.

JNIEXPORT jint JNICALL test_GetVersion(JNIEnv *env) 
{
    return (*env)->GetVersion( env );
}

// #############
// String operations
// ##############

JNIEXPORT const char * JNICALL test_GetStringUTFChars(JNIEnv *env, jstring string, jboolean *isCopy)
{
    return (*env)->GetStringUTFChars( env, string, NULL );
}

JNIEXPORT jstring JNICALL test_NewString(JNIEnv *env, const jchar *c, jsize size)
{
    return (*env)->NewString(env, c, size);
}

JNIEXPORT jint JNICALL test_GetStringLength(JNIEnv *env, jstring string)
{
    return (*env)->GetStringLength(env, string);
}

JNIEXPORT const jchar * JNICALL test_GetStringChars(JNIEnv *env, jstring string,
 jboolean *isCopy)
{
    return (*env)->GetStringChars(env, string, isCopy);
}

JNIEXPORT void JNICALL test_ReleaseStringChars(JNIEnv *env, jstring string, 
 const jchar *chars)
{
    (*env)->ReleaseStringChars(env, string, chars);
}

JNIEXPORT jstring JNICALL test_NewStringUTF(JNIEnv *env, const char *bytes)
{
    return (*env)->NewStringUTF(env, bytes);
}

JNIEXPORT jsize JNICALL test_GetStringUTFLength(JNIEnv *env, jstring string)
{
    return (*env)->GetStringUTFLength(env, string);
}

JNIEXPORT void JNICALL test_ReleaseStringUTFChars(JNIEnv *env, jstring string, const char *utf)
{
    (*env)->ReleaseStringUTFChars(env, string, utf);
}

JNIEXPORT void JNICALL test_GetStringRegion(JNIEnv *env, jstring str, jsize start, jsize len, jchar *buf)
{
    (*env)->GetStringRegion(env, str, start, len, buf);
}

JNIEXPORT void JNICALL test_GetStringUTFRegion(JNIEnv *env, jstring str, jsize start, jsize len, char *buf)
{
    (*env)->GetStringUTFRegion(env, str, start, len, buf);
}

JNIEXPORT const jchar * JNICALL test_GetStringCritical(JNIEnv *env, jstring string, jboolean *isCopy)
{
    return (*env)->GetStringCritical(env, string, isCopy);
}

JNIEXPORT void JNICALL test_ReleaseStringCritical(JNIEnv *env, jstring string, const jchar *carray)
{
    (*env)->ReleaseStringCritical(env, string, carray);
}

JNIEXPORT jfieldID JNICALL test_GetFieldID(JNIEnv *env, jclass clazz, 
 const char *name, const char *sig)
{
    return (*env)->GetFieldID(env, clazz, name, sig);
}

jclass test_pyobject(jclass clazz)
{
    return clazz;
}

// #####################
// get and set  field
// ##################

JNIEXPORT void JNICALL test_SetObjectField(JNIEnv *env, jobject obj, jfieldID fieldID, jobject value)
{
    (*env)->SetObjectField(env, obj, fieldID, value);
}

JNIEXPORT jobject JNICALL test_GetObjectField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetObjectField(env, obj, fieldID);
}

JNIEXPORT void JNICALL test_SetBooleanField(JNIEnv *env, jobject obj, jfieldID fieldID, jboolean value)
{
    (*env)->SetBooleanField(env, obj, fieldID, value);
}

JNIEXPORT jboolean JNICALL test_GetBooleanField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetBooleanField(env, obj, fieldID);
}

JNIEXPORT void JNICALL test_SetByteField(JNIEnv *env, jobject obj, jfieldID fieldID, jbyte value)
{
    (*env)->SetByteField(env, obj, fieldID, value);
}

JNIEXPORT jbyte JNICALL test_GetByteField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetByteField(env, obj, fieldID);
}

JNIEXPORT void JNICALL test_SetCharField(JNIEnv *env, jobject obj, jfieldID fieldID, jchar value)
{
    (*env)->SetCharField(env, obj, fieldID, value);
}

JNIEXPORT jchar JNICALL test_GetCharField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetCharField(env, obj, fieldID);
}

JNIEXPORT void JNICALL test_SetShortField(JNIEnv *env, jobject obj, jfieldID fieldID, jshort value)
{
    (*env)->SetShortField(env, obj, fieldID, value);
}

JNIEXPORT jshort JNICALL test_GetShortField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetShortField(env, obj, fieldID);
}

JNIEXPORT void JNICALL test_SetIntField(JNIEnv *env, jobject obj, jfieldID fieldID, jint value)
{
    (*env)->SetIntField(env, obj, fieldID, value);
}

JNIEXPORT jint JNICALL test_GetIntField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetIntField(env, obj, fieldID);
}

JNIEXPORT void JNICALL test_SetLongField(JNIEnv *env, jobject obj, jfieldID fieldID, jlong value)
{
    (*env)->SetLongField(env, obj, fieldID, value);
}

JNIEXPORT jlong JNICALL test_GetLongField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetLongField(env, obj, fieldID);
}

JNIEXPORT void JNICALL test_SetFloatField(JNIEnv *env, jobject obj, jfieldID fieldID, jfloat value)
{
    (*env)->SetFloatField(env, obj, fieldID, value);
}

JNIEXPORT jfloat JNICALL test_GetFloatField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetFloatField(env, obj, fieldID);
}

JNIEXPORT void JNICALL test_SetDoubleField(JNIEnv *env, jobject obj, jfieldID fieldID, jdouble value)
{
    (*env)->SetDoubleField(env, obj, fieldID, value);
}

JNIEXPORT jdouble JNICALL test_GetDoubleField(JNIEnv *env, jobject obj, 
 jfieldID fieldID)
{
    return (*env)->GetDoubleField(env, obj, fieldID);
}

// #######################
// call instance method
// #####################

JNIEXPORT void JNICALL test_CallVoidMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    (*env)->CallVoidMethodV(env, obj, methodID, args);
}

JNIEXPORT jobject JNICALL test_CallObjectMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallObjectMethodV(env, obj, methodID, args);
}

JNIEXPORT jboolean JNICALL test_CallBooleanMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallBooleanMethodV(env, obj, methodID, args);
}

JNIEXPORT jbyte JNICALL test_CallByteMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallByteMethodV(env, obj, methodID, args);
}

JNIEXPORT jshort JNICALL test_CallShortMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallShortMethodV(env, obj, methodID, args);
}

JNIEXPORT jint JNICALL test_CallIntMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallIntMethodV(env, obj, methodID, args);
}

JNIEXPORT jchar JNICALL test_CallCharMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallCharMethodV(env, obj, methodID, args);
}

JNIEXPORT jlong JNICALL test_CallLongMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallLongMethodV(env, obj, methodID, args);
}

JNIEXPORT jfloat JNICALL test_CallFloatMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallFloatMethodV(env, obj, methodID, args);
}

JNIEXPORT jdouble JNICALL test_CallDoubleMethodV(JNIEnv *env, jobject obj, 
 jmethodID methodID, va_list args)
{
    return (*env)->CallDoubleMethodV(env, obj, methodID, args);
}

JNIEXPORT jmethodID JNICALL test_GetMethodID(JNIEnv *env, jclass clazz, 
 const char *name, const char *sig)
{
    return (*env)->GetMethodID(env, clazz, name, sig);
}

JNIEXPORT jfieldID JNICALL test_GetStaticFieldID(JNIEnv *env, jclass clazz, 
 const char *name, const char *sig)
{
    return (*env)->GetStaticFieldID(env, clazz, name, sig);
}

// ######################
// get static field
// ####################

JNIEXPORT jint JNICALL test_GetStaticIntField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticIntField(env, clazz, fieldID);
}

JNIEXPORT jobject JNICALL test_GetStaticObjectField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticObjectField(env, clazz, fieldID);
}

JNIEXPORT jboolean JNICALL test_GetStaticBooleanField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticBooleanField(env, clazz, fieldID);
}

JNIEXPORT jbyte JNICALL test_GetStaticByteField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticByteField(env, clazz, fieldID);
}

JNIEXPORT jchar JNICALL test_GetStaticCharField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticCharField(env, clazz, fieldID);
}

JNIEXPORT jshort JNICALL test_GetStaticShortField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticShortField(env, clazz, fieldID);
}

JNIEXPORT jlong JNICALL test_GetStaticLongField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticLongField(env, clazz, fieldID);
}

JNIEXPORT jfloat JNICALL test_GetStaticFloatField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticFloatField(env, clazz, fieldID);
}

JNIEXPORT jdouble JNICALL test_GetStaticDoubleField(JNIEnv *env, jclass clazz, jfieldID fieldID)
{
        return (*env)->GetStaticDoubleField(env, clazz, fieldID);
}

// ####################
// set static field
// ####################

JNIEXPORT void JNICALL test_SetStaticObjectField(JNIEnv *env, jclass clazz, jfieldID fieldID, jobject value)
{
    return (*env)->SetStaticObjectField(env, clazz, fieldID, value);
}

JNIEXPORT void JNICALL test_SetStaticBooleanField(JNIEnv *env, jclass clazz, jfieldID fieldID, jboolean value)
{
    return (*env)->SetStaticBooleanField(env, clazz, fieldID, value);
}

JNIEXPORT void JNICALL test_SetStaticByteField(JNIEnv *env, jclass clazz, jfieldID fieldID, jbyte value)
{
    return (*env)->SetStaticByteField(env, clazz, fieldID, value);
}

JNIEXPORT void JNICALL test_SetStaticCharField(JNIEnv *env, jclass clazz, jfieldID fieldID, jchar value)
{
    return (*env)->SetStaticCharField(env, clazz, fieldID, value);
}

JNIEXPORT void JNICALL test_SetStaticShortField(JNIEnv *env, jclass clazz, jfieldID fieldID, jshort value)
{
    return (*env)->SetStaticShortField(env, clazz, fieldID, value);
}

JNIEXPORT void JNICALL test_SetStaticIntField(JNIEnv *env, jclass clazz, jfieldID fieldID, jint value)
{
    return (*env)->SetStaticIntField(env, clazz, fieldID, value);
}

JNIEXPORT void JNICALL test_SetStaticLongField(JNIEnv *env, jclass clazz, jfieldID fieldID, jlong value)
{
    return (*env)->SetStaticLongField(env, clazz, fieldID, value);
}

JNIEXPORT void JNICALL test_SetStaticFloatField(JNIEnv *env, jclass clazz, jfieldID fieldID, jfloat value)
{
    return (*env)->SetStaticFloatField(env, clazz, fieldID, value);
}

JNIEXPORT void JNICALL test_SetStaticDoubleField(JNIEnv *env, jclass clazz, jfieldID fieldID, jdouble value)
{
    return (*env)->SetStaticDoubleField(env, clazz, fieldID, value);
}

// ##########################
// call static method
// ########################

JNIEXPORT void JNICALL test_CallStaticVoidMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticVoidMethodV(env, clazz, methodID, args);
}

JNIEXPORT jobject JNICALL test_CallStaticObjectMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticObjectMethodV(env, clazz, methodID, args);
}

JNIEXPORT jboolean JNICALL test_CallStaticBooleanMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticBooleanMethodV(env, clazz, methodID, args);
}

JNIEXPORT jbyte JNICALL test_CallStaticByteMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticByteMethodV(env, clazz, methodID, args);
}

JNIEXPORT jchar JNICALL test_CallStaticCharMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticCharMethodV(env, clazz, methodID, args);
}

JNIEXPORT jshort JNICALL test_CallStaticShortMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticShortMethodV(env, clazz, methodID, args);
}

JNIEXPORT jint JNICALL test_CallStaticIntMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticIntMethodV(env, clazz, methodID, args);
}

JNIEXPORT jlong JNICALL test_CallStaticLongMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticLongMethodV(env, clazz, methodID, args);
}

JNIEXPORT jfloat JNICALL test_CallStaticFloatMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticFloatMethodV(env, clazz, methodID, args);
}

JNIEXPORT jdouble JNICALL test_CallStaticDoubleMethodV(JNIEnv *env, jclass clazz,
 jmethodID methodID, va_list args)
{
    return (*env)->CallStaticDoubleMethodV(env, clazz, methodID, args);
}

// #################
// Array operations
// ##############

JNIEXPORT void JNICALL test_SetBooleanArrayRegion(JNIEnv *env, jbooleanArray array, 
 jsize start, jsize len, jboolean *buf)
{
    (*env)->SetBooleanArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_SetByteArrayRegion(JNIEnv *env, jbyteArray array, 
 jsize start, jsize len, jbyte *buf)
{
    (*env)->SetByteArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_SetCharArrayRegion(JNIEnv *env, jcharArray array, 
 jsize start, jsize len, jchar *buf)
{
    (*env)->SetCharArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_SetShortArrayRegion(JNIEnv *env, jshortArray array, 
 jsize start, jsize len, jshort *buf)
{
    (*env)->SetShortArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_SetIntArrayRegion(JNIEnv *env, jintArray array, 
 jsize start, jsize len, jint *buf)
{
    (*env)->SetIntArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_SetLongArrayRegion(JNIEnv *env, jlongArray array, 
 jsize start, jsize len, jlong *buf)
{
    (*env)->SetLongArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_SetFloatArrayRegion(JNIEnv *env, jfloatArray array, 
 jsize start, jsize len, jfloat *buf)
{
    (*env)->SetFloatArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_SetDoubleArrayRegion(JNIEnv *env, jdoubleArray array, 
 jsize start, jsize len, jdouble *buf)
{
    (*env)->SetDoubleArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_GetBooleanArrayRegion(JNIEnv *env, jbooleanArray array,
 jsize start, jsize len, jboolean *buf)
{
    (*env)->GetBooleanArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_GetByteArrayRegion(JNIEnv *env, jbyteArray array,
 jsize start, jsize len, jbyte *buf)
{
    (*env)->GetByteArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_GetCharArrayRegion(JNIEnv *env, jcharArray array,
 jsize start, jsize len, jchar *buf)
{
    (*env)->GetCharArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_GetShortArrayRegion(JNIEnv *env, jshortArray array,
 jsize start, jsize len, jshort *buf)
{
    (*env)->GetShortArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_GetIntArrayRegion(JNIEnv *env, jintArray array,
 jsize start, jsize len, jint *buf)
{
    (*env)->GetIntArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_GetLongArrayRegion(JNIEnv *env, jlongArray array,
 jsize start, jsize len, jlong *buf)
{
    (*env)->GetLongArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_GetFloatArrayRegion(JNIEnv *env, jfloatArray array,
 jsize start, jsize len, jfloat *buf)
{
    (*env)->GetFloatArrayRegion(env, array, start, len, buf);
}

JNIEXPORT void JNICALL test_GetDoubleArrayRegion(JNIEnv *env, jdoubleArray array,
 jsize start, jsize len, jdouble *buf)
{
    (*env)->GetDoubleArrayRegion(env, array, start, len, buf);
}

JNIEXPORT jobjectArray JNICALL test_NewObjectArray(JNIEnv *env, jsize length, 
 jclass elementClass, jobject initialElement)
{
    return (*env)->NewObjectArray(env, length, elementClass, initialElement);
}

JNIEXPORT jsize JNICALL test_GetArrayLength(JNIEnv *env, jarray array)
{
    return (*env)->GetArrayLength(env, array);
}

JNIEXPORT jobject JNICALL test_GetObjectArrayElement(JNIEnv *env, 
 jobjectArray array, jsize index)
{
    return (*env)->GetObjectArrayElement(env, array, index);
}

JNIEXPORT void JNICALL test_SetObjectArrayElement(JNIEnv *env, jobjectArray array, jsize index, jobject value)
{
    return (*env)->SetObjectArrayElement(env, array, index, value);
}

JNIEXPORT jbooleanArray JNICALL test_NewBooleanArray(JNIEnv *env, jsize length)
{
    return (*env)->NewBooleanArray(env, length);
}

JNIEXPORT jbyteArray JNICALL test_NewByteArray(JNIEnv *env, jsize length)
{
    return (*env)->NewByteArray(env, length);
}

JNIEXPORT jcharArray JNICALL test_NewCharArray(JNIEnv *env, jsize length)
{
    return (*env)->NewCharArray(env, length);
}

JNIEXPORT jshortArray JNICALL test_NewShortArray(JNIEnv *env, jsize length)
{
    return (*env)->NewShortArray(env, length);
}

JNIEXPORT jintArray JNICALL test_NewIntArray(JNIEnv *env, jsize length)
{
    return (*env)->NewIntArray(env, length);
}

JNIEXPORT jlongArray JNICALL test_NewLongArray(JNIEnv *env, jsize length)
{
    return (*env)->NewLongArray(env, length);
}

JNIEXPORT jfloatArray JNICALL test_NewFloatArray(JNIEnv *env, jsize length)
{
    return (*env)->NewFloatArray(env, length);
}

JNIEXPORT jdoubleArray JNICALL test_NewDoubleArray(JNIEnv *env, jsize length)
{
    return (*env)->NewDoubleArray(env, length);
}

jboolean *test_GetBooleanArrayElements(JNIEnv *env, jbooleanArray array, jboolean *isCopy)
{
    return (*env)->GetBooleanArrayElements(env, array, isCopy);
}

jbyte *test_GetByteArrayElements(JNIEnv *env, jbyteArray array, jboolean *isCopy)
{
    return (*env)->GetByteArrayElements(env, array, isCopy);
}

jchar *test_GetCharArrayElements(JNIEnv *env, jcharArray array, jboolean *isCopy)
{
    return (*env)->GetCharArrayElements(env, array, isCopy);
}

jshort *test_GetShortArrayElements(JNIEnv *env, jshortArray array, jboolean *isCopy)
{
    return (*env)->GetShortArrayElements(env, array, isCopy);
}

jint *test_GetIntArrayElements(JNIEnv *env, jintArray array, jboolean *isCopy)
{
    return (*env)->GetIntArrayElements(env, array, isCopy);
}

jlong *test_GetLongArrayElements(JNIEnv *env, jlongArray array, jboolean *isCopy)
{
    return (*env)->GetLongArrayElements(env, array, isCopy);
}

jfloat *test_GetFloatArrayElements(JNIEnv *env, jfloatArray array, jboolean *isCopy)
{
    return (*env)->GetFloatArrayElements(env, array, isCopy);
}

jdouble *test_GetDoubleArrayElements(JNIEnv *env, jdoubleArray array, jboolean *isCopy)
{
    return (*env)->GetDoubleArrayElements(env, array, isCopy);
}

// #################
// class operations
// ############

JNIEXPORT jclass JNICALL test_GetSuperclass(JNIEnv *env, jclass clazz)
{
    return (*env)->GetSuperclass(env, clazz);
}

JNIEXPORT jboolean JNICALL test_IsAssignableFrom(JNIEnv *env, jclass clazz1, 
 jclass clazz2)
{
    return (*env)->IsAssignableFrom(env, clazz1, clazz2);
}

// ###################
// object operations
// ##############
JNIEXPORT jobject JNICALL test_AllocObject(JNIEnv *env, jclass clazz)
{
    return (*env)->AllocObject(env, clazz);
}

JNIEXPORT jclass JNICALL test_GetObjectClass(JNIEnv *env, jobject obj)
{
    return (*env)->GetObjectClass(env, obj);
}

JNIEXPORT jboolean JNICALL test_IsInstanceOf(JNIEnv *env, jobject obj, jclass clazz)
{
    return (*env)->IsInstanceOf(env, obj, clazz);
}

JNIEXPORT jboolean JNICALL test_IsSameObject(JNIEnv *env, jobject ref1, 
 jobject ref2)
{
    return (*env)->IsSameObject(env, ref1, ref2);
}

// ###################
// nonvirtual methodcall
// ################
JNIEXPORT void JNICALL test_CallNonvirtualVoidMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualVoidMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jobject JNICALL test_CallNonvirtualObjectMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualObjectMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jboolean JNICALL test_CallNonvirtualBooleanMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualBooleanMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jbyte JNICALL test_CallNonvirtualByteMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualByteMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jchar JNICALL test_CallNonvirtualCharMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualCharMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jshort JNICALL test_CallNonvirtualShortMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualShortMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jint JNICALL test_CallNonvirtualIntMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualIntMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jlong JNICALL test_CallNonvirtualLongMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualLongMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jfloat JNICALL test_CallNonvirtualFloatMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualFloatMethodV(env, obj, clazz, methodID, args);
}

JNIEXPORT jdouble JNICALL test_CallNonvirtualDoubleMethodV(JNIEnv *env, jobject obj,
 jclass clazz, jmethodID methodID, va_list args)
{
    return (*env)->CallNonvirtualDoubleMethodV(env, obj, clazz, methodID, args);
}

