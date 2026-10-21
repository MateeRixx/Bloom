import numpy as np
import pytest

from src.edge_detection import canny_edges, edge_density, laplacian_map, sobel_gradient


def test_constant_image_has_no_gradient():
    image = np.full((32, 32, 3), 100, np.uint8)
    result = sobel_gradient(image)
    assert result["magnitude"].max() == 0
    assert canny_edges(image).max() == 0


def test_vertical_step_has_strong_gradient():
    image = np.zeros((32, 32), np.uint8)
    image[:, 16:] = 255
    result = sobel_gradient(image)
    assert result["magnitude"].max() > 0
    edges = canny_edges(image, 20, 60)
    assert (edges > 0).sum() > 0


def test_laplacian_and_edge_density():
    image = np.zeros((32, 32), np.uint8)
    image[:, 16:] = 255
    response = laplacian_map(image)
    assert response["display"].shape == image.shape
    density = edge_density(canny_edges(image, 20, 60))
    assert 0 < density < 1


def test_invalid_canny_thresholds_raise():
    with pytest.raises(ValueError):
        canny_edges(np.zeros((8, 8), np.uint8), 100, 50)
