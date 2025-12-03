import customtkinter as ctk
from tkinter import filedialog, messagebox
from pdf2image import convert_from_path
import threading
import os
import sys
from PIL import Image
from etdx_generator import ETDXGenerator

# Configuration
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class PDFConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("PDF to Image & ETDX Converter")
        self.geometry("600x520")
        self.resizable(False, False)

        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Input
        self.grid_rowconfigure(2, weight=0)  # Output
        self.grid_rowconfigure(3, weight=0)  # Convert Button
        self.grid_rowconfigure(4, weight=1)  # Status/Progress

        # Variables
        # Variables
        self.input_mode = ctk.StringVar(value="PDF")  # "PDF" or "Images"
        self.input_path = ctk.StringVar()
        self.output_folder = ctk.StringVar()
        self.orientation = ctk.StringVar(value="Landscape") # "Landscape" or "Portrait"
        self.generate_etdx = ctk.BooleanVar(value=False)
        self.is_converting = False
        self.generate_etdx = ctk.BooleanVar(value=False)
        self.is_converting = False

        # UI Elements
        self.create_widgets()

    def create_widgets(self):
        # Title
        self.title_label = ctk.CTkLabel(self, text="PDF/Images to ETDX Converter", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Mode Selection
        self.mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mode_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.mode_label = ctk.CTkLabel(self.mode_frame, text="Source Mode:", font=ctk.CTkFont(weight="bold"))
        self.mode_label.pack(side="left", padx=(0, 10))
        
        self.pdf_radio = ctk.CTkRadioButton(self.mode_frame, text="PDF File", variable=self.input_mode, value="PDF", command=self.update_ui_mode)
        self.pdf_radio.pack(side="left", padx=10)
        
        self.img_radio = ctk.CTkRadioButton(self.mode_frame, text="Image Folder (PNG)", variable=self.input_mode, value="Images", command=self.update_ui_mode)
        self.img_radio.pack(side="left", padx=10)

        # Orientation Selection
        self.orient_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.orient_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.orient_label = ctk.CTkLabel(self.orient_frame, text="Orientation:", font=ctk.CTkFont(weight="bold"))
        self.orient_label.pack(side="left", padx=(0, 10))
        
        self.land_radio = ctk.CTkRadioButton(self.orient_frame, text="Landscape (86x54)", variable=self.orientation, value="Landscape")
        self.land_radio.pack(side="left", padx=10)
        
        self.port_radio = ctk.CTkRadioButton(self.orient_frame, text="Portrait (54x86)", variable=self.orientation, value="Portrait")
        self.port_radio.pack(side="left", padx=10)

        # Orientation Selection
        self.orient_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.orient_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.orient_label = ctk.CTkLabel(self.orient_frame, text="Orientation:", font=ctk.CTkFont(weight="bold"))
        self.orient_label.pack(side="left", padx=(0, 10))
        
        self.land_radio = ctk.CTkRadioButton(self.orient_frame, text="Landscape (86x54)", variable=self.orientation, value="Landscape")
        self.land_radio.pack(side="left", padx=10)
        
        self.port_radio = ctk.CTkRadioButton(self.orient_frame, text="Portrait (54x86)", variable=self.orientation, value="Portrait")
        self.port_radio.pack(side="left", padx=10)

        # Input Section
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.input_label = ctk.CTkLabel(self.input_frame, text="PDF File:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10)

        self.input_entry = ctk.CTkEntry(self.input_frame, textvariable=self.input_path, placeholder_text="Select a PDF file...")
        self.input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.browse_input_btn = ctk.CTkButton(self.input_frame, text="Browse", width=80, command=self.browse_input)
        self.browse_input_btn.grid(row=0, column=2, padx=10, pady=10)

        # Output Section
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.output_frame.grid_columnconfigure(1, weight=1)

        self.output_label = ctk.CTkLabel(self.output_frame, text="Output Folder:")
        self.output_label.grid(row=0, column=0, padx=10, pady=10)

        self.output_entry = ctk.CTkEntry(self.output_frame, textvariable=self.output_folder, placeholder_text="Select output folder...")
        self.output_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.browse_output_btn = ctk.CTkButton(self.output_frame, text="Browse", width=80, command=self.browse_output)
        self.browse_output_btn.grid(row=0, column=2, padx=10, pady=10)

        # ETDX Option
        self.etdx_checkbox = ctk.CTkCheckBox(
            self, 
            text="Generate Epson Photo+ Templates (.etdx)",
            variable=self.generate_etdx,
            font=ctk.CTkFont(size=13)
        )
        self.etdx_checkbox.grid(row=5, column=0, padx=20, pady=(10, 5), sticky="w")

        # Convert Button
        self.convert_btn = ctk.CTkButton(self, text="Convert", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self.start_conversion)
        self.convert_btn.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Status/Progress
        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.grid(row=7, column=0, padx=20, pady=10)

        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.progressbar.set(0)

    def update_ui_mode(self):
        mode = self.input_mode.get()
        if mode == "PDF":
            self.input_label.configure(text="PDF File:")
            self.input_entry.configure(placeholder_text="Select a PDF file...")
            self.etdx_checkbox.configure(state="normal")
        else:
            self.input_label.configure(text="Images Folder:")
            self.input_entry.configure(placeholder_text="Select folder with PNG images...")
            self.generate_etdx.set(True)
            self.etdx_checkbox.configure(state="disabled") # Always generate ETDX in Image mode

    def browse_input(self):
        mode = self.input_mode.get()
        if mode == "PDF":
            filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
            if filename:
                self.input_path.set(filename)
                if not self.output_folder.get():
                    self.output_folder.set(os.path.dirname(filename))
        else:
            folder = filedialog.askdirectory()
            if folder:
                self.input_path.set(folder)
                if not self.output_folder.get():
                    self.output_folder.set(folder)

    def browse_output(self):
        foldername = filedialog.askdirectory()
        if foldername:
            self.output_folder.set(foldername)

    def start_conversion(self):
        if self.is_converting:
            return

        input_path = self.input_path.get()
        output_dir = self.output_folder.get()
        mode = self.input_mode.get()

        if not input_path or not os.path.exists(input_path):
            msg = "Please select a valid PDF file." if mode == "PDF" else "Please select a valid folder."
            messagebox.showerror("Error", msg)
            return
        
        if not output_dir:
            messagebox.showerror("Error", "Please select an output folder.")
            return

        self.is_converting = True
        self.convert_btn.configure(state="disabled", text="Processing...")
        self.progressbar.set(0)
        self.status_label.configure(text="Starting process...", text_color="blue")
        
        orientation = self.orientation.get()

        # Run in a separate thread to keep GUI responsive
        threading.Thread(target=self.convert_process, args=(input_path, output_dir, mode, orientation), daemon=True).start()

    def convert_process(self, input_path, output_dir, mode, orientation):
        try:
            image_paths = []
            base_name = "output"

            if mode == "PDF":
                # Get PDF name for file naming
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                
                self.update_status("Reading PDF info...")
                self.update_status("Converting pages... (this may take a moment)")
                self.progressbar.start()
                
                # Use high DPI (300) for maximum quality - matches print quality
                images = convert_from_path(input_path, dpi=300)
                
                # Rotate if Portrait
                if orientation == "Portrait":
                    self.update_status("Rotating images for portrait mode...")
                    images = [img.rotate(90, expand=True) for img in images]
                
                self.progressbar.stop()
                self.progressbar.set(0.4)
                self.update_status(f"Saving {len(images)} images...")

                # Save PNG images
                for i, image in enumerate(images):
                    image_name = f"{base_name}_page_{i + 1}.png"
                    image_path = os.path.join(output_dir, image_name)
                    image.save(image_path, "PNG")
                    image_paths.append(image_path)
                    
                    # Update progress (40% to 70%)
                    progress = 0.4 + (0.3 * (i + 1) / len(images))
                    self.progressbar.set(progress)
            
            else: # Image Mode
                self.update_status("Reading images from folder...")
                base_name = os.path.basename(input_path)
                
                # Find all PNGs
                all_files = [f for f in os.listdir(input_path) if f.lower().endswith('.png')]
                
                # Sort naturally
                import re
                def natural_sort_key(s):
                    return [int(text) if text.isdigit() else text.lower()
                            for text in re.split('([0-9]+)', s)]
                
                all_files.sort(key=natural_sort_key)
                
                raw_image_paths = [os.path.join(input_path, f) for f in all_files]
                
                if not raw_image_paths:
                    raise ValueError("No PNG images found in the selected folder.")
                
                # Handle rotation if Portrait
                if orientation == "Portrait":
                    self.update_status("Rotating images for portrait mode...")
                    # Create temp dir for rotated images
                    temp_rot_dir = os.path.join(output_dir, "_temp_rotated")
                    os.makedirs(temp_rot_dir, exist_ok=True)
                    
                    image_paths = []
                    for i, p in enumerate(raw_image_paths):
                        try:
                            with Image.open(p) as img:
                                rotated = img.rotate(90, expand=True)
                                new_name = os.path.basename(p)
                                new_path = os.path.join(temp_rot_dir, new_name)
                                rotated.save(new_path)
                                image_paths.append(new_path)
                        except Exception as e:
                            print(f"Error rotating {p}: {e}")
                else:
                    image_paths = raw_image_paths
                
                self.progressbar.set(0.6)
                self.update_status(f"Found {len(image_paths)} images...")

            # Generate ETDX templates if requested
            if self.generate_etdx.get():
                self.progressbar.set(0.7)
                self.update_status("Generating ETDX templates...")
                
                # Pad with last 2 images if not a multiple of 4
                remainder = len(image_paths) % 4
                if remainder != 0:
                    # Need to add (4 - remainder) images
                    padding_needed = 4 - remainder
                    # Clone the last 2 images to complete the set
                    if len(image_paths) >= 2:
                        padding_images = image_paths[-2:] * ((padding_needed + 1) // 2)
                        image_paths.extend(padding_images[:padding_needed])
                        self.update_status(f"Padded with {padding_needed} images to complete template...")
                    else:
                        self.conversion_complete(
                            False, 
                            f"Not enough images to pad. Need at least 2 images."
                        )
                        return
                
                try:
                    # Initialize ETDX generator
                    template_base = os.path.join(os.path.dirname(__file__), "template_base")
                    generator = ETDXGenerator(template_base)
                    
                    # Generate templates
                    etdx_files = generator.batch_generate(image_paths, output_dir, base_name)
                    
                    self.progressbar.set(1.0)
                    self.conversion_complete(
                        True, 
                        f"Successfully processed {len(image_paths)} images!\n"
                        f"Generated {len(etdx_files)} ETDX template(s)."
                    )
                except Exception as e:
                    self.conversion_complete(False, f"ETDX generation failed: {str(e)}")
                    return
            else:
                self.progressbar.set(1.0)
                self.conversion_complete(True, f"Successfully converted {len(image_paths)} pages!")

        except Exception as e:
            self.conversion_complete(False, str(e))

    def update_status(self, message):
        self.status_label.configure(text=message)

    def conversion_complete(self, success, message):
        self.is_converting = False
        self.convert_btn.configure(state="normal", text="Convert")
        self.progressbar.stop()
        
        if success:
            self.progressbar.set(1)
            self.status_label.configure(text="Done!", text_color="green")
            messagebox.showinfo("Success", message)
        else:
            self.progressbar.set(0)
            self.status_label.configure(text="Error", text_color="red")
            messagebox.showerror("Error", f"An error occurred:\n{message}")

if __name__ == "__main__":
    app = PDFConverterApp()
    app.mainloop()
