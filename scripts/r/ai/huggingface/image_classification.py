# https://github.com/huggingface/notebooks/blob/main/examples/image_classification.ipynb

import argparse
from pprint import pprint

import evaluate
import numpy as np
import requests
import torch
from datasets import load_dataset
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


def fine_tunning_model(image_dir: str):
    # Load dataset from local/remote files or folders using the ImageFolder feature
    dataset = load_dataset("imagefolder", data_dir=image_dir)

    labels = dataset["train"].features["label"].names
    label2id, id2label = dict(), dict()
    for i, label in enumerate(labels):
        label2id[label] = i
        id2label[i] = label

    print("id2label:", id2label)

    metric = evaluate.load("accuracy")

    image_processor = AutoImageProcessor.from_pretrained(model_checkpoint)
    model = AutoModelForImageClassification.from_pretrained(
        model_checkpoint,
        label2id=label2id,
        id2label=id2label,
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
    splits = dataset["train"].train_test_split(test_size=0.1)
    train_ds = splits["train"]
    val_ds = splits["test"]

    train_ds.set_transform(preprocess_train)
    val_ds.set_transform(preprocess_val)

    # the compute_metrics function takes a Named Tuple as input:
    # predictions, which are the logits of the model as Numpy arrays,
    # and label_ids, which are the ground-truth labels as Numpy arrays.
    def compute_metrics(eval_pred):
        """Computes accuracy on a batch of predictions"""
        predictions = np.argmax(eval_pred.predictions, axis=1)
        return metric.compute(predictions=predictions, references=eval_pred.label_ids)

    def collate_fn(examples):
        pixel_values = torch.stack([example["pixel_values"] for example in examples])
        labels = torch.tensor([example["label"] for example in examples])
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
        image = Image.open(requests.get(args.image_file, stream=True).raw)
        pprint(pipe(image))
