import csv

import numpy as np

from src.features import export_features_csv, region_features


def test_square_region_features():
    image = np.full((64, 64, 3), 180, np.uint8)
    mask = np.zeros((64, 64), np.uint8)
    mask[20:40, 20:40] = 255
    rows = region_features(image, mask, concern="test")
    assert len(rows) == 1
    row = rows[0]
    assert row["area_px"] == 400
    assert row["aspect_ratio"] == 1.0
    assert row["extent"] == 1.0
    assert 0 < row["circularity"] <= 1.0
    assert row["glcm_contrast"] is not None
    assert row["lbp_entropy"] is not None
    assert 0 <= row["edge_density"] <= 1


def test_empty_mask_returns_no_rows():
    image = np.zeros((32, 32, 3), np.uint8)
    mask = np.zeros((32, 32), np.uint8)
    assert region_features(image, mask) == []


def test_export_features_csv(tmp_path):
    image = np.full((32, 32, 3), 100, np.uint8)
    mask = np.zeros((32, 32), np.uint8)
    mask[8:16, 8:16] = 255
    rows = region_features(image, mask, concern="acne")
    target = export_features_csv(rows, tmp_path / "features.csv")
    assert target.exists()
    with target.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        written = list(reader)
    assert len(written) == 1
    assert written[0]["concern"] == "acne"
