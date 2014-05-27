import os, logging

log = logging.getLogger()

def call_for_each_bug(bug_cache_dir, analyzer_func):
    # do analysis for each bug in bug_cache_dir
    i = 0
    for root, dirs, files in os.walk(bug_cache_dir, topdown=True):
        log.debug("processing %s (#%d)" % (root, i))
        i += 1
        if i > 100: # TODO: delete this
            break

        if "vulture.json" not in files:
            continue

        try:
            analyzer_func(root)
        except Exception as e:
            log.exception(e)
            #continue
            raise e
