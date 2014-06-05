import os, json, logging

from functools import partial

log = logging.getLogger()

from vlib.analyzers import exploitability, freshness, popularity, reproducibility
from vlib.analyzers.tools import call_for_each_bug
from vlib.supertrace import SuperTrace

def store_analysis(summary_dict, analyzers, bug_cache_dir, analysis_dir, popularity_dict, bugdir):

    # mirror bug_cache_dir structure in analysis_dir
    dir_tail = bugdir[len(bug_cache_dir):]
    dir_tail = dir_tail.strip("/")
    out_dir = "%s/%s" % (analysis_dir, dir_tail)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    metadata = json.load(open("%s/vulture.json" % bugdir, "rt"))

    #st = SuperTrace()
    #st.start()
    #st.stop()
    #log.debug("supertrace LEN!!!=%d" % len(st.results))
    #st.dump("%s/trace.json" % out_dir)

    bug_id_str = bugdir.split("/")[-1]
    results = {}
    bugrow = {}
    bugrow['detail'] = '<a href="http://s3.amazonaws.com/vulture88/bug.html?%s">%s</a>' % (bug_id_str, bug_id_str) #TODO fix this to relative path (via https) once i upload js/css to S3
    bugrow['title'] = "<a href='%s'>%s</a>" % (metadata['web_link'], metadata['title'])

    if 'popularity' in analyzers:
        pop = popularity.get(metadata, popularity_dict)
        results['popularity'] = pop
        bugrow['installs'] = pop['sum_inst']
    if 'freshness' in analyzers:
        fresh = freshness.get(metadata)
        results['freshness']  = fresh
        bugrow['date_modified'] = fresh['date_last_updated']
        bugrow['date_created'] = fresh['date_created']
        bugrow['status'] = "<br>".join(["%s: %s" % (pn, md['status']) for pn, md in fresh['project_metadata'].items()])
        bugrow['status_score'] = fresh['best_status_score']

    if 'exploitability' in analyzers:
        exp = exploitability.get(bugdir)
        results['exploitability'] = exp 
        bugrow['exp_rank'] = exp.ranking[0] if exp else 100
        bugrow['exp_tags'] = ',<br>'.join([t.split()[0] for t in exp['tags']]) if exp else ""

    if 'reproducibility' in analyzers:
        repro = reproducibility.get(metadata, bugdir)
        results['reproducibility']  = repro
        bugrow['file_arg'] = repro['cmdline_uri'] if bool(repro['cmdline_uri']) else "None"
        bugrow['testcases'] = "<br>,".join(repro['files'])
        bugrow['repro_score'] = int(bool(repro['files'])) + int(bool(repro['cmdline_uri']))
 
    json.dump(results, open("%s/analysis.json" % out_dir, "wt"), indent=4)
    summary_dict[bug_id_str] = bugrow

def analyze(bug_cache_dir, analysis_dir, popularity_cache_dir, limit=None, analyzers=[], buglist=[]):
    '''
    This function should cache a JSON object corresponding to the
    data that will be used on index.html: bug_id, bug_title, <metric ranks>
    If analyzers is set, will run only the specified analyzers 
    If buglist is set, will analyze only those bugs and merge them into existing
    summary (if it exists)
    '''
    popularity_dict = json.load(open("%s/popularity.json" % popularity_cache_dir, "rt"))

    if buglist:
        summary_dict = json.load(open("%s/summary_dict.json" % analysis_dir, "rt"))
    else:
        summary_dict = {}

    # gather/store analysis for each bug
    call_for_each_bug(bug_cache_dir, 
            partial(store_analysis, summary_dict, analyzers, bug_cache_dir, analysis_dir, popularity_dict), limit, buglist)

    # store summary for all bugs: first store dict, then stores as rows for use by dynatable
    json.dump(summary_dict, open("%s/summary_dict.json" % analysis_dir, "wt"), indent=4)
    json.dump(summary_dict.values(), open("%s/summary.json" % analysis_dir, "wt"), indent=4)

    return summary_dict
