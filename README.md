# SecMonitor



## Introduction

SecMonitor is a concise eBPF-based Monitor for Container, which **eliminates the dependence** on specific kernel version and syscall type (though must supports eBPF). As a dynamic analysis tool, SecMonitor cannot ensure 100% accuracy of correct minimum previleges set. So we also decoupled the Tester as an independent thread, which brings potential flexibility of creating customized test scripts based on container types and functions.

### Key Features

- 大幅安全性提升. 通过对容器行为的观测, 将容器获准的系统调用数目从默认的200+个降低至几十或十余个, 极大降低安全风险.

- 低性能开销. 基于Linux内核的`SYS_ENTER`追踪点, 实现对系统调用进入点的抽象, 相较于为400+个系统调用分别挂载追踪程序, 只需挂载1个BPF程序, 极大降低内核负载.

- 开箱即用. 用户无需了解BPF技术和编写BPF程序即可获得应用的推荐配置和行为报告, 并可直接用于容器的后续部署.

- 无内核版本依赖. 可运行在任何引入了eBPF的Linux内核上, 不依赖具体的内核版本, 即使系统调用有增删变化也能正常工作.

- 对容器透明. SecMonitor运行在目标容器外, 对容器运行不产生影响. 在此基础上, 可以从用户视角编写模拟脚本, 或直接运行已有的单元测试.

## Architecture

![arch](/assets/archu.svg)

The architecture of SecMonitor. 

- Docker Client utilizes Docker Python SDK to launch certain container and reports information of processes inside the container. 
- Emulator runs as an independent thread and execute proper test scripts to stimulate the container, making it perform as many system calls as possible.
- Monitor loads the BPF C code into the eBPF environment in the kernel through BCC, and consumes the output of our BPF Program through BCC's API. It produces a statistics file after the monitoring is stopped.
- Analyzer reads the default SECCOMP configuration, a syscall table of current kernel version, and the statistics file produced by Monitor, and generates a secure and accurate SECCOMP Config File.

Chinese description of the architecture:

### 系统操作时序

为确保BPF观测到的系统调用记录无遗漏, SecMonitor确定了系统内不同操作的时序, 在架构图中用括号数字标注. 

1. 首先由Monitor向内核中挂载BPF C代码并开始监测, 获得的信息暂时在PERF Buffer中缓存. 
2. 随后Docker Client启动容器, 并利用docker SDK获取进程列表, 提供给Monitor作为filter. 
3. 容器启动后, 同时启动Emulator进程, 模拟真实环境对容器发起多种业务请求. 
4. 获得进程信息后, Monitor开始从缓存中拉取(pull)BPF记录并处理, 一段时间后观测终止, 生成中间文件(Statistics File). 
5. Analyzer最后启动, 读取中间文件, SECCOMP默认配置和系统调用映射表等必要信息, 为用户生成可读报告和新的SECCOMP配置文件.

### 模块功能描述

- Monitor: 主线程. 向内核挂载BPF程序, 读取并处理内核返回的观测信息
- Docker Client: 启动容器, 并生成进程信息, 提供给Monitor
- Emulator: 独立线程. 加载合适的业务环境模拟脚本, 向容器发起业务请求.
- Analyzer: 尾部调用. 读取系统信息, SECCOMP配置模板, 中间统计文件等, 为用户生成最终报告和新的配置文件.

## Usage

### Dependency

python packages:

```
docker-py
bcc
```

system requirements:

```
Docker
linux kernel >= 5.0.0
```

### Run

```bash
./monitor.py -i|--image <image-name> [-d|--display] [-t|--test <test_script.py>] [-c|--config <docker_config>] [-l|--log <log_address>] [-o|--output <statistics_output_address>] [-g|--generate [config_generation_address]]
```

- ```-i```: Required. Setting docker image name to run and monitor.
- ```-d```: Optional. Whether display every captured syscall records into logs. Default is True.
- ```-t```: Optional. Setting customized test script to run.
- ```-c```: Optional. Setting docker configuration, a json file.
- ```-l```: Optional. Setting log file address, default secmon.log
- ```-o```: Optional. Setting statistics file output address.
- ```-g```: Optional. Whether generate the SECCOMP config file for the monitored container. One may use ```generate.py``` later to do this.

```bash
./generate.py <statistics_file> [-o|--output <config_generation_address>]
```

- ```statistics_file```: Required. Setting the statistics file to be analyzed.
- ```-o```: Optional. Setting SECCOMP config file output address. Default address is the same as statistics file, named ```<statistics_file>_secmonitor.json```

```bash
./arch.py
```

- Generating syscalls id-name mapping table by kernel version and architecture.

## Examples

The following example monitors the behavior of a plain nginx container when responding to a GET request.

### Operations

- test\_case\_1.py:

```python
import requests

ret = requests.get("http://127.0.0.1:8080/")
print(ret.text)
```

![ops](/assets/terminal.png)

### Results

- syscalls.json

![syscalls](/assets/statistics.png)

- secmon.log

![log](/assets/log.png)

- secmonitor.json

![log](/assets/seccomp.png)

Compared with the default whitelist in [the default SECCOMP config](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json), we have decreased the number from 200+ to only 21.

The following example shows how to generate a syscall id-name mapping table using `arch.py`. (On Linux 5.14, x86 platform.)

### Operations

![archg](/assets/arch.png)

### Results

![tbl](/assets/table.png)
