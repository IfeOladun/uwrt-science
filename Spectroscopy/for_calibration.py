import cv2
import numpy as np
import matplotlib.pyplot as plt


def center_crop(img, crop_w, crop_h):
    # Get current dimensions
    h, w = img.shape[:2]
    
    # Calculate top-left start coordinates
    # Use floor division (//) to ensure integer indices
    start_x = (w - crop_w) // 2
    start_y = (h - crop_h) // 2
    
    # Perform crop: img[y_start:y_end, x_start:x_end]
    return img[start_y : start_y + crop_h, start_x : start_x + crop_w]

def crop_image(image, x, y, width, height):
    """
    Crop an image using top-left corner (x, y) and size (width, height).
    """
    return image[y:y+height, x:x+width]


camera = cv2.VideoCapture(1, cv2.CAP_DSHOW) # adjust based on number of cameras and camera order 

fig, ax = plt.subplots()
dark_spectrum = np.loadtxt("./references/dark_spectrum.txt") # this gets the spectrum when the led is off
reference_spectrum = np.loadtxt("./references/reference_spectrum.txt") # this gets the spectrum with empty cuvette
corrected_reference_spectrum = reference_spectrum - dark_spectrum
corrected_reference_spectrum[corrected_reference_spectrum <= 1] = 1

while(True):
    ret, frame = camera.read()
    cropped_frame_width, cropped_frame_height = 158, 110
    cropped_frame = crop_image(frame, 220, 175, cropped_frame_width, cropped_frame_height)
    grayscale = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
    spectrum = np.mean(grayscale, axis=0)
    x = np.arange(len(spectrum))

    corrected_spectrum = spectrum - dark_spectrum
    corrected_spectrum[corrected_spectrum <= 1] = 1
    transmittance = corrected_spectrum / corrected_reference_spectrum
    absorbance = -np.log10(transmittance)

    ax.cla()
    ax.plot(x, absorbance)
    ax.set_title("Absorbance vs pixel")
    ax.set_xlabel("Pixel")
    ax.set_ylabel("Absorbance")
    ax.set_ylim(-.5, 2)
    ax.set_xlim(0, 157)

    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())

    cv2.imshow('frame', cropped_frame)
    cv2.imshow("spectrum", img)

    if cv2.waitKey(10) & 0xFF == ord('p'):
        # np.savetxt("./references/reference_spectrum.txt", spectrum)
        # np.savetxt("./references/dark_spectrum.txt", spectrum)
        break


camera.release()
cv2.destroyAllWindows()


