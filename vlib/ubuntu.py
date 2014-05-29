import os, subprocess, shlex, json, logging

log = logging.getLogger()

def cache_popularity(cachedir, force=False):

    fpath = "%s/by_inst" % cachedir
    if not force and os.path.exists(fpath):
        log.debug("%s exists and force=%s, skipping download" % (fpath, force))
    else:
        # download file; could get zipped version
        if not os.path.exists(cachedir):
            os.makedirs(cachedir)
        path = "http://popcon.ubuntu.com/by_inst"
        cmd = "wget \"%s\" -O \"%s\"" % (path, fpath)
        subprocess.check_call(shlex.split(cmd)) 

    # parse file into json object
    out = {}
    fields = ['rank', 'name', 'inst', 'vote', 'old', 'recent', 'no-files']
    for line in open(fpath, "rt").readlines():
        line = line.strip()
        if line[0] == "#": # comment
            continue
        item = {}
        for word, field in zip(line.split()[:-1], fields):
            try:
                item[field] = word.strip().encode("UTF-8")
            except Exception as e:
                log.warning("error parsing by_inst; field=%s" % field)
                log.exception(e)
        if not item.get('name', False) or not item.get('inst', False):
            continue
        if int(item['inst']) < 100: # got all of the popular ones
            break

        out[item['name']] = item
    json.dump(out, open("%s/popularity.json" % cachedir, "wt"), indent=4)

def cache_desktop_entries(cachedir, force=False):
    import subprocess, shlex

    # get list of desktop entries from apt-file
    #subprocess.check_call(shlex.split("apt-file update"))
    print os.getcwd()
    out = subprocess.check_output("apt-file search desktop | grep /usr/share/applications", shell=True)
    pkgs = {}
    for line in out.splitlines():
        pkg = line.split(":")[0]
        fn = line.split("/")[-1]
        pkgs[pkg] = fn

    failures = []
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    tpath = "%s/tmp-src" % cachedir 
    for pkg, filename in pkgs.items():
        if not os.path.exists(tpath):
            os.makedirs(tpath)
        try:
            subprocess.check_call(shlex.split("apt-get source %s" % pkg), cwd=tpath)
            subprocess.check_call("cp `find %s -name \"%s*\"` %s" % (tpath, filename, cachedir), shell=True)
        except Exception as e:
            log.exception(e)
            failures.append((pkg, filename))
        finally:
            if os.path.exists(tpath):
                subprocess.check_call(shlex.split("rm -rf %s" % tpath))

    for pkg, filename in failures:
        log.warning("failed to get desktop entry for %s: %s" % (pkg, filename))



