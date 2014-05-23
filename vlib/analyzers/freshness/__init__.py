import json, logging
from functools import partial

log = logging.getLogger()

def analyze_bug(results, bugdir): # results must be mutable (passed by ref)
    '''
    Post: results (a dict) stores 
    bug_id_str : 
        'project_metadata':
           'status' : status
           'date_closed' : date_closed
        'date_created' : date_created
        'date_last_updated' : date_last_updated
    yes, i should be using classes 
    '''

    metadata = json.load(open("%s/vulture.json" % bugdir, "rt"))
    bug_results = {}

    # get project bug status
    metadata_by_proj = {}
    for pn, project_bug in metadata['project_metadata'].items():
        metadata_by_proj[pn] = {}
        metadata_by_proj[pn]['status'] = project_bug['status']
        metadata_by_proj[pn]['date_closed'] = project_bug['date_closed'][:10]
        bug_results['project_metadata'] = metadata_by_proj

    # get modification info
    for field in ['date_created', 'date_last_updated']:
        bug_results[field] = metadata[field][:10] # just y-m-d

    # store results for this bug
    bug_id_str = bugdir.strip("/").split("/")[-1]
    results[bug_id_str] = bug_results

def get_score_by_status():
    # sort bug statuses for scoring
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
    return score_by_status


def get_rank_by_date_field(data_dict, field_name):
    '''
    returns a dict of 'bug_id_str' : rank (int)
    '''
    sorted_data = sorted(data_dict.items(), cmp=lambda a,b: cmp(a[1][field_name], 
        b[1][field_name]))
    scores = {}
    i = 0
    last = ""
    for bug_id_str, md in sorted_data:
        date = md[field_name][:10] 
        if date != last: 
            i += 1 # new day
        last = date
        scores[bug_id_str] = i

    return scores

def get_scores(bug_cache_dir):
    '''
    This function should cache a JSON object corresponding to the analysis data
    that will be shown on each bug-specific page: freshness "tags", freshness ranks
    '''
    from vlib.analyzers.tools import call_for_each_bug


    # get data we'll score on for each bug in bug_cache_dir (stored to results)
    metadata = {}
    call_for_each_bug(bug_cache_dir, partial(analyze_bug, metadata))

    # calculate date-related scores
    date_mod_ranks = get_rank_by_date_field(metadata, 'date_last_updated')
    date_created_ranks = get_rank_by_date_field(metadata, 'date_created')

    # calculate bug status score
    # score the 'best' status for any project each bug is in
    status_scores = {}
    score_by_status = get_score_by_status()
    for bug_id_str, bug_md in metadata.items():
        best_score = None
        for field, project_md in bug_md['project_metadata'].items():
            status = project_md['status']
            score = score_by_status[status]
            if best_score == None or score < best:
                best_score = score
        status_scores[bug_id_str] = best_score

    # store scores by bug_id_str
    scores = {}
    bug_id_strs = list(set(date_mod_ranks.keys() + date_created_ranks.keys() + status_scores.keys()))
    for bug_id_str in bug_id_strs:
        bscores = {}
        bscores['status'] = status_scores.get(bug_id_str, None)
        bscores['date_created'] = date_created_ranks.get(bug_id_str, None)
        bscores['date_last_updated'] = date_mod_ranks.get(bug_id_str, None)
        scores[bug_id_str] = bscores

    return scores


    '''
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
    '''
