import * as mo from "movy";

export function addRedCross({ t, scale = 1.0 } = {}) {
  const g = mo.addGroup({ scale });
  g.addRect({
    width: Math.sqrt(2),
    height: 0.1,
    rz: -45,
    z: 1,
    color: "red",
  }).wipeIn({
    t,
  });
  g.addRect({
    width: Math.sqrt(2),
    height: 0.1,
    rz: 45,
    z: 1,
    color: "red",
  }).wipeIn({
    t: "<0.25",
    direction: "left",
  });
  return g;
}
