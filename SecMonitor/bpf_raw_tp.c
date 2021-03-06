#define TASK_COMM_LEN 16
struct data_t {
    u64 cgroup_id;
    u32 syscall_id;
    u32 pid;
    char comm[TASK_COMM_LEN];
};
BPF_PERF_OUTPUT(events);


RAW_TRACEPOINT_PROBE(sys_enter)
{
    struct data_t data = {};

    data.pid = bpf_get_current_pid_tgid();
    data.cgroup_id = bpf_get_current_cgroup_id();
    data.syscall_id = (long)ctx->args[1];
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    events.perf_submit(ctx, &data, sizeof(data));
    
    return 0;
}
