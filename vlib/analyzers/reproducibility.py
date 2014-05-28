import json, logging, os, re, subprocess, shlex

from tools import get_category_by_status

log = logging.getLogger()

meta_files = ['Disassembly', 'Stacktrace', 'Registers', 
        'SegvAnalysis', 'ProcMaps', "BootLog" , "CoreDump", 
        "BootDmesg", "syslog", "UbiquityDebug.gz", "Casper.gz",
        "UbiquityPartman.gz", "UbiquityDm.gz", "GdmLog", "XorgLog"
        "log", "Log"]

def get(metadata, bugdir):
    indicators = {}

    # look for file arg; this needs work TODO
    cmdline = None
    uri = None
    for line in metadata['description'].splitlines():
        if "proccmdline" in line.lower():
            cmdline = ":".join(line.split(":")[1:]).strip()
            try:
                toks = shlex.split(cmdline)
            except ValueError as e:
                log.error("error while parsing cmdline: %s" % cmdline)
                log.exception(e)
                continue
            if len(toks) > 1:
                if ("//" in toks[-1]) or ("." in toks[-1]):
                    uri = toks[-1].strip()
    indicators['cmdline'] = cmdline
    indicators['cmdline_uri'] = uri

    # look for interesting attachments; ugly
    interesting_files = []
    for f in os.listdir(bugdir):
        fpath = os.path.join(bugdir, f)
        if not os.path.isfile(fpath):
            continue
        for fn in meta_files:
            if fn.lower() in f.lower():
                break
        else:
            # no break in loop above, i.e. still interested
            out = subprocess.check_output(["file", fpath])
            ftype = out.split(":")[-1]
            if ftype.strip() == "empty":
                continue
            
            for tstr in ["ASCII", "text", "core file"]:
                if tstr in ftype:
                    break
            else:
                # only runs if we didn't break, i.e., this might be interesting
                interesting_files.append(f)
    indicators['files'] = interesting_files

    # TODO: look for recv, etc. in stacks (shoudl this be in exploitability maybe (remote?))

    return indicators
