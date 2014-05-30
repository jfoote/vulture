#!/usr/bin/env python
# encoding: utf-8

import os, sys, json
from functools import partial

class SuperTrace(object):
    def __init__(self, rootdir=None):
        if not rootdir:
            self.rootdir = os.getcwd()
        import inspect
        self.inspect = inspect
        self.results = []

    def get_size(self):
        size = sys.getsizeof(self.results)
        for li in self.results:
            size += sys.getsizeof(li)
            if getattr(li, '__iter__'):
                for lii in li:
                    size += sys.getsizeof(lii)
        return size

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
        if event != 'call':
            # quick hack
            return partial(self.trace)
        if event == 'exception':
            print "exception hit"
            return partial(self.trace)

        line_no = frame.f_lineno

        # if not related to branching, don't trace
        if event == 'line':
            lines, start = self.inspect.getsourcelines(frame)
            thisline = lines[line_no-start].strip("\r\n")
            if "if" != thisline.strip()[:2]:
                return partial(self.trace)
        #if event == 'exception':
        #    print self.inspect.getargvalues(frame)

        func_name = co.co_name

        ''' deprecated
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
        '''
        arginfo = self.inspect.getargvalues(frame)
        argdict = { 'keywords' : str(arginfo.keywords),
                'varargs' : str(arginfo.varargs),
                'args' : str(arginfo.args),
                'locals' : str(arginfo.locals) }
        lineinfo = { 
                #'filepath' : filepath,
                'filename' : filename,
                'line_no' : line_no,
                'arginfo' : argdict,
                #'globs' : globs
                }
        self.results.append(lineinfo)

        return partial(self.trace)

    def dump(self, path):
        json.dump(self.results, file(path, "wt"))
   
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
