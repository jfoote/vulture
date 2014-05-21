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
        os.makedir(path)
    open(path, "wt").write("\n".join(projects))
    log.debug("cache written to %s" % path)

    return projects

def cache_bug_attachments(bug, dpath):
    import subprocess, shlex
    for attachment in bug.attachments:
        try:
            path = "%s/+files/%s" % (attachment.web_link, attachment.title)
            fpath = "%s/%s" % (dpath, attachment.title)
            log.debug("path=%s, fpath=%s" % (path, fpath))
            if "\"" in path or "'" in path:
                raise RuntimeError("funny character in path: %s" % path)
            cmd = "wget \"%s\" -O \"%s\"" % (path, fpath)
            if os.path.exists(fpath):
                log.info("%s found, skipping %s" % (fpath, cmd))
                return
            subprocess.check_call(shlex.split(cmd))
        except Exception as e:
            log.exception(e)
 
def cache_bug(bug, dpath):
    import json
    if not os.path.exists(dpath):
        os.makedir(dpath)
    metadata = get_metadata(bug)
    json.dump(open("%s/vulture.json" % dpath), metadata, indent=4)
    cache_bug_attachments(bug, dpath)

def get_metadata(bug):
    out = {}
    fields = ['title', 'web_link', 'security_related', 'date_created', 
            'date_last_updated', 'tags', 'description', 'target', 'target_name', 'target_display_name']
    for f in fields:
        out[f] = getattr(bug, f, "").encode("UTF-8")

    start = bug.title.find("crashed with ") + len("crashed with ")
    end = start + bug.title[start:].find(" ")
    sigtext = bug.title[start:end]
    out['sigtext'] = sigtext

    return out

def cache_bugs_for_projects(project_names, outdir, ffwd=""):
    import time, sys, os, subprocess, shlex
    import logging
    log = logging
    
    from launchpadlib.launchpad import Launchpad
    launchpad = Launchpad.login_anonymously('hello-world', 'production')
    
    def has_stack_trace(bug):
        '''
        Returns True if this bug report has an Apport-style stack trace attachment.
        Returns False otherwise.
        '''
        for attachment in bug.attachments:
            if attachment.title == "Stacktrace.txt":
                return True
        return False
    
    total_projects = len(project_names)
    i = 0
    start_time = time.time()
    
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    
    # iterate over all projects and log Apport crash bug report info
    for project_name in project_names:

        # fast-forward to project, if specified (resume)
        if ffwd and project_name != ffwd:
            log.debug("resume: skipping %s" % project_name)
            total_projects -= 1
            continue
        ffwd = None
    
        try:
            log.debug(project_name)
            pillar = launchpad.projects[project_name]
            
            #bugs = pillar.searchTasks(status=["Fix Committed", "Fix Released"])
            #bugs = pillar.searchTasks()
            bugs = pillar.searchTasks(status=["New", "Opinion", "Invalid", "Won't Fix", "Expired", "Confirmed", "Triaged", "In Progress", "Fix Committed", "Incomplete (with response)", "Incomplete (without response)"], tags='apport-crash') # TODO: maybe just iterate over distros and skip caching projects?
            for bug in bugs:
        
                # verify bug report was produced by Apport, w/ stack trace 
                if not "crashed with" in bug.title.lower():
                    continue

                # make dirs
                bug_id_str = str(bug).split("/")[-1]
                bug = launchpad.bugs[bug_id_str]
                if not has_stack_trace(bug):
                    continue
                dpath = "%s/%s" % (outdir, project_name)
                if not os.path.exists(dpath):
                    os.mkdir(dpath)
                dpath += "/%s" % bug_id_str
                if not os.path.exists(dpath):
                    os.mkdir(dpath)

                # download info
                cache_bug(bug, dpath)
           
            i += 1
            print "%d/%d, %f sec remaining" % (i, total_projects, 
                (time.time()-start_time)/i * (total_projects-i))
            sys.stdout.flush()
        except Exception as e:
            log.error("%s: %s" % (project_name, str(e)))
            log.exception(e)
    log.info("done")

def cache_all(outdir, force=False):
    projects = cache_project_names(outdir, force)
    cache_bugs_for_projects(projects, outdir)

def cache_bugs(cachedir, modified_since):

    from launchpadlib.launchpad import Launchpad
    launchpad = Launchpad.login_anonymously('hello-world', 'production')
    import pdb; pdb.set_trace()

    search_args = { 
            'modified_since' : modified_since, 
            'tags' : 'apport-crash' 
            }
    bug_ids = set()
    for distro in launchpad.distributions:
        import pdb; pdb.set_trace()
        for bug in distro.searchTasks(**search_args):
            bug_id_str = str(bug).split("/")[-1]
            if bug_id_str in bug_ids:
                continue
            bug_ids.add(bug_id_str)
            log.debug("caching modified bug: %s" % bug_id_str)
            bug_id_str = str(bug).split("/")[-1]
            cache_bug(bug, cachedir)
    log.debug("found %d updated bugs" % len(bug_ids))

    '''
    for root, dirs, files in os.walk(cachedir, topdown=True):
        if "launchpad-metadata.txt" in files:
            log.debug("processing %s" % root)
        project = root.split("/")[-2]
        bug_id = root.split("/")[-1]
        bug = launchpad.bugs[bug_id]
        try:
            outfile = open("%s/launchpad-description.txt" % root, "wt")
            outfile.write(bug.description.encode("UTF-8"))

        except Exception as e:
            #open(os.path.join(root, 'analysis-error.txt'), "at").write(str(e) + "\n")
            import pdb; pdb.set_trace()
            raise e
 
    '''
