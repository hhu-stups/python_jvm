# -*- coding: utf-8 -*-
import py
from test_interp import RunTests

class TestThread(RunTests):

    def test_currentThread(self):
        cls = self.getclass('''
            public class AClass
            {
                public static void main(String args[])
                {
                    Thread thisThread = Thread.currentThread();
                    String name = thisThread.toString();
                    // Thread[name, pri, groupname]
                    System.out.println(name);
                }
            }
            ''',"AClass")
        self.run(cls, [],"Thread[main,5,main]\n")


    def test_lock_loop(self):
        #Hook wrong implemented?: objectFieldOffset method of sun/misc/Unsafe
        # deadlocks always for reasons unknown
        py.test.skip("in-progress test_lock_loops")
        cls = self.getclass('''
            import java.awt.Point;
            import java.util.concurrent.locks.ReentrantLock;
            import java.util.concurrent.locks.Lock;

            public class TLock
            {
                public static void main(String[] args)
                {
                    final Lock lock = new ReentrantLock();
                    final Point p = new Point();

                    Runnable r = new Runnable()
                    {
                    @Override public void run()
                    {
                        int x = (int)(Math.random() * 1000), y = x;
                        for(int i=0; i<1000;i++)
                        {
                            lock.lock();
                            p.x = x; p.y = y;
                            int xc = p.x, yc = p.y;
                            lock.unlock();
                            if ( xc != yc )
                                System.out.println( "Aha: x=" + xc + ", y=" + yc );
                        }
                    }
                    };
                    new Thread( r ).start();
                    new Thread( r ).start();
                }
            }
            ''',"TLock")
        self.run(cls, [], "")

    def test_sleep(self):
        cls = self.getclass('''
            public class ZZZ
            {
                public static void main(String[] args)
                {
                    try{
                    Thread.sleep(10);
                    }
                    catch(java.lang.InterruptedException e)
                    {
                        System.out.println("fail");
                    }
                    System.out.println("pass");
                }
            }
            ''', "ZZZ")
        self.run(cls,[],"pass\n")

    def test_thread_state(self):
        cls = self.getclass('''
            public class TState
            {
                public static void main(String[] args)
                {
                    java.lang.Thread.State state = Thread.currentThread().getState();
                    System.out.println(state);
                }
            }
            ''', "TState")
        self.run(cls,[],"RUNNABLE\n")

    def test_thread_state2(self):
        cls = self.getclass('''
            public class TState extends Thread
            {
                public static void main(String[] args)
                {
                    TState t = new TState();
                    java.lang.Thread.State state = t.getState();
                    System.out.println(state);
                    t.start();
                }

                public void run()
                {
                    java.lang.Thread.State state = Thread.currentThread().getState();
                    System.out.println(state);
                }
            }
            ''', "TState")
        self.run(cls,[],"NEW\nRUNNABLE\n")


    def test_currentThread2(self):
        # gnucp Bug. The threadnames are staring by one insted of zero
        py.test.skip("in-progress test_currentThread2") 
        cls = self.getclass('''
            public class MyThread extends Thread
            {
                public static void main(String args[])
                {
                    System.out.println(Thread.currentThread().toString());
                    new MyThread().start();
                    for(int i=0; i<100000; i++);
                }

                public void run()
                {
                    System.out.println(Thread.currentThread().toString());
                }
            }
            ''',"MyThread")
        self.run(cls, [],"Thread[main,5,main]\nThread[Thread-0,5,main]\n")

    def test_mainThread_singleton(self):
        cls = self.getclass('''
            public class AClass
            {
                public static void main(String args[])
                {
                    Thread t1 = Thread.currentThread();
                    Thread t2 = Thread.currentThread();
                    System.out.println(t1==t2);
                }

            }
            ''',"AClass")
        self.run(cls, [],"true\n")

    # FIXME:(2) deadlocks sometimes for reasons unknown
    def test_dummy(self):
        cls = self.getclass('''
            public class MyThread extends Thread
            {
                public static void main(String args[])
                {
                    MyThread blub = new MyThread();
                }

                public void run()
                {
                }
            }
            ''',"MyThread")
        self.run(cls, [],"")

    # (3) daedlocks sometimes for reasons unknown
    def test_two_threads_no_join(self):
        cls = self.getclass('''
            public class MyThread extends Thread
            {
                static int i;
                static Object o = new Object();
                public static void main(String args[])
                {
                    MyThread t1 = new MyThread();
                    MyThread t2 = new MyThread();
                    t1.start();
                    t2.start();
                    while(i<42);
                }

                public void run()
                {
                    synchronized(o){
                    i+=21;}
                    System.out.println("Bunga");
                }
            }
            ''',"MyThread")
        self.run(cls, [],"Bunga\nBunga\n")

    # (4) daedlocks sometimes for reasons unknown
    def test_two_threads_no_join_sync_method(self):
        cls = self.getclass('''
            public class MyThread extends Thread
            {
                static int i;
                static Object o = new Object();
                public static void main(String args[])
                {
                    MyThread t1 = new MyThread();
                    MyThread t2 = new MyThread();
                    t1.start();
                    t2.start();
                    while(i<42);
                }

                public void run()
                {
                    set();
                    System.out.println("Bunga");
                }

                public synchronized void set()
                {
                    i+=21;
                }
            }
            ''',"MyThread")
        self.run(cls, [],"Bunga\nBunga\n")

    # (5) daedlocks sometimes for reasons unknown
    def test_two_threads_and_join(self):
        cls = self.getclass('''
            public class MyThread extends Thread
            {
                public static void main(String args[])
                {
                    MyThread t1 = new MyThread();
                    MyThread t2 = new MyThread();
                    t1.start();
                    t2.start();
                    try{
                        t1.join();
                        t2.join();
                    }catch(java.lang.InterruptedException e){}
                }

                public void run()
                {
                    System.out.println("Bunga");
                }
            }
            ''',"MyThread")
        self.run(cls, [],"Bunga\nBunga\n")

    def test_two_threads_yield(self):
        cls = self.getclass('''
            public class MyThread extends Thread
            {
                public static void main(String args[])
                {
                    MyThread t1 = new MyThread();
                    MyThread t2 = new MyThread();
                    t1.start();
                    t2.start();
                    try{
                        t1.join();
                        t2.join();
                    }catch(java.lang.InterruptedException e){}
                }

                public void run()
                {
                    Thread.yield();
                    System.out.println("Bunga");
                }
            }
            ''',"MyThread")
        self.run(cls, [],"Bunga\nBunga\n")


    def test_threads_isInterrupted(self):
        cls = self.getclass('''
            class ThreadusInterruptus extends Thread
            {

            public void run()
            {
                System.out.println( "1" );
                while (! isInterrupted())
                {
                    try
                    {
                        Thread.sleep( 500 );
                    }
                    catch ( InterruptedException e )
                    {
                        interrupt();
                        System.out.println( "2" );
                    }
                }
                System.out.println( "3" );
            }

            public static void main( String[] args ) throws InterruptedException
            {
                ThreadusInterruptus t = new ThreadusInterruptus();
                t.start();
                Thread.sleep( 2000 );
                t.interrupt()  ;
            }
            }

            ''',"ThreadusInterruptus")
        self.run(cls, [],"1\n2\n3\n")