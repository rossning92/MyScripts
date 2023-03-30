const { execSync } = require("child_process");

async function monitorCpuUsage() {
  let lastTotalIdle = null;
  const procName = process.env._PROC_NAME;

  let prevTicks = null;
  let past = null;

  for (let i = 0; i < 999999; i++) {
    const now = Date.now() / 1000;
    const out = execSync(`adb shell cat /proc/$(pidof ${procName})/stat`)
      .toString()
      .trim();

    const arr = out.split(" ");
    const utime = parseFloat(arr[13]);
    const stime = parseFloat(arr[14]);
    const ticks = utime + stime;

    if (prevTicks) {
      console.log(((ticks - prevTicks) / (now - past)).toFixed(2));
    }

    prevTicks = ticks;
    past = now;

    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}

monitorCpuUsage();
