import os, json, logging

from functools import partial

log = logging.getLogger()

from vlib.analyzers import exploitability, freshness, popularity
from vlib.analyzers.tools import call_for_each_bug

def store_analysis(summary, scores, bug_cache_dir, analysis_dir, bugdir):

    # mirror bug_cache_dir structure in analysis_dir
    dir_tail = bugdir[len(bug_cache_dir):]
    dir_tail = dir_tail.strip("/")
    out_dir = "%s/%s" % (analysis_dir, dir_tail)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # dump analysis for this bug 
    bug_id_str = bugdir.split("/")[-1]
    bscores = scores[bug_id_str]
    json.dump(bscores, open("%s/analysis.json" % out_dir, "wt"), indent=4)

    # add this bug to summary
    metadata = json.load(open("%s/vulture.json" % bugdir, "rt"))

    bugrow = {}
    bugrow['id'] = bug_id_str
    bugrow['title'] = metadata['title']
    bugrow['web_link'] = metadata['web_link']
    bugrow['installs_score'] = bscores['popularity']['inst']
    bugrow['date_modified_score'] = bscores['freshness']['date_last_updated']
    bugrow['date_created_score'] = bscores['freshness']['date_created']
    bugrow['project_status_score'] = bscores['freshness']['status']
    bugrow['exploitability_score'] = bscores['exploitability']['score']
    summary.append(bugrow)

def analyze(bug_cache_dir, analysis_dir, popularity_cache_dir):
    '''
    This function should cache a JSON object corresponding to the
    data that will be used on index.html: bug_id, bug_title, <metric ranks>
    '''
    scores = {}

    # get scores for each metric
    f_scores = freshness.get_scores(bug_cache_dir)
    p_scores = popularity.get_scores(bug_cache_dir, popularity_cache_dir)
    e_scores = exploitability.get_scores(bug_cache_dir)

    bug_id_strs = list((set(f_scores.keys() + p_scores.keys() + 
        e_scores.keys()))) 
    
    for bug_id_str in bug_id_strs:
        scores[bug_id_str] = {}
        scores[bug_id_str]['freshness'] = f_scores.get(bug_id_str, None)
        scores[bug_id_str]['popularity'] = p_scores.get(bug_id_str, None)
        scores[bug_id_str]['exploitability'] = e_scores.get(bug_id_str, None)

    # store analysis for each bug
    summary = []
    call_for_each_bug(bug_cache_dir, 
            partial(store_analysis, summary, scores, bug_cache_dir, analysis_dir))

    # store summary for all bugs (used by report javascript, hopefully)
    json.dump(summary, open("%s/summary.json" % analysis_dir, "wt"), indent=4)

    return scores
