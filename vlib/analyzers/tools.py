import os, logging

log = logging.getLogger()

def call_for_each_bug(bug_cache_dir, analyzer_func, limit=None):
    # do analysis for each bug in bug_cache_dir
    i = 0
    for root, dirs, files in os.walk(bug_cache_dir, topdown=True):
        log.debug("processing %s (#%d)" % (root, i))
        i += 1
        if limit and i > limit:
            log.debug("limit(%d) reached" % limit)
            break

        if "vulture.json" not in files:
            continue

        try:
            analyzer_func(root)
        except Exception as e:
            log.exception(e)
            #continue
            raise e

# being lazy
status_by_category = {
        'fresh': [
            "New",  
            "Opinion", 
            "Confirmed", ],
        'wip' : [
            "Triaged", 
            "Incomplete (with response)", 
            "Incomplete (without response)", 
            "Incomplete",
            "In Progress", ],
        'fixed' : [
            "Fix Committed", 
            "Fix Released", ], 
        'abandoned' : [
            "Invalid", 
            "Won't Fix", 
            "Expired", ]
        }

score_by_category = {
        'fresh' : 1,
        'wip' : 2,
        'abandoned' : 3,
        'fixed': 4
        }

category_by_status = {}
for cat, stats in status_by_category.items():
    for stat in stats:
        category_by_status[stat] = cat
score_by_status = {status:score_by_category[cat] for status, cat in category_by_status.items()}

def get_category_by_status(in_status):
    return category_by_status[in_status]

def get_score_by_status(in_status):
    # sort bug statuses for scoring
    return score_by_status[in_status]


