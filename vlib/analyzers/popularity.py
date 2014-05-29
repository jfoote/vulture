import json, logging

from tools import get_category_by_status

log = logging.getLogger()

def get(metadata, pop_dict):

    # maybe the package name is the project name, so grab them
    packages = metadata['project_metadata'].keys()

    # search bug description for package name
    for line in metadata['description'].splitlines():
        line = line.strip()
        if "Package:" in line:
            package = line.split(":")[1].split()[0].strip()
            if package in packages:
                # this way the most-likely-correct package is always first
                packages.remove(package)
            packages.insert(1, package)
            break

    # get popularity for package
    sum_inst = 0
    pops = {}
    for pn in packages:
        pop = pop_dict.get(pn, None)
        if not pop:
            continue
        pops[pn] = pop

        # if we know this bug has been fixed, don't make this bug more 'popular'
        # NOTE: this may be counterintuitive wrt. to the key name 'insts'
        pmd = metadata['project_metadata'].get(pn, None)
        if pmd and get_category_by_status(pmd['status']).lower() == "fixed":
            continue

        sum_inst += int(pop['inst'])

    if len(pops.keys()) == 0:
        log.info("no popcon data for bug, packages are %s" % ",".join(packages))

    pops['sum_inst'] = sum_inst
    pops['packages'] = packages

    return pops
