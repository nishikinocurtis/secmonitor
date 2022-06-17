import json
import csv

def generate_seccomp(generate_name):
	# read default SECCOMP configuration file
	F = open("default.json", "r")
	config = json.load(F)
	F.close()

	# generate syscalls list
	Statistics = open("syscalls.json", "r")
	syscall_statistics = json.load(Statistics)
	Statistics.close()

	Syscalls = open("syscall_ids.json", "r")
	syscall_map = json.load(Syscalls)
	Syscalls.close()

	syscall_whitelist = []
	for item in syscall_statistics["syscall_list"]:
		syscall_id = item["syscall_id"]
		syscall_name = syscall_map[str(syscall_id)]
		syscall_whitelist.append(syscall_name)

	config["syscalls"][0]["names"] = syscall_whitelist
	F = open(generate_name, "w")
	json.dump(config, F)
	F.close()

if __name__ == "__main__":
	generate_seccomp("secmonitor.json")