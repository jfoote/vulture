import json, logging, os, re, subprocess, shlex

from tools import get_category_by_status

log = logging.getLogger()

def get(metadata, bugdir):
    sum_inst = 0
    indicators = {}
    for line in metadata['description'].splitlines():
        if "proccmdline" in line.lower():
            indicators['ProcCmdLine'] = ":".join(line.split(":")[1:]).strip()
            break
    else:
        log.info("No ProcCmdLine for %s" % bugdir)
        print "\n".join(metadata['description'].splitlines())
        import pdb; pdb.set_trace()

    for f in os.listdir(bugdir):
        fpath = os.path.join(bugdir, f)
        if not os.path.isfile(fpath):
            continue
        if "BootLog" in f or "CoreDump" in f or "BootDmesg.gz" in f:
            continue
        out = subprocess.check_output(["file", fpath])
        ftype = out.split(":")[-1]
        if ftype.strip() == "empty":
            continue
        
        for tstr in ["ASCII", "text", "core file"]:
            if tstr in ftype:
                break
        else:
            # only runs if we didn't break, i.e., this might be interesting
            print out
            import pdb; pdb.set_trace()


        


    return indicators
