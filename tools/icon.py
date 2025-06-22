from PIL import Image
from pathlib import Path

def convert_to_ico(input_image_path: str, output_ico_path: str):
    """Convertit un PNG ou JPG en fichier .ico multi-résolution pour Windows."""
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    img = Image.open(input_image_path).convert("RGBA")
    img.save(output_ico_path, format='ICO', sizes=sizes)
    print(f"✅ Fichier .ico généré : {output_ico_path}")

# Exemple d'utilisation :
if __name__ == "__main__":
    convert_to_ico("assets/icon.png", "assets/icon.ico")
