from audioop import add
import os, glob

POWER_OF_PAGE = 12
PAGE_MASK = (1 << POWER_OF_PAGE) - 1
PRIVATE_BITS = 7
TOTAL_WRITES = 0

bench = '500.perlbench_r'

write_histo = dict()
num_cachelines_histo = dict()

class simple_entry:
    def __init__(self):
        self.shared_counter = 0
        self.private_counters = [0] * 64
    
    def increment_counter(self, cacheline_id):
        global TOTAL_WRITES
        TOTAL_WRITES += 1
        self.private_counters[cacheline_id] += 1
        if self.private_counters[cacheline_id] > (1 << PRIVATE_BITS) - 1:
            self.shared_counter += 1
            self.private_counters[cacheline_id] = 0
            return True
        
        return False

entry_map = dict()


def parse_trace(trace):
    try:
        timestamp, controller, func, _, rw, _, address = trace.split()
    except:
        print(trace.split())
        exit(0)
    address = int("0x" + address, 16)
    page_id = (address >> POWER_OF_PAGE) << POWER_OF_PAGE
    cacheline_id = (address & PAGE_MASK) // 64

    if page_id not in entry_map:
        entry_map[page_id] = simple_entry()
    
    return 'W' in rw and entry_map[page_id].increment_counter(cacheline_id)

traces_list = []

for filename in glob.glob(f'/mnt/sda/spec/end_to_end_trace/{bench}/*.trace'):
    with open(os.path.join(os.getcwd(), filename), 'r') as f: # open in readonly mode
        traces_list.append([line for line in f])

max_len = max([len(i) for i in traces_list])

for j in range(max_len):
    i = j % max_len
    for traces in traces_list:
        if i < len(traces):
            traces[i] = traces[i].replace('\n', ' ' + str(int(parse_trace(traces[i]))) + '\n')
            # parse_trace(traces[i])

# for filename, traces in zip(glob.glob('traces/*.trace'), traces_list):
#     with open(os.path.join(os.getcwd(), filename + '.annotated'), 'w') as f:
#         for trace in traces:
#             f.write(trace)

with open(f'traces/summary_stats_{bench}.txt', 'w') as f:
    total_overflows = 0
    m = 0
    all_written_once = 0
    for entry in entry_map:
        total_overflows += entry_map[entry].shared_counter
        num_cachelines = 0
        all_one = 1
        for private_counter in entry_map[entry].private_counters:
            all_one &= private_counter
            if private_counter not in write_histo:
                write_histo[private_counter] = 0
            write_histo[private_counter] += 1

            m = max(m, private_counter)
            if private_counter > 0:
                num_cachelines += 1
        
        if num_cachelines not in num_cachelines_histo:
            num_cachelines_histo[num_cachelines] = 0
        num_cachelines_histo[num_cachelines] += 1

        if all_one == 1:
            all_written_once += 1


    f.write(f"Max writes: {m}\n")
    f.write(f"Total writes: {TOTAL_WRITES}\n")
    f.write(f"All written once pages: {all_written_once}\n")
    f.write(f"Total pages: {len(entry_map)}\n")
    f.write(f"Total overflows: {total_overflows}\n\n")
    f.write('Write Histo\n')
    write_histo = dict(sorted(write_histo.items()))
    for key in write_histo:
        f.write(f'{key} {write_histo[key]}\n')
    f.write('\n')

    num_cachelines_histo = dict(sorted(num_cachelines_histo.items()))
    f.write('Num Cachelines Histo\n')
    for key in num_cachelines_histo:
        f.write(f'{key} {num_cachelines_histo[key]}\n')
    f.write('\n')

    f.write("Page | Overflows\n")

    for entry in entry_map:
        f.write(f"{hex(entry)} {entry_map[entry].shared_counter}\n")
