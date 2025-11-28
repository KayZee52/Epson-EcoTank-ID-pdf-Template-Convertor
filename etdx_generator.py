"""
ETDX Template Generator for Epson Photo+ ID Card Printing
This module generates .etdx template files from PDF pages for use with
Epson Photo+ software. Each template contains 2 ID cards (front and back).
"""
import json
import os
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import List, Tuple
from PIL import Image
class ETDXGenerator:
    """Generate Epson Photo+ .etdx template files from images."""
    
    # Target card dimensions at 300 DPI (86mm x 54mm)
    TARGET_WIDTH = 1016
    TARGET_HEIGHT = 638
    
    # Photo positioning (from template analysis)
    PHOTO_CENTER = [0.4488523602485657, 0.7050654292106628]
    PHOTO_CROP_RECT = [0, 0, TARGET_WIDTH, TARGET_HEIGHT]
    
    def __init__(self, base_template_dir: str):
        """
        Initialize ETDX generator with base template.
        
        Args:
            base_template_dir: Path to extracted base template directory
        """
        self.base_template_dir = Path(base_template_dir)
        self.load_base_template()
    
    def load_base_template(self):
        """Load base template JSON files."""
        # Load projectinfo.json
        with open(self.base_template_dir / "projectinfo.json", 'r') as f:
            self.project_info = json.load(f)
        
        # Load an existing page template as base (not BaseData)
        # Find first page UUID directory
        page_dirs = [d for d in self.base_template_dir.iterdir() 
                    if d.is_dir() and d.name != "BaseData"]
        
        if not page_dirs:
            raise ValueError("No page template found in base template directory")
        
        # Load first page's _info.json as template
        with open(page_dirs[0] / "_info.json", 'r') as f:
            self.page_template = json.load(f)
    
    def calculate_scale(self, original_width: int, original_height: int) -> float:
        """
        Calculate scale factor to fit image into target dimensions.
        
        Args:
            original_width: Original image width in pixels
            original_height: Original image height in pixels
            
        Returns:
            Scale factor
        """
        # Empirical correction:
        # Target 86mm / Observed 71.7mm (at ~0.83 scale) ~= 1.2
        # Target 86mm / Observed 45.8mm (at ~0.64 scale) ~= 1.88 -> 0.64 * 1.88 ~= 1.2
        # Likely due to Epson using 360 DPI vs our 300 DPI (360/300 = 1.2)
        return 1.2
    
    def create_photo_object(self, image_path: str, workspace_number: int, 
                           original_size: Tuple[int, int]) -> dict:
        """
        Create photo object for JSON metadata.
        
        Args:
            image_path: Relative path to image in template
            workspace_number: 1 or 2 (top or bottom card)
            original_size: (width, height) of original image
            
        Returns:
            Photo object dictionary
        """
        width, height = original_size
        scale = self.calculate_scale(width, height)
        
        return {
            "angle": 0,
            "center": self.PHOTO_CENTER.copy(),
            "effectInfo": {
                "blur": 0,
                "transparency": 0
            },
            "originalsize": [float(width), float(height)],
            "zindex": 0,
            "frameIndex": -1,
            "imagePath": image_path,
            "workSpaceNumber": workspace_number,
            "apfInfo": {
                "saturation": 0,
                "brightness": 0,
                "level": 5,
                "contrast": 0,
                "mode": "standard",
                "sharpness": 0
            },
            "crop": {
                "type": 1,
                "rect": self.PHOTO_CROP_RECT.copy()
            },
            "scale": scale
        }
    
    def create_page_info(self, photos: List[dict]) -> dict:
        """
        Create page _info.json with photos.
        
        Args:
            photos: List of photo objects
            
        Returns:
            Page info dictionary
        """
        # Clone page template structure
        page_info = json.loads(json.dumps(self.page_template))
        
        # Update with photos
        page_info["editedPaperSize"]["photos"] = photos
        
        return page_info
    
    def generate_etdx(self, image_pairs: List[Tuple[str, str, str, str]], 
                     output_path: str, template_name: str = "kay"):
        """
        Generate .etdx template file.
        
        Args:
            image_pairs: List of (front1, back1, front2, back2) image paths
            output_path: Directory to save .etdx file
            template_name: Base name for template (e.g., "kay1")
        """
        if len(image_pairs) != 4:
            raise ValueError("Expected 4 images: front1, back1, front2, back2")
        
        front1_path, back1_path, front2_path, back2_path = image_pairs
        
        # Create temporary directory for template assembly
        temp_dir = Path(output_path) / f"_temp_{template_name}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Generate UUIDs
            front_page_uuid = str(uuid.uuid4()).upper()
            back_page_uuid = str(uuid.uuid4()).upper()
            
            front1_img_uuid = str(uuid.uuid4()).upper()
            front2_img_uuid = str(uuid.uuid4()).upper()
            back1_img_uuid = str(uuid.uuid4()).upper()
            back2_img_uuid = str(uuid.uuid4()).upper()
            
            # Copy base files
            shutil.copy(self.base_template_dir / "projectinfo.json", temp_dir / "projectinfo.json")
            shutil.copytree(self.base_template_dir / "BaseData", temp_dir / "BaseData")
            
            # Create page.json
            page_json = [front_page_uuid, back_page_uuid]
            with open(temp_dir / "page.json", 'w') as f:
                json.dump(page_json, f)
            
            # Get image sizes
            with Image.open(front1_path) as img:
                front1_size = img.size
            with Image.open(front2_path) as img:
                front2_size = img.size
            with Image.open(back1_path) as img:
                back1_size = img.size
            with Image.open(back2_path) as img:
                back2_size = img.size
            
            # Create Front page
            front_page_dir = temp_dir / front_page_uuid
            front_page_dir.mkdir()
            
            # Copy front images
            front1_dir = front_page_dir / front1_img_uuid
            front1_dir.mkdir()
            front1_filename = Path(front1_path).name
            shutil.copy(front1_path, front1_dir / front1_filename)
            
            front2_dir = front_page_dir / front2_img_uuid
            front2_dir.mkdir()
            front2_filename = Path(front2_path).name
            shutil.copy(front2_path, front2_dir / front2_filename)
            
            # Create front page photos
            front_photos = [
                self.create_photo_object(
                    f"{front1_img_uuid}/{front1_filename}",
                    1,
                    front1_size
                ),
                self.create_photo_object(
                    f"{front2_img_uuid}/{front2_filename}",
                    2,
                    front2_size
                )
            ]
            
            # Save front page _info.json
            front_page_info = self.create_page_info(front_photos)
            with open(front_page_dir / "_info.json", 'w') as f:
                json.dump(front_page_info, f)
            
            # Create Back page
            back_page_dir = temp_dir / back_page_uuid
            back_page_dir.mkdir()
            
            # Copy back images
            back1_dir = back_page_dir / back1_img_uuid
            back1_dir.mkdir()
            back1_filename = Path(back1_path).name
            shutil.copy(back1_path, back1_dir / back1_filename)
            
            back2_dir = back_page_dir / back2_img_uuid
            back2_dir.mkdir()
            back2_filename = Path(back2_path).name
            shutil.copy(back2_path, back2_dir / back2_filename)
            
            # Create back page photos
            back_photos = [
                self.create_photo_object(
                    f"{back1_img_uuid}/{back1_filename}",
                    1,
                    back1_size
                ),
                self.create_photo_object(
                    f"{back2_img_uuid}/{back2_filename}",
                    2,
                    back2_size
                )
            ]
            
            # Save back page _info.json
            back_page_info = self.create_page_info(back_photos)
            with open(back_page_dir / "_info.json", 'w') as f:
                json.dump(back_page_info, f)
            
            # Create .etdx ZIP file
            etdx_path = Path(output_path) / f"{template_name}.etdx"
            with zipfile.ZipFile(etdx_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_dir)
                        zf.write(file_path, arcname)
            
            return str(etdx_path)
        
        finally:
            # Clean up temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def batch_generate(self, pdf_images: List[str], output_dir: str, 
                      base_name: str = "kay") -> List[str]:
        """
        Generate multiple .etdx files from PDF images.
        
        Args:
            pdf_images: List of image paths in order [F1, B1, F2, B2, F3, B3, ...]
            output_dir: Directory to save .etdx files
            base_name: Base name for templates (e.g., "kay" -> "kay1.etdx", "kay2.etdx")
            
        Returns:
            List of generated .etdx file paths
        """
        if len(pdf_images) % 4 != 0:
            raise ValueError(f"Expected multiple of 4 images, got {len(pdf_images)}")
        
        generated_files = []
        
        # Process in groups of 4
        for i in range(0, len(pdf_images), 4):
            template_num = (i // 4) + 1
            template_name = f"{base_name}{template_num}"
            
            image_group = pdf_images[i:i+4]
            etdx_path = self.generate_etdx(image_group, output_dir, template_name)
            generated_files.append(etdx_path)
        
        return generated_files
if __name__ == "__main__":
    # Test the generator
    print("ETDX Generator module loaded successfully")
