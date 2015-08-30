# -*- coding: utf-8 -*-
# https://sourceforge.net/projects/javavm/
# http://javavm.svn.sourceforge.net/
import sys, py, os
from interp import ClassLoader, Stack
from classloader import encode_name, descriptor
from helper import  make_String
from objectmodel import Arrayref

# FIXME: Uses the BootstrapClassloader
# TODO: Use the AppClassLoader
current_dir = os.getcwd()
if len(sys.argv)>1:
    classname = sys.argv[1]
    loader = ClassLoader([str(current_dir)])
    jcls = loader.getclass(classname)
    main_name = encode_name(u'main', [u'array:reference:java/lang/String', None])
    str_list = []
    for arg in sys.argv[2:]:
        str_list.append(make_String(arg, self.loader))#XXX
    stack = Stack()
    stack.push(Arrayref(str_list, "", loader.getclass("[Ljava.lang.String;")))
    method = jcls.methods[unicode(main_name)]
    const = jcls.cls.constant_pool
    descr = descriptor(const[method.descriptor_index])
    res = loader.invoke_method(jcls.cls, method, descr, stack)
else:
    print "use python java.py <ClassName,[Args...]>"