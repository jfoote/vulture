#!/usr/bin/python

import logging, os

from optparse import OptionParser
if __name__ == "__main__":
    usage = "usage: %prog [OPTIONS] CMD"
    desc = "Analyzes open source bug trackers for interesting vulnerabilites. So unpolished you need to read the source code to know how to use it. This implementation assumes it is running in an EC2 instance with a role that has access to the 'vulture88' bucket. I'm sorry."
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
        days = int(args[1])
        # cache info for recently updated bugs, popularity
        from vlib.launchpad import cache_bugs
        from vlib.ubuntu import cache_popularity
        from vlib.analyzers import analyze
        from datetime import date, timedelta

        # cache info for modified bugs
        modified_since = (date.today()-timedelta(days=days)).strftime("%Y-%m-%d")
        buglist = cache_bugs(bug_cache_dir, modified_since, True)
        cache_popularity(os.path.join(options.cache_dir, "popularity"), True)

        # analyze modified bugs
        analyzers = filter(None, options.analyzers.split(","))
        analyze(bug_cache_dir, options.analysis_dir, popularity_cache_dir, None, analyzers, buglist)

        if len(args) > 2 and args[2] == "publish":
            from vlib.report import publish
            publish(options.analysis_dir, [], buglist)

    elif args[0] == "report":
        raise NotImplementedError("TODO this should generate a report (static HTML)")
    elif args[0] == "publish":
        plist = []
        if len(args) > 1: 
            plist = args[1].split(",")
        from vlib.report import publish
        publish(options.analysis_dir, plist)
    else:
        parser.error("Unable to parse command. args=%s" % str(args))

