import json, logging

log = logging.getLogger()

def get_freshness(bugdir, popularity):
    metadata = json.load(open("%s/vulture.json" % bugdir, "rt"))
    result = {'popularity' : {} }

    # get popularity 
    for pn in metadata['project_metadata'].keys():
        total += 1
        pop = popularity.get(pn, None)
        if not pop:
            log.warning("%s not found in popcon dataset" % pn)
            continue
        result['popularity'][pn] = pop
