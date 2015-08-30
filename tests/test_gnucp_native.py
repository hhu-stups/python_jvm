# -*- coding: utf-8 -*-
# this file contains tests of the native libs of gnu classpath
# <gnu-cp>\native\jni\ ...
from test_interp import RunTests

class TestNative(RunTests):


    # tests/uses native-code:
    # Java_gnu_java_nio_VMChannel_stdin_1fd
    # Java_java_io_VMFile_isDirectory
    # Java_java_io_VMFile_exists
    # Java_gnu_java_nio_VMChannel_stdout_1fd
    # Java_gnu_java_nio_VMChannel_stderr_1fd
    # Java_java_io_VMFile_create
    def test_gnu_native_java_io_VMFile(self):
        cls = self.getclass('''
            import java.io.*;

            public class TestFile
            {
                public static void main( String[] args )
                {
                    try
                    {
                        new File("Test.txt").createNewFile();
                    }
                    catch ( IOException e ) { e.printStackTrace(); }
                }
            }
        ''', "TestFile")
        self.run(cls, [], "")
        import os
        assert os.path.exists("Test.txt")


    # tests/uses native-code:
    #Java_gnu_java_nio_VMChannel_initIDs
    #Java_gnu_java_nio_VMChannel_stdin_1fd
    #Java_gnu_java_nio_VMChannel_stdout_1fd
    #Java_gnu_java_nio_VMChannel_stderr_1fd
    #Java_java_io_VMFile_isDirectory
    #Java_java_io_VMFile_exists
    #Java_java_io_VMFile_canRead
    #Java_java_io_VMFile_canWriteDirectory
    #Java_java_io_VMFile_canExecute
    def test_gnu_native_java_io_VMFile2(self):
        cls = self.getclass('''
            import java.io.*;

            public class TestFile
            {
                public static void main( String[] args )
                {
                     File f = new File("tests");
                     System.out.println(f.isDirectory());
                     System.out.println(f.canRead());
                     System.out.println(f.canWrite());
                     System.out.println(f.canExecute());
                }
            }
        ''', "TestFile")
        self.run(cls, [], "true\ntrue\ntrue\ntrue\n")


    def test_gnu_native_java_io_VMFile3(self):
        cls = self.getclass('''
            import java.io.*;

            public class TestFile
            {
                public static void main( String[] args )
                {
                    try
                    {
                        File f = new File("Test.txt");
                        f.createNewFile();
                        f.setReadable(true); // <- java 6
                        f.setExecutable(true);
                        System.out.println(f.getFreeSpace()>0);
                        System.out.println(f.getUsableSpace()>0);
                        System.out.println(f.length()==0);
                        System.out.println(f.isFile());
                    }
                    catch ( IOException e ) { e.printStackTrace(); }
                }
            }
        ''', "TestFile")
        self.run(cls, [], "true\ntrue\ntrue\ntrue\n")