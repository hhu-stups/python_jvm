# -*- coding: utf-8 -*-
import struct, re, StringIO

DEBUG = False

class SimpleField(object):
    def __new__(cls, f):
        fmt = "!" + cls.structfmt
        res, = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
        return res

class u1(SimpleField):    structfmt = 'B'
class u2(SimpleField):    structfmt = 'H'
class u4(SimpleField):    structfmt = 'I'

# Baseclass of every other classfile item
class JVMData(object):
    r_fieldformat = re.compile(r"(\w+)\s+(\w+)([[].+[]])?;")

    def __init__(self, f):
        if DEBUG:
            print self.__class__.__name__, '{'
        lines = self._fields_.splitlines()
        for line in lines:
            line = line.strip()
            if line:
                match = JVMData.r_fieldformat.match(line)
                typename  = match.group(1)
                fieldname = match.group(2)
                length    = match.group(3)
                typecls = globals()[typename] # XXX not Rpython
                if DEBUG:
                    print line,
                if not length:
                    value = typecls(f)
                else:
                    length = eval(length[1:-1], self.__dict__)
                    if typecls is u1:
                        value = f.read(length)
                        assert len(value) == length
                    else:
                        value = []
                        while len(value) < length:
                            x = typecls(f)
                            value.append(x)
                            if getattr(x, '_two_entries_', False): # XXX not Rpython
                                value.append(None)
                if DEBUG:
                    print repr(value)
                self.__dict__[fieldname] = value
        if DEBUG:
            print '}'


class ClassFile(JVMData):
    _fields_ = """
         u4 magic;
         u2 minor_version;
         u2 major_version;
         u2 constant_pool_count;
         cp_info constant_pool[constant_pool_count-1];
         u2 access_flags;
         u2 this_class;
         u2 super_class;
         u2 interfaces_count;
         u2 interfaces[interfaces_count];
         u2 fields_count;
         field_info fields[fields_count];
         u2 methods_count;
         method_info methods[methods_count];
         u2 attributes_count;
         attribute_info attributes[attributes_count];
    """
    def __init__(self, f):
        JVMData.__init__(self, f)
        assert self.magic == 0xCAFEBABE
        self.constant_pool.insert(0, None)

    def getattr(self, info, name, cls=None):
        for attr in info.attributes:
            if self.constant_pool[attr.attribute_name_index] == name:
                result = attr.info
                if cls is not None:
                    result = cls(StringIO.StringIO(result))
                return result
        raise ValueError(name)


class field_info(JVMData):
    _fields_ = """
        u2 access_flags;
        u2 name_index;
        u2 descriptor_index;
        u2 attributes_count;
        attribute_info attributes[attributes_count];
    """
    ACC_STATIC   = 0x0008

class method_info(JVMData):
    _fields_ = """
        u2 access_flags;
        u2 name_index;
        u2 descriptor_index;
        u2 attributes_count;
        attribute_info attributes[attributes_count];
    """
    ACC_STATIC   = 0x0008
    ACC_NATIVE   = 0x0100
    ACC_ABSTRACT = 0x0400
    ACC_SYNCHRONIZED = 0x0020

class attribute_info(JVMData):
    _fields_ = """
        u2 attribute_name_index;
        u4 attribute_length;
        u1 info[attribute_length];
    """

def CONSTANT_Utf8_info(f):
    length, = struct.unpack("!H", f.read(2))
    data = f.read(length)
    # be careful: NULL ==c080 could be used by hackers
    # but must be allowed to parse classfiles
    return data.replace("\xc0\x80","\x00").decode('utf8')

class CONSTANT_Class_info(JVMData):
    _fields_ = """
        u2 name_index;
    """

class CONSTANT_String_info(JVMData):
    _fields_ = """
        u2 string_index;
    """

class CONSTANT_Fieldref_info(JVMData):
    _fields_ = """
        u2 class_index;
        u2 name_and_type_index;
    """

class CONSTANT_Methodref_info(JVMData):
    _fields_ = """
        u2 class_index;
        u2 name_and_type_index;
    """

class CONSTANT_InterfaceMethodref_info(JVMData):
    _fields_ = """
        u2 class_index;
        u2 name_and_type_index;
    """

class CONSTANT_NameAndType_info(JVMData):
    _fields_ = """
        u2 name_index;
        u2 descriptor_index;
    """

class CONSTANT_Integer_info(JVMData):
    _fields_ = """
        u4 bytes;
    """

class CONSTANT_Long_Info(JVMData):
    _two_entries_ = True
    _fields_ = """
        u4 high_bytes;
        u4 low_bytes;
    """

class CONSTANT_Double(JVMData):
    _two_entries_ = True
    _fields_ = """
        u4 high_bytes;
        u4 low_bytes;
    """

class CONSTANT_Float(JVMData):
    _fields_ = """
        u4 bytes;
    """

CONSTANT_TYPE = {1:  CONSTANT_Utf8_info,
                 3:  CONSTANT_Integer_info,
                 4:  CONSTANT_Float,
                 5:  CONSTANT_Long_Info,
                 6:  CONSTANT_Double,
                 7:  CONSTANT_Class_info,
                 8:  CONSTANT_String_info,
                 9:  CONSTANT_Fieldref_info,
                 10: CONSTANT_Methodref_info,
                 11: CONSTANT_InterfaceMethodref_info,
                 12: CONSTANT_NameAndType_info,
                 }

def cp_info(f):
    tag = ord(f.read(1))
    return CONSTANT_TYPE[tag](f)


class Code_attribute(JVMData):
    _fields_ = """
        u2 max_stack;
        u2 max_locals;
        u4 code_length;
        u1 code[code_length];
        u2 exception_table_length;
        exception_entry exception_table[exception_table_length];
        u2 attributes_count;
        attribute_info attributes[attributes_count];
    """

class exception_entry(JVMData):
    _fields_ = """
        u2 start_pc;
        u2 end_pc;
        u2 handler_pc;
        u2 catch_type;
    """

class Exceptions_attribute(JVMData):
    _fields_ = """
        u2 number_of_exceptions;
        u2 exceptions_index_table[number_of_exceptions];
    """

class InnerClasses_attribute(JVMData):
    _fields_ = """
        u2 number_of_classes;
        innerClasses_entry classes[number_of_classes];
    """

class innerClasses_entry(JVMData):
    _fields_ = """
        u2 inner_class_info_index;
        u2 outer_class_info_index;
        u2 inner_name_index;
        u2 inner_class_access_flags;
    """

def test_helloworld():
    cls = ClassFile(open('helloworld.class', 'rb'))
    main_code = cls.getattr(cls.methods[1], 'Code', Code_attribute)
