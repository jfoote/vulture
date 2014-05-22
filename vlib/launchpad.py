import os, sys, subprocess, shlex, time, re, json

import logging
log = logging.getLogger()

from launchpadlib.launchpad import Launchpad
launchpad = Launchpad.login_anonymously('hello-world', 'production')

def cache_project_names(outdir, force=False, batch=300, total=34026): 
    # Quick-and-dirty script to scrape project names from Launchpad website. 
    # Used as a workaround to issue with Launchpad Python API that prohibits
    # looping over all projects via an iterator. Prints results to stdout.
    # total as of 2014-05-21; can be found by browsing "all projects"; could be scraped

    path = os.path.join(outdir, "projects.txt")
    if not force and os.path.exists(path):
        log.debug("cache found at %s" % path)
        return [p.strip() for p in open(path, "rt").read().split("\n")]

    for i in range(0, total, batch):
        uri = "https://launchpad.net/projects/+all?batch=%d&memo=%d&start=%d" % (batch, i, i)
        page = requests.get(uri)
        proj_count = 0
        lines = page.text.splitlines()
        projects = []
        for j in range(0, len(lines)):
            m = re.match("^[ ]*<a href=\"/(.*)\" class=\".*$", lines[j])
            if m:
                if j > 1 and "<div>" in lines[j-1]:
                    proj_count += 1
                    projects.append(m.groups()[0])
        if proj_count!= batch:
            log.warning("hiccup: proj_count=%d, batch=%d, uri=%s" % (proj_count, batch,
                uri))

    if not os.path.exists(path):
        os.mkdir(path)
    open(path, "wt").write("\n".join(projects))
    log.debug("cache written to %s" % path)

    return projects

def cache_bug_attachments(bug, dpath, force=False):
    import subprocess, shlex
    for attachment in bug.attachments:
        try:
            path = "%s/+files/%s" % (attachment.web_link, attachment.title)
            fpath = "%s/%s" % (dpath, attachment.title)
            # no launchpadlib for python3, so no shlex.quote :( hack:
            for p in [path, fpath]:
                for char in ["<", ">", " ", "(", ")"]:
                    p = p.replace(char, "\%s" % char)
            log.debug("path=%s, fpath=%s" % (path, fpath))
            if "\"" in path or "'" in path:
                raise RuntimeError("funny character in path: %s" % path)
            cmd = "wget \"%s\" -O \"%s\"" % (path, fpath)
            if not force and os.path.exists(fpath):
                log.info("%s found, skipping %s" % (fpath, cmd))
                return
            subprocess.check_call(shlex.split(cmd))
        except Exception as e:
            log.exception(e)
 

def cache_metadata(bug, bbug, dpath, force=False):
    metadata = get_metadata(bug, bbug)
    path = "%s/vulture.json" % dpath

    # if not forcing, merge new data into old data
    if not force and os.path.exists(path):
        log.debug("found existing metadata at %s, merging" % path)
        prev_metadata = json.load(open(path, "rt"))

        # merge old project-specific metadata into new metadata 
        project_name = str(bug).split("/")[-3]
        for k, v in prev_metadata.items():
            if k == "project_metadata":
                for pname, md in v.items():
                    if pname == project_name:
                        raise RuntimeError("already have metadata for project: %s" % pname)
                    metadata['project_metadata'][pname] = md
            elif prev_metadata[k] != metadata[k]:
                raise RuntimeError("non-project-specific metadata for bug %s does not match existing metadata for bug. key=%s, old_val=%s, new_val=%s" % (str(bug), k, prev_metadata[k], metadata[k]))

    json.dump(metadata, open(path, "wt"), indent=4)

def cache_bug(bug, dpath, force=False):
    bbug = bug.bug
    cache_metadata(bug, bbug, dpath, force)
    cache_bug_attachments(bbug, dpath, force)

def get_metadata(pbug, bbug):
    out = {}

    # get data from 'project' bug and add it to list
    pout = {}
    fields = ['date_closed', 'related_tasks', 'assignee', 'date_assigned', 'date_left_closed', 'date_fix_committed', 'date_fix_released', 'date_in_progress', 'status', 'bug_target_name', 'importance', 'date_triaged', 'bug_target_display_name', 'milestone', 'target', 'date_confirmed', 'date_left_new', 'bug_watch', 'date_incomplete', 'is_complete', 'web_link']
    for f in fields:
        val = getattr(pbug, f, "")
        if getattr(val, 'encode', False):
            val = val.encode("UTF-8")
        else:
            val = str(val).encode("UTF-8")
        pout[f] = val
    project_name = str(pbug).split("/")[-3]
    out['project_metadata'] = {project_name : pout}

    # get data from 'bug' bug
    fields = ['title', 'web_link', 'security_related', 'date_created', 
            'date_last_updated', 'tags', 'description', 'target', 'target_name', 'target_display_name']
    for f in fields:
        val = getattr(bbug, f, "")
        if getattr(val, 'encode', False):
            val = val.encode("UTF-8")
        else:
            val = str(val).encode("UTF-8")
        out[f] = val

    m = re.match("^.*(SIG[A-Z]+).*$", bbug.title)
    if m:
        out['sigtext'] = m.groups()[0]
    else:
        out['sigtext'] = "None"

    return out

# see https://help.launchpad.net/Bugs/Statuses
# and https://help.launchpad.net/Bugs/Statuses/External
valid_status = ["New", "Opinion", "Invalid", 
    "Won't Fix", "Expired", "Confirmed", "Triaged", 
    "In Progress", "Fix Committed", "Fix Released", 
    "Incomplete (with response)", "Incomplete (without response)", 
    "Incomplete"]
unreleased_status = list(set(valid_status) - set(["Fix Released"]))
 
def has_stack_trace(bug):
     '''
     Returns True if this bug report has an Apport-style stack trace attachment.
     Returns False otherwise.
     '''
     for attachment in bug.attachments:
         if attachment.title == "Stacktrace.txt":
             return True
     return False
  
def cache_bugs(cachedir, modified_since=None, force=False):

    search_args = { 
            'status' : unreleased_status,
            'tags' : 'apport-crash' 
            }
    if modified_since:
        search_args['modified_since'] = modified_since

    i = 0
    start_time = time.time()
    total = 30000 #sum([len(d.searchTasks(**search_args)) for d in launchpad.distributions]) SLOW!

    bug_ids = set()
    for distro in launchpad.distributions:
        log.debug("processing bugs for distro: %s" % distro)
        for bug in distro.searchTasks(**search_args):
            # TODO: may want to multi-thread this inner loop, a la downloader
            bug_id_str = str(bug).split("/")[-1]
            project_name = str(bug).split("/")[-3]
            if bug_id_str in bug_ids:
                i += 1
                continue
            if not has_stack_trace(bug.bug):
                log.debug("bug at %s was reported by apport, but doesn't have a stack trace" % bug.web_link)
                log.debug("bug attachments: %s" % ", ".join([a.title for a in bug.bug.attachments]))
                i += 1
                continue
            bug_ids.add(bug_id_str)
            dpath = "%s/%s" % (cachedir, bug_id_str)
            if not os.path.exists(dpath):
                os.makedirs(dpath)
            log.debug("caching bug: %s" % dpath)
            try:
                cache_bug(bug, dpath, force)
            except Exception as e:
                log.error("ERROR while caching bug %s to %s" % (str(bug), dpath))
                log.exception(e)
                raise e # TODO: may want to remove this

            i += 1
            log.debug("roughly: %d/%d, %f sec remaining" % (i, total, 
                (time.time()-start_time)/i * (total-i)))
            sys.stdout.flush()

    log.debug("found %d matching bugs" % len(bug_ids))
