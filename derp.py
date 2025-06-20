class Derp:

    def foo(self, x):
        return x/2
    test:
        foo(4) == 2: "foo failed with 4",
        foo(8) == 4: "foo failed with 8"
    doc:
        returns half the input

    def bar(self, x):
        return x*2
    test:
        bar(2) == 4: "bar failed with 2",
        bar(4) == 8: "bar failed with 4"
    doc:
        returns double the input
        
    def baz(self, x):
        return self.bar(x) + self.foo(x)
    doc:
        #for baz
        combines bar and foo operations - returns x*2 + x/2
    test:
        #for baz
        baz(2) == 5: "baz failed with 2",
        baz(4) == 10: "baz failed with 4"
test:
    #for class Derp
    foo(2)*bar(2) == 4: "foo bar test failed",
    a = bar(2)
    b = foo(12)
    a+b == 10: "separate foo bar test failed"
doc:
    #for class derp
    a simple math module for multiplying and dividing numbers by 2

def main():
    f = Derp().foo(2)  # This should create a dependency
    j = Derp().baz(2)  # This should create a dependency
test:
    t = Derp().foo(4)
    t == 2: "main passed"
doc:
    main entry point that demonstrates PyTestEmbed dependency tracking by calling Derp.foo
