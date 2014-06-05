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
    parser.add_option("-b", "--buglist", dest="buglist", default="", help="List of bug IDs to process")
    parser.add_option("-z", "--analyzers", dest="analyzers", default="popularity,reproducibility,exploitability,freshness", help="List of top-level analyzers to apply to each bug, only makes sense if command is analyzing bugs, OFC")
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
        limit = None
        if len(args) > 1:
            limit = int(args[1])
        buglist = filter(None, options.buglist.split(","))
        analyzers = filter(None, options.analyzers.split(","))
        from vlib.analyzers import analyze
        log.info("Analyzing bug cache in directory: %s" % bug_cache_dir)
        scores = analyze(bug_cache_dir, options.analysis_dir, popularity_cache_dir, limit, analyzers, buglist)
    elif args[0] == "build-cache":
        # cache everything
        from vlib.launchpad import cache_bugs
        from vlib.ubuntu import cache_popularity
        cache_bugs(bug_cache_dir)
        cache_popularity(popularity_cache_dir, False)
    elif args[0] == "build-bug-cache":
        # cache only bugs
        from vlib.launchpad import cache_bugs
        cache_bugs(bug_cache_dir)
    elif args[0] == "build-popularity-cache":
        # cache only popularity
        from vlib.ubuntu import cache_popularity
        cache_popularity(os.path.join(options.cache_dir, "popularity"), True)
    elif args[0] == "build-desktop-entry-cache":
        # cache only desktop entries
        from vlib.ubuntu import cache_desktop_entries
        cache_desktop_entries(os.path.join(options.cache_dir, "desktop-entries"), True)
    elif args[0] == "update-cache":
        # cache info for recently updated bugs, popularity
        from vlib.launchpad import cache_bugs
        from vlib.ubuntu import cache_popularity
        from datetime import date, timedelta

        # cache info for modified bugs
        modified_since = (date.today()-timedelta(days=3)).strftime("%Y-%m-%d")
        buglist = cache_bugs(bug_cache_dir, modified_since, True)
        cache_popularity(os.path.join(options.cache_dir, "popularity"), True)

        # analyze modified bugs
        analyzers = filter(None, options.analyzers.split(","))
        analyze(bug_cache_dir, options.analysis_dir, popularity_cache_dir, None, analyzers, buglist)

        if args[1] == "publish":
            from vlib.report import publish
            publish(options.analysis_dir, html_only, buglist)
            # TODO test this :)

    elif args[0] == "report":
        raise NotImplementedError("TODO this should generate a report (static HTML)")
    elif args[0] == "publish":
        html_only = False
        if len(args) > 1 and args[1] == 'html':
            html_only = True
        from vlib.report import publish
        publish(options.analysis_dir, html_only)
    else:
        parser.error("Unable to parse command. args=%s" % str(args))

