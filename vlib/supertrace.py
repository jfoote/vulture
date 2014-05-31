#!/usr/bin/env python
# encoding: utf-8

import os, sys, json
from functools import partial

import logging
log = logging.getLogger()

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
        filename = co.co_filename

        # if not in this project, don't trace
        if len(os.path.split(filename)) > 1:
            if self.rootdir not in filename:
                return partial(self.trace)
            else:
                # otherwise strip project dir
                filename = filename[len(self.rootdir):].strip("/\\")

        if event != 'call' and event != 'exception':
            return partial(self.trace)

        line_no = frame.f_lineno

        func_name = co.co_name

        arginfo = self.inspect.getargvalues(frame)
        argdict = { 'keywords' : arginfo.keywords,
                'varargs' : arginfo.varargs,
                'args' : arginfo.args,
                'locals' : {k: repr(v) for k,v in arginfo.locals.items() }
                }
        lineinfo = { 
                #'filepath' : filepath,
                'filename' : filename,
                'line_no' : line_no,
                'arginfo' : argdict,
                #'globs' : globs
                }
        self.results.append(lineinfo)

        return partial(self.trace)

    def dump(self, path, maxbytes=None): #16777216*4): # 16MB*4
        out = json.dumps(self.results, indent=4)
        if maxbytes and sys.getsizeof(out) > maxbytes:
            log.error("trace too big: %d > %d" % (sys.getsizeof(out), maxbytes))
        else:
            file(path, "wt").write(out)
   
if __name__ == "__main__":
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
