# -*- coding: utf-8 -*-
import py
from test_interp import RunTests
from ctypes import cdll

class TestJNI(RunTests):

    def test_static_method_call(self):
        cls = self.getclass('''
        class CallMe {
            static int x=1;
            public static native void callit(int j);
            public static void callme(int j){x=j;}
            public static void main(String[] args)
            {
                System.loadLibrary( "test_native" ); 
                System.out.println(x);
                callit(2);
                System.out.println(x);
            }
        }
        ''', "")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "1\n2\n")

    def test_jni_add(self):
        py.test.skip("in-progress test_jni_add") 
        # works but can't capure the print
        cls = self.getclass('''
        public class Add {

            int number;

            public native void calc(int j);

            public static void main(String[] args)
            {
                System.loadLibrary( "test_native" ); 
                Add a = new Add();
                a.number = 40;
                a.calc(1);
            }
        }
        ''', "Add")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "41 \n")

    def test_jni_fac(self):
        cls = self.getclass('''
        class Fac {
            public native int fun();
            public int i;
            public static void main(String[] args)
            {
                System.loadLibrary( "test_native" );
                Fac fac = new Fac();
                fac.i = 7;
                System.out.println(fac.fun());
            }
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "720\n")

    def test_jni_methodcallA(self):
        cls = self.getclass('''
        class Sum {
            static int x=1;
            static int y=2;
            public native void cCode();
            public void set_it(int a, int b)
            {
                x = a;
                y = b;
            }

            public static void main(String[] args)
            {
                System.loadLibrary( "test_native" );
                Sum s = new Sum();
                System.out.println(x+y);
                s.cCode();
                System.out.println(x+y);
            }
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "3\n7\n")

    def test_jni_var_args(self):
        cls = self.getclass('''
        class Va {
            public native void nativeMethod();
            public native int nativeMethod2();
            public void method(int a, int b)
            {
                System.out.println(a+b);
            }
            public int method2(int a, int b)
            {
                return a+b;
            }
            public static void main(String[] args)
            {
                System.loadLibrary( "test_native" ); 
                Va va = new Va();
                int x = va.nativeMethod2();
                System.out.println(x);
            }
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "3\n")

    def test_strlen(self):
        cls = self.getclass('''
        class StrLen {
            public static native int strlen( String s );
            public static void main(String[] args)
            {
                System.loadLibrary( "test_native" ); 
                int len = strlen("Hallo Peter");
                System.out.println(len);
            }
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "11\n")

    def test_intArray(self):
        cls = self.getclass('''
        class IntArray {
            private native int sumArray(int[] arr);
            public static void main(String[] args) {
                IntArray p = new IntArray();
                int arr[] = new int[10];
                for (int i = 0; i < 10; i++) {
                    arr[i] = i;
                }
                int sum = p.sumArray(arr);
                System.out.println("sum = " + sum);
            }
            static {
                System.loadLibrary("test_native");
            }
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "sum = 45\n")

    def test_ObjectArrayTest(self):
        cls = self.getclass('''
        class ObjectArrayTest {
            private static native int[][] initInt2DArray(int size);
            public static void main(String[] args) {
                int[][] i2arr = initInt2DArray(3);
                for (int i = 0; i < 3; i++) {
                    for (int j = 0; j < 3; j++) {
                        System.out.print(" " + i2arr[i][j]);
                    }
                    System.out.println();
                }
            }
            static {
                System.loadLibrary("test_native");
            }
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], " 0 1 2\n 1 2 3\n 2 3 4\n")

    def test_ObjectArrayTest2(self):
        cls = self.getclass('''
        class ObjectArrayTest2 {
            private static native Object[] initObjArray(int size);
            public static void main(String[] args) {
                Object[] objArr = initObjArray(3);
                A obj;
                for (int i = 0; i < 3; i++) {
                        obj = (A) objArr[i];
                        System.out.println(obj.x);
                    }
                }
            static {
                System.loadLibrary("test_native");
            }
        }

        class A{
            int x;
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "41\n42\n43\n")

    def test_ObjectArrayTest3(self):
        # this test uses an other init on the c-level
        cls = self.getclass('''
        class ObjectArrayTest3 {
            private static native Object[] initObjArray(int size);
            public static void main(String[] args) {
                Object[] objArr = initObjArray(3);
                A obj;
                for (int i = 0; i < 3; i++) {
                        obj = (A) objArr[i];
                        System.out.println(obj.x);
                    }
                }
            static {
                System.loadLibrary("test_native");
            }
        }

        class A{
            int x = 42;
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "41\n41\n41\n")

    def test_ObjectArrayTest4(self):
        # this test inits the String Array with "C" insted of null
        cls = self.getclass('''
        class ObjectArrayTest4 {
            private static native String[] initObjArray(int size);
            public static void main(String[] args) {
                String[] strArr = initObjArray(3);
                //String[] strArr2 = new String[3];
                for (int i = 0; i < strArr.length; i++) 
                {
                        System.out.println(strArr[i]);
                        //System.out.println(strArr2[i]);
                }
            }

            static {
                System.loadLibrary("test_native");
            }
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "C\nC\nC\n")

    def test_ReadFile(self):
        # from http://java.sun.com/developer/onlineTraining/Programming/JDCBook/jniexamp.html
        data = ""
        fobj = open("/home/stupsi/pypy_kram/jvm/jvm/test_classes/ReadFile.java", "r")
        for line in fobj:
            data += line
        fobj.close()
        cls = self.getclass('''
        import java.util.*;

        class ReadFile {
        //Native method declaration
        native byte[] loadFile(String name);
        //Load the library
        static {
            System.loadLibrary("test_native");
        }

        public static void main(String args[]) {
            byte buf[];
        //Create class instance
            ReadFile mappedFile=new ReadFile();
        //Call native method to load ReadFile.java
            buf=mappedFile.loadFile("/home/stupsi/pypy_kram/jvm/jvm/test_classes/ReadFile.java");
        //Print contents of ReadFile.java
            for(int i=0;i<buf.length;i++) {
            System.out.print((char)buf[i]);
            }
        }
        }
        ''', "ReadFile")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], data)

    # tests throw on java level
    def test_native_Exception(self):
        cls = self.getclass('''
        public class NativeExc {
            static{ System.loadLibrary("test_native");}

            public native static void nativeMethod() throws NativeException;

            public static void callBack() throws Exception
            {
                throw new NativeException("callBack: Error on Javaside");
            }

            public static void main(String[] args)
            {
                try{
                    nativeMethod();
                }
                catch(NativeException e)
                {
                    System.out.println("catch:NativeException");
                }
                finally
                {
                    System.out.println("finally");
                }
            }
        }

        class NativeException extends Exception {
            public NativeException(String s){super(s);}
        }
        ''', "NativeExc")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "catch:NativeException\nfinally\n")

    # tests JNI-Env-fct ThrowNew
    def test_native_Exception2(self):
        cls = self.getclass('''
        public class NativeExc2 {
            static{ System.loadLibrary("test_native");}

            public native static void nativeMethod() throws NativeException;

            public static void main(String[] args)
            {
                try{
                    nativeMethod();
                }
                catch(NativeException e)
                {
                    System.out.println("catch:NativeException");
                }
                finally
                {
                    System.out.println("finally");
                }
            }
        }

        class NativeException extends Exception {
            public NativeException(String s){super(s);}
        }
        ''', "NativeExc2")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "catch:NativeException\nfinally\n")

    #TODO: use String constructor
    # tests JNI-Env-fct Throw
    def test_native_Exception3(self):
        cls = self.getclass('''
        public class NativeExc3 {
            static{ System.loadLibrary("test_native");}

            public native static void nativeMethod() throws NativeException;

            public static void main(String[] args)
            {
                try{
                    nativeMethod();
                }
                catch(NativeException e)
                {
                    System.out.println("catch:NativeException");
                }
                finally
                {
                    System.out.println("finally");
                }
            }
        }

        class NativeException extends Exception {
            public NativeException(){super();}
            public NativeException(String s){super(s);}
        }
        ''', "NativeExc3")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "catch:NativeException\nfinally\n")

    #tests ExceptionOccured, ExceptionCheck and ExceptionClear
    def test_native_Exception4(self):
        cls = self.getclass('''
        public class NativeExc4 {
            static{ System.loadLibrary("test_native");}

            public native static boolean nativeMethod() throws NativeException;

            public static void main(String[] args)
            {
                boolean b = false;
                try{
                    b = nativeMethod();
                }
                catch(NativeException e)
                {
                    System.out.println("catch:NativeException");
                }
                finally
                {
                    System.out.println("finally");
                }
                System.out.println(b);
            }
        }

        class NativeException extends Exception {
            public NativeException(String s){super(s);}
        }
        ''', "NativeExc4")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "finally\ntrue\n")

    def test_ArrayHandler(self):
        # from http://java.sun.com/developer/onlineTraining/Programming/JDCBook/jnistring.html
        cls = self.getclass('''
        public class ArrayHandler {
            public native String[] returnArray();
            static{
                System.loadLibrary("test_native");
            }

            public static void main(String args[]) {
                String ar[];
                ArrayHandler ah= new ArrayHandler();
                ar = ah.returnArray();
                for (int i=0; i<5; i++) {
                System.out.println("array element"+i+ 
                                        "=" + ar[i]);
                }
            }
        }''',"ArrayHandler")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "array element0=first\narray element1=second\narray element2=third\narray element3=fourth\narray element4=fifth\n")

    # uses threading JNI-Env functions which are not implemented
    def test_ArrayManipulation(self):
        py.test.skip("in-progress test_ArrayManipulation") 
        cls = self.getclass('''
        public class ArrayManipulation {
        private int arrayResults[][];
        Boolean lock=new Boolean(true);
        int arraySize=-1;

        public native void manipulateArray(
                        int[][] multiplier, Boolean lock);

        static{
            System.loadLibrary("test_native");
        }

        public void sendArrayResults(int results[][]) {
            arraySize=results.length;
            arrayResults=new int[results.length][];
            System.arraycopy(results,0,arrayResults,
                            0,arraySize);
        }

        public void displayArray() {
            for (int i=0; i<arraySize; i++) {
            for(int j=0; j <arrayResults[i].length;j++) {
                System.out.println("array element "+i+","+j+ 
                "= "  + arrayResults[i][j]);
            }
            }
        }

        public static void main(String args[]) {
            int[][] ar = new int[3][3];
            int count=3;
            for(int i=0;i<3;i++) {
            for(int j=0;j<3;j++) {
                ar[i][j]=count;
            }
            count++;
            }
            ArrayManipulation am= new ArrayManipulation();
            am.manipulateArray(ar, am.lock);
            am.displayArray();
        }
        }
        ''',"ArrayManipulation")
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "array element 0,0= 12\narray element 0,1= 0\narray element 0,2= 12\narray element 1,0= 16\narray element 1,1= 0\narray element 1,2= 16\narray element 2,0= 20\narray element 2,1= 0\narray element 2,2= 20\n")

    def test_StringTest(self):
        py.test.skip("in-progress test_StringTest") 
        # works but can't capure the print
        cls = self.getclass('''
        class Prompt {
            // native method that prints a prompt and reads a line
            private native String getLine(String prompt);
            public static void main(String args[]) {
                Prompt p = new Prompt();
                String input = p.getLine("Type a line: ");
                System.out.println("User typed: " + input);
            }

            static {
                System.loadLibrary("test_native");
            }
        }
        ''')
        string = "libtest_native.so"
        self.loader.extern_libs[string] = cdll.LoadLibrary("/usr/lib/"+string)
        self.run(cls, [], "User typed: \n")