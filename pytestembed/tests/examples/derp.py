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

test:
    foo(2)*bar(2) == 4: "foo bar test failed",
    a = bar(2)
    b = foo(12)
    a+b == 10: "separate foo bar test failed"
doc:
    a simple math module for multiplying and dividing numbers by 2

def main():
    t = Derp().foo(2)
test:
    # no tests needed
doc:
    example to show off the concept