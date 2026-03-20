import cv2
import numpy as np


def crop_image(image, x, y, width, height):
    """
    Crop an image using top-left corner (x, y) and size (width, height).
    """
    return image[y:y+height, x:x+width]


camera = cv2.VideoCapture(1, cv2.CAP_DSHOW) # adjust based on number of cameras and camera order 


while(True):
    ret, frame = camera.read()
    cropped_frame_width, cropped_frame_height = 158, 110 # from manual calibration
    cropped_frame = crop_image(frame, 220, 175, cropped_frame_width, cropped_frame_height)
    grayscale = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
    spectrum = np.mean(grayscale, axis=0)
    x = np.arange(len(spectrum))

    cv2.imshow('frame', cropped_frame)

    if cv2.waitKey(10) & 0xFF == ord('p'):
        np.savetxt("./references/reference_spectrum.txt", spectrum)
        break


camera.release()
cv2.destroyAllWindows()


