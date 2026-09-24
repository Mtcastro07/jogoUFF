import re

def parse(filename):
    with open(filename) as f:
        lines = f.readlines()
    
    code = []
    
    for line in lines:
        if line.startswith("Disassembly"): continue
        if line.strip() == "": continue
        
        m = re.search(r'^\s*(\d+)?\s+([A-Z_]+)\s+(\d+)\s+(\(.*\))?', line)
        if m:
            lineno = m.group(1)
            op = m.group(2)
            arg = m.group(3)
            argval = m.group(4)
            # just print it for now to see if regex works
    
