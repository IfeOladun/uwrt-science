import cv2, random
import numpy as np
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry


def remove_nested_masks(masks, overlap_thresh=0.95):
    """
    masks: list of dicts from SAM (with 'segmentation' key)
    overlap_thresh: fraction of smaller mask covered by larger mask
    """
    
    # Sort masks by area (largest first)
    masks = sorted(masks, key=lambda mask: mask['area'], reverse=True)
    
    filtered = []
    
    for i, mask_i in enumerate(masks):
        keep = True
        mask_i_bool = mask_i['segmentation']
        area_i = mask_i['area']
        
        for mask_j in filtered:
            mask_j_bool = mask_j['segmentation']
            
            intersection = np.logical_and(mask_i_bool, mask_j_bool).sum()
            
            # If most of mask_i is inside mask_j → discard
            if intersection / area_i > overlap_thresh:
                keep = False
                break
        
        if keep:
            filtered.append(mask_i)
    
    return filtered

def overlay_masks(image, masks, alpha=0.5):
    """
    image: original BGR image (cv2 format)
    masks: list of SAM masks
    alpha: transparency level
    """
    
    output = image.copy()

    for mask in masks:
        segmentation = mask['segmentation']
        
        # Random color
        color = np.array([random.randint(0,255),
                          random.randint(0,255),
                          random.randint(0,255)])
        
        # Create colored mask
        colored_mask = np.zeros_like(image)
        colored_mask[segmentation] = color
        
        # Blend
        output = cv2.addWeighted(output, 1, colored_mask, alpha, 0)

    return output

def save_images_from_masks(original_img, masks):
    for i, mask_info in zip(range(len(masks)), masks):
        new = original_img.copy()
        temp = original_img.copy()
        new[:] = 0

        mask = mask_info["segmentation"]
        new[mask] = temp[mask]    
        
        new = new.astype("uint8")
        cv2.imwrite(f"./seperated_images/{i}.png", new)

def filter_by_size(original_img, masks):
    x, _ = original_img.shape[:2]

    min_width = 0.4 * x

    filtered_masks = []

    for mask in masks:
        bounding_box_width = mask["bbox"][2]
        if min_width <= bounding_box_width:
            filtered_masks.append(mask)

    return filtered_masks


sam = sam_model_registry["vit_h"](checkpoint="./checkpoints/sam_vit_h_4b8939.pth")
mask_generator = SamAutomaticMaskGenerator(sam, pred_iou_thresh=0.9, stability_score_thresh=0.95)
print("Loaded SAM")

img = cv2.imread("./images/test3.png")
print("Read Image")
masks = mask_generator.generate(img)
print("Generated Masks")
filtered_masks = filter_by_size(img, masks)
print("Filtered Masks")
denested_masks = remove_nested_masks(filtered_masks)
print("Denested Masks")
masked_img = overlay_masks(img, denested_masks)
print("Overlayed Masks")
save_images_from_masks(img, denested_masks)
print("Saved Masks")

# envs = ['Aeolian', 'Alluvial', 'Paludal', 'Paludal']

# for env, mask in zip(envs, denested_masks):
#     x = mask["bbox"][0]
#     y = mask["bbox"][1]
#     cv2.putText(masked_img, env, (x, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)

cv2.imshow("masked image", masked_img)
cv2.imwrite("full.png", masked_img)
cv2.waitKey(0)
