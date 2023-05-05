import { execSync } from "child_process";

// https://stackoverflow.com/questions/16726779/how-do-i-get-the-total-cpu-usage-of-an-application-from-proc-pid-stat
async function getCpuUsageProc({ pid, samples = 10 } = {}) {
  const clkTck = parseInt(
    execSync(`adb shell getconf CLK_TCK`).toString().trim(),
    "10"
  );

  let prevTicks = null;
  let past = null;
  const result = [];

  while (samples > 0) {
    const now = Date.now() / 1000;
    const out = execSync(`adb shell cat /proc/${pid}/stat`).toString().trim();

    const arr = out.split(" ");
    const utime = parseFloat(arr[13]);
    const stime = parseFloat(arr[14]);
    const ticks = utime + stime;

    if (prevTicks) {
      const cpuUtil = ((ticks - prevTicks) / clkTck / (now - past)) * 100;
      console.log(cpuUtil.toFixed(2));
      result.push(cpuUtil);
      samples--;
    }

    prevTicks = ticks;
    past = now;

    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  return result;
}

(async () => {
  try {
    const procName = process.env._PROC_NAME;
    const pid = execSync(`adb shell "pidof ${procName}"`).toString().trim();
    const values = await getCpuUsageProc({ pid: pid, samples: 10 });
    const avg = values.reduce((acc, val) => acc + val, 0) / values.length;
    console.log(`avg: ${avg}`);
  } catch (error) {
    console.error(`Failed to get PID: ${error}`);
  }
})();
