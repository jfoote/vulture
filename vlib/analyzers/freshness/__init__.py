import json, logging
from functools import partial

log = logging.getLogger()

def analyze_bug(popularity, results, bugdir): # results must be mutable (passed by ref)

    metadata = json.load(open("%s/vulture.json" % bugdir, "rt"))
    bug_results = {}

    # get popularity 
    bug_results['popularity'] = {} # a popularity for each project
    for pn in metadata['project_metadata'].keys():
        pop = popularity.get(pn, None)
        if not pop:
            log.warning("%s not found in popcon dataset" % pn)
            continue
        bug_results['popularity'][pn] = pop

    # get project bug status
    for pn, project_bug in metadata['project_metadata'].items():
        for field in ['status', 'date_closed']:
            bug_results[field] = project_bug[field]

    # get modification info
    for field in ['date_created', 'date_last_updated']:
        bug_results[field] = metadata[field][:10] # just y-m-d

    # store results for this bug
    bug_id_str = bugdir.strip("/").split("/")[-1]
    results[bug_id_str] = bug_results


status_order = ["New", # most interesting to least interesting
    "Opinion", 
    "Confirmed", 
    "Triaged",
    "Invalid", 
    "In Progress", 
    "Incomplete (with response)", 
    "Incomplete (without response)", 
    "Incomplete",
    "Fix Committed", 
    "Won't Fix", 
    "Expired", 
    "Fix Released", 
]

def get_scores(bug_cache_dir, popularity_cache_dir):
    from vlib.analyzers.tools import call_for_each_bug

    # load popularity (big) into memory
    popularity = json.load(open("%s/popularity.json" % popularity_cache_dir, "rt"))

    # aggregate data for each bug in bug_cache_dir
    results = {}
    call_for_each_bug(bug_cache_dir, partial(analyze_bug, popularity, results))

    # calculate scores

    # rank each bug by each metric
    max_popularity = max([int(pop['rank']) for pop in popularity.values()])
    
    pop_scores = {}
    for bug_id_str, md in results.items():
        pop_by_proj = md.get('popularity', None)
        pops = []
        for project, pop in pop_by_proj.items():
            rank = pop.get('rank', None)
            if rank:
                pops.append(int(rank))
        if pops:
            pop_score = min(pops)
        else:
            pop_score = max_popularity / 2
        pop_scores[bug_id_str] = pop_score

    sorted_data = sorted(results.items(), cmp=lambda a,b: cmp(a[1]['date_last_updated'], b[1]['date_last_updated']))
    date_mod_scores = {}
    i = 0
    last = ""
    for bug_id_str, md in sorted_data:
        date = md['date_last_updated'][:10] 
        if date != last: 
            i += 1 # new day
        last = date
        date_mod_scores[bug_id_str] = i

    sorted_data = sorted(results.items(), cmp=lambda a,b: cmp(a[1]['date_created'], b[1]['date_created']))
    date_created_scores = {}
    i = 0
    last = ""
    for bug_id_str, md in sorted_data:
        date = md['date_created'][:10] 
        if date != last: 
            i += 1 # new day
        last = date
        date_created_scores[bug_id_str] = i

    sorted_data = sorted(results.items(), cmp=lambda a,b: cmp(a[1]['date_closed'], b[1]['date_closed']))
    date_closed_scores = {}
    i = 0
    last = ""
    for bug_id_str, md in sorted_data:
        date = md['date_closed'][:10] 
        if date == "None":
            date_closed_scores[bug_id_str] = 0
            continue
        elif date != last: 
            i += 1 # new day
        last = date
        date_closed_scores[bug_id_str] = i

    # status
    status_ranks = {}
    i = 0
    for status in status_order:
        status_ranks[status] = i
        i += 1

    status_scores = {}
    for bug_id_str, md in results.items():
        status_scores[bug_id_str] = status_ranks[md['status']]

    # calculate combined score; this is a complete WAG
    # date_mod, date_created, status, popularity, date_closed
    scores = {}
    for bug_id_str, status_score in status_scores.items():
        score = status_score * 20 + \
                date_mod_scores[bug_id_str] * 20 + \
                pop_scores[bug_id_str] * 50 + \
                date_created_scores[bug_id_str] * 1 + \
                date_closed_scores[bug_id_str] * 30
        scores[bug_id_str] = score

    return scores

    '''
    # TODO: maybe dump this so we can use it to generate a webpage that shows the rationale for a given bug's score (freshness in this case)
    # dump json for analysis in analysis_dir
    dpath = "%s/%s" % (analysis_dir, id_dirs)
    if not os.path.exists(dpath):
        os.makedirs(dpath)
    json.dump(analysis, open("%s/analysis.json" % dpath, "wt"), indent=4)
    '''
