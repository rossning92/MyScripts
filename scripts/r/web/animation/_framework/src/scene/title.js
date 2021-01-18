import yo from "yo";

yo.enableBloom();

const t = yo.add("编程", { font: "gdh", fontSize: 1.5, x:-3 });
t.reveal();

const t2 = yo.add("三分钟", { font: "gdh", fontSize: 1.5, x:2 });
t2.reveal();

yo.addGlitch({ t: 1 });
yo.addGlitch({ t: 1.5 });

yo.run();
