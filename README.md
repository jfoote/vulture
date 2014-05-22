vulture
=======

Analyzes open source bug trackers for interesting vulnerabilities

## TODO: will sort by "interestingness," broken into these categories:

- exploitability

- remotely exploitable
    - handles untrusted input
    - recv/ libc::open/libc::open64 in crashing backtrace
    - " / " / " in any backtrace

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

## other plans
- don't worry about users/editing -- leave that to launchpad, bugzilla, etc. (why re-invent the wheel?)
- should be able to be run nightly to generate report/publish to website

## tentative file layout
- vulture.py
- lib/
    - analyzers/
        - exploitabiliity/
        - freshness/
        - popularity/
        - reproducibility/

## big wants
- Red Hat bugzilla integration; [looks like ABRT's backtrace file supplies enough for exploitability analysis](https://bugzilla.redhat.com/show_bug.cgi?id=1048457)


## trade study
- found a paper from dawn song, et. al. that only ended up being a tech report, talking about doing ML on firefox to find security patches: [how open should open source be](http://www.eecs.berkeley.edu/Pubs/TechRpts/2011/EECS-2011-98.html)
- how abrt does exploitability analysis [here](https://github.com/abrt/abrt/blob/1fe8dc16e855c7802ed57cd5b47a11235dc53b07/src/plugins/abrt-gdb-exploitable)
    - note the link above may not be 'master' (it is now)
    - it does a pretty good job; is opcode aware; based loosely on my plugin : )
        - i can edge it out (i can resolve addrs, etc.) but i'm not sure how important that will be; other 'interestness metrics' may prevail over automated exploitability analysis
- how apport does exploitability analysis can be found via 'apt-get source apport' and then look for parse\_segv.py
    - confuses src/dst at times (is not opcode aware)
    - generally not too great
