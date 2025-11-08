import torch
from torchvision import models, transforms
from PIL import Image, ImageDraw, ImageFont


def classify_food(image_path, model_path="model.pth", class_names=None, img_size=256, visualize=True):
    """
    Classify a food image using a trained EfficientNet-B2 model.

    Args:
        image_path (str): Path to the input image.
        model_path (str): Path to the trained .pth model weights.
        class_names (list): List of class names corresponding to model output indices.
        img_size (int): Input image size for resizing.
        visualize (bool): Whether to display the image with label overlay.

    Returns:
        tuple: (predicted_label, confidence_percent)
    """
    if class_names is None:
        class_names = [
            'caesar_salad', 'chicken_wings', 'french_fries',
            'fried_rice', 'hamburger', 'ice_cream',
            'pizza', 'spaghetti_bolognese', 'steak', 'sushi'
        ]

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # --- Load Model ---
    model = models.efficientnet_b2(weights=None)
    num_features = model.classifier[1].in_features
    model.classifier[1] = torch.nn.Linear(num_features, len(class_names))

    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    # --- Preprocessing ---
    transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    img = Image.open(image_path).convert("RGB")
    x = transform(img).unsqueeze(0).to(device)

    # --- Inference ---
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        conf, pred = torch.max(probs, dim=1)

    label = class_names[pred.item()]
    confidence = conf.item() * 100

    # --- Visualization (optional) ---
    if visualize:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 22)
        except:
            font = ImageFont.load_default()
        text = f"{label} ({confidence:.1f}%)"
        draw.rectangle([0, 0, len(text)*12, 35], fill="yellow")
        draw.text((5, 5), text, fill="black", font=font)
        img.show()

    return label, confidence
