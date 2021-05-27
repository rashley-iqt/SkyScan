"""test all scripts."""

from customvox51 import build_image_list, create_voxel51_dataset
from main import read_config

import fiftyone as fo

def test_build_image_list():
    """Test build_image_list()."""
    output = build_image_list("test")
    assert output[0]["bearing"] == "194"
    assert output[0]["distance"] == "11882"
    assert output[0]["elevation"] == "50"
    assert output[0]["external_id"] == "ac760d_194_50_11882_2021-05-13-14-13-42"
    assert output[0]["icao24"] == "ac760d"

def test_create_voxel51_dataset():
    """Test create_voxel51_dataset()."""
    test_dataset = create_voxel51_dataset("test")
    assert isinstance(test_dataset, fo.core.dataset.Dataset)


def test_read_config():
    """Test read_config()."""
    config = read_config("test_config.ini")
    assert config["file_names"]["dataset_name"] == "hello_world"
    assert config["file_locations"]["image_directory"] == "foo"
