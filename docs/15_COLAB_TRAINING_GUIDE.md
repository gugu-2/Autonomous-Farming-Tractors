# AGRO-AI: Google Colab Training Guide

This guide details how to train the **Category 2 Vision Brains** (e.g., YOLOv8 for the Crop Sprayer) using Google Colab's free T4 GPUs. Colab is the fastest and cheapest way to fine-tune our perception models before exporting them to the NVIDIA Jetson hardware.

---

## Part 1: Setting up the Colab Environment

1. Go to [Google Colab](https://colab.research.google.com/) and create a **New Notebook**.
2. **Enable the GPU:** Go to `Runtime` > `Change runtime type`. Select **T4 GPU**.
3. **Mount Google Drive (Optional but recommended):** This ensures your trained weights are saved permanently. Run this in the first cell:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```

## Part 2: Installing Dependencies

In the next cell, install the Ultralytics YOLO package and Roboflow (for downloading our weed dataset):

```python
!pip install ultralytics roboflow
```

## Part 3: Downloading the Dataset

We use Roboflow to manage our dataset (images of crops and weeds). Run this cell, replacing the `API_KEY` with your actual key from the AGRO-AI Roboflow workspace:

```python
from roboflow import Roboflow

rf = Roboflow(api_key="YOUR_API_KEY_HERE")
project = rf.workspace("agro-ai").project("weed-detection")
dataset = project.version(1).download("yolov8")

print(f"Dataset downloaded to: {dataset.location}")
```

## Part 4: The Training Script

Create a new cell and run the following Python code. This script contains **agricultural-specific augmentations**. For example, it disables `flipud` (because the ground is always down) but heavily augments saturation and value to account for muddy fields and harsh sunlight.

```python
import os
import torch
from ultralytics import YOLO

# 1. Verify GPU
if torch.cuda.is_available():
    print(f"Training on GPU: {torch.cuda.get_device_name(0)}")
else:
    print("WARNING: Not using GPU!")

# 2. Initialize Model
# We use YOLOv8s (small) because it runs at 60+ FPS on the Jetson Orin Nano
model = YOLO('yolov8s.pt') 

# 3. Train Model
# Assuming dataset.location from Part 3 is '/content/weed-detection-1'
data_yaml_path = '/content/weed-detection-1/data.yaml'

results = model.train(
    data=data_yaml_path,
    epochs=100,
    imgsz=640,
    batch=16, # Optimized for 16GB T4 VRAM
    name="agro_ai_sprayer",
    
    # Agronomic Augmentations:
    augment=True,
    hsv_h=0.015,  # Hue variation
    hsv_s=0.7,    # Saturation (simulates different soil moisture)
    hsv_v=0.4,    # Value (simulates harsh lighting/shadows)
    degrees=15.0, # Camera boom bounce simulation
    translate=0.1,
    scale=0.5,
    flipud=0.0,   # Ground is always down, do not flip upside down
    fliplr=0.5,   # Left/Right symmetry is fine
    mosaic=1.0    # Excellent for detecting tiny weeds
)

print(f"Final mAP50: {results.box.map50:.3f}")
```

## Part 5: Exporting for NVIDIA Jetson

Once training is complete, the weights (`best.pt`) are stored in `/content/runs/detect/agro_ai_sprayer/weights/best.pt`.

To run this model on our physical tractor hardware at maximum speed, we must export it to **ONNX** format (which we later compile to TensorRT on the Jetson):

```python
# Export the model to ONNX with half-precision (FP16)
success = model.export(format='onnx', half=True)
print("Export complete!")

# Copy the file to your Google Drive so you don't lose it
import shutil
shutil.copy("/content/runs/detect/agro_ai_sprayer/weights/best.onnx", "/content/drive/MyDrive/best_weed_model.onnx")
print("Saved to Google Drive!")
```

---

> [!TIP]
> **Next Step:** You take this `best_weed_model.onnx` file on a USB drive (or via cloud download) and load it onto the NVIDIA Jetson box mounted on your crop sprayer. Our ROS2 `trt_yolo_node.py` will ingest this file and use it to fire the sprayer nozzles!
