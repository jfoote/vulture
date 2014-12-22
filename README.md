# vulture

Analyzes open source bug trackers for interesting vulnerabilites. See [the latest report](https://s3.amazonaws.com/vulture88/index.html?sorts%5Bdate_modified%5D=-1&sorts%5Binstalls%5D=-1) for an example.

**WARNING: This code is a mess and has not been factored for maintainability or consumption by others in general.**

*Very unpolished: you'll almost definitely need to read the source code to figure out how to use this*

This implementation assumes it is running in an EC2 instance with a role that has access to the 'vulture88' bucket. I'm sorry. If you're interested in how this came to be, how it works, or if you want to collaborate on pushing it forward [drop me a line](jmfoote@loyola.edu).

## How it works

Vulture runs on an EC2 node. The script downloads bug info from public trackers for the time period since it was last run. The script then runs some analysis (see below) over the dataset and produces a JSON file. The JSON file and an html file that points to it are uploaded to an S3-hosted static site for consumption.

## The story (adapted from an email)

A while back I had a suspicion that there was untapped 0day circulating as public bugs in open source trackers. Despite many other obligations curiosity started to get the better of me so I hacked together a tool to probe ubuntu’s bug tracker for 0day as an after-hours project. I got partway there before I stepped back and adjusted to focus my after-hours research on more tangible defensive problems. 

## Status stuff 

unpolished, circa sometime during summer 2014

### Some things that are done
- 'analyze' does this:
    - generates a json file for each bug that shows more detailed analysis 
        - should correspond to a per-bug analysis page
    - generates a summary json file 
        - should correspond to the main page, made into a table by dynatable
- 'publish' does this:
    - copies the summary + report HTML to s3

### TODOs
- fix "ubuntu" project parsing
    - ubuntu not found in popcon -- bad sign
- add recv/etc. checks to vulture
- debug existing issues
- fix bug: bugs in vulture are not associated with all of their projects, only one
- generate and merge in "default handler" database (could use true/false, as well as ProcCmd from launcher) [started]
- add better search fields, etc. to dynatable page (also make sure GA is working)
    - just being able to stack searches/filters should be good enough
- add ubuntu version to fields (filterable), if possible

## Design stuff

### Guidelines
- the idea is to show the values for each bug on the front page so the user can tune up the bugs they want
- may want to give more bg on the bug on the main page.. project titles, etc., but don't go overboard (it needs to fit on the width of a screen) (could make column names short, maybe)

### will sort by "interestingness," broken into these categories:

- exploitability
    - remotely exploitable
        - reasonining:
            1. "is this remotely exploitable" becomes..
            2. "was this bug triggered by handling input that is considered untrusted" and/or 
            3. "does this program handle untrusted input"
        - handles untrusted input
            - takes file param +1
            - handles mime types +1 for each
            - is default handler +1
            - is default handler and is installed by default +5
            - recv/ libc::open/libc::open64 in crashing backtrace
            - recv/open in any backtrace

- reproducibility
    - input file is attached to bug tracker
    - input file is available via google
    - ProcCmd takes a file
    - maybe "confirmed" launchpad status

- freshness
    - recency/likelihood of because unnoticed/a mistake ; unpatchedness
    - launchpad status
    - date created
    - date last modified

- popularity
    - ubuntu popularity contest (popcon) stats for project. see [here](http://popcon.ubuntu.com/)
    - installed by default in ubuntu (see my blog post)

### other plans

- don't worry about users/editing -- leave that to launchpad, bugzilla, etc. (why re-invent the wheel?)
- should be able to be run nightly to generate report/publish to website
- Red Hat bugzilla integration; [looks like ABRT's backtrace file supplies enough for exploitability analysis](https://bugzilla.redhat.com/show_bug.cgi?id=1048457)

### related research

- found a paper from dawn song, et. al. that only ended up being a tech report, talking about doing ML on firefox to find security patches: [how open should open source be](http://www.eecs.berkeley.edu/Pubs/TechRpts/2011/EECS-2011-98.html)
- how abrt does exploitability analysis [here](https://github.com/abrt/abrt/blob/1fe8dc16e855c7802ed57cd5b47a11235dc53b07/src/plugins/abrt-gdb-exploitable)
    - note the link above may not be 'master' (it is now)
    - it does a pretty good job; is opcode aware; based loosely on my plugin : )
        - vulture could edge it out (it can resolve addrs, etc.) but i'm not sure how important that will be; other 'interestness metrics' may prevail over automated exploitability analysis
- how apport does exploitability analysis can be found via 'apt-get source apport' and then look for parse\_segv.py
    - confuses src/dst at times (is not opcode aware)
    - in some cases not too great

### making analyze self-explanatory, automatically

- the idea here is to allow a user to click on something on the per-bug page that will lead them through the logic used to arrive at conclusions
    - was originally thinking of exploitability 'tags', though for this to be worth the effort this should be generalizble
- could instrument execution to record traces ; see trace.py
    - records just calls (with args) and conditionals (with args)
    - after i got it working i looked at the output and decided it needed context
- record/replay python execution traces
