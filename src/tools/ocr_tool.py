import torch
import torchvision.transforms as transforms
from PIL import Image
import cv2
import numpy as np
import pytesseract
import easyocr
import re
class DnCNN(torch.nn.Module):
    def __init__(self, channels, num_of_layers=17):
        super(DnCNN, self).__init__()
        layers = []
        layers.append(torch.nn.Conv2d(in_channels=channels, out_channels=64, kernel_size=3, stride=1, padding=1, bias=False))
        layers.append(torch.nn.ReLU(inplace=True))
        for _ in range(num_of_layers-2):
            layers.append(torch.nn.Conv2d(in_channels=64, out_channels=64, kernel_size=3, stride=1, padding=1, bias=False))
            layers.append(torch.nn.BatchNorm2d(64))
            layers.append(torch.nn.ReLU(inplace=True))
        layers.append(torch.nn.Conv2d(in_channels=64, out_channels=channels, kernel_size=3, stride=1, padding=1, bias=False))
        self.dncnn = torch.nn.Sequential(*layers)

    def forward(self, x):
        out = self.dncnn(x)
        return out

class ImageDenoiser:
    def __init__(self, model_path):
        self.model = DnCNN(channels=1)  # DnCNN modell egy csatornával (grayscale képek)
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))  # Modell betöltése
        self.model.eval()  # Eval mód, mert csak inference-t végzünk
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def preprocess_image(self, image_path):
        """Kép előfeldolgozása a modell bemenetéhez"""
        image = Image.open(image_path).convert('L')  # Kép grayscale konvertálása
        transform = transforms.Compose([
            transforms.Resize((256, 256)),  # Átméretezés
            transforms.ToTensor(),  # Tensorrá alakítás
        ])
        image_tensor = transform(image).unsqueeze(0)  # Batch dimenzió hozzáadása
        return image_tensor.to(self.device)

    def denoise_image(self, image_tensor):
        """Zajcsökkentés alkalmazása a modellen keresztül"""
        with torch.no_grad():
            output = self.model(image_tensor)
            denoised_image_tensor = image_tensor - output  # Zaj csökkentése
        
        # Visszaalakítás numpy tömbbe
        denoised_image = denoised_image_tensor.squeeze(0).cpu().numpy().transpose(1, 2, 0)
        denoised_image = (denoised_image * 255).astype(np.uint8)  # Pixelértékek visszaállítása 0-255 közé
        return denoised_image

class OCRProcessor:
    def __init__(self, use_easyocr=False):
        self.use_easyocr = use_easyocr
        if self.use_easyocr:
            self.reader = easyocr.Reader(['hu'], gpu=torch.cuda.is_available())  # EasyOCR GPU támogatással, ha elérhető

    def run_ocr(self, image_path):
        """OCR futtatása a képen"""
        if self.use_easyocr:
            # EasyOCR használata
            result = self.reader.readtext(image_path, detail=0)
            return "\n".join(result)
        else:
            # Tesseract OCR használata
            return pytesseract.image_to_string(image_path, lang='hun')

    def clean_text(self, text):
        """Nem kívánt karakterek és sorok tisztítása"""
        cleaned_text = re.sub(r'[^a-zA-Z0-9áéíóöőüűÁÉÍÓÖŐÜŰ\s]', '', text)
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text)  # Üres sorok eltávolítása
        return cleaned_text

if __name__ == "__main__":
    # Kép és modell betöltése
    image_path = './szoveg.jpg'
    model_path = 'path_to_pretrained_dncnn_model.pth'  # Előre betanított modell (DnCNN)

    # Zajcsökkentés
    denoiser = ImageDenoiser(model_path)
    image_tensor = denoiser.preprocess_image(image_path)
    denoised_image = denoiser.denoise_image(image_tensor)

    # Zajmentesített kép mentése
    denoised_image_path = 'denoised_image.jpg'
    cv2.imwrite(denoised_image_path, denoised_image)

    # OCR feldolgozás (választhatsz EasyOCR vagy Tesseract közül)
    ocr_processor = OCRProcessor(use_easyocr=False)  # EasyOCR vagy Tesseract beállítása
    ocr_result = ocr_processor.run_ocr(denoised_image_path)

    # Szöveg tisztítása
    cleaned_text = ocr_processor.clean_text(ocr_result)
    print("Felismert szöveg:")
    print(cleaned_text)
