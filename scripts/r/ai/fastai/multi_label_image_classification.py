# https://docs.fast.ai/tutorial.vision.html#multi-label-classification

import matplotlib.pyplot as plt
from fastai.vision.all import *

path = untar_data(URLs.PASCAL_2007)
print(path.ls())

df = pd.read_csv(path / "train.csv")
print(df.head())


dls = ImageDataLoaders.from_df(
    df,
    path,
    folder="train",
    valid_col="is_valid",
    label_delim=" ",
    item_tfms=Resize(460),
    batch_tfms=aug_transforms(size=224),
    num_workers=0,  # Workaround for windows
)
# dls.show_batch()
# plt.show()

f1_macro = F1ScoreMulti(thresh=0.5, average="macro")
f1_macro.name = "F1(macro)"
f1_samples = F1ScoreMulti(thresh=0.5, average="samples")
f1_samples.name = "F1(samples)"
learn = vision_learner(
    dls, resnet50, metrics=[partial(accuracy_multi, thresh=0.5), f1_macro, f1_samples]
)
# learn.lr_find()

learn.fine_tune(2, 3e-2)
learn.save("tmpmodel")

learn.show_results()
plt.show()

print(learn.predict(path / "train/000005.jpg"))
