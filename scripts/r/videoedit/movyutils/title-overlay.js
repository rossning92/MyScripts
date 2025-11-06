import * as mo from "movy";

var titleCount = 0;
export function addTitleOverlay(
  text1,
  text2,
  {
    titleHeight = 1.4,
    titleFontSize = 0.7,
    supHeight = 0.6,
    supFontSize = 0.3,
    width,
    exit = false,
    x,
    y,
    z,
    t,
    titleDuration = 2,
    exitAnimationType = "conceal", // "conceal" | "fadeOut",
    dimBackground = true,
    dimOpacity = 0.9,
  } = {}
) {
  if (width === undefined) {
    width =
      [...text1]
        .map((x) => (/[a-zA-Z ]/.test(x) ? 0.5 : 1))
        .reduce((a, b) => a + b) + 3;
  }

  const halfTotalHeight = (titleHeight + supHeight) * 0.5;

  const y1 = halfTotalHeight - titleHeight * 0.5;
  const g = mo.addGroup({ x, y, z });

  titleCount++;
  mo.addMarker(`title${titleCount}`, t);

  let overlay;
  if (dimBackground) {
    overlay = g
      .addRect({
        width: 20,
        height: 20,
        opacity: dimOpacity,
        z: 0.05,
        color: "black",
      })
      .fadeIn({ t });
  }

  const titleRect = g
    .addRect({
      width,
      height: titleHeight,
      color: "#56008d",
      y: y1,
      z: 0.1,
    })
    .revealU({
      ease: "power2.inOut",
      t: "<",
    });
  const titleText = g
    .addText(text1, {
      font: "gdh",
      color: "white",
      scale: titleFontSize,
      y: y1,
      z: 0.2,
    })
    .revealR({
      ease: "power2.inOut",
      t: "<0.1",
    });

  const y2 = -(halfTotalHeight - supHeight * 0.5);
  const supRect = g
    .addRect({
      width,
      height: supHeight,
      color: "#ffffff",
      y: y2,
      z: 0.1,
    })
    .revealD({
      ease: "power2.inOut",
      t: "<0.25",
    });
  const supText = g
    .addText(text2, {
      color: "black",
      scale: supFontSize,
      y: y2,
      z: 0.2,
      font: "gdh",
    })
    .revealL({
      ease: "power2.inOut",
      t: "<0.1",
    });

  if (exit) {
    if (exitAnimationType === "conceal") {
      titleRect.concealU({
        t: `<${titleDuration}`,
        duration: 0.5,
        ease: "power2.inOut",
      });
      titleText.concealR({ t: "<", duration: 0.5, ease: "power2.inOut" });
      supRect.concealD({ t: "<0.1", duration: 0.5, ease: "power2.inOut" });
      supText.concealL({ t: "<", duration: 0.5, ease: "power2.inOut" });
    } else {
      titleRect.fadeOut({
        t: `<${titleDuration}`,
        duration: 0.5,
      });
      titleText.fadeOut({ t: "<0.05", duration: 0.5 });
      supRect.fadeOut({ t: "<0.05", duration: 0.5 });
      supText.fadeOut({ t: "<0.05", duration: 0.5 });
    }
    if (dimBackground) {
      overlay.fadeOut({ t: "<0.05", duration: 0.75 });
    }
  }

  return g;
}
