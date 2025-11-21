import torch
from torchvision import models, transforms
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------
# GLOBAL STATE (kept for the lifetime of the process)
# ----------------------------------------------------------
_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_MODEL = None
_MODEL_CLASS_NAMES = None
_MODEL_PATH = None

_TRANSFORM = None
_IMG_SIZE = None


def _get_model(model_path, class_names):
    """
    Load the model once and cache it in globals.

    Subsequent calls:
      - reuse the same model
      - enforce same model_path and class_names for safety
    """
    global _MODEL, _MODEL_CLASS_NAMES, _MODEL_PATH

    if _MODEL is None:
        # First time: build architecture and load weights
        model = models.efficientnet_b2(weights=None)
        num_features = model.classifier[1].in_features
        model.classifier[1] = torch.nn.Linear(num_features, len(class_names))

        state_dict = torch.load(model_path, map_location=_DEVICE)
        model.load_state_dict(state_dict)
        model.to(_DEVICE)
        model.eval()

        _MODEL = model
        _MODEL_CLASS_NAMES = list(class_names)
        _MODEL_PATH = model_path
    else:
        # Later calls: sanity checks for safety
        if model_path != _MODEL_PATH:
            raise ValueError(
                f"classify_food was already initialized with "
                f"model_path={_MODEL_PATH!r}. "
                f"You cannot change model_path within the same process."
            )
        if list(class_names) != _MODEL_CLASS_NAMES:
            raise ValueError(
                "classify_food was already initialized with a different "
                "class_names list. Use the same class_names on every call."
            )

    return _MODEL, _MODEL_CLASS_NAMES


def _get_transform(img_size):
    """
    Get (or build) the preprocessing transform.

    Rebuilds only if img_size changes.
    """
    global _TRANSFORM, _IMG_SIZE

    if _TRANSFORM is None or img_size != _IMG_SIZE:
        _TRANSFORM = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
        _IMG_SIZE = img_size

    return _TRANSFORM


def classify_food(image_path,
                  model_path="model.pth",
                  class_names=None,
                  img_size=256,
                  visualize=False):
    """
    Classify a food image using a trained EfficientNet-B2 model.

    This function is safe to import and call repeatedly. The model is
    loaded only once and kept in memory until the process ends.

    Args:
        image_path (str): Path to the input image.
        model_path (str): Path to the trained .pth model weights.
        class_names (list): List of class names corresponding to model outputs.
        img_size (int): Input image size for resizing.
        visualize (bool): Whether to display the image with label overlay.

    Returns:
        tuple: (predicted_label, confidence_percent)
    """
    if class_names is None:
        class_names = [
            'Caesar Salad', 'Chicken Wings', 'French Fries',
            'Fried Rice', 'Hamburger', 'Ice Cream',
            'Pizza', 'Spaghetti Bolognese', 'Steak', 'Sushi'
        ]

    # Get cached model and class names (or load them on first call)
    model, class_names = _get_model(model_path, class_names)
    transform = _get_transform(img_size)

    # --- Load and preprocess image ---
    img = Image.open(image_path).convert("RGB")
    x = transform(img).unsqueeze(0).to(_DEVICE)

    # --- Inference ---
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        conf, pred = torch.max(probs, dim=1)

    label = class_names[pred.item()]
    confidence = conf.item() * 100.0

    # --- Visualization (optional) ---
    if visualize:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 22)
        except Exception:
            font = ImageFont.load_default()

        text = f"{label} ({confidence:.1f}%)"
        # crude background box size; fine for simple overlays
        draw.rectangle([0, 0, len(text) * 12, 35], fill="yellow")
        draw.text((5, 5), text, fill="black", font=font)
        img.show()

    return label, confidence
