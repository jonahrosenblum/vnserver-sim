from audioop import add
import os, glob

POWER_OF_PAGE = 12
PAGE_MASK = (1 << POWER_OF_PAGE) - 1
PRIVATE_BITS = 6

class simple_entry:
    def __init__(self):
        self.shared_counter = 0
        self.private_counters = [0] * 64
    
    def increment_counter(self, cacheline_id):
        self.private_counters[cacheline_id] += 1
        if self.private_counters[cacheline_id] > (1 << PRIVATE_BITS) - 1:
            self.shared_counter += 1
            self.private_counters[cacheline_id] = 0
            return True
        
        return False

entry_map = dict()


def parse_trace(trace):
    timestamp, controller, func, _, rw, _, address, _, latency = trace.split()
    address = int("0x" + address, 16)
    page_id = (address >> POWER_OF_PAGE) << POWER_OF_PAGE
    cacheline_id = (address & PAGE_MASK) // 64

    if page_id not in entry_map:
        entry_map[page_id] = simple_entry()
    
    return 'W' in rw and entry_map[page_id].increment_counter(cacheline_id)

traces_list = []

for filename in glob.glob('traces/*.trace'):
    with open(os.path.join(os.getcwd(), filename), 'r') as f: # open in readonly mode
        traces_list.append([line for line in f])

max_len = max([len(i) for i in traces_list])

for i in range(max_len):
    for traces in traces_list:
        if i < len(traces):
            traces[i] = traces[i].replace('\n', ' ' + str(int(parse_trace(traces[i]))) + '\n')

for filename, traces in zip(glob.glob('traces/*.trace'), traces_list):
    with open(os.path.join(os.getcwd(), filename + '.annotated'), 'w') as f:
        for trace in traces:
            f.write(trace)
