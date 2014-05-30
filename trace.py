#!/usr/bin/env python
# encoding: utf-8

import sys
from functools import partial # importing in callbacks fails sometimes
import inspect

def trace_lines(inspect, frame, event, arg):
    if event != 'line':
        return
    line_no = frame.f_lineno
    lines, start = inspect.getsourcelines(frame)
    thisline = lines[line_no-start].strip("\r\n")
    if "if" != thisline.strip()[:2]:
        return
    co = frame.f_code
    func_name = co.co_name
    filename = co.co_filename
    arginfo = inspect.getargvalues(frame)
    print "COND %s:%d:%s (%s)" % (filename, line_no, thisline, arginfo)
    # NOTE: this contains definitions for globals!
    # print frame.f_globals

y = 7

def trace_calls(inspect, frame, event, arg):
    if event != 'call':
        return
    co = frame.f_code
    func_name = co.co_name
    if func_name == 'write':
        # Ignore write() calls from print statements
        return
    line_no = frame.f_lineno
    filename = co.co_filename
    arginfo = inspect.getargvalues(frame)
    lines, start = inspect.getsourcelines(frame)
    thisline = lines[line_no-start].strip("\r\n")
    print "CALL %s:%d:%s (%s)" % (filename, line_no, thisline, arginfo)
    #print 'Call to %s on line %s of %s' % (func_name, line_no, filename)
    #if func_name in TRACE_INTO:
        # Trace into this function
    return partial(trace_lines, inspect)

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
    print 'Leaving a()'
    
TRACE_INTO = ['b']

sys.settrace(partial(trace_calls, inspect))
a()
