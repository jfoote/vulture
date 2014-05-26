import json, logging
from functools import partial

log = logging.getLogger()

from vlib.analyzers.tools import call_for_each_bug

def get_scores(bug_cache_dir, popularity_cache_dir):
    '''
    inst = number of installs for each project (summed)
    if inst:
        score = max_inst - inst 
    else:
        score = max_inst/2
    '''
    log.debug("scoring")

    # load popularity (big) into memory
    popularity = json.load(open("%s/popularity.json" % popularity_cache_dir, "rt"))

    # aggregate data for each bug in bug_cache_dir
    results = {}
    results['maxs'] = {}
    call_for_each_bug(bug_cache_dir, partial(analyze_bug, popularity, results))
    maxs = results['maxs']
    del results['maxs']
    
    # turn population field sums into scores (lower score is better)
    # inst: high is good; rank: low is good; old: low (relative to inst) is good
    # recent: high (relative to inst) is good; vote: high is good
    # ALSO, if 
    scores = {}
    summed_fields = ['inst', 'rank', 'old', 'recent', 'vote']
    for bug_id_str, sums_by_popfield in results.items():
        scores[bug_id_str] = {}
        print sums_by_popfield

        # TODO: note that this logic works ONLY for 'inst' -- it is broken for other 
        # metrics (think about rank, etc.). If you're going to use others, fix this!
        for field in summed_fields:
            if not sums_by_popfield.get(field, None):
                scores[bug_id_str][field] = maxs[field] / 2
            else:
                scores[bug_id_str][field] = maxs[field] - sums_by_popfield[field]

    log.debug("done scoring")
    return scores

def analyze_bug(popularity, results, bugdir): # results must be mutable (passed by ref)
    # post: results[bug_id] = { projecta : popa, projectb : popb }

    metadata = json.load(open("%s/vulture.json" % bugdir, "rt"))
    summed_fields = ['inst', 'rank', 'old', 'recent', 'vote']

    # get popularity 
    sums_by_project = {}
    for pn in metadata['project_metadata'].keys():
        sums_by_field = {}
        pop = popularity.get(pn, None)
        if not pop:
            log.warning("%s not found in popcon dataset" % pn)
            pop = None
            continue
        for field in summed_fields:
            # add sum for this bug
            sums_by_field[field] = sums_by_field.get(field, 0) +\
                    int(pop[field]) 

            # increase max for each field if new one has been seen
            # (used in caller's scoring logic)
            rmax = results['maxs'].get(field, 0)
            if sums_by_field[field] > rmax:
                results['maxs'][field] = sums_by_field[field]
        sums_by_project[pn] = sums_by_field


    # store results for this bug
    bug_id_str = bugdir.strip("/").split("/")[-1]
    # ^^ yes i should do this in the tools function and pass it in 
    # since all callees do it
    results[bug_id_str] = sums_by_project


