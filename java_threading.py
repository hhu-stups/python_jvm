# -*- coding: utf-8 -*-
from objectmodel import Stack, Objectref
from helper import make_String, find_method
#import interp
import threading

thread_lst = []

# is set after every task-change by the thread himself
# This is main_no_init if the main thread was not created
# by Thread.currentThread() called inside main
# I choose this impl. (insted of calling give_main_thread() on
# every startup for) performance reasons
currentVMThread = "main_no_init" # instance of vmdata_VMThread

# holds the main-Thread,
# ensures that the main-Thread is a singleton
main_thread_cache = None


def monitorenter(loader, monitor):
    global currentVMThread
    #print "monitorenter:",monitor.jcls.__name__
    #print monitor.owner_thread
    #if monitor.jcls.__name__ == "java/lang/VMThread":
    #    print currentVMThread," try to get:", monitor.fields.get('vmdata', "ref")
    while not (monitor.owner_thread == None or monitor.owner_thread == currentVMThread):
        if not currentVMThread == "main_no_init":
            currentVMThread.STATE =make_String("BLOCKED", loader)
        temp = currentVMThread
        interp.interp_lock.release()
        # if there is an other thread it will get the
        # exc. control here!
        interp.interp_lock.acquire()
        currentVMThread = temp
        if not currentVMThread == "main_no_init":
            currentVMThread.STATE =make_String("RUNNABLE", loader)
        #print monitor.owner_thread
    #if monitor.jcls.__name__ == "java/lang/VMThread":
    #    print currentVMThread," got:", monitor.fields.get('vmdata', "ref")
    assert not currentVMThread==None
    if monitor.owner_thread == currentVMThread:
        monitor.lock_count = monitor.lock_count +1
    else: # first lock
        #print "owner_name:",currentVMThread
        #print "on:",monitor.jcls.__name__
        assert monitor.owner_thread==None
        monitor.owner_thread = currentVMThread
        assert monitor.lock_count==0
        monitor.lock_count = 1


def monitorexit(monitor):
    global currentVMThread
    # TODO: Throw Exception here
    # FIXME: this assert randomly throws python-level exceptions
    #print "monitorexit:", monitor.jcls.__name__
    #print "currentVMThread:", currentVMThread
    #print "not none?:", monitor, ":",monitor.owner_thread 
    assert monitor.owner_thread == currentVMThread
    monitor.lock_count = monitor.lock_count -1
    if monitor.lock_count==0:
        monitor.owner_thread = None # end of locking
        #print "put none:", monitor



# TODO: think of deamon threads
def wait_for_all_threads():
    for thread in thread_lst:
        thread.join()

def give_main_thread(loader):
    global main_thread_cache
    if main_thread_cache==None:
        thread_ref = make_main_thread(loader)
        main_thread_cache = thread_ref
    else:
        thread_ref = main_thread_cache
    return thread_ref

def make_main_thread(loader):
    # Goal: build the main-Thread Object
    # (1) Make a Thread object and find the 4 args for the thread Constructor
    jcls = loader.getclass("java/lang/Thread") #XXX empty
    thread_ref = Objectref(jcls, True)
    # (1.1) create a VMThread Object
    jcls2 = loader.getclass("java/lang/VMThread")
    vmthread_ref = Objectref(jcls2, True)
    # special case: the main Thread has no run method
    vmdata = vmdata_VMThread(loader, vmthread_ref, None, None, None)
    vmthread_ref.fields.set("vmdata", vmdata, "ref")
    # (1.2) The Threadname
    name_str = make_String("main", loader) 
    # (2) Call the Constructor Thread(VMThread, String, int, boolean)
    # search method_info for constructor
    method = find_method(jcls, "<init>", "(Ljava/lang/VMThread;Ljava/lang/String;IZ)V")
    descr = [u'reference:java/lang/VMThread',u'reference:java/lang/String', "int", "boolean", None]
    args = Stack()
    args.push(False)            # boolean daemon
    args.push(5)                # int priority
    args.push(name_str)         # String name
    args.push(vmthread_ref)     # VMThread vmThread
    args.push(thread_ref)       # this
    loader.invoke_method(jcls.cls, method, descr, args)
    # (3) TODO: SysClassloader and synchronized

    # (4) TODO: Add to Threadgroup (there should only be one)
    jcls3 = loader.getclass("java/lang/ThreadGroup")
    tg_ref = Objectref(jcls3, True)
    # search constructor
    method = find_method(jcls3, "<init>", "()V")
    descr = [None]
    args = Stack()
    args.push(tg_ref) # this
    # XXX Hack: call a private Constructor
    loader.invoke_method(jcls3.cls, method, descr, args)
    thread_ref.fields.set(u'group', tg_ref, "ref")
    # (5) TODO: Do InheritableThreadLocal stuff
    # (6) done
    return thread_ref



# it is no java.lang.VMThread
class vmdata_VMThread(threading.Thread):
    def __init__(self, loader, vmthread_objref, method_info, descr, args):
        threading.Thread.__init__(self)
        self.loader = loader
        self.vmthread_objref = vmthread_objref
        self.method_info = method_info
        self.descr = descr
        self.args = args
        if not method_info == None: #main thread
            thread_lst.append(self)
        self.STATE = make_String("RUNNABLE", self.loader)
        self.isInterrupted = False

    def run(self):
        global currentVMThread
        #print "starting Thread:",self
        interp.interp_lock.acquire()
        #print "getting lock: (Thread):",self
        currentVMThread = self
        self.loader.invoke_method(self.vmthread_objref.jcls.cls, self.method_info, self.descr, self.args)
        #print "calc done:",self
        self.STATE = make_String("TERMINATED", self.loader)
        #print "terminating Thread:",self
        interp.interp_lock.release()
