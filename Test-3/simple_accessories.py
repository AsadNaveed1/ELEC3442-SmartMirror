import cv2
import numpy as np
import os

class SimpleAccessoryOverlay:
    def __init__(self, accessories_dir="accessories"):
        os.makedirs(accessories_dir, exist_ok=True)
        
        # Use absolute path for the cascade file to avoid path issues
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(cascade_path):
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            # Fallback to a local file if the OpenCV directory isn't accessible
            local_cascade = os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml')
            if os.path.exists(local_cascade):
                self.face_cascade = cv2.CascadeClassifier(local_cascade)
            else:
                print(f"WARNING: Could not find face cascade file at {cascade_path} or locally")
                self.face_cascade = None
        
        self.accessories = {}
        if os.path.exists(accessories_dir):
            for filename in os.listdir(accessories_dir):
                if filename.endswith('.png'):
                    path = os.path.join(accessories_dir, filename)
                    try:
                        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                        if img is not None and img.shape[2] == 4:  # Make sure it has an alpha channel
                            name = os.path.splitext(filename)[0]
                            self.accessories[name] = img
                            print(f"Loaded accessory: {name}")
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
        else:
            print(f"Accessories directory not found: {accessories_dir}")
            
        # Create default accessories if none are found
        if not self.accessories:
            self._create_default_accessories(accessories_dir)
    
    def _create_default_accessories(self, directory):
        """Create very simple default accessories for testing"""
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        # Create a simple glasses accessory (rectangle with transparency)
        glasses = np.zeros((100, 300, 4), dtype=np.uint8)
        cv2.rectangle(glasses, (50, 30), (120, 60), (0, 0, 0, 255), 2)  # Left eye
        cv2.rectangle(glasses, (180, 30), (250, 60), (0, 0, 0, 255), 2)  # Right eye
        cv2.line(glasses, (120, 45), (180, 45), (0, 0, 0, 255), 2)  # Bridge
        
        # Create a simple hat (triangle with transparency)
        hat = np.zeros((150, 300, 4), dtype=np.uint8)
        pts = np.array([[150, 20], [50, 120], [250, 120]], np.int32)
        cv2.fillPoly(hat, [pts], (0, 0, 0, 255))
        
        # Create a simple mask (rectangle with transparency)
        mask = np.zeros((100, 300, 4), dtype=np.uint8)
        cv2.rectangle(mask, (75, 20), (225, 80), (0, 0, 0, 255), -1)
        
        try:
            cv2.imwrite(os.path.join(directory, "glasses.png"), glasses)
            cv2.imwrite(os.path.join(directory, "hat.png"), hat)
            cv2.imwrite(os.path.join(directory, "mask.png"), mask)
            
            # Load them
            self.accessories["glasses"] = glasses
            self.accessories["hat"] = hat
            self.accessories["mask"] = mask
            
            print("Created default accessories")
        except Exception as e:
            print(f"Error creating default accessories: {e}")
    
    def apply_accessory(self, frame, accessory_name):
        if accessory_name not in self.accessories:
            print(f"Accessory {accessory_name} not found")
            return frame
        
        # Make a copy to avoid modifying the original
        result = frame.copy()
        
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Check if face_cascade is available
            if self.face_cascade is None:
                print("Face cascade not available, can't detect faces")
                return frame
            
            # Detect faces - use more conservative parameters for better detection on Jetson Nano
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.2,
                minNeighbors=4, 
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(faces) == 0:
                print("No faces detected")
                return frame
            
            # Apply accessory to each detected face
            for (x, y, w, h) in faces:
                if "glasses" in accessory_name:
                    self._apply_glasses(result, x, y, w, h, self.accessories[accessory_name])
                elif "hat" in accessory_name:
                    self._apply_hat(result, x, y, w, h, self.accessories[accessory_name])
                elif "mask" in accessory_name:
                    self._apply_mask(result, x, y, w, h, self.accessories[accessory_name])
            
            return result
        except Exception as e:
            print(f"Error applying accessory: {e}")
            return frame
    
    def _apply_glasses(self, frame, x, y, w, h, glasses_img):
        try:
            glasses_width = w
            aspect_ratio = glasses_img.shape[1] / glasses_img.shape[0]
            glasses_height = int(glasses_width / aspect_ratio)
            
            glasses_x = x
            glasses_y = y + h // 4
            
            glasses_resized = cv2.resize(glasses_img, (glasses_width, glasses_height))
            
            self._overlay_transparent(frame, glasses_resized, glasses_x, glasses_y)
        except Exception as e:
            print(f"Error applying glasses: {e}")
    
    def _apply_hat(self, frame, x, y, w, h, hat_img):
        try:
            hat_width = int(w * 1.2)
            aspect_ratio = hat_img.shape[1] / hat_img.shape[0]
            hat_height = int(hat_width / aspect_ratio)
            
            hat_x = x - (hat_width - w) // 2
            hat_y = max(0, y - hat_height // 2)
            
            hat_resized = cv2.resize(hat_img, (hat_width, hat_height))
            
            self._overlay_transparent(frame, hat_resized, hat_x, hat_y)
        except Exception as e:
            print(f"Error applying hat: {e}")
    
    def _apply_mask(self, frame, x, y, w, h, mask_img):
        try:
            mask_width = w
            aspect_ratio = mask_img.shape[1] / mask_img.shape[0]
            mask_height = int(mask_width / aspect_ratio)
            
            mask_x = x
            mask_y = y + h // 2
            
            mask_resized = cv2.resize(mask_img, (mask_width, mask_height))
            
            self._overlay_transparent(frame, mask_resized, mask_x, mask_y)
        except Exception as e:
            print(f"Error applying mask: {e}")
    
    def _overlay_transparent(self, background, overlay, x, y):
        # Handle error cases to avoid crashes
        if x < 0 or y < 0:
            return
            
        h, w = overlay.shape[:2]
        
        if x + w > background.shape[1]:
            w = background.shape[1] - x
        if y + h > background.shape[0]:
            h = background.shape[0] - y
            
        if w <= 0 or h <= 0:
            return
            
        # Make sure everything is within bounds
        try:
            overlay_crop = overlay[:h, :w]
            bg_crop = background[y:y+h, x:x+w]
            
            # Make sure the shapes match before proceeding
            if overlay_crop.shape[:2] != bg_crop.shape[:2]:
                print(f"Shape mismatch: overlay={overlay_crop.shape}, bg={bg_crop.shape}")
                return
            
            # Ensure overlay_crop has 4 channels
            if overlay_crop.shape[2] != 4:
                print(f"Expected overlay to have 4 channels, got {overlay_crop.shape[2]}")
                return
                
            alpha = overlay_crop[:, :, 3:4] / 255.0
            rgb = overlay_crop[:, :, :3]
            
            alpha_rgb = np.concatenate([alpha, alpha, alpha], axis=2)
            
            background[y:y+h, x:x+w] = (bg_crop * (1 - alpha_rgb) + rgb * alpha_rgb).astype(np.uint8)
        except Exception as e:
            print(f"Error in overlay operation: {e}")