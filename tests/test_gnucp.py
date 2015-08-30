# -*- coding: utf-8 -*-
import py
from test_interp import RunTests

class TestGnuClasspath(RunTests):


    def test_classloader_bootstrap(self):
        cls = self.getclass('''
        class TestCLSLaod {

            public static void main(String[] a)
            {
                //  Bootstrap-Classloader
                ClassLoader c = null;
                c = java.lang.Object.class.getClassLoader();
                System.out.println(c);
                c = java.lang.String.class.getClassLoader();
                System.out.println(c);
                c = a.getClass().getClassLoader();
                System.out.println(c);
                c = java.applet.Applet.class.getClassLoader();
                System.out.println(c);
                c = java.awt.Canvas.class.getClassLoader();
                System.out.println(c);
                c = java.beans.Beans.class.getClassLoader();
                System.out.println(c);
                c = java.io.File.class.getClassLoader();
                System.out.println(c);
                c = java.net.Socket.class.getClassLoader();
                System.out.println(c);
                c = java.nio.Buffer.class.getClassLoader();
                System.out.println(c);
                c = java.rmi.Naming.class.getClassLoader();
                System.out.println(c);
                c = java.security.KeyPair.class.getClassLoader();
                System.out.println(c);
                c = java.text.Annotation.class.getClassLoader();
                System.out.println(c);
                c = java.util.List.class.getClassLoader();
                System.out.println(c);
                c = javax.accessibility.AccessibleState.class.getClassLoader();
                System.out.println(c);
                c = javax.sql.ConnectionEvent.class.getClassLoader();
                System.out.println(c);
                c = javax.swing.JFrame.class.getClassLoader();
                System.out.println(c);
                c = javax.xml.XMLConstants.class.getClassLoader();
                System.out.println(c);
                c = org.omg.CORBA.Context.class.getClassLoader();
                System.out.println(c);
                c = org.w3c.dom.DOMException.class.getClassLoader();
                System.out.println(c);
                c = org.xml.sax.HandlerBase.class.getClassLoader();
                System.out.println(c);
                c = org.ietf.jgss.Oid.class.getClassLoader();
                System.out.println(c);
                c = javax.net.SocketFactory.class.getClassLoader();
                System.out.println(c);
                c = java.lang.reflect.Field.class.getClassLoader();
                System.out.println(c);
            }
        }''',"TestCLSLaod")
        self.run(cls, [],"null\n"*23)


    # missing hook
    def test_classloader2(self):
        py.test.skip("in-progress test_classloader2") 
        cls = self.getclass('''
        class TestCLSLaod {

            public static void main(String[] a)
            {
                ClassLoader c = null;
                c = java.math.BigInteger.class.getClassLoader();
                System.out.println(c);
                c = java.sql.Date.class.getClassLoader();
                System.out.println(c);
            }
        }''',"TestCLSLaod")
        self.run(cls, [],"null\n"*2)


    # support clsloaders first
    def test_classloader3(self):
        py.test.skip("in-progress test_classloader3") 
        cls = self.getclass('''
        class TestCLSLaod {

            public static void main(String[] a)
            {
                ClassLoader c = TestCLSLaod.class.getClassLoader();
                ClassLoader c2 = c.getParent();
                System.out.println(c.getSystemClassLoader().getClass().getName());
                System.out.println(c2.getClass().getName());
                System.out.println(c2.getParent()); //Bootstrap-Classloader
            }
        }''')
        self.run(cls, [], "sun.misc.Launcher$AppClassLoader\nsun.misc.Launcher$ExtClassLoader\nnull\n")



    def test_classloader_ext(self):
        py.test.skip("in-progress test_classloader_ext") 
        cls = self.getclass('''
        class ClsLoad2
        {

            public static void main(String[] a)
            {
                System.out.println(System.getProperty("java.ext.dirs"));
            }
        }''')
        self.run(cls, [], "???")



    # tests/uses native-code:
    # Java_gnu_java_nio_VMChannel_initIDs
    # Java_gnu_java_nio_VMChannel_stdin_1fd
    # Java_gnu_java_nio_VMChannel_stdout_1fd
    # Java_gnu_java_nio_VMChannel_stderr_1fd
    # Java_java_io_VMFile_isDirectory
    # Java_java_io_VMFile_exists
    # Java_java_io_VMFile_create
    # Java_java_io_VMFile_canRead
    # Java_java_io_VMFile_canWrite
    # Java_java_io_VMFile_setReadOnly
    # Java_java_io_VMFile_setWritable
    def test_file(self):
        cls = self.getclass('''
            import java.io.File;

            public class TestFile
            {
                static public void prnt(boolean b1, boolean b2)
                {
                    System.out.println("readable="+b1+", writable="+b2);
                }

                static public void main( String[] args ) 
                { 
                    try{
                        File f = File.createTempFile( "bla", "blub" );
                        prnt(f.canRead(), f.canWrite());
                        f.setReadOnly();
                        prnt(f.canRead(), f.canWrite());
                        f.setWritable( true );
                        prnt(f.canRead(), f.canWrite());
                        f.deleteOnExit();
                    }catch(java.io.IOException e)
                    {
                        System.out.println(e.getMessage());
                    }
                }
            }
            ''', "TestFile")
        self.run(cls, [], "readable=true, writable=true\nreadable=true, writable=false\nreadable=true, writable=true\n")


    # tests/uses native-code:
    # Java_gnu_java_nio_VMChannel_initIDs
    # Java_gnu_java_nio_VMChannel_stdin_1fd
    # Java_gnu_java_nio_VMChannel_stdout_1fd
    # Java_gnu_java_nio_VMChannel_stderr_1fd
    # Java_java_io_VMFile_isDirectory
    # Java_java_io_VMFile_exists
    # Java_java_io_VMFile_setLastModified
    def test_file2(self):
        cls = self.getclass('''
            import java.io.*;

            public class Touch
            {
            public static void main( String[] args )
            {
                for ( String s : args )
                {
                File f = new File( s );

                if ( f.exists() )
                {
                    //if ( 
                    f.setLastModified( System.currentTimeMillis() );
                    //)
                    //System.out.println( "Berührte " + s );
                    //else
                    //System.out.println( "Konnte nicht berühren " + s );
                }
                else
                {
                    try
                    {
                    f.createNewFile();
                    //System.out.println( "Legte neue Datei an " + s );
                    } catch ( IOException e ) { e.printStackTrace(); }
                }
                }
            }
            }
        ''', "Touch")
        self.run(cls, ["kaboom.txt"], "")


    def test_security(self):
        cls = self.getclass('''
            public class TestSec
            {
            static public void main( String[] args ) 
            { 
                System.out.println( System.getSecurityManager() ); 
            } 
            }
        ''', "TestSec")
        self.run(cls, [], "null\n")

    #this test also tests the pop2 bytecode
    def test_time(self):
        cls = self.getclass('''
            public class TestTime
            {
                static public void main( String[] args ) 
                {
                    System.currentTimeMillis();
                    new java.util.Date();
                }
            }
        ''', "TestTime")
        self.run(cls, [], "")


    # dont know how to impl. this system ind.
    def test_runtime(self):
        py.test.skip("in-progress: test_runtime: multiprocessing BUg")
        cls = self.getclass('''
            public class TestRunTime
            {
                static public void main( String[] args ) 
                {
                    Runtime runtime = Runtime.getRuntime();
                    System.out.println(runtime.availableProcessors());
                    //System.out.println(runtime.freeMemory());
                    //System.out.println(runtime.totalMemory());
                }
            }
        ''', "TestRunTime")
        import multiprocessing
        num = multiprocessing.cpu_count()
        self.run(cls, [], str(num) +"\n")

    # VMClass.getClassLoader dont returns the right classloader
    # this test fails in the classloader lookup in java.lang.Class
    def test_jframe(self):
        py.test.skip("in-progress: test_jframe")
        cls = self.getclass('''
            import javax.swing.JFrame;
            public class Win extends JFrame {
                public static void main(String[] args)
                {
                }
            }
        ''', "Win")
        self.run(cls, [], "")


    # hook not implemented: VMClassLoader_getSystemClassLoader
    def test_socket(self):
        py.test.skip("in-progress: test_socket")
        cls = self.getclass('''
            import java.net.Socket;
            import java.net.URL;
            import java.net.MalformedURLException;
            public class Online {
                public static void main(String[] args)
                {
                    try{
                        URL url = new URL("http://www.google.de");
                        Socket s = new Socket();
                    }
                    catch (MalformedURLException e)
                    {
                    }
                }
            }
        ''', "Online")
        self.run(cls, [], "")


    # same problem like the jframe test
    def test_window(self):
        py.test.skip("in-progress: test_window")
        cls = self.getclass('''
            import java.awt.*;
            public class Win extends Frame {
                public static void main(String[] args)
                {
                }
            }
        ''', "Win")
        self.run(cls, [], "")


    # adds mysterious zero strings \x00
    # this is the standardvalue added by DEFAULT_BY_TYPECODE
    # e.g to empty char arrays
    def test_collection(self):
        py.test.skip("in-progress: test_collection")
        cls = self.getclass('''
            import java.util.*;

            public class FirstSet{
                public static void main(String[] args){
                    List c = (List) new LinkedList();
                    for(int i=0; i<5; i++)
                        c.add("" + i);
                    System.out.println(Arrays.toString(c.toArray()));
                }
            }
        ''', "FirstSet")
        self.run(cls, [], "[0, 1, 2, 3, 4]\n")


    # adds mysterious zero strings \x00
    # this is the standardvalue added by DEFAULT_BY_TYPECODE
    # e.g to empty char arrays
    def test_CPStringBuilder(self):
        py.test.skip("in-progress: test_CPStringBuilder")
        cls = self.getclass('''
            import java.util.Arrays;

            public class CPSBTest{
                public static void main(String[] args){
                    boolean[] arr =  {true, false};
                    System.out.println(Arrays.toString(arr));
                }
            }
        ''', "CPSBTest")
        self.run(cls, [], "[true, false]\n")

    def test_linkedlist(self):
        cls = self.getclass('''
            import java.util.*;

            public class MyList{
                public static void main(String[] args){
                    LinkedList l = new LinkedList();
                    for(int i=0; i<5; i++)
                        l.add(i);
                    for(int i=0; i<5; i++)
                        System.out.println(l.get(i));
                }
            }
        ''', "MyList")
        self.run(cls, [], "0\n1\n2\n3\n4\n")

    def test_stack(self):
        cls = self.getclass('''
            import java.util.*;

            public class MyStack{
                public static void main(String[] args){
                    Stack s = new Stack();
                    for(int i=0; i<5; i++)
                        s.push(i);
                    for(int i=0; i<5; i++)
                        System.out.println(s.pop());
                }
            }
        ''', "MyStack")
        self.run(cls, [], "4\n3\n2\n1\n0\n")

    #TODO: lose of precicion
    def test_math(self):
        cls = self.getclass('''
            import java.lang.Math;

            public class LittleMath{
                public static void main(String[] args){
                    System.out.println(Math.sin(0));
                    System.out.println(Math.cos(0));
                    System.out.println(Math.tan(0));
                    System.out.println(Math.asin(0));
                    System.out.println(Math.acos(1));
                    System.out.println(Math.atan(0));
                    System.out.println(Math.atan2(0,1));
                    System.out.println(Math.exp(0));
                    System.out.println(Math.log(1));
                    System.out.println(Math.pow(2,3));
                    System.out.println(Math.sqrt(144));
                    System.out.println(Math.floor(0.9999999));
                    System.out.println(Math.ceil(0.9999999));
                    System.out.println(Math.sinh(0));
                    System.out.println(Math.cosh(0));
                    System.out.println(Math.tanh(0));
                    System.out.println(Math.hypot(4,3));
                    System.out.println(Math.log10(100));
                    System.out.println(Math.floor(Math.log1p(3)));
                    System.out.println(Math.floor(Math.expm1(1)));
                    System.out.println(Math.IEEEremainder(4,3));
                    System.out.println(Math.cbrt(8));
                    System.out.println(Math.rint(1));
                    System.out.println(Math.rint(1.00000001));
                    System.out.println(Math.rint(0.99999999));
                }
            }
        ''', "LittleMath")
        self.run(cls, [], "0.0\n1.0\n0.0\n0.0\n0.0\n0.0\n0.0\n1.0\n0.0\n8.0\n12.0\n0.0\n1.0\n0.0\n1.0\n0.0\n5.0\n2.0\n1.0\n1.0\n1.0\n2.0\n1.0\n1.0\n1.0\n")

    def test_string(self):
        cls = self.getclass('''
            class StringTest {
                public static void main(String[] args)
                {
                    String s = "Hallo Welt";
                    String s2 = "Hallo Weld";
                    System.out.println(s);
                    System.out.println(s.length());
                    System.out.println(s.charAt(0));
                    System.out.println(s.charAt(8));
                    System.out.println(s.equals(s2));
                }
            }
        ''')
        self.run(cls,[],"Hallo Welt\n10\nH\nl\nfalse\n")


    def test_string2(self):
        cls = self.getclass('''
            class StringTest {
                public static void main(String[] args)
                {
                    String s = "Hallo Welt";
                    System.out.println(s.toLowerCase());
                }
            }
        ''')
        self.run(cls,[],"hallo welt\n")

    def test_class(self):
        cls = self.getclass('''
            class ClassTest {
                ClassTest()
                {
                    System.out.println(this.getClass());
                    System.out.println(this.getClass().getName());
                    System.out.println(this.getClass().isInterface());
                    Class dClass = double.class;
                    System.out.println(this.getClass().isPrimitive());
                    System.out.println(dClass.isPrimitive());
                }

                public static void main(String[] args)
                {
                    new ClassTest();
                }
            }
        ''')
        self.run(cls,[],"class ClassTest\nClassTest\nfalse\nfalse\ntrue\n")

    def test_clone(self):
        cls = self.getclass('''
            class Klon implements Cloneable{
                int x;
                public static void main(String[] args) throws java.lang.CloneNotSupportedException
                {
                    Klon klon1 = new Klon();
                    Klon klon2 = klon1;
                    Klon klon3 = (Klon) klon1.clone();
                    klon1.x = 1;
                    klon2.x = 2;
                    klon3.x = 3;
                    System.out.println(klon1.x);
                    System.out.println(klon2.x);
                    System.out.println(klon3.x);
                }
            }
        ''')
        self.run(cls,[],"2\n2\n3\n")

    def test_gen(self):
        cls = self.getclass('''
            class Box<T>
            {
            private T val;
            private Box<T>[] buckets;

            void setValue( T val )
            {
                this.val = val;
            }

            T getValue()
            {
                return val;
            }

            void make()
            {
                buckets = (Box<T>[]) new Box[10];
            }

            public static void main(String[] args)
            {
                Box<String> box = new Box<String>();
                box.setValue("Hallo");
                System.out.println(box.getValue());
                box.make();
                Box<Integer> box2 = new Box<Integer>();
                box2.setValue(41);
                System.out.println(box2.getValue());
            }
        }''',"Box")
        self.run(cls,[],"Hallo\n41\n")

    # works but cant capture print
    def test_properties(self):
        py.test.skip("in-progress: test_properties")
        cls = self.getclass('''
            import java.util.Properties;

            class Pro
            {
            private static final Properties defaultProperties = new Properties();
            static{
                    String userAgent = ("gnu-classpath/"
                    + defaultProperties.getProperty("gnu.classpath.version")
                    + " ("
                    + defaultProperties.getProperty( "gnu.classpath.vm.shortname")
                    + "/"
                    + defaultProperties.getProperty("java.vm.version")
                    + ")");
                    System.out.println(userAgent==null);
                }
                public static void main(String[] args)
                {}
            }
        ''', "Pro")
        self.run(cls, [], "false\n")