from vlib.analyzers.exploitability.exploitable import exploitable

def analyze(bug_cache_dir, analysis_dir):
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)

    for root, dirs, files in os.walk(bug_cache_dir, topdown=True):
        log.debug("processing %s" % root)
        analysis = {}
        project = root.split("/")[-2]
        try:
            target, c = exploitable(root)
            analysis['exploitability'] = c

            dpath = "%s/%s"
            json.dump(TODO)
        except Exception as e:
            log.exception(e)
            continue
    # TODO: this should also get other types of analysis (reproducibility, etc.) and merge result
