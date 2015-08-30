# -*- coding: utf-8 -*-
import py
from test_interp import RunTests

class TestReflection(RunTests):


    def test_forName_package(self):
        cls = self.getclass('''
            package x;
            public class Rfl2 {
                public static void main(String[] args)
                {
                    Class c = null;
                    try
                    {
                        c = Class.forName("x.Rfl2");
                    }
                    catch(Exception e)
                    {
                        //dum di dum..
                    }
                    System.out.println(c);
                }
            }
            ''',"x/Rfl2")
        self.run(cls, [],"class x.Rfl2\n")


    def test_isAssignableFrom_exception(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    Rfl r = new Rfl();
                    Class c = r.getClass();
                    try {
                        c.isAssignableFrom(null);
                    }
                    catch(java.lang.NullPointerException e)
                    {
                        System.out.println(e.getMessage());
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"null\n")

    def test_getClass(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    Rfl r = new Rfl();
                    Class c = r.getClass();
                    System.out.println(c);
                    System.out.println(Rfl.class);
                }
            }
            ''',"Rfl")
        self.run(cls, [],"class Rfl\nclass Rfl\n")

    def test_TYPE(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    Class c = Integer.TYPE;
                    System.out.println(c);
                    System.out.println(c.getName());
                }
            }
            ''',"Rfl")
        self.run(cls, [],"int\nint\n")

    def test_isPrimitive(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    Class c = null;
                    try
                    {
                        c = Class.forName("Rfl");
                    }
                    catch(Exception e)
                    {
                        //dum di dum..
                    }
                    System.out.println(c);
                    System.out.println(c.isPrimitive());
                    System.out.println(boolean.class.isPrimitive());
                    System.out.println(byte.class.isPrimitive());
                    System.out.println(short.class.isPrimitive());
                    System.out.println(int.class.isPrimitive());
                    System.out.println(char.class.isPrimitive());
                    System.out.println(long.class.isPrimitive());
                    System.out.println(float.class.isPrimitive());
                    System.out.println(double.class.isPrimitive());
                    System.out.println(void.class.isPrimitive());
                    Integer i = new Integer(42);
                    System.out.println(int.class.isPrimitive());
                }
            }
            ''',"Rfl")
        self.run(cls, [],"class Rfl\nfalse\ntrue\ntrue\ntrue\ntrue\ntrue\ntrue\ntrue\ntrue\ntrue\ntrue\n")

    def test_isInterface(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    Class c = null;
                    try
                    {
                        c = Class.forName("Rfl");
                    }
                    catch(Exception e)
                    {
                        //dum di dum..
                    }
                    Class c2 = IFace.class;
                    System.out.println(c.isInterface());
                    System.out.println(c2.isInterface());
                }
            }

            interface IFace {}
            ''',"Rfl")
        self.run(cls, [],"false\ntrue\n")

    def test_instanceOf(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    Rfl object = new Rfl();
                    Object object2 = new Object();
                    System.out.println(object instanceof Rfl);
                    System.out.println(object instanceof Object);
                    System.out.println(Rfl.class.isInstance(object));
                    System.out.println(Object.class.isInstance(object));
                    System.out.println(object2 instanceof Rfl);
                    System.out.println(object2 instanceof Object);
                    System.out.println(Rfl.class.isInstance(object2));
                    System.out.println(Object.class.isInstance(object2));
                    System.out.println(Rfl.class.isAssignableFrom(Rfl.class));
                    System.out.println(Object.class.isAssignableFrom(Rfl.class));
                    System.out.println(Rfl.class.isAssignableFrom(Object.class));
                }
            }
            ''',"Rfl")
        self.run(cls, [],"true\ntrue\ntrue\ntrue\nfalse\ntrue\nfalse\ntrue\ntrue\ntrue\nfalse\n")

    def test_getSuperClass(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    Class c =  Rfl.class;
                    Class c2 = c.getSuperclass();
                    Class c3 = Object.class.getSuperclass();
                    Class c4 = IFace.class;
                    System.out.println(c.getName());
                    System.out.println(c2.getName());
                    System.out.println(c3);
                    System.out.println(boolean.class.getSuperclass());
                    System.out.println(c4.getSuperclass());
                }
            }

            interface IFace {}
            ''',"Rfl")
        self.run(cls, [],"Rfl\njava.lang.Object\nnull\nnull\nnull\n")

    def test_getInterfaces(self):
        cls = self.getclass('''
            public class Rfl implements IFace, IFace2{
                public static void main(String[] args)
                {
                    Class c = Rfl.class;
                    Class[] in = c.getInterfaces();
                    for(int i=0; i<in.length; i++)
                        System.out.println(in[i].getName());
                    Class c2 = Object.class;
                    Class[] in2 = c2.getInterfaces();
                    System.out.println(in2.length==0);
                    Class[] in3 = IFace.class.getInterfaces();
                    for(int i=0; i<in3.length; i++)
                        System.out.println(in3[i].getName());
                    Class[] in4 = boolean.class.getInterfaces();
                    System.out.println(in4.length==0);
                }
            }

            interface IFace extends IFace2, IFace3{}
            interface IFace2 {}
            interface IFace3 {}
            ''',"Rfl")
        self.run(cls, [],"IFace\nIFace2\ntrue\nIFace2\nIFace3\ntrue\n")

    def test_getDeclaredClasses(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    Class c = Rfl.class;
                    Class[] inner = c.getDeclaredClasses();
                    for(int i=0; i< inner.length; i++)
                        System.out.println(inner[i].getName());
                }

                interface IFace extends IFace2, IFace3{}
                interface IFace2 {}
                interface IFace3 {}
                class A extends B{}
                class B {}
            }


            ''',"Rfl")
        self.run(cls, [],"Rfl$B\nRfl$A\nRfl$IFace3\nRfl$IFace2\nRfl$IFace\n")

    def test_getDeclaredFields_setX(self):
        cls = self.getclass('''
            import java.lang.reflect.Field;

            public class Rfl {
                int a,b,c;
                byte d,e,f;
                short g,h,i;
                long j,k,l;
                float m,n,o;
                double p,q,r;
                boolean s,t,u;
                char v,w,x;
                Rfl object;
                public static void main(String[] args)
                {
                    Field[] farray = Rfl.class.getDeclaredFields();
                    for(int i=0; i< farray.length; i++)
                        System.out.println(farray[i].getName());
                    Rfl object = new Rfl();
                    object.a=1;
                    
                    System.out.println(object.a);
                    try{
                        farray[0].setInt(object, 2);}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.a);
                    
                    System.out.println(object.d);
                    try{
                        farray[3].setByte(object, (byte)2);}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.d);
                    
                    System.out.println(object.g);
                    try{
                        farray[6].setShort(object, (short)2);}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.g);
                    
                    System.out.println(object.j);
                    try{
                        farray[9].setLong(object, (long)2);}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.j);
                    
                    System.out.println(object.m);
                    try{
                        farray[12].setFloat(object, (float)2);}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.m);
                    
                    System.out.println(object.p);
                    try{
                        farray[15].setDouble(object, 2.1);}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.p);
                    
                    System.out.println(object.s);
                    try{
                        farray[18].setBoolean(object, true);}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.s);
                    
                    System.out.println(object.v);
                    try{
                        farray[21].setChar(object, 'x');}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.v);
                    
                    object.object = new Rfl();
                    Rfl object2 = new Rfl();
                    object2.a=2;
                    System.out.println(object.object.a);
                    try{
                        farray[24].set(object, object2);}
                    catch(java.lang.IllegalAccessException e){}
                    System.out.println(object.object.a);
                }
            }
            ''',"Rfl")
        self.run(cls, [],"a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\nm\nn\no\np\nq\nr\ns\nt\nu\nv\nw\nx\nobject\n1\n2\n0\n2\n0\n2\n0\n2\n0.0\n2.0\n0.0\n2.1\nfalse\ntrue\n\x00\nx\n0\n2\n")

    def test_getDeclaredFields_getX(self):
        cls = self.getclass('''
            import java.lang.reflect.Field;

            public class Rfl {
                byte b;
                short s;
                int i;
                long l;
                float f;
                double d;
                char c;
                boolean bo;
                Rfl o;
                public static void main(String[] args)
                {
                    Field[] farray = Rfl.class.getDeclaredFields();
                    for(int i=0; i< farray.length; i++)
                        System.out.println(farray[i].getName());
                    Rfl object = new Rfl();
                    object.b=1;
                    object.s=1;
                    object.i=1;
                    object.l=1;
                    object.f=1.0f;
                    object.d=1.0;
                    object.c='1';
                    object.bo=true;
                    object.o = object;
                    
                    try{
                        System.out.println(farray[0].getByte(object));
                        System.out.println(farray[1].getShort(object));
                        System.out.println(farray[2].getInt(object));
                        System.out.println(farray[3].getLong(object));
                        System.out.println(farray[4].getFloat(object));
                        System.out.println(farray[5].getDouble(object));
                        System.out.println(farray[6].getChar(object));
                        System.out.println(farray[7].getBoolean(object));
                        System.out.println(((Rfl)farray[8].get(object)).i);
                    }
                    catch(java.lang.IllegalAccessException e){}
                }
            }
            ''',"Rfl")
        self.run(cls, [],"b\ns\ni\nl\nf\nd\nc\nbo\no\n1\n1\n1\n1\n1.0\n1.0\n1\ntrue\n1\n")

    def test_getDeclaringClass(self):
        cls = self.getclass('''
            import java.lang.reflect.Field;
            
            public class Rfl {
                int i;
                public static void main(String[] args)
                {
                    Field[] farray = Rfl.class.getDeclaredFields();
                    Class c = farray[0].getDeclaringClass();
                    System.out.println(c==Rfl.class); //true
                    Rfl r = new Rfl();
                    Rfl r2 = new Rfl();
                    Class c2 = r.getClass();
                    Class c3 = r2.getClass();
                    System.out.println(c3==c2);//true
                    System.out.println(c3==Rfl.class);//true
                }
            }
            ''',"Rfl")
        self.run(cls, [],"true\ntrue\ntrue\n")

    def test_Fields_getType(self):
        cls = self.getclass('''
            import java.lang.reflect.Field;

            public class Rfl {
                byte b;
                short s;
                int i;
                long l;
                float f;
                double d;
                char c;
                boolean bo;
                Rfl o;
                Object ob;
                public static void main(String[] args)
                {
                    Field[] farray = Rfl.class.getDeclaredFields();
                    Rfl object = new Rfl();
                    object.o = object;

                    for(int i=0; i<farray.length; i++)
                        System.out.println(farray[i].getType());
                    System.out.println(Integer.TYPE == int.class);
                    System.out.println(farray[2].getType()==int.class);
                    System.out.println(int.class==Integer.TYPE);
                }
            }
            ''',"Rfl")
        self.run(cls, [],"byte\nshort\nint\nlong\nfloat\ndouble\nchar\nboolean\nclass Rfl\nclass java.lang.Object\ntrue\ntrue\ntrue\n")

    def test_Fields_getModifiers(self):
        cls = self.getclass('''
            import java.lang.reflect.Field;

            public class Rfl {
                int a;
                private int b;
                public int c;
                static int d;
                final int e = 42;
                volatile int f;
                transient int g;
                private static volatile transient int guttenberg;
                public static void main(String[] args)
                {
                    Field[] farray = Rfl.class.getDeclaredFields();

                    for(int i=0; i<farray.length; i++)
                        System.out.println(farray[i].getModifiers());
                    try{
                        Field fi = Rfl.class.getField("c");
                        System.out.println(fi.getModifiers());}
                    catch(NoSuchFieldException e){
                        System.out.println(e.getMessage());}
                    try{
                        Field fi = Rfl.class.getField("d"); //not public
                        System.out.println(fi.getModifiers());}
                    catch(NoSuchFieldException e){
                        System.out.println(e.getMessage());}

                }
            }
            ''',"Rfl")
        self.run(cls, [],"0\n2\n1\n8\n16\n64\n128\n202\n1\nd\n")

    def test_Fields_java5(self):
        cls = self.getclass('''
            import java.lang.reflect.Field;

            public class Rfl {
                int a;
                enum Col {RED, BLUE, BLACK};
                Col b;
                public static void main(String[] args)
                {
                    Field[] farray = Rfl.class.getDeclaredFields();
                    System.out.println(farray[0].isSynthetic());
                    System.out.println(farray[0].isEnumConstant());
                    System.out.println(farray[1].isEnumConstant());
                    Class c = Col.class;
                    System.out.println(c.isEnum());
                }
            }
            ''',"Rfl")
        self.run(cls, [],"false\nfalse\nfalse\ntrue\n")

    def test_Methods(self):
        cls = self.getclass('''
            import java.lang.reflect.Method;

            public class Rfl {
                public int a(){return 42;}
                private boolean b(){return true;}
                protected double c(){return 42.0;}
                public static void d(){}
                public static void main(String[] args)
                {
                    Method[] marray = Rfl.class.getDeclaredMethods();
                    System.out.println(marray[0].getDeclaringClass().getName());
                    // There is no order...
                    //for(int i=0; i<marray.length; i++)
                    //    System.out.println(marray[i].getName());
                }
            }
            ''',"Rfl")
        self.run(cls, [],"Rfl\n")

    def test_Methods_getName(self):
        cls = self.getclass('''
            import java.lang.reflect.Method;

            public class Rfl {
                public int method(){return 42;}
                public int method_with_args(int i){return i;}
                public int method_with_args(String s){return 42;}
                public static void main(String[] args)
                {
                    try{
                        Method m = Rfl.class.getMethod("method");
                        System.out.println(m.getName());
                        Method m2 = Rfl.class.getMethod("method_with_args", int.class);
                        System.out.println(m2.getName());
                        Method m3 = Rfl.class.getMethod("method_with_args", String.class);
                        System.out.println(m3.getName());
                    }
                    catch(java.lang.NoSuchMethodException e)
                    {
                        System.out.println("Error:"+e.getMessage());
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"method\nmethod_with_args\nmethod_with_args\n")

    def test_Methods_getReturn(self):
        cls = self.getclass('''
            import java.lang.reflect.Method;

            public class Rfl {
                public int method(){return 42;}
                public String method2(){return "Hallo Welt";}
                public static void main(String[] args)
                {
                    try{
                        Method m = Rfl.class.getMethod("method");
                        System.out.println(m.getReturnType().getName());
                        Method m2 = Rfl.class.getMethod("method2");
                        System.out.println(m2.getReturnType().getName());
                    }
                    catch(java.lang.NoSuchMethodException e)
                    {
                        System.out.println("Error:"+e.getMessage());
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"int\njava.lang.String\n")

    def test_Methods_getExceptions(self):
        cls = self.getclass('''
            import java.lang.reflect.Method;

            public class Rfl {
                public void method(){}
                public void method2() throws RuntimeException {}
                public void method3() throws RuntimeException, NullPointerException {}
                public static void main(String[] args)
                {
                    try{
                        Method m = Rfl.class.getMethod("method");
                        Class[] clsArray = m.getExceptionTypes();
                        for(int i=0; i<clsArray.length; i++)
                            System.out.println(clsArray[i].getName());
                        
                        Method m2 = Rfl.class.getMethod("method2");
                        Class[] clsArray2 = m2.getExceptionTypes();
                        for(int i=0; i<clsArray2.length; i++)
                            System.out.println(clsArray2[i].getName());
                        
                        Method m3 = Rfl.class.getMethod("method3");
                        Class[] clsArray3 = m3.getExceptionTypes();
                        for(int i=0; i<clsArray3.length; i++)
                            System.out.println(clsArray3[i].getName());
                    }
                    catch(java.lang.NoSuchMethodException e)
                    {
                        System.out.println("Error:"+e.getMessage());
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"java.lang.RuntimeException\njava.lang.RuntimeException\njava.lang.NullPointerException\n")

    # FIXME: Bug with char repr inside the jvm
    def test_Methods_invoke(self):
        cls = self.getclass('''
            import java.lang.reflect.Method;

            public class Rfl {
                public void method()
                {
                    System.out.println("Hello World");
                }
                
                public int method2(int a, int b)
                {
                    return a+b;
                }
                
                public String method3()
                {
                    return "Boom";
                }
                
                public short method4(short a, short b)
                {
                    return (short)(a+b);
                }
                
                public long method5(long a, long b)
                {
                    return a+b;
                }
                
                public byte method6(byte a, byte b)
                {
                    return (byte)(a+b);
                }

                public float method7(float a, float b)
                {
                    return a+b;
                }
                
                public double method8(double a, double b)
                {
                    return a+b;
                }
                
                public char method9(char a, char b)
                {
                    return a;
                }
                
                public boolean method10(boolean a, boolean b)
                {
                    return a&&b;
                }
                
                public boolean method11(int a, int b)
                {
                    return a==b;
                }
                
                public static void main(String[] args)
                {
                    try{
                        Method m = Rfl.class.getMethod("method");
                        Rfl r = new Rfl();
                        m.invoke(r, new Object[0]);
                        
                        Method m2 = Rfl.class.getMethod("method2", int.class, int.class);
                        Integer i = (Integer) m2.invoke(r, 1,2);
                        System.out.println(i);
                        
                        Method m3 = Rfl.class.getMethod("method3");
                        String s = (String) m3.invoke(r);
                        System.out.println(s);
                        
                        Method m4 = Rfl.class.getMethod("method4", short.class, short.class);
                        Short sh = (Short) m4.invoke(r, new Short((short)7), new Short((short)3));
                        System.out.println(sh);
                        
                        Method m5 = Rfl.class.getMethod("method5", long.class, long.class);
                        Long l = (Long) m5.invoke(r, new Long(2), new Long(3));
                        System.out.println(l);
                        
                        Method m6 = Rfl.class.getMethod("method6", byte.class, byte.class);
                        Byte by = (Byte) m6.invoke(r, new Byte((byte)1), new Byte((byte)5));
                        System.out.println(by);
                        
                        Method m7 = Rfl.class.getMethod("method7", float.class, float.class);
                        Float f = (Float) m7.invoke(r, new Float(1.0), new Float(2.0));
                        System.out.println(f);
                        
                        Method m8 = Rfl.class.getMethod("method8", double.class, double.class);
                        Double d = (Double) m8.invoke(r, new Double(7), new Double(3));
                        System.out.println(d);
                        /*
                        Method m9 = Rfl.class.getMethod("method9", char.class, char.class);
                        Character c = (Character) m9.invoke(r, new Character('A'), new Character('B'));
                        System.out.println(c);
                        */
                        Method m10 = Rfl.class.getMethod("method10", boolean.class, boolean.class);
                        Boolean b = (Boolean) m10.invoke(r, new Boolean(true), new Boolean(false));
                        System.out.println(b);
                        
                        Method m11 = Rfl.class.getMethod("method11", int.class, int.class);
                        Boolean b2 = (Boolean) m11.invoke(r, new Integer(1), new Integer(1));
                        System.out.println(b2);
                    }
                    catch(java.lang.Exception e)
                    {
                        System.out.println("Error:"+e.getMessage());
                        System.out.println("Error:"+e.toString());
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"Hello World\n3\nBoom\n10\n5\n6\n3.0\n10.0\nfalse\ntrue\n")

    def test_Constructor(self):
        cls = self.getclass('''
            import java.lang.reflect.Constructor;
            import java.lang.reflect.Type;

            public class Rfl {
                public static void main(String[] args)
                {
                    try
                    {
                        Constructor c = Rfl.class.getConstructor();
                        System.out.println(c.getName());
                        System.out.println(c.getDeclaringClass().getName());
                        System.out.println(c.getModifiers());
                        System.out.println(c.isSynthetic());
                        System.out.println(c.isVarArgs());
                        System.out.println(c.getParameterTypes().length==0);
                        System.out.println(c.getExceptionTypes().length==0);
                        System.out.println(c.equals(Rfl.class));
                        System.out.println(c.equals(Rfl.class.getConstructor()));
                        //System.out.println(c.toString());
                        Rfl object = (Rfl) c.newInstance();
                        System.out.println(object instanceof Rfl);
                        Type[] types = c.getGenericParameterTypes();
                    }
                    catch(java.lang.NoSuchMethodException e)
                    {
                    }
                    catch(java.lang.InstantiationException e)
                    {
                    }
                    catch(java.lang.IllegalAccessException e)
                    {
                    }
                    catch(java.lang.reflect.InvocationTargetException e)
                    {
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"Rfl\nRfl\n1\nfalse\nfalse\ntrue\ntrue\nfalse\ntrue\ntrue\n")


    def test_ArrayClass(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    int[] array = new int[42];
                    Class c = array.getClass();
                    System.out.println(c.getName());
                    System.out.println(c.isArray());
                    System.out.println(Rfl.class.isArray());
                    try{
                        Class c2 = Class.forName("[LRfl;");
                        System.out.println(c2.isArray());
                        System.out.println(c2.getName());
                        Class c3 = c2.getComponentType();
                        System.out.println(c3.getName());
                        Class c4 = c.getComponentType();
                        System.out.println(c4.getName());
                        }
                    catch(java.lang.ClassNotFoundException e){
                        System.out.println("Nf"+e.getMessage());}
                }
            }
            ''',"Rfl")
        self.run(cls, [],"[I\ntrue\nfalse\ntrue\n[LRfl;\nRfl\nint\n")

    # TODO: hooks dont throw exceptions now...
    def test_throwException(self):
        py.test.skip("in-progress test_throwException") 
        cls = self.getclass('''
            public class Rfl {
                public Rfl() throws Exception
                {throw new Exception("Arg!");}
                public static void main(String[] args)
                {
                    try{
                        Rfl.class.newInstance();
                    }
                    catch(Exception e)
                    {
                        System.out.println(e.getMessage());
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"Arg!\n")

    def test_innerClass(self):
        cls = self.getclass('''
            public class Rfl {
                static class InnerClass{}
                private class InnerClass2{}
                public static void main(String[] args)
                {
                    InnerClass i = new InnerClass();
                    Class c = i.getClass();
                    Class c2 = c.getDeclaringClass();
                    System.out.println(c2==Rfl.class);
                    Class c3 = new Rfl().method();
                    System.out.println(c3.getDeclaringClass()==Rfl.class);
                    Class c4 = Other.class;
                    System.out.println(c4.getDeclaringClass()==Rfl.class);
                    System.out.println(Rfl.class.getEnclosingClass());
                    System.out.println(c4.getEnclosingClass());
                    System.out.println(c3.getEnclosingClass().getName());
                    System.out.println(c.isMemberClass());
                    System.out.println(c2.isMemberClass());
                }
                public Class method(){return InnerClass2.class;}
            }
            
            class Other{}
            ''',"Rfl")
        self.run(cls, [],"true\ntrue\nfalse\nnull\nnull\nRfl\ntrue\nfalse\n")

    def test_innerMethod(self):
        cls = self.getclass('''
            import java.lang.reflect.Method;
            import java.lang.reflect.Constructor;
            
            public class Rfl {
                class NotLocal{}
                public static void main(String[] args)
                {
                    class Prmpf{
                        public int plumpf(){return 42;}
                    }
                    Class c = Prmpf.class;
                    System.out.println(c.getName());
                    try{
                        Method m = c.getMethod("plumpf");
                        Method m2 = c.getEnclosingMethod();
                        System.out.println(m.getName());
                        System.out.println(m2.getName());
                        System.out.println(m.getDeclaringClass().getName());
                        System.out.println(m2.getDeclaringClass().getName());
                        System.out.println(m.getModifiers());
                        System.out.println(m2.getModifiers());
                        Constructor co = c.getEnclosingConstructor();
                        System.out.println(co);
                        System.out.println(c.isLocalClass());
                        System.out.println(Rfl.class.isLocalClass());
                        System.out.println(NotLocal.class.isLocalClass());
                    }
                    catch(java.lang.NoSuchMethodException e)
                    {
                        System.out.println(e.getMessage());
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"Rfl$1Prmpf\nplumpf\nmain\nRfl$1Prmpf\nRfl\n1\n9\nnull\ntrue\nfalse\nfalse\n")

    def test_outerConstructor(self):
        cls = self.getclass('''
            import java.lang.reflect.Constructor;

            public class Rfl {
                public Rfl(int x, int y, String str)
                {
                    class Inner{};
                    Class c = Inner.class;
                    Constructor co = c.getEnclosingConstructor();
                    System.out.println(co==null);
                    System.out.println(co.getDeclaringClass().getName());
                    System.out.println(co.getName());
                    System.out.println(co.getModifiers());
                    Class[] args = co.getParameterTypes();
                    for(int i=0; i<args.length; i++)
                        System.out.println(args[i].getName());
                    args = co.getExceptionTypes();
                    System.out.println(args.length==0);
                    Constructor co2 = Rfl.class.getEnclosingConstructor();
                    System.out.println(co2==null); // true (toplevel class)
                }
                public static void main(String[] args)
                {
                    new Rfl(1,2,"mööp");
                }
            }
            ''',"Rfl")
        self.run(cls, [],"false\nRfl\nRfl\n1\nint\nint\njava.lang.String\ntrue\ntrue\n")

    def test_isAnonymousClass(self):
        cls = self.getclass('''
            public class Rfl {
                public static void main(String[] args)
                {
                    System.out.println(Rfl.class.getSimpleName());
                    System.out.println(Rfl.class.isAnonymousClass());
                    Object o = new Object(){};
                    System.out.println(o.getClass().isAnonymousClass());
                }
            }
            ''',"Rfl")
        self.run(cls, [],"Rfl\nfalse\ntrue\n")

    def test_Constructor_no_stdc(self):
        cls = self.getclass('''
            import java.lang.reflect.Constructor;

            public class Rfl {
                int j =0;
                public Rfl(int i, String s) throws Exception
                {j=i;}
                public static void main(String[] args)
                {
                    try
                    {
                        Constructor c = Rfl.class.getConstructor(int.class, String.class);
                        System.out.println(c.getName());
                        System.out.println(c.getDeclaringClass().getName());
                        System.out.println(c.getModifiers());
                        System.out.println(c.isSynthetic());
                        System.out.println(c.isVarArgs());
                        System.out.println(c.getParameterTypes().length==2);
                        System.out.println(c.getExceptionTypes().length==1);
                        System.out.println(c.equals(Rfl.class));
                        System.out.println(c.equals(Rfl.class.getConstructor(int.class, String.class)));
                        Rfl object = (Rfl) c.newInstance(new Integer(42), "Peter");
                        System.out.println(object.j);
                        //System.out.println(c.toString());
                    }
                    catch(java.lang.NoSuchMethodException e)
                    {System.out.println("NoSuchMethodException:"+e.getMessage());
                    }
                    catch(java.lang.InstantiationException e)
                    {System.out.println("InstantiationException:"+e.getMessage());
                    }
                    catch(java.lang.IllegalAccessException e)
                    {System.out.println(e.getMessage());
                    }
                    catch(java.lang.reflect.InvocationTargetException e)
                    {System.out.println(e.getMessage());
                    }
                }
            }
            ''',"Rfl")
        self.run(cls, [],"Rfl\nRfl\n1\nfalse\nfalse\ntrue\ntrue\nfalse\ntrue\n42\n")

    # TODO: find calling class e.g Rfl
    # this change is some work...
    def test_Fields_private(self):
        py.test.skip("in-progress test_Fields_private") 
        cls = self.getclass('''
            import java.lang.reflect.Field;

            public class Rfl {
                private boolean a;
                public static void main(String[] args)
                {
                    Field[] farray = Rfl.class.getDeclaredFields();
                    Rfl object = new Rfl();
                    System.out.println(object.a);
                    try{
                        farray[0].setBoolean(object, true);}
                    catch(java.lang.IllegalAccessException e){
                        System.out.println(e.getMessage());}
                    System.out.println(object.a);
                    
                    A object2 = new A();
                    System.out.println(object2.getB());
                    farray = A.class.getDeclaredFields();
                    try{
                        farray[0].setBoolean(object2, true);}
                    catch(java.lang.IllegalAccessException e){
                        System.out.println(e.getMessage());}
                    System.out.println(object2.getB());
                }
            }
            
            class A
            {
                private boolean b;
                boolean getB(){return b;}
            }
            ''',"Rfl")
        self.run(cls, [],"false\ntrue\nfalse\nClass Rfl can not access a member of class A with modifiers \"private\"\nfalse\n")