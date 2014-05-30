#!/usr/bin/env python
# encoding: utf-8

import os, sys
from functools import partial
class SuperTrace(object):
    def __init__(self, rootdir=None):
        if not rootdir:
            self.rootdir = os.getcwd()
        import inspect
        self.inspect = inspect
        self.results = []

    def start(self):
        sys.settrace(partial(self.trace))

    stop = partial(sys.settrace, None)

    def trace(self, frame, event, arg):
        co = frame.f_code
        func_name = co.co_name
        filename = co.co_filename
        line_no = frame.f_lineno
        try:
            filepath = self.inspect.getfile(co)
        except TypeError as e:
            # built-in
            return partial(self.trace)
        arginfo = self.inspect.getargvalues(frame)
        # globs = frame.f_globals 
        # ^^ too much info for sure
        if self.rootdir in filepath:
            filepath = filepath[len(self.rootdir):].strip("/\\")
        lineinfo = { 
                'filepath' : filepath,
                'line_no' : line_no,
                'arginfo' : arginfo,
                #'globs' : globs
                }
        self.results.append(lineinfo)

        return partial(self.trace)

    def dump(self, path):
        import json
        json.dump(self.results, file(path, "wt"))
   
if __name__ == "__main__"
    import sys
    from functools import partial # importing in callbacks fails sometimes
    import inspect
    
    y = 7
    results = []
    
    
    def c(input):
        print 'input =', input
        print 'Leaving c()'
    
    def b(arg):
        val = arg * 5
        c(val)
        print 'Leaving b()'
    
    def a():
        x = 7
        if x > 5:
            b(2)
        else:
            c("hoohaa")
        gg("dog")
        print 'Leaving a()'
    
    
    from subdir.whatever import gg
    st = SuperTrace()
    st.start()
    a()
    st.stop()
    
    for li in st.results:
        print li['filepath'], li['line_no'], li['arginfo']
    st.dump("foo.json")
