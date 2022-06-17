import platform
# check system type
if 'Linux' not in platform.system():
	raise OSError("Linux supported only")

# get architecture type and fetch syscall table
arch = platform.machine()
if "x86" in arch:
	arch = "x86"

tbl_path = arch + "/syscall_64.tbl"

itos = dict()
stoi = dict()
with open(tbl_path, "r") as F:
	lines = F.readlines()
	for line in lines:
		if line[0] not in "0123456789":
			continue
		words = line.split()
		itos[words[0]] = words[2]
		stoi[words[2]] = int(words[0])

import json
itos = json.dumps(itos)
with open("syscall_ids.json", "w") as W:
	W.write(itos)