import cv2
import numpy as np

def get_skeleton(img_path):
    """
    Generate skeleton from image without saving intermediate files.
    Returns the skeleton image as numpy array.
    """
    # 1. Load image
    img = cv2.imread(img_path, 0)
    if img is None:
        print("Error: Image not found.")
        return None, None

    # 2. Gaussian Blur 
    img_blurred = cv2.GaussianBlur(img, (5, 5), 0)

    # 3. Binary Thresholding (Otsu)
    # Invert: Lines = White, Background = Black
    ret, thresh = cv2.threshold(img_blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 4. Aggressive Morphological Closing
    kernel = np.ones((3,3), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=4)

    # 5. Robust Thinning Function
    def thinning(img_input):
        size = np.size(img_input)
        skel = np.zeros(img_input.shape, np.uint8)
        element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
        done = False
        
        eroded = img_input.copy()
        while not done:
            open_op = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, element)
            temp = cv2.subtract(eroded, open_op)
            eroded = cv2.erode(eroded, element)
            skel = cv2.bitwise_or(skel, temp)
            if cv2.countNonZero(eroded) == 0:
                done = True
        return skel

    # Run Thinning First Pass
    skeleton = thinning(closing)

    # 6. Bridge Micro-Gaps
    kernel_bridge = np.ones((3,3), np.uint8)
    bridged = cv2.dilate(skeleton, kernel_bridge, iterations=1)
    
    # Thin again to return to 1-pixel width
    final_skeleton = thinning(bridged)

    return img, final_skeleton
