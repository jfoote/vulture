import json, logging

from tools import get_category_by_status

log = logging.getLogger()

def get(metadata, pop_dict):
    sum_inst = 0
    pops = {}
    for pn in metadata['project_metadata'].keys():
        pop = pop_dict.get(pn, None)
        if not pop:
            log.info("%s not found in popcon dataset" % pn)
            continue
        pops[pn] = pop
        cat = get_category_by_status(metadata['project_metadata'][pn]['status'])
        if cat != 'fixed':
            sum_inst += int(pop['inst'])
    pops['sum_inst'] = sum_inst
    return pops
