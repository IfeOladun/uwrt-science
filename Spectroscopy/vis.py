import cv2
import numpy as np
import matplotlib.pyplot as plt


def crop_image(image, x, y, width, height):
    """
    Crop an image using top-left corner (x, y) and size (width, height).
    """
    return image[y:y+height, x:x+width]

camera = cv2.VideoCapture(1, cv2.CAP_DSHOW) # adjust based on number of cameras and camera order 

fig, [ax1, ax2] = plt.subplots(1, 2)
fig.set_figwidth(10)
reference_spectrum = np.loadtxt("./references/reference_spectrum.txt") # this gets the spectrum with empty cuvette
reference_spectrum[reference_spectrum <= 1] = 1

spectrum_frame = ax2.imshow(np.random.randn(158, 110))

while(True):
    ret, frame = camera.read()
    cropped_frame_width, cropped_frame_height = 158, 110 # from manual calibration
    cropped_frame = crop_image(frame, 220, 175, cropped_frame_width, cropped_frame_height)
    grayscale = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
    spectrum = np.mean(grayscale, axis=0)
    x = np.arange(len(spectrum))

    spectrum[spectrum <= 1] = 1
    transmittance = spectrum / reference_spectrum
    absorbance = -np.log10(transmittance)

    wavelengths = (x * 300/np.max(x)) + 400

    ax1.cla()
    ax1.plot(wavelengths, absorbance, "k")
    ax1.set_title("Absorbance vs Wavelength")
    ax1.set_xlabel("Wavelength")
    ax1.set_ylabel("Absorbance")
    ax1.set_ylim(-.5, 3)
    ax1.set_xlim(400, 700)

    spectrum_frame.set_array(cropped_frame)
    ax2.axis("off")
    ax2.set_title("Visible Light Spectrum")

    fig.canvas.draw()

    img = np.asarray(fig.canvas.buffer_rgba())

    cv2.imshow("Visible Light Absorption Spectrometer", img)

    if cv2.waitKey(10) & 0xFF == ord('p'):
        break


camera.release()
cv2.destroyAllWindows()


