import os, subprocess, shlex, json, logging

log = logging.getLogger()

def cache_popularity(cachedir):
    # download file; could get zipped version
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    path = "http://popcon.ubuntu.com/by_inst"
    fpath = "%s/by_inst" % cachedir
    cmd = "wget \"%s\" -O \"%s\"" % (path, fpath)
    subprocess.check_call(shlex.split(cmd))

    # parse file into json object
    out = []
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
        out.append(item)
    json.dump(out, open("%s/popularity.json" % cachedir, "wt"), indent=4)
