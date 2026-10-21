import json

import numpy as np
import pytest

from evaluation import run_evaluation
from evaluation.run_evaluation import load_ground_truth, read_manifest


def test_empty_manifest_reports_pending(tmp_path, monkeypatch):
    dataset = tmp_path / "dataset"
    (dataset / "images").mkdir(parents=True)
    (dataset / "ground_truth").mkdir(parents=True)
    (dataset / "manifest.csv").write_text(
        "image_id,image_file,source,license,width,height,annotation_status,concerns,notes\n",
        encoding="utf-8",
    )
    out = tmp_path / "results"
    monkeypatch.setattr("sys.argv", [
        "run_evaluation", "--dataset", str(dataset), "--out", str(out),
    ])
    run_evaluation.main()
    status = json.loads((out / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "pending"
    assert status["n_annotated"] == 0
    assert not (out / "summary.json").exists()


def test_manifest_requires_columns(tmp_path):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("image_id,image_file\nimg1,a.png\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_manifest(manifest)


def test_ground_truth_shape_is_not_silently_resized(tmp_path):
    import cv2

    path = tmp_path / "mask.png"
    cv2.imwrite(str(path), np.zeros((32, 32), np.uint8))
    with pytest.raises(ValueError):
        load_ground_truth(path, (512, 512))


def test_ground_truth_values_are_validated(tmp_path):
    import cv2

    path = tmp_path / "mask.png"
    cv2.imwrite(str(path), np.full((32, 32), 127, np.uint8))
    with pytest.raises(ValueError):
        load_ground_truth(path, (32, 32))
