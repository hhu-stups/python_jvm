# -*- coding: utf-8 -*-

from classloader import encode_name, descriptor
from interp import ClassLoader, Stack, Arrayref, make_String
from javaclasses import JavaIoPrintStream


#import interp
#import java_threading
import py, os, StringIO

udir = py.path.local.make_numbered_dir(prefix='usession-', keep=3)
#current_dir = py.magic.autopath().dirpath()
current_dir = os.path.abspath(os.path.dirname("test_interp.py"))

# CALL: This class is a baseclass of Testsimple.
# It contains two methods to parse, create and run
# (python-)javaclasses
class RunTests:
    ClassLoader = ClassLoader
    classpath = [str(udir), str(current_dir.join("test_classes")), str(current_dir)]
    #classpath = [str(udir), str(current_dir.join("classpath"))]
    #classpath = [str(udir)]

    # CALL: This method is called by every test
    # It creates a java (content=src) file into the temp dir and checks
    # if it compiles correctly with the sun jvm, than it
    # uses our Classloader to return a python repr. of this class
    def getclass(self, src, name=None):
        interp.interp_lock.acquire()
        #import java_threading
        java_threading.main_thread_cache = None
        java_threading.currentVMThread = "main_no_init"
        words = src.split()
        assert name or words[0] == 'class'
        classname = name or words[1]

        if "/" in classname:
            self.create_dirs_helper(classname)

        javafilepath = udir.join(classname + '.java')
        javafilepath.write(src)
        res = os.system('CLASSPATH=%r javac -encoding utf8 %r' % (
            os.path.pathsep.join(self.classpath), str(javafilepath),))
        assert res == 0
        self.loader = self.ClassLoader([str(udir)])
        result = self.loader.getclass(classname)
        interp.interp_lock.release()
        return result

    # check for packages and create folders:
    def create_dirs_helper(self, classname):
        folderlist = classname.split("/")
        dirs = ""
        for folder in folderlist[:-1]:
            dirs += "/"+folder
        path = str(udir) + dirs
        os.makedirs(path)


    def run(self, jcls, args, expected=None, regex=None, skip = False, expected_err = None):
        # first check against the official java result
        from subprocess import Popen, PIPE #for stderr
        quoted_args = ' '.join([repr(arg) for arg in args])
        p =  Popen("CLASSPATH=%r java %s %s" % (os.path.pathsep.join(self.classpath),jcls.__name__,quoted_args) ,shell=True, stderr=PIPE, stdin=PIPE, stdout=PIPE)
        w, r, e = (p.stdin, p.stdout, p.stderr)
        out = r.read()
        err_out = e.read()
        r.close()
        w.close()
        e.close()
        if not skip:
            assert out == expected     # as run with 'java'
        if expected_err:
            assert err_out == expected_err
        #print "out:",out
        # next, run with our interpreter
        out = StringIO.StringIO()
        JavaIoPrintStream.output = out
        try:
            interp.interp_lock.acquire()
            #import java_threading
            java_threading.currentVMThread = "main_no_init"
            java_threading.main_thread_cache = None
            main_name = encode_name(u'main', [u'array:reference:java/lang/String', None])
            str_list = []
            for arg in args:
                str_list.append(make_String(arg, self.loader))
            stack = Stack()
            stack.push(Arrayref(str_list, "", self.loader.getclass("[Ljava.lang.String;")))
            method = jcls.methods[unicode(main_name)]
            const = jcls.cls.constant_pool
            descr = descriptor(const[method.descriptor_index])
            res = self.loader.invoke_method(jcls.cls, method, descr, stack)
            assert res is None
        finally:
            interp.interp_lock.release()
            java_threading.wait_for_all_threads()
            JavaIoPrintStream.output = None
        assert out.getvalue() == expected   # our interpreter's result

class TestSimple(RunTests):
    def test_helloworld(self):
        cls = self.getclass('''
            class helloworld {
                public static void main(String[] args)
                {
                    System.out.println("Hello, world");
                }
            }
        ''')
        self.run(cls, ["foo", "bar"], "Hello, world\n")

    def test_class_fields(self):
        cls = self.getclass('''
            class ClassFields {
                boolean bo;
                char c;
                byte by;
                short s;
                int i;
                long l;
                float f;
                double d;

                ClassFields()
                {
                    this.bo = true;
                    this.c = 'X';
                    this.by = 1;
                    this.s = 2;
                    this.i = 3;
                    this.l = 4;
                    this.f = 5.0f;
                    this.d = 6.0;
                }

                public static void main(String[] args)
                {
                    ClassFields cf = new ClassFields();
                    System.out.println(cf.bo);
                    System.out.println(cf.c);
                    System.out.println(cf.by);
                    System.out.println(cf.s);
                    System.out.println(cf.i);
                    System.out.println(cf.l);
                    System.out.println(cf.f);
                    System.out.println(cf.d);
                }
            }
        ''')
        self.run(cls, [], "true\nX\n1\n2\n3\n4\n5.0\n6.0\n")

    def test_args(self):
        cls = self.getclass('''
            class helloworld2 {
                public static void main(String[] args)
                {
                    System.out.println(args[0]);
                    System.out.println(args[1]);
                }
            }
        ''')
        self.run(cls, ["foo", "bar"], "foo\nbar\n")

    def test_arithmetic(self):
        cls = self.getclass('''
            class helloworld3 {
                public static void main(String[] args)
                {
                    int x = Integer.parseInt(args[0]);
                    int y = Integer.parseInt(args[1]);
                    System.out.println(x + y);
                    System.out.println(x - y);
                    System.out.println(x | y);
                    System.out.println(x & y);
                    System.out.println(x ^ y);
                }
            }
        ''')
        self.run(cls, ["10", "3"], "13\n7\n11\n2\n9\n")

    def test_loop(self):
        cls = self.getclass('''
            class helloworld4 {
                public static void main(String[] args)
                {
                    int i, total=0;
                    for (i=0; i<args.length; i++) {
                        total += args[i].length();
                    }
                    System.out.println(total);
                }
            }
        ''')
        self.run(cls, ["foo", "barz"], "7\n")

    def test_simple_instance(self):
        cls = self.getclass('''
            class Demo {
                public int xy;

                public static void main(String[] args)
                {
                    Demo obj = new Demo();
                    obj.xy = args.length;
                    System.out.println(obj.xy);
                }
            }
        ''')
        self.run(cls, ["foo", "bar"], "2\n")

    def test_abstract_class(self):
        cls = self.getclass('''
            public class B extends A
            {
                    public static void main(String[] args)
                    {
                        A a = new B();
                        System.out.println(a.method());
                        System.out.println(a.a_method());
                    }

                    int a_method(){return 42;}
            }

            abstract class A 
            {
                int method(){return 41;}
                abstract int a_method();
            }
        ''',"B")
        self.run(cls, [], "41\n42\n")

    def test_treemap(self):
        cls = self.getclass('''
            import java.util.TreeMap;

            class Demo {
                public static void main(String[] args)
                {
                    TreeMap t = new TreeMap();
                    t.put(args[0], new Integer(1));
                    t.put(args[1], new Integer(2));
                    System.out.println(t.get(args[1]).toString() + t.get(args[0]).toString());
                }
            }
        ''', "Demo")
        self.run(cls, ["foo", "bar"], "21\n")

    def test_constructor(self):
        cls = self.getclass('''
            class Demo {
                public int xy;

                public Demo(int value) {
                    xy = value * 6;
                }

                public static void main(String[] args)
                {
                    Demo obj = new Demo(args.length);
                    System.out.println(obj.xy);
                }
            }
        ''')
        self.run(cls, list("1234567"), "42\n")

    def test_method(self):
        cls = self.getclass('''
            class Demo {
                public int factorial(int n) {
                    if (n <= 1)
                        return 1;
                    else
                        return n * factorial(n - 1);
                }

                public static void main(String[] args)
                {
                    Demo obj = new Demo();
                    int n = Integer.parseInt(args[0]);
                    System.out.println(obj.factorial(n));
                }
            }
        ''')
        self.run(cls, ["11"], "39916800\n")

    def test_interface(self):
        cls = self.getclass('''
            class Demo {
                String myvalue;

                public int cmp(Comparable value1) {
                    return value1.compareTo(myvalue);
                }

                public static void main(String[] args)
                {
                    Demo obj = new Demo();
                    obj.myvalue = args[1];
                    System.out.println(obj.cmp(args[0]));
                }
            }
        ''')
        self.run(cls, ["abc", "abd"], "-1\n")

    def test_references(self):
        cls = self.getclass('''
            class Demo {
                public static void main(String[] args)
                {
                    Demo obj1 = new Demo();
                    Demo obj2 = new Demo();
                    Demo obj3 = null;
                    System.out.println(obj1 == null);
                    System.out.println(obj1 != null);
                    System.out.println(obj1 == obj1);
                    System.out.println(obj1 != obj1);
                    System.out.println(obj1 == obj2);
                    System.out.println(obj1 != obj2);
                    System.out.println(obj1 == obj3);
                    System.out.println(obj1 != obj3);
                    System.out.println(obj3 == null);
                    System.out.println(obj3 != null);
                }
            }
        ''')
        self.run(cls, [], "false\ntrue\n"
                          "true\nfalse\n"
                          "false\ntrue\n"
                          "false\ntrue\n"
                          "true\nfalse\n"
                 )

    def test_constants(self):
        cls = self.getclass('''
            class Demo {
                public static void main(String[] args)
                {
                    System.out.println(5);
                    System.out.println(6);
                    System.out.println(-128);
                    System.out.println(-129);
                    System.out.println(32767);
                    System.out.println(-32768);
                    System.out.println(1000000);
                    System.out.println(-10000000);
                }
            }
        ''')
        self.run(cls, [], "5\n"
                          "6\n"
                          "-128\n"
                          "-129\n"
                          "32767\n"
                          "-32768\n"
                          "1000000\n"
                          "-10000000\n"
                 )

    def test_compares(self):
        cls = self.getclass('''
            class Demo {
                public static void main(String[] args)
                {
                    int i = args[0].length();
                    int j = args[1].length();
                    int k = args[2].length();
                    System.out.println(i == 0);
                    System.out.println(i != 0);
                    System.out.println(i <  0);
                    System.out.println(i >= 0);
                    System.out.println(i >  0);
                    System.out.println(i <= 0);

                    System.out.println(i == j);
                    System.out.println(i != j);
                    System.out.println(i <  j);
                    System.out.println(i >= j);
                    System.out.println(i >  j);
                    System.out.println(i <= j);

                    System.out.println(i == k);
                    System.out.println(i != k);
                    System.out.println(i <  k);
                    System.out.println(i >= k);
                    System.out.println(i >  k);
                    System.out.println(i <= k);
                }
            }
        ''')
        self.run(cls, ["ab", "cde", "fg"], "false\ntrue\n"
                                           "false\ntrue\n"
                                           "true\nfalse\n"

                                           "false\ntrue\n"
                                           "true\nfalse\n"
                                           "false\ntrue\n"

                                           "true\nfalse\n"
                                           "false\ntrue\n"
                                           "false\ntrue\n"
                 )

    def test_interface_2(self):
        cls = self.getclass('''
            class Demo {
                interface FooBar {
                    int getter(int x);
                }
                class C1 implements FooBar {
                    private int f;
                    public C1(int nf) {
                        f = nf;
                    }
                    public int getter(int x) {
                        return x * f;
                    }
                }
                class C2 implements FooBar {
                    public int getter(int x) {
                        return x + 100;
                    }
                }

                public static void show(FooBar fb) {
                    System.out.println(fb.getter(6));
                }

                public static void main(String[] args)
                {
                    Demo me = new Demo();
                    me.run();
                }

                public void run() {
                    C1 c1 = new C1(7);
                    C2 c2 = new C2();
                    show(c1);
                    show(c2);
                }
            }
        ''')
        self.run(cls, [], "42\n106\n")

    def test_inner_class(self):
        cls = self.getclass('''
            class Demo {
                static int i=1;
                int j= 41;
                static class C  {int method(){return i;}}
                       class C2 {int method(){return j;}}
                public static void main(String[] args)
                {
                    C2 c2 = new Demo().method();
                    System.out.println(new C().method()+c2.method());
                }
                C2 method(){return new C2();}
            }
        ''')
        self.run(cls, [], "42\n")

    def test_inner_class2(self):
        cls = self.getclass('''
            class Haus
            {
            String s = "Haus";
            class Zimmer
            {
                String s = "Zimmer";
                class Stuhl
                {
                String s = "Stuhl";
                void ausgabe()
                {
                    System.out.println( s );               // Stuhl
                    System.out.println(   this.s   );          // Stuhl
                    System.out.println(   Stuhl.this.s   );    // Stuhl
                    System.out.println(   Zimmer.this.s   );   // Zimmer
                    System.out.println(   Haus.this.s   );     // Haus
                }
                }
            }
            public static void main( String[] args )
            {
                new Haus().new Zimmer().new Stuhl().ausgabe();
            }
            }
        ''')
        self.run(cls, [], "Stuhl\nStuhl\nStuhl\nZimmer\nHaus\n")

    def test_overloading(self):
        cls = self.getclass('''
            class Demo {
                public int xy;

                public Demo() {
                    this(42);
                }

                public Demo(int value) {
                    xy = value * 6;
                }

                public static void main(String[] args) {
                    Demo obj = new Demo(args.length);
                    System.out.println(obj.xy);
                    obj = new Demo();
                    System.out.println(obj.xy);
                }
            }
        ''')
        self.run(cls, list("1234567"), "42\n252\n")

    def test_array(self):
        cls = self.getclass('''
            class Demo {
                public static void main(String[] args)
                {
                    int[][] aa = new int[12][];
                    aa[5] = new int[3];
                    aa[5][1] = 41;
                    System.out.println(aa[5][1]);

                    Demo[] ad = new Demo[4];
                    ad[3] = new Demo();
                    System.out.println(ad[3] == null);

                    aa = new int[12][4];
                    aa[11][3] = 42;
                    System.out.println(aa[11][3]);

                    boolean[] a4 = new boolean[3];
                    a4[2] = true;
                    System.out.println(a4[2]);

                    char[] a5 = new char[6];
                    a5[2] = 'X';
                    System.out.println(a5[2]);

                    byte[] a8 = new byte[7];
                    a8[0] = -128;
                    System.out.println(a8[0]);

                    short[] a9 = new short[8];
                    a9[7] = 1938;
                    System.out.println(a9[7]);

                    int[] a10 = new int[5];
                    a10[0] = 100;
                    System.out.println(a10[0]);
                }
            }
        ''')
        self.run(cls, [], "41\nfalse\n42\ntrue\nX\n-128\n1938\n100\n")


    def test_unicode_method_names(self):
        cls = self.getclass('''
            class Demo {
                public int xy = 0;

                public Demo() {
                }

                public void österreich() {
                    xy = 3;
                }

                public static void main(String[] args) {
                    Demo obj = new Demo();
                    obj.österreich();
                    System.out.println(obj.xy);
                }
            }
        ''')
        self.run(cls, list("1234567"), "3\n")


    def test_instanceof(self):
        cls = self.getclass('''
            class Demo {
                public int checkit(Object o)
                {
                    return (o instanceof Demo) ? 1 : 0;
                }

                public static void main(String[] args)
                {
                    Demo obj = new Demo();
                    System.out.println(obj.checkit(null));
                    System.out.println(obj.checkit(obj));
                    System.out.println(obj.checkit(new Object()));
                }
            }
        ''')
        self.run(cls, [], "0\n1\n0\n")

    def test_instanceof_array(self):
        cls = self.getclass('''
            class Demo {
                public static void main(String[] args)
                {
                    int[][][] array = new int[2][2][2];
                    System.out.println(array instanceof Object);
                    System.out.println(array instanceof int[][][]);
                    
                    Demo[][][] arrayO = new Demo[2][2][2];
                    arrayO[1][1][1] = new Demo();
                    System.out.println(arrayO[1][1][1].getClass());
                    System.out.println(arrayO[1][1].getClass());
                    System.out.println(arrayO[1].getClass());
                    System.out.println(arrayO.getClass());
                }
            }
        ''')
        self.run(cls, [], "true\ntrue\nclass Demo\nclass [LDemo;\nclass [[LDemo;\nclass [[[LDemo;\n")

    def test_float(self):
        cls = self.getclass('''
           class Floating {

               public final static float c = 0.0f;

               public static float afloat_method(float a, float b)
               {
                    return a % b + c;
               }

               public static void main(String[] args)
               {
                    float x = 1.0f;
                    float y = 2.0f;
                    float[] array = new float[6];
                    array[2] = 41.0f;
                    System.out.println(array[2]);
                    System.out.println(x+y);
                    System.out.println(x-y);
                    System.out.println(x/y);
                    System.out.println(x*y);
                    System.out.println(afloat_method(4.0f, 3.0f));
                    if ( x < y) System.out.println(-x);
                    if ( y > x) System.out.println(-y);
                    if ( y != x) System.out.println(x);
                    if ( y == x) System.out.println(x);
                    float f0 = 0.0f; // test fstore
                    float f1 = 1.0f;
                    float f2 = 2.0f;
                    float f3 = 3.0f;
               }
           }
        ''')
        self.run(cls, [], "41.0\n3.0\n-1.0\n0.5\n2.0\n1.0\n-1.0\n-2.0\n1.0\n")

    def test_double(self):
        cls = self.getclass('''
           class DoubleTest {

               public static double z = 0.0;

               public static double adouble_method(double a, double b)
               {
                    return a % b;
               }

               public static void whileDouble(){
                    double i = 0.0;
                        while(i< 100.1) {
                            i++;
                        }
               }

               public static void main(String[] args)
               {
                    double x = 1.0;
                    double y = 40.0;
                    double d0 = 0.0;
                    double d2 = 2.0;
                    double d3 = 3.0;
                    double d4 = 4.0;
                    double[] array = new double[6];
                    array[4] = 12345.0;
                    System.out.println(array[4]);
                    System.out.println(x+y);
                    System.out.println(x-y);
                    System.out.println(d2/d4);
                    System.out.println(d3*d4);
                    System.out.println(adouble_method(y,d4));
                    if ( x < y) System.out.println(-x);
                    if ( y > x) System.out.println(-y);
                    if ( y != x) System.out.println(x);
                    if ( y == x) System.out.println(x);
                    whileDouble();
               }
           }
           ''')
        self.run(cls, [], "12345.0\n41.0\n-39.0\n0.5\n12.0\n0.0\n-1.0\n-40.0\n1.0\n")

    def test_long(self):
        cls = self.getclass('''
           class LongTest {

               public static long method(long a, long b)
               {
                    return a % b;
               }

               public static void main(String[] args)
               {
                    long x = 1;
                    long y = 40;
                    long l0 = 0;
                    long l1 = 1;
                    long l2 = 2;
                    long l3 = 3;
                    long[] array = new long[12];
                    array[11] = 123456;
                    System.out.println(array[11]);
                    System.out.println(x+y);
                    System.out.println(x-y);
                    System.out.println(l2*l3);
                    System.out.println(y/l2);
                    System.out.println(method(47,23));
                    if ( x < y) System.out.println(-x);
                    if ( y > x) System.out.println(-y);
                    if ( y != x) System.out.println(x);
                    if ( y == x) System.out.println(x);
                    System.out.println(x & y);
                    System.out.println(x | y);
                    System.out.println(x ^ y);
                    System.out.println(x << 2);
                    System.out.println(y >> 2);
                    System.out.println(-16 >> 2);
               }
           }
           ''')
        self.run(cls, [], "123456\n41\n-39\n6\n20\n1\n-1\n-40\n1\n0\n41\n41\n4\n10\n-4\n")

    def test_shift(self):
        cls = self.getclass('''
           class IntTest {
               public static void main(String[] args)
               {
                    int x = 1;
                    int y = 20;
                    System.out.println(x << 2);
                    System.out.println(y >> 2);
                    System.out.println(-1 << 2);
                    System.out.println(-20 >> 2);
                    for (int i = 0; i<30;i++)
                    {
                        x = x*2;
                    }
                    System.out.println( x << 1);
                    // TODO: ushift
                    System.out.println(40 /2);
                    System.out.println(41 % 3);
                    System.out.println(-y);
               }
           }
           ''')
        self.run(cls, [], "4\n5\n-4\n-5\n-2147483648\n20\n2\n-20\n")

    def test_shift2(self):
        cls = self.getclass('''
           class IntTest {
               public static void main(String[] args)
               {
                    int x = -64;
                    System.out.println(x >>> 2);
                    System.out.println(x >> 2);
                    System.out.println(x >>> 3);
                    System.out.println(x >> 3);
               }
           }
           ''')
        self.run(cls, [], "1073741808\n-16\n536870904\n-8\n")

    def test_int_cast(self):
        cls = self.getclass('''
            class IntCast {
                public static void main(String[] bla)
                {
                    int i = 40;
                    long l = i;
                    float f = i;
                    double d = i;
                    System.out.println(i+1);
                    System.out.println(l+1);
                    System.out.println(f+1.0f);
                    System.out.println(d+1.0);
                    char c = (char) i;
                    byte b = (byte) i;
                    short s = (short) i;
                    System.out.println(c);
                    System.out.println(b+1);
                    System.out.println(s+1);
                }
                }
           ''')
        self.run(cls, [], "41\n41\n41.0\n41.0\n(\n41\n41\n")

    def test_long_cast(self):
        cls = self.getclass('''
            class LongCast {
                public static void main(String[] bla)
                {
                    long l = 40;
                    int i = (int) l;
                    float f = l;
                    double d = l;
                    System.out.println(i+1);
                    System.out.println(l+1);
                    System.out.println(f+1.0f);
                    System.out.println(d+1.0);
                }
            }
           ''')
        self.run(cls, [], "41\n41\n41.0\n41.0\n")

    def test_float_cast(self):
        cls = self.getclass('''
            class FloatCast {
                public static void main(String[] bla)
                {
                    float f = 40.0f;
                    int i = (int)  f;
                    long l = (long) f;
                    double d =  f;
                    System.out.println(i+1);
                    System.out.println(l+1);
                    System.out.println(f+1.0f);
                    System.out.println(d+1.0);
                }
            }
           ''')
        self.run(cls, [], "41\n41\n41.0\n41.0\n")

    def test_double_cast(self):
        cls = self.getclass('''
            class DoubleCast {
                public static void main(String[] bla)
                {
                    double d = 40.0;
                    int i = (int)  d;
                    long l = (long) d;
                    float f = (float) d;
                    System.out.println(i+1);
                    System.out.println(l+1);
                    System.out.println(f+1.0f);
                    System.out.println(d+1.0);
                }
            }
           ''')
        self.run(cls, [], "41\n41\n41.0\n41.0\n")

    def test_import(self):
        cls = self.getclass('''
            import java.util.*;
            import java.awt.*;

            class Blubby {
                public static void main(String[] ups)
                {
                    System.out.println("41"); // ;)
                }
            }
           ''', "Blubby")
        self.run(cls, [], "41\n")

    def test_static_var(self):
        cls = self.getclass('''
            class StaticVar {
                public static int x;
                public static boolean b;
                public static void main(String[] bla)
                {
                    x = 41;
                    b = true;
                    System.out.println(x);
                    System.out.println(b);
                }
            }
           ''')
        self.run(cls, [], "41\ntrue\n")

    def test_switch(self):
        cls = self.getclass('''
            class Case {

                static int chooseFar(int i){
                    switch(i){
                        case -100:      return -1;
                        case 0:         return 0;
                        case 100:       return 1;
                        default:        return -1;
                    }
                }

                public static void main (String[] args)
                {
                    int x = 4;
                    switch(x){
                        case 1: {System.out.println(x+1); break;}
                        case 2: {System.out.println(x+2); break;}
                        case 3: {System.out.println(x+3); break;}
                        case 4: {System.out.println(x+4); break;}
                    }
                    switch(x-1){
                        case 1: System.out.println(x-1);
                        case 2: System.out.println(x-2);
                        case 3: System.out.println(x-3);
                        case 4: System.out.println(x-4);
                    }
                    switch(x*41){
                        case 1: System.out.println(x);
                        case 2: System.out.println(x);
                        case 3: System.out.println(x);
                        case 4: System.out.println(x);
                        default: System.out.println(41);
                    }
                    System.out.println(chooseFar(50));
                    System.out.println(chooseFar(100));
                }
            }
        ''')
        self.run(cls, [], "8\n1\n0\n41\n-1\n1\n")

    def test_stack(self):
        cls = self.getclass('''
            class StackTest {
                private static double index = 41;
                private static long index2 = 41;

                public static double nextIndex(){
                    return index++;
                }

                public static long nextIndex2(){
                    return index2++;
                }

                public static void main(String[] bla)
                {
                    System.out.println(nextIndex());
                    System.out.println(nextIndex2());
                    // provoke wide
                    int blub1,blub2,blub3,blub4,blub5,blub6,blub7,blub8,blub9,blub10;
                    int blub11,blub12,blub13,blub14,blub15,blub16,blub17,blub18,blub19,blub20;
                    int blub21,blub22,blub23,blub24,blub25,blub26,blub27,blub28,blub29,blub30;
                    int blub31,blub32,blub33,blub34,blub35,blub36,blub37,blub38,blub39,blub40;
                    int blub41,blub42,blub43,blub44,blub45,blub46,blub47,blub48,blub49,blub50;
                    int blub51,blub52,blub53,blub54,blub55,blub56,blub57,blub58,blub59,blub60;
                    int blub61,blub62,blub63,blub64,blub65,blub66,blub67,blub68,blub69,blub70;
                    int blub71,blub72,blub73,blub74,blub75,blub76,blub77,blub78,blub79,blub80;
                    int bla1,bla2,bla3,bla4,bla5,bla6,bla7,bla8,bla9,bla10;
                    int bla11,bla12,bla13,bla14,bla15,bla16,bla17,bla18,bla19,bla20;
                    int bla21,bla22,bla23,bla24,bla25,bla26,bla27,bla28,bla29,bla30;
                    int bla31,bla32,bla33,bla34,bla35,bla36,bla37,bla38,bla39,bla40;
                    int bla41,bla42,bla43,bla44,bla45,bla46,bla47,bla48,bla49,bla50;
                    int bla51,bla52,bla53,bla54,bla55,bla56,bla57,bla58,bla59,bla60;
                    int bla61,bla62,bla63,bla64,bla65,bla66,bla67,bla68,bla69,bla70;
                    int bla71,bla72,bla73,bla74,bla75,bla76,bla77,bla78,bla79,bla80;
                    int foo1,foo2,foo3,foo4,foo5,foo6,foo7,foo8,foo9,foo10;
                    int foo11,foo12,foo13,foo14,foo15,foo16,foo17,foo18,foo19,foo20;
                    int foo21,foo22,foo23,foo24,foo25,foo26,foo27,foo28,foo29,foo30;
                    int foo31,foo32,foo33,foo34,foo35,foo36,foo37,foo38,foo39,foo40;
                    int foo41,foo42,foo43,foo44,foo45,foo46,foo47,foo48,foo49,foo50;
                    int foo51,foo52,foo53,foo54,foo55,foo56,foo57,foo58,foo59,foo60;
                    int foo61,foo62,foo63,foo64,foo65,foo66,foo67,foo68,foo69,foo70;
                    int foo71,foo72,foo73,foo74,foo75,foo76,foo77,foo78,foo79,foo80;
                    int var1,var2,var3,var4,var5,var6,var7,var8,var9,var10;
                    int var11,var12,var13,var14,var15,var16,var17,var18,var19,var20;
                    int var21,var22,var23,var24,var25,var26,var27,var28,var29,var30;
                    int var31,var32,var33,var34,var35,var36,var37,var38,var39,var40;
                    int var41,var42,var43,var44,var45,var46,var47,var48,var49,var50;
                    int var51,var52,var53,var54,var55,var56,var57,var58,var59,var60;
                    int var61,var62,var63,var64,var65,var66,var67,var68,var69,var70;
                    int var71,var72,var73,var74,var75,var76,var77,var78,var79,var80;
                    var80 = 41;
                    System.out.println(var80);
                }
            }
            ''')
        self.run(cls, [],"41.0\n41\n41\n")

    def test_extends(self):
        cls = self.getclass('''
            class Inher extends Base{
                public static void main(String[] args)
                {
                    Inher I = new Inher();
                    I.x = 41;
                    I.method();
                    System.out.println(I.x);
                    System.out.println(I.y);
                }
            }

            class Base{
                int x;
                int y;

                public void method()
                {
                    System.out.println("N00B");
                    y = 23;
                }
            }
            ''')
        self.run(cls,[],"N00B\n41\n23\n")

    def test_this(self):
        cls = self.getclass('''
            class This implements IFace{

                public int x;
                public This()
                {
                    x = 41;
                    System.out.println(this.x);
                }

                public static void main(String[] args)
                {
                    This T = new This();
                    T.method();
                }

                public void method()
                {
                    System.out.println(this.x);
                }
            }

            interface IFace{
                public void method();
            }
            ''')
        self.run(cls,[],"41\n41\n")

    def test_throw(self):
        cls = self.getclass('''
            class Exc {
                public static void method() throws Exception{
                    throw new Exception("a error");
                }
                public static void main(String[] args){
                    try{
                        method();
                    }
                    catch(Exception e)
                    {
                        System.out.println("help! an error!");
                    }
                    finally
                    {
                        System.out.println("fin.");
                    }
                }
            }
           ''')
        self.run(cls, [], "help! an error!\nfin.\n")

    def test_throw2(self):
        cls = self.getclass('''
            public class Exc2 {
                public static void main(String[] args)
                {
                    try{
                        throw new EvilException();}
                    catch(EvilException e){
                        System.out.println("EvilException");}
                }
            }
            class EvilException extends Exception {}
            ''', "Exc2")
        self.run(cls, [], "EvilException\n")

    def test_throw3(self):
        cls = self.getclass('''
            public class Exc3 {
                public static void method() throws Exception
                {throw new EvilException();}
                public static void main(String[] args)
                {
                    try{
                        method();}
                    catch(EvilException e){
                        System.out.println("EvilException");}
                    catch(Exception e){
                        System.out.println("Exception");}
                }
            }
            class EvilException extends Exception {}
            ''', "Exc3")
        self.run(cls, [], "EvilException\n")

    def test_throw4(self):
        cls = self.getclass('''
            class Exc {
                public static int method() throws Exception{
                    throw new Exception("help! an error!");
                }
                public static void main(String[] args){
                    try{
                        method();
                    }
                    catch(Exception e)
                    {
                        System.out.println(e.getMessage());
                    }
                }
            }
           ''')
        self.run(cls, [], "help! an error!\n")

    def test_throw5(self):
        cls = self.getclass('''
            class Exc {
                public static int method() throws Exception
                {
                    try{
                        throw new Exception();
                    }
                    catch(Exception e)
                    {
                        System.out.println("1");
                    }
                    finally
                    {
                        try{
                            System.out.println("2");
                            throw new Exception();
                        }
                        catch(Exception e)
                        {
                            System.out.println("3");
                        }
                        finally
                        {
                            System.out.println("4");
                            throw new Exception();
                        }
                    }
                }
                public static void main(String[] args){
                    try{
                        method();
                    }
                    catch(Exception e)
                    {
                        System.out.println("5");
                    }
                    finally
                    {
                        System.out.println("6");
                    }
                }
            }
           ''')
        self.run(cls, [], "1\n2\n3\n4\n5\n6\n")

    def test_runntimeException_div(self):
        cls = self.getclass('''
            class Exc {
                public static void main(String[] args){
                    int x=42;
                    int y=0;
                    try{
                        System.out.println(x/y);
                    }
                    catch(java.lang.ArithmeticException e)
                    {
                        System.out.println(e.getMessage());
                    }
                    try{
                        System.out.println(x%y);
                    }
                    catch(java.lang.ArithmeticException e)
                    {
                        System.out.println(e.getMessage());
                    }
                }
            }
           ''')
        self.run(cls, [], "/ by zero\n/ by zero\n")

    def test_runntimeException_arrays(self):
        cls = self.getclass('''
            class Exc {
                public static void main(String[] args){
                    int[] array = new int[2];
                    try{
                        System.out.println(array[42]);
                    }
                    catch(java.lang.ArrayIndexOutOfBoundsException e)
                    {
                        System.out.println(e.getMessage());
                    }
                }
            }
           ''')
        self.run(cls, [], "42\n")

    def test_runntimeException_cls_cast(self):
        cls = self.getclass('''
            class Exc {
                public static void main(String[] args){
                    try{
                        // Object x = new Integer(0)
                        Object x = new Object();
                        System.out.println((String)x);
                    }
                    catch(java.lang.ClassCastException e)
                    {
                        System.out.println(e.getMessage());
                    }
                }
            }
           ''')
        self.run(cls, [], "java.lang.Object cannot be cast to java.lang.String\n")

    def test_obj_cast(self):
        cls = self.getclass('''
            class Cast extends A {
                public static void main(String[] args){
                    Object x = new Cast();
                    System.out.println(((A)x).a);
                }
            }

            class A{
                int a=42;
            }
           ''',"Cast")
        self.run(cls, [], "42\n")

    def test_runntimeException_null(self):
        cls = self.getclass('''
            class Exc {
                int attr = 42;
                public void instanceMethod(){}
                public static void main(String[] args){
                    Exc obj = null;
                    try{
                        System.out.println(obj.attr);
                    }
                    catch(java.lang.NullPointerException e)
                    {
                        System.out.println(e.getMessage());
                    }
                    try{
                        obj.instanceMethod();
                    }
                    catch(java.lang.NullPointerException e)
                    {
                        System.out.println(e.getMessage());
                    }
                    int[] array = null;
                    try{
                        System.out.println(array.length);
                    }
                    catch(java.lang.NullPointerException e)
                    {
                        System.out.println(e.getMessage());
                    }
                    try{
                        System.out.println(array[42]);
                    }
                    catch(java.lang.NullPointerException e)
                    {
                        System.out.println(e.getMessage());
                    }
                    Exception ups = null;
                    try{
                        throw ups;
                    }
                    catch(java.lang.NullPointerException e)
                    {
                        System.out.println(e.getMessage());
                    }
                    catch(java.lang.Exception e)
                    {
                        System.out.println("you never see this text");
                    }
                }
            }
           ''')
        self.run(cls, [], "null\nnull\nnull\nnull\nnull\n")

    # crashs in VMCPStringBuilder while the static class construction
    # 0:   ldc     #10; //class java/lang/String
    # AttributeError: 'CONSTANT_Class_info' object has no attribute 'bytes'
    # FIXME: maybe this comment is not up to date
    def test_stacktrace(self):
        py.test.skip("in-progress test_stacktrace")
        cls = self.getclass('''
            public class Exc4 {
                public static void main(String[] args)
                {
                    try{
                        throw new Exception();
                    }
                    catch(Exception e){
                        e.printStackTrace();
                    }
                }
            }
            ''', "Exc4")
        self.run(cls, [], "", expected_err="java.lang.Exception\n\tat Exc4.main(Exc4.java:6)\n")


    def test_print_double(self):
        cls = self.getclass('''
            class PrintDouble {
                public static void main(String[] blub)
                {
                    double d = 1000.56;
                    System.out.println("Double: "+(d/1000.0));
                }
            }
            ''')
        self.run(cls, [], "Double: 1.00056\n")

    def test_char(self):
        cls = self.getclass('''
            class Character {
                public static void main(String[] blub)
                {
                    char h = 'H';
                    char a = 'a';
                    char l = 'l';
                    char o = 'o';
                    System.out.println(""+h+a+l+l+o);
                }
            }
            ''')
        self.run(cls, [], "Hallo\n")


    def test_char_overflow(self):
        cls = self.getclass('''
            class CharTest {
                public static void main(String[] args)
                {
                    String s = "\017\0275\00744Z\uff90\uff9d\uff93\013";
                    char[] value = s.toCharArray();
                    char c = (char)(value[7]+ 116); //Overflow
                    System.out.println((int)c);
                }
            }
        ''')
        self.run(cls, [], "4\n")


    def test_char_cast(self):
        cls = self.getclass('''
            class CharTest {
                public static void main(String[] args)
                {
                    System.out.println((int)'Z');
                    System.out.println((int)'t');
                    System.out.println((int)'ö');
                    System.out.println((int)'\u1234');
                    System.out.println('Z'+'o');
                    System.out.println('Z'+'t');
                }
            }
        ''')
        self.run(cls,[],"90\n116\n246\n4660\n201\n206\n")

    def test_autoBoxing(self):
        cls = self.getclass('''
            class AutoBox {
                public static void main(String[] args)
                {
                    Integer a = 127;
                    Integer b = 127;
                    System.out.println(a==b);
                    System.out.println(a++);
                    System.out.println(b++);
                    System.out.println(a==b);
                }
            }
        ''')
        self.run(cls, [], "true\n127\n127\nfalse\n")

    def test_wrapper(self):
        cls = self.getclass('''
            class WrappMe {
                public static void main(String[] args)
                {
                    Integer[] a = new Integer[4];
                    a[0] = new Integer(4);
                    System.out.println(a[0]);
                }
            }
        ''')
        self.run(cls, [], "4\n")

    def test_static_vars(self):
        cls = self.getclass('''
            class A extends B{
                public static void main(String[] args) {
                    A a2 = new A();
                    B b2 = new B();
                    a2.i = 23;
                    System.out.println(b2.i);
                    System.out.println(a2.i);
                    A a = new A();
                    B b = new B();
                    b.i = 41;
                    System.out.println(b.i);
                    System.out.println(a.i);
                    C c = new C();
                    System.out.println(c.i);
                    c.i = 55;
                    System.out.println(b.i);
                    System.out.println(a.i);
                    System.out.println(c.i);
                }
            }
            class B extends C{
                static int i = 42;
            }
            class C {
                static int i = 43;
            }
            ''', "A")
        self.run(cls,[],"23\n23\n41\n41\n43\n41\n41\n55\n")

    def test_static_method_lookup(self):
        cls = self.getclass('''
            class A extends B{
                public static void main(String[] args) {
                   System.out.println(method());
                }
            }
            class B{
                public static int method(){return 42;}
            }
            ''', "A")
        self.run(cls,[],"42\n")


    def test_static_init(self):
        cls = self.getclass('''
            public class TestInit
            {
                int j = method();
                
                public static void main(String[] args)
                {
                    System.out.println("1");
                    TestInit t = new TestInit();
                    System.out.println("2");
                }

                int method()
                {
                    System.out.println("3");
                    return 3;
                }
            }
            ''',"TestInit")
        self.run(cls,[],"1\n3\n2\n")
            
    def test_lookup(self):
        cls = self.getclass('''
            class A extends B{
                public static void main(String[] args) {
                    A a2 = new A();
                    B b2 = new B();
                    a2.i = 23;
                    System.out.println(b2.i);
                    System.out.println(a2.i);
                    A a = new A();
                    B b = new B();
                    b.i = 41;
                    System.out.println(b.i);
                    System.out.println(a.i);
                    C c = new C();
                    System.out.println(c.i);
                    c.i = 55;
                    System.out.println(b.i);
                    System.out.println(a.i);
                    System.out.println(c.i);
                }
            }
            class B extends C{
                int i = 42;
            }
            class C {
                int i = 43;
            }
            ''', "A")
        self.run(cls,[],"42\n23\n41\n42\n43\n41\n42\n55\n")

    # Linux: libstrlen.so must be in e.g var/lib
    # Windows: strlen.dll must be "somewhere" :)
    def test_native(self):
        py.test.skip("in-progress: test_native")
        cls = self.getclass('''
            class StrLen 
            { 
            static { 
                System.loadLibrary( "strlen" ); 
            } 
            public static void main(String[] args)
            {
                System.out.println(strlen("Hallo"));
            }
            public static native int strlen( String s ); 
            }
            ''')
        self.run(cls, [], "5\n")

    def test_print_object(self):
        py.test.skip("in-progress: test_print_object")
        cls = self.getclass('''
           class Printobj {
               public static void main(String[] args)
               {
                       Printobj prtobj = new Printobj();
                       System.out.println(prtobj);
               }
           }
        ''')
        # TODO Regexp for memoryaddress e.g Printobj@7d8a992f
        self.run(cls, [], regex="Printobj@[0-9a-f]*s\n")

    def test_parser(self):
        py.test.skip("in-progress test_parser")
        cls = self.getclass('''
           public class ParseMe{public static void main(String[] args){System.out.println("Hallo");}}
        ''')
        self.run(cls, [], "Hallo\n")

    # not realy a test, its a Benchmark
    def test_Richards(self):
        py.test.skip("not realy a test: test_Richards(disabled)")
        self.loader = self.ClassLoader([str(current_dir)])

        #test_name = "COM/sun/labs/kanban/richards_gibbons/Richards"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
        #test_name = "COM/sun/labs/kanban/richards_gibbons_final/Richards"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
        #test_name ="COM/sun/labs/kanban/richards_gibbons_no_switch/Richards"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
        #test_name ="COM/sun/labs/kanban/richards_deutsch_no_acc/Richards"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
        #test_name ="COM/sun/labs/kanban/richards_deutsch_acc_virtual/Richards"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
        #test_name ="COM/sun/labs/kanban/richards_deutsch_acc_final/Richards"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
        #test_name ="COM/sun/labs/kanban/richards_deutsch_acc_interface/Richards"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
        #test_name ="COM/sun/labs/kanban/allRichards"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
        #test_name ="COM/sun/labs/kanban/DeltaBlue/DeltaBlue"
        #cls = self.loader.getclass(test_name)
        #self.run(cls, [], "", None, True)
