"""Per-pixel feature stack for the Random Forest."""
import numpy as np
from scipy.ndimage import uniform_filter

from metrics import ndvi

FEATURE_NAMES = ["red", "green", "blue", "nir", "ndvi", "texture_3", "texture_9"]


def local_variance(band, size):
    """Variance in a size x size window around each pixel."""
    b = band.astype("float32")
    mean = uniform_filter(b, size)
    mean_sq = uniform_filter(b * b, size)
    # E[x^2] - E[x]^2. clip because float error can push it barely below zero
    return np.clip(mean_sq - mean * mean, 0, None)


def chip_features(img):
    """
    img: (4, H, W) uint8, NAIP band order R G B NIR.
    Returns (H*W, 7) float32 - one row per pixel, one column per feature.
    """
    nir = img[3].astype("float32")

    feats = [
        img[0].astype("float32"),      # red
        img[1].astype("float32"),      # green
        img[2].astype("float32"),      # blue
        nir,
        ndvi(img),
        local_variance(nir, 3),        # fine texture
        local_variance(nir, 9),        # coarser texture
    ]

    # stack to (7, H, W) then flatten each to a column -> (H*W, 7)
    return np.stack(feats, axis=0).reshape(len(feats), -1).T


def stack_chips(chips):
    """Feature matrix and labels for a list of chips."""
    X = np.concatenate([chip_features(c["img"]) for c in chips])
    y = np.concatenate([c["msk"].ravel() for c in chips])
    return X, y