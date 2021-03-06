from .types import *
from collections import defaultdict


class ClassInfo:
    def __init__(self, name: str, superclass: str = None):
        self.name = name
        self.superclass = superclass
        self.attrs = defaultdict(lambda: None)  # (attr type, init value)
        self.methods = defaultdict(lambda: None)  # type of method
        self.orderedAttrs = []

    def __str__(self):
        return f"class {self.name}({self.superclass}): {self.attrs} {self.methods}"


class TypeSystem:
    def __init__(self):
        # information for each class
        self.classes = defaultdict(lambda: None)

        objectInfo = ClassInfo("object")
        objectInfo.methods["__init__"] = FuncType([ObjectType()], NoneType())

        intInfo = ClassInfo("int", "object")
        intInfo.methods["__init__"] = FuncType([ObjectType()], NoneType())

        boolInfo = ClassInfo("bool", "object")
        boolInfo.methods["__init__"] = FuncType([ObjectType()], NoneType())

        strInfo = ClassInfo("str", "object")
        strInfo.methods["__init__"] = FuncType([ObjectType()], NoneType())

        self.classes["object"] = objectInfo
        self.classes["int"] = intInfo
        self.classes["bool"] = boolInfo
        self.classes["str"] = strInfo
        self.classes["<None>"] = ClassInfo("<None>", "object")
        self.classes["<Empty>"] = ClassInfo("<Empty>", "object")

    def getMethodHelper(self, className: str, methodName: str):
        # requires className to be the name of a valid class
        if methodName not in self.classes[className].methods:
            if self.classes[className].superclass is None:
                return (None, None)
            return self.getMethodHelper(self.classes[className].superclass, methodName)
        return (self.classes[className].methods[methodName], className)

    def getMethod(self, className: str, methodName: str):
        # requires className to be the name of a valid class
        return self.getMethodHelper(className, methodName)[0]

    def getMethodDefClass(self, className: str, methodName: str):
        # returns the class that the method was originally defined in
        # requires className to be the name of a valid class
        return self.getMethodHelper(className, methodName)[1]

    def getAttrHelper(self, className: str, attrName: str):
        # requires className to be the name of a valid class
        if attrName not in self.classes[className].attrs:
            if self.classes[className].superclass is None:
                return (None, None)
            return self.getAttrHelper(self.classes[className].superclass, attrName)
        return self.classes[className].attrs[attrName]

    def getAttr(self, className: str, attrName: str):
        # returns type of attribute
        # requires className to be the name of a valid class
        return self.getAttrHelper(className, attrName)[0]

    def getAttrInit(self, className: str, attrName: str):
        # returns initial value of attribute
        # requires className to be the name of a valid class
        return self.getAttrHelper(className, attrName)[1]

    def getAttrOrMethod(self, className: str, name: str):
        # returns type of attribute or method
        # requires className to be the name of a valid class
        if name in self.classes[className].methods:
            return self.classes[className].methods[name]
        elif name in self.classes[className].attrs:
            return self.classes[className].attrs[name][0]
        else:
            if self.classes[className].superclass is None:
                return None
            return self.getAttrOrMethod(self.classes[className].superclass, name)

    def classExists(self, className: str) -> bool:
        # we cannot check for None because it is a defaultdict
        return className in self.classes

    def isSubClass(self, a: str, b: str) -> bool:
        # requires a and b to be the names of valid classes
        # return if a is the same class or subclass of b
        curr = a
        while curr is not None:
            if curr == b:
                return True
            else:
                curr = self.classes[curr].superclass
        return False

    def isSubtype(self, a: ValueType, b: ValueType) -> bool:
        # return if a is a subtype of b
        if b == ObjectType():
            return True
        if isinstance(a, ClassValueType) and isinstance(b, ClassValueType):
            return self.isSubClass(a.className, b.className)
        return a == b

    def canAssign(self, a: ValueType, b: ValueType) -> bool:
        # return if value of type a can be assigned/passed to type b (ex: b = a)
        if self.isSubtype(a, b):
            return True
        if a == NoneType() and b not in [IntType(), StrType(), BoolType()]:
            return True
        return False

    def join(self, a: ValueType, b: ValueType):
        # return closest mutual ancestor on typing tree
        if self.canAssign(a, b):
            return b
        if self.canAssign(b, a):
            return a
        # for 2 classes that aren't related by subtyping
        # find paths from A & B to root of typing tree
        a, b = a.className, b.className
        aAncestors = []
        bAncestors = []
        while self.classes[a].superclass is not None:
            aAncestors.append(self.classes[a].superclass)
            a = self.classes[a].superclass
        while self.classes[b].superclass is not None:
            aAncestors.append(self.classes[b].superclass)
            b = self.classes[b].superclass
        # reverse lists to find lowest common ancestor
        aAncestors = aAncestors[::-1]
        bAncestors = bAncestors[::-1]
        for i in range(min(len(aAncestors), len(bAncestors))):
            if aAncestors[i] != bAncestors[i]:
                return self.classes[aAncestors[i - 1]]
        # this really shouldn't be returned
        return ObjectType()

    def getAllMethods(self, className: str):
        # return map of method names to tuples of
        # (signature, classname of their definition)
        methods = {}
        if self.classes[className].superclass is not None:
            methods = self.getAllMethods(self.classes[className].superclass)
        for name in self.classes[className].methods:
            methods[name] = (self.classes[className].methods[name], className)
        return methods

    def getOrderedAttrs(self, className: str):
        # return list of (name, type, init value) triples
        attrs = []
        if self.classes[className].superclass is not None:
            attr = self.getOrderedAttrs(self.classes[className].superclass)
        for attr in self.classes[className].orderedAttrs:
            attrType, attrInit = self.classes[className].attrs[attr]
            attrs.append((attr, attrType, attrInit))
        return attrs
