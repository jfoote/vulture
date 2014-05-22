import os, json

import logging
log = logging.getLogger()

from vlib.analyzers.exploitability.exploitable import exploitable

def analyze(bug_cache_dir, analysis_dir):

    # do analysis for each bug in bug_cache_dir
    for root, dirs, files in os.walk(bug_cache_dir, topdown=True):
        log.debug("processing %s" % root)

        if "vulture.json" not in files:
            continue

        analysis = {}

        # prep to mirror directory structure in bug_cache_dir
        id_dirs = root[len(bug_cache_dir):]
        if id_dirs[0] == "/":
            id_dirs = id_dirs[1:]

        try:
            # do analysis
            target, c = exploitable(root)
            analysis['exploitability'] = c

            # dump json for analysis in analysis_dir
            dpath = "%s/%s" % (analysis_dir, id_dirs)
            if not os.path.exists(dpath):
                os.makedirs(dpath)
            json.dump(analysis, open("%s/analysis.json" % dpath, "wt"), indent=4)
        except Exception as e:
            log.exception(e)
            continue
