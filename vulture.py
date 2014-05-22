#!/usr/bin/python

import logging, os


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
    parser.add_option("-c", "--cache-directory", dest="cache_dir", default="data", help="Local directory to use as cache for remote bug information (bug info is read/written here)")
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

    logging.basicConfig()
    log = logging.getLogger()
    log.level = getattr(logging, options.loglevel)
    log.info(str(options))

    #bucket = boto.connect_s3().get_bucket(options.bucket) 
    if len(args) < 1:
        parser.error("Wrong number of arguments")

    bug_cache_dir = os.path.join(options.cache_dir, "bugs", "launchpad")
    popularity_cache_dir = os.path.join(options.cache_dir, "popularity")

    if args[0] == "analyze":
        from vlib.analyzers import analyze
        log.info("Analyzing bug cache in directory: %s" % bug_cache_dir)
        analyze(bug_cache_dir, options.analysis_dir, popularity_cache_dir)
    elif args[0] == "build-cache":
        # cache everything
        from vlib.launchpad import cache_bugs
        from vlib.ubuntu import cache_popularity
        cache_bugs(bug_cache_dir)
        cache_popularity(popularity_cache_dir)
    elif args[0] == "build-bug-cache":
        # cache only bugs
        from vlib.launchpad import cache_bugs
        cache_bugs(bug_cache_dir)
    elif args[0] == "build-popularity-cache":
        # cache only popularity
        from vlib.ubuntu import cache_popularity
        cache_popularity(os.path.join(options.cache_dir, "popularity"))
    elif args[0] == "update-cache":
        # cache info for recently updated bugs, popularity
        from vlib.launchpad import cache_bugs
        from vlib.ubuntu import popularity
        from datetime import date, timedelta
        modified_since = (date.today()-timedelta(days=1)).strftime("%Y-%m-%d")
        cache_bugs(bug_cache_dir, modified_since, True)
        cache_popularity(os.path.join(options.cache_dir, "popularity"))
    elif args[0] == "report":
        raise NotImplementedError("TODO this should generate a report (static HTML)")
    elif args[0] == "publish":
        raise NotImplementedError("TODO this should publish static HTML + analysis (and maybe cache) to S3, probably via s3cmd. Maybe should be implemented outside this script ")
    else:
        parser.error("Unable to parse command. args=%s" % str(args))

