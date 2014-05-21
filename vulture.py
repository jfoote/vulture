#!/usr/bin/python

import logging, os
#log = logging.getLogger('vulture')
logging.basicConfig()
log = logging

from vlib.launchpad import *

'''
try:
    log._nh = logging.NullHandler() # no logging by default
    log.addHandler(log._nh)
except AttributeError as e:
    logging.warning("unable to add log null handler (may be Python2.6): %s" %\
        str(e))
'''

from optparse import OptionParser
if __name__ == "__main__":
    usage = "usage: %prog [OPTIONS] CMD"
    desc = "Scrapes pages from bing results on S3 for links to files and stores results to S3."
    parser = OptionParser(usage=usage, description=desc)
    parser.add_option("-l", "--logfile", dest="logfile")
    parser.add_option("-e", "--loglevel", dest="loglevel", default="DEBUG")
    #parser.add_option("-b", "--bucket", dest="bucket", default="evde", help="S3 bucket to use for read/write")
    parser.add_option("-b", "--bug-cache-directory", dest="bug_cache_dir", default="data/bugs", help="Local directory to use as cache for remote bug information (bug info is read/written here)")
    parser.add_option("-a", "--analysis-cache-directory", dest="analysis_dir", default="data/analysis", help="Local directory to use as cache for analysis results (anallysis info is read/written here)")
    
    
    (options, args) = parser.parse_args()
     
    if options.logfile:
        lformat = '%(asctime)s %(name)s %(levelname)s %(filename)s %(funcName)s %(message)s'
        if getattr(log, "_nh", None):
            log.removeHandler(log._nh)
        hdlr = logging.FileHandler(options.logfile)
        formatter = logging.Formatter(lformat)
        hdlr.setFormatter(formatter)
        log.addHandler(hdlr)
        log.setLevel(getattr(logging, options.loglevel))
        
    log.info(str(options))

    #bucket = boto.connect_s3().get_bucket(options.bucket) 
    if len(args) < 1:
        parser.error("Wrong number of arguments")

    if args[0] == "analyze":
        from vlib.analyzers import analyze
        log.info("Analyzing bug cache in directory: %s" % options.bug_cache_dir)
        for root, dirs, files in os.walk(options.bug_cache_dir, topdown=True):
            if "Disassembly.txt" not in files:
                log.debug("Disassembly.txt not found for %s" % root)
                continue
            log.debug("processing %s" % root)
            project = root.split("/")[-2]
            try:
                print analyze(root)
            except Exception as e:
                log.exception(e)
                continue
    elif args[0] == "rebuild-bug-cache":
        cache_all(options.bug_cache_dir, False)
    elif args[0] == "rebuild-bug-cache-force":
        cache_all(options.bug_cache_dir, True)
    elif args[0] == "update-cache":
        from datetime import date, timedelta
        modified_since = (date.today()-timedelta(days=1)).strftime("%Y-%m-%d")
        cache_bugs(options.bug_cache_dir, modified_since)
        # cache info for recently updated bugs
        # for bug in launchpad.search(date): download(bug_info)
    else:
        parser.error("Unable to parse command. args=%s" % str(args))

