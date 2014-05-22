from vlib.analyzers.exploitability.exploitable import exploitable

def analyze(root):
    target, c = exploitable(root)
    return c
