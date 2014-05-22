import os, json

import logging
log = logging.getLogger()

from vlib.analyzers import exploitability, freshness

def analyze(bug_cache_dir, analysis_dir, popularity_cache_dir):
    results = {}
    # each analysis function should return dict of scores by bug:
    # {'192492' : 5 }
    # get scores for each metric
    scores = freshness.get_scores(bug_cache_dir, popularity_cache_dir)
    for bug_id_str, score in scores.items():
        results[bug_id_str] = {}
        results[bug_id_str]['freshness_score'] = score
        
    scores = exploitability.get_scores(bug_cache_dir)
    for bug_id_str, score in scores.items():
        results[bug_id_str]['exploitability_score'] = score

    # for each bug, combine scores
    for bug_id_str, scores in results.items():
        bugdata = results[bug_id_str]
        cscore = bugdata['freshness_score'] * 2 +\
                 bugdata['exploitability_score'] * 1
        bugdata['combined_score'] = cscore

    return results
