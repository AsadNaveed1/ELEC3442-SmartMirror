import cv2
import numpy as np
import os

class SimpleAccessoryOverlay:
    def __init__(self, accessories_dir="accessories"):
        os.makedirs(accessories_dir, exist_ok=True)
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.accessories = {}
        if os.path.exists(accessories_dir):
            for filename in os.listdir(accessories_dir):
                if filename.endswith('.png'):
                    path = os.path.join(accessories_dir, filename)
                    try:
                        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                        if img is not None and img.shape[2] == 4:
                            name = os.path.splitext(filename)[0]
                            self.accessories[name] = img
                            print(f"Loaded accessory: {name}")
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
        else:
            print(f"Accessories directory not found: {accessories_dir}")
    
    def apply_accessory(self, frame, accessory_name):
        if accessory_name not in self.accessories:
            print(f"Accessory {accessory_name} not found")
            return frame
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            if "glasses" in accessory_name:
                self._apply_glasses(frame, x, y, w, h, self.accessories[accessory_name])
            elif "hat" in accessory_name:
                self._apply_hat(frame, x, y, w, h, self.accessories[accessory_name])
            elif "mask" in accessory_name:
                self._apply_mask(frame, x, y, w, h, self.accessories[accessory_name])
        
        return frame
    
    def _apply_glasses(self, frame, x, y, w, h, glasses_img):
        glasses_width = w
        aspect_ratio = glasses_img.shape[1] / glasses_img.shape[0]
        glasses_height = int(glasses_width / aspect_ratio)
        
        glasses_x = x
        glasses_y = y + h // 4
        
        glasses_resized = cv2.resize(glasses_img, (glasses_width, glasses_height))
        
        self._overlay_transparent(frame, glasses_resized, glasses_x, glasses_y)
    
    def _apply_hat(self, frame, x, y, w, h, hat_img):
        hat_width = int(w * 1.2)
        aspect_ratio = hat_img.shape[1] / hat_img.shape[0]
        hat_height = int(hat_width / aspect_ratio)
        
        hat_x = x - (hat_width - w) // 2
        hat_y = max(0, y - hat_height // 2)
        
        hat_resized = cv2.resize(hat_img, (hat_width, hat_height))
        
        self._overlay_transparent(frame, hat_resized, hat_x, hat_y)
    
    def _apply_mask(self, frame, x, y, w, h, mask_img):
        mask_width = w
        aspect_ratio = mask_img.shape[1] / mask_img.shape[0]
        mask_height = int(mask_width / aspect_ratio)
        
        mask_x = x
        mask_y = y + h // 2
        
        mask_resized = cv2.resize(mask_img, (mask_width, mask_height))
        
        self._overlay_transparent(frame, mask_resized, mask_x, mask_y)
    
    def _overlay_transparent(self, background, overlay, x, y):
        h, w = overlay.shape[:2]
        if x < 0 or y < 0:
            return
            
        if x + w > background.shape[1]:
            w = background.shape[1] - x
        if y + h > background.shape[0]:
            h = background.shape[0] - y
            
        if w <= 0 or h <= 0:
            return
            
        overlay_crop = overlay[:h, :w]
        
        bg_crop = background[y:y+h, x:x+w]
        
        alpha = overlay_crop[:, :, 3:4] / 255.0
        rgb = overlay_crop[:, :, :3]
        
        alpha_rgb = np.concatenate([alpha, alpha, alpha], axis=2)
        
        background[y:y+h, x:x+w] = (bg_crop * (1 - alpha_rgb) + rgb * alpha_rgb).astype(np.uint8)