from pathlib import Path

from livp_maker import build_livp_variants, build_output_path


def test_build_output_path_adds_index(tmp_path: Path):
    output_path = tmp_path / "sample.livp"

    assert build_output_path(str(output_path), 3) == str(tmp_path / "sample_3.livp")


def test_build_livp_variants_creates_ten_files(tmp_path: Path):
    static_file = tmp_path / "cover.jpg"
    dynamic_file = tmp_path / "clip.mp4"
    static_file.write_bytes(b"static")
    dynamic_file.write_bytes(b"dynamic")

    created_files = build_livp_variants(
        str(static_file),
        str(dynamic_file),
        str(tmp_path / "result.livp"),
        start=1,
        end=10,
    )

    assert len(created_files) == 10
    assert created_files[0].endswith("result_1.livp")
    assert created_files[-1].endswith("result_10.livp")
    assert all(Path(path).exists() for path in created_files)
