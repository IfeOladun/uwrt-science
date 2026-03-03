import cv2, random, os, time
import numpy as np
from google import genai
from google.genai.errors import ServerError
from dotenv import load_dotenv
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

def save_images_from_masks(original_img, masks, path):
    for i, mask_info in zip(range(len(masks)), masks):
        new = original_img.copy()
        temp = original_img.copy()
        new[:] = 0

        mask = mask_info["segmentation"]
        new[mask] = temp[mask]    
        
        new = new.astype("uint8")
        cv2.imwrite(f"{path}/{i}.png", new)

def filter_by_size(original_img, masks):
    x, y = original_img.shape[:2]
    size = x * y

    lower_threshold = 0.05 * size
    upper_threshold = 0.7 * size

    filtered_masks = []

    for mask in masks:
        area = mask["area"]
        if lower_threshold <= area <= upper_threshold:
            filtered_masks.append(mask)

    return filtered_masks

def ask_gemini(image_url, question):
    with open(image_url, "rb") as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
        genai.types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg",
        ),
        question
        ]
    )

    return response.text


load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key)

sam = sam_model_registry["vit_h"](checkpoint="./checkpoints/sam_vit_h_4b8939.pth")
mask_generator = SamAutomaticMaskGenerator(sam, pred_iou_thresh=0.9, stability_score_thresh=0.95)
print("Loaded SAM")

img = cv2.imread("./testing/images/test3.png")
saved_imgs_path = "./testing/seperated_images"
print("Read Image")
masks = mask_generator.generate(img)
print("Generated Masks")
filtered_masks = filter_by_size(img, masks)
print("Filtered Masks")
denested_masks = remove_nested_masks(filtered_masks)
print("Denested Masks")
masked_img = overlay_masks(img, denested_masks)
cv2.imwrite("./testing/full.png", masked_img)
print("Overlayed Masks")
save_images_from_masks(img, denested_masks, saved_imgs_path)
print("Saved Masks")

# cv2.imshow("masked image", masked_img)
# cv2.waitKey(0)

question = "Can you tell me the original depositional environment of the " \
            "strata in this image. The depositional environment must be one of these: Fluvial, " \
            "Alluvial, Lacustrine, Paludal, Aeolian, or Glacial. Note that there is only one " \
            "strata present in the photo. Give reasoning behind why the strata is " \
            "from the corresponding depositional environment. Don't respond in markdown. " \
            "Respond with Depositional Environment: and Reasoning: sections. It should be a " \
            "dict like this: {'Depositional Environment': '...', 'Reasoning': '...'}. " \
            "Don't add any extra spaces for any reason. If for any reason " \
            "the image looks like the sky you can return this: " \
            "{'Depositional Environment': 'Sky', 'Reasoning': '...'}."
number_of_images = len(denested_masks)

depositional_environments = []
reasonings = []
for index in range(number_of_images):
    try:
        response = ask_gemini(f"{saved_imgs_path}/{index}.png", question)
        if response == None:
            print("No response from Gemini. Trying Again.")
            response = ask_gemini(f"{saved_imgs_path}/{index}.png", question)
    except ServerError as e:
        print("Server Error. Trying Again.")
        time.sleep(30)
        response = ask_gemini(f"{saved_imgs_path}/{index}.png", question)

    response_dict = eval(response)
    depositional_environments.append(response_dict["Depositional Environment"])
    reasonings.append(response_dict["Reasoning"])

for env, mask in zip(depositional_environments, denested_masks):
    x = mask["bbox"][0]
    y = mask["bbox"][1]
    cv2.putText(masked_img, env, (x, y + 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 1, cv2.LINE_AA)

cv2.imshow("masked image", masked_img)
cv2.imwrite("annotated.png", masked_img)
cv2.waitKey(0)