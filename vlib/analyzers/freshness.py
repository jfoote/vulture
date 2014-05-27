import logging

log = logging.getLogger()

from tools import get_score_by_status

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
