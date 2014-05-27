import logging

log = logging.getLogger()

def get_score_by_status(in_status):
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
    return score_by_status[in_status]

def get(metadata):

    bug_results = {}
    best_score = 0
    best_status = None

    # get project bug status
    metadata_by_proj = {}
    for pn, project_bug in metadata['project_metadata'].items():
        metadata_by_proj[pn] = {}
        metadata_by_proj[pn]['date_closed'] = project_bug['date_closed'][:10] # just y-m-d
        status = project_bug['status']
        metadata_by_proj[pn]['status'] = status
        score = get_score_by_status(status)
        metadata_by_proj[pn]['status_score'] = score
        if score > best_score:
            best_score = score
            best_status = status
        bug_results['project_metadata'] = metadata_by_proj
    bug_results['best_status_score'] = best_score
    bug_results['best_status'] = best_status

    # get modification info
    for field in ['date_created', 'date_last_updated']:
        bug_results[field] = metadata[field][:10] # just y-m-d

    return bug_results
