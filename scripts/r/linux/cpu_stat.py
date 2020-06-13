from _shutil import *
from _math import *


core_names = []
total_idle = []
for i in range(10):

    sample = subprocess.check_output(
        'adb shell cat /proc/stat', universal_newlines=True)
    # print(sample)

    matches = re.findall('^(cpu.*?) (.*)', sample, flags=re.MULTILINE)

    total_idle_per_sample = []
    core_names.clear()
    for grps in matches:
        core_name = grps[0]
        ticks = [int(x) for x in grps[1].split()]

        total_ticks = np.sum(ticks)
        COL_IDLE = 3
        total_idle_per_core = np.array([total_ticks, ticks[COL_IDLE]])
        total_idle_per_sample.append(total_idle_per_core)
        core_names.append(core_name)

    total_idle.append(total_idle_per_sample)

    if i > 0:
        total_idle_diff = np.diff(np.array(total_idle), axis=0)

        # select gold core only
        # cores = [4, 5, 6, 7]
        # total_idle_diff = total_idle_diff[:, cores, ]

        cpu_util = np.apply_along_axis(
            lambda x: 1 - x[1] / x[0], -1, total_idle_diff)

        df = pd.DataFrame(cpu_util, columns=core_names)

        call2('cls')
        print(df.mean())

    time.sleep(1)


df.plot(kind='line')
plt.title('CPU Usage')
plt.ylabel('CPU Utilization')
plt.xlabel('Time Secs')
save_fig(size_inch=(12, 6))
