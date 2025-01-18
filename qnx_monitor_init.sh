rm -rf /fota/qnx_gpu.log
echo gpu_perf_governor 1 > /dev/kgsl-control
echo gpu_set_log_level 4 > /dev/kgsl-control
echo gpubusystats 1000 > /dev/kgsl-control
slog2info -b KGSL -w | grep measurement > /fota/qnx_gpu.log