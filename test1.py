import torch
from torchvision import models, transforms
from PIL import Image, ImageDraw, ImageFont

# ----------- USER SETTINGS -----------
MODEL_PATH = "model.pth"             # path to your trained weights (.pth)
IMAGE_PATH = "Perfect-Pan-Seared-Ribeye-Steak.jpg"              # single image path
CLASS_NAMES = ['caesar_salad', 'chicken_wings', 'french_fries', 'fried_rice', 'hamburger', 'ice_cream', 'pizza', 'spaghetti_bolognese', 'steak', 'sushi']
IMG_SIZE = 256                       # EfficientNet_B2 expects 260x260
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# -------------------------------------

# Load base model architecture
model = models.efficientnet_b2(weights=None)
num_features = model.classifier[1].in_features
model.classifier[1] = torch.nn.Linear(num_features, len(CLASS_NAMES))

# Load trained weights
state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
model.load_state_dict(state_dict)
model.to(DEVICE)
model.eval()

# Image preprocessing (same as training)
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Load image
img = Image.open(IMAGE_PATH).convert("RGB")
x = transform(img).unsqueeze(0).to(DEVICE)

# Inference
with torch.no_grad():
    logits = model(x)
    probs = torch.softmax(logits, dim=1)
    conf, pred = torch.max(probs, dim=1)

label = CLASS_NAMES[pred.item()]
confidence = conf.item() * 100

# Print result
print(f"Prediction: {label} ({confidence:.2f}%)")

# Visualize result
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("arial.ttf", 22)
except:
    font = ImageFont.load_default()
text = f"{label} ({confidence:.1f}%)"
draw.rectangle([0, 0, len(text)*12, 35], fill="yellow")
draw.text((5, 5), text, fill="black", font=font)
img.show()
