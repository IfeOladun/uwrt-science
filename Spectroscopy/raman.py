import cv2
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.signal import savgol_filter, find_peaks


def crop_image(image, x, y, width, height):
    """
    Crop an image using top-left corner (x, y) and size (width, height).
    """
    return image[y:y+height, x:x+width]

def baseline_als(y, lam, p, niter=10):
    L = len(y)
    D = sparse.csc_matrix(np.diff(np.eye(L), 2))
    w = np.ones(L)
    for i in range(niter):
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w*y)
        w = p * (y > z) + (1-p) * (y < z)
    return z

def lookup_raman_df(wavenumber):
    return df[
        (df["Wavenumber_Start_cm-1"] <= wavenumber) &
        (df["Wavenumber_End_cm-1"] >= wavenumber)
    ]


df = pd.read_csv("raman_band_correlation.csv") # get dataframe from raman correlations for later
camera = cv2.VideoCapture(1, cv2.CAP_DSHOW) # adjust based on number of cameras and camera order 
#(cv2.CAP_DSHOW/cv2.CAP_MSMF are for windows cv2.CAP_V4L2/cv2.CAP_FFMPEG/cv2.CAP_GSTREAMER are for linux)
camera.set(cv2.CAP_PROP_FPS, 30)

fig, ax = plt.subplots()

# commented out. rn for testing
start = time.time()
raman_duration = 10 # amount of time sample will be exposed to light
spectra = []


while (time.time() - start <= raman_duration):
# while(True):
    ret, frame = camera.read()
    cropped_frame_width, cropped_frame_height = 290, 140
    cropped_frame = crop_image(frame, 145, 155, cropped_frame_width, cropped_frame_height)
    grayscale = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
    
    spectrum = np.mean(grayscale, axis=0)

    # box filter to smooth out the spectrum 
    # filtered_spectrum = np.convolve(spectrum, np.ones(11)/11, mode='same')

    # Savitzky-Golay filter
    sg_filtered_spectrum = savgol_filter(spectrum, window_length=21, polyorder=3) # way better

    x = np.arange(len(sg_filtered_spectrum))
    # baseline = np.polyval(np.polyfit(x, sg_filtered_spectrum, deg=4), x)
    als = baseline_als(sg_filtered_spectrum, 10000, 0.01, 100) # way better than above (asymmetric least squares smoothing)
    baseline_adjusted_spectrum = sg_filtered_spectrum - als
    spectra.append(baseline_adjusted_spectrum)

    nm_per_pixel = 250/cropped_frame_width # manually callibrated (currently using ceiling cfls)
    starting_nm = 375
    wavelengths = nm_per_pixel * x + starting_nm

    raman_shift = (1/532 - 1/wavelengths) * 1e7

    # peaks, _ = find_peaks(sg_filtered_spectrum)
    # for peak in peaks:
    #     print(f"peak at {wavelengths[peak]}, {sg_filtered_spectrum[peak]}")

    ax.cla()
    # ax.plot(raman_shift, als, "r")
    # ax.plot(raman_shift, sg_filtered_spectrum, "k")
    ax.plot(wavelengths, baseline_adjusted_spectrum, "b")
    ax.plot(wavelengths, spectrum)
    # ax.set_title("Raw intensity vs pixel")
    ax.set_xlabel("Approx. Wavelengths")
    # ax.set_xlabel("Raman Shift (cm^-1)")
    ax.set_ylabel("Intensity")

    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    cv2.imshow("Raman", img_bgr)
    cv2.imshow('frame', cropped_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


camera.release()

np_spectra_avg = np.mean(np.array(spectra), axis=0)
min_peak_distance = 10
min_peak_height = 3*np.std(np_spectra_avg) # the 3 subject to change / needs to be fine tuned
peaks, _ = find_peaks(np_spectra_avg, height=min_peak_height, distance=min_peak_distance)
# print(wavelengths[peaks])

ax.cla()
ax.plot(raman_shift, np_spectra_avg)
# vals = [min_peak_height/6, min_peak_height/3, 2*min_peak_height/3, min_peak_height]
# [ax.axhline(y=val, color='k', linestyle='--') for val in vals]
ax.set_xlabel("Approx. Wavelengths")
ax.set_ylabel("Intensity")
plt.show()

cv2.destroyAllWindows()
