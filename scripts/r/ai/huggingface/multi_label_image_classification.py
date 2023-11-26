# https://github.com/huggingface/notebooks/blob/main/examples/image_classification.ipynb

import argparse
import glob
import os
from pprint import pprint
from typing import List

import datasets
import numpy as np
import requests
import torch
from PIL import Image
from torchvision.transforms import (
    CenterCrop,
    Compose,
    Normalize,
    RandomHorizontalFlip,
    RandomResizedCrop,
    Resize,
    ToTensor,
)
from transformers import (
    AutoImageProcessor,
    AutoModelForImageClassification,
    Trainer,
    TrainingArguments,
    pipeline,
)

model_checkpoint = "microsoft/swin-tiny-patch4-window7-224"  # pre-trained model from which to fine-tune
batch_size = 32  # batch size for training and evaluation

model_name = model_checkpoint.split("/")[-1]


# fmt: off
image_extensions = {
    ".blp", ".bmp", ".dib", ".bufr", ".cur", ".pcx", ".dcx", ".dds", ".ps", ".eps", ".fit", ".fits", ".fli", ".flc",
    ".ftc", ".ftu", ".gbr", ".gif", ".grib", ".h5", ".hdf", ".png", ".apng", ".jp2", ".j2k", ".jpc", ".jpf", ".jpx",
    ".j2c", ".icns", ".ico", ".im", ".iim", ".tif", ".tiff", ".jfif", ".jpe", ".jpg", ".jpeg", ".mpg", ".mpeg",
    ".msp", ".pcd", ".pxr", ".pbm", ".pgm", ".ppm", ".pnm", ".psd", ".bw", ".rgb", ".rgba", ".sgi", ".ras", ".tga",
    ".icb", ".vda", ".vst", ".webp", ".wmf", ".emf", ".xbm", ".xpm"
}
# fmt: on


def fine_tunning_model(image_dir: str):
    # Load multi-label image dataset
    label_set = set()
    image_files = []
    image_labels = []
    for file in glob.glob(
        os.path.join("**", "*.*"), root_dir=image_dir, recursive=True
    ):
        ext = os.path.splitext(file)[1].lower()

        # Check if its a image file
        if ext in image_extensions:
            dirname = os.path.dirname(file)
            if dirname:
                labels = os.path.dirname(file).split(os.path.sep)
                for label in labels:
                    label_set.add(label)
                image_files.append(os.path.join(image_dir, file))
                image_labels.append(labels)

    unique_labels = sorted(list(label_set))
    print("num unique labels:", len(unique_labels))
    label2id = {v: i for i, v in enumerate(unique_labels)}
    id2label = {i: v for i, v in enumerate(unique_labels)}
    print(label2id)

    def labels_to_N_hot(labels: List[str]):
        true_index = [label2id[cl] for cl in labels]
        label = np.zeros((len(unique_labels),), dtype=float)
        label[true_index] = 1
        return label.tolist()

    dataset = datasets.Dataset.from_dict(
        {
            "image": image_files,
            "labels": [labels_to_N_hot(labels) for labels in image_labels],
        }
    ).cast_column("image", datasets.Image())

    image_processor = AutoImageProcessor.from_pretrained(model_checkpoint)
    model = AutoModelForImageClassification.from_pretrained(
        model_checkpoint,
        label2id=label2id,
        id2label=id2label,
        num_labels=len(unique_labels),
        ignore_mismatched_sizes=True,  # provide this in case you're planning to fine-tune an already fine-tuned checkpoint
    )

    normalize = Normalize(
        mean=image_processor.image_mean, std=image_processor.image_std
    )
    if "height" in image_processor.size:
        size = (image_processor.size["height"], image_processor.size["width"])
        crop_size = size
        max_size = None
    elif "shortest_edge" in image_processor.size:
        size = image_processor.size["shortest_edge"]
        crop_size = (size, size)
        max_size = image_processor.size.get("longest_edge")

    train_transforms = Compose(
        [
            RandomResizedCrop(crop_size),
            RandomHorizontalFlip(),
            ToTensor(),
            normalize,
        ]
    )

    val_transforms = Compose(
        [
            Resize(size),
            CenterCrop(crop_size),
            ToTensor(),
            normalize,
        ]
    )

    def preprocess_train(example_batch):
        """Apply train_transforms across a batch."""
        example_batch["pixel_values"] = [
            train_transforms(image.convert("RGB")) for image in example_batch["image"]
        ]
        return example_batch

    def preprocess_val(example_batch):
        """Apply val_transforms across a batch."""
        example_batch["pixel_values"] = [
            val_transforms(image.convert("RGB")) for image in example_batch["image"]
        ]
        return example_batch

    # split up training into training + validation
    splits = dataset.train_test_split(test_size=0.1)
    train_ds = splits["train"]
    val_ds = splits["test"]

    train_ds.set_transform(preprocess_train)
    val_ds.set_transform(preprocess_val)

    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

    # source: https://jesusleal.io/2021/04/21/Longformer-multilabel-classification/
    def multi_label_metrics(predictions, labels, threshold=0.5):
        # first, apply sigmoid on predictions which are of shape (batch_size, num_labels)
        sigmoid = torch.nn.Sigmoid()
        probs = sigmoid(torch.Tensor(predictions))
        # next, use threshold to turn them into integer predictions
        y_pred = np.zeros(probs.shape)
        y_pred[np.where(probs >= threshold)] = 1
        # finally, compute metrics
        y_true = labels
        f1_micro_average = f1_score(y_true=y_true, y_pred=y_pred, average="micro")
        roc_auc = roc_auc_score(y_true, y_pred, average="micro")
        accuracy = accuracy_score(y_true, y_pred)
        # return as dictionary
        metrics = {"f1": f1_micro_average, "roc_auc": roc_auc, "accuracy": accuracy}
        return metrics

    def compute_metrics(p):
        preds = p.predictions[0] if isinstance(p.predictions, tuple) else p.predictions
        result = multi_label_metrics(predictions=preds, labels=p.label_ids)
        return result

    def collate_fn(examples):
        pixel_values = torch.stack([example["pixel_values"] for example in examples])
        labels = torch.tensor([example["labels"] for example in examples])
        return {"pixel_values": pixel_values, "labels": labels}

    args = TrainingArguments(
        f"{model_name}-finetuned-eurosat",
        remove_unused_columns=False,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=5e-5,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=20,
        warmup_ratio=0.1,
        logging_steps=10,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        push_to_hub=True,
    )

    trainer = Trainer(
        model,
        args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=image_processor,
        compute_metrics=compute_metrics,
        data_collator=collate_fn,
    )

    train_results = trainer.train()
    # rest is optional but nice to have
    trainer.save_model()
    trainer.log_metrics("train", train_results.metrics)
    trainer.save_metrics("train", train_results.metrics)
    trainer.save_state()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    train_parser = subparsers.add_parser("train")
    train_parser.add_argument("image_dir", type=str)

    predict_parser = subparsers.add_parser("predict")
    predict_parser.add_argument("image_file", type=str)

    args = parser.parse_args()

    if args.command == "train":
        fine_tunning_model(args.image_dir)

    elif args.command == "predict":
        pipe = pipeline("image-classification", f"{model_name}-finetuned-eurosat")
        image_file: str = args.image_file
        if image_file.startswith("http"):
            image = Image.open(requests.get(args.image_file, stream=True).raw)
        else:
            image = Image.open(image_file)
        pprint(pipe(image))
