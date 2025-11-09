import * as mo from "movy";

export function addSlideshow(
  imageUrls,
  { imageSize = 10, imageDuration = 2, imageZoom = 1.01 ** imageDuration } = {}
) {
  for (const [i, file] of imageUrls.entries()) {
    const image = mo
      .addImage(file, { scale: imageSize })
      .show()
      .moveTo({
        ease: "linear",
        scale: imageSize * imageZoom,
        duration: imageDuration,
      });

    if (i < imageUrls.length - 1) {
      image.hide();
    }
  }
}
