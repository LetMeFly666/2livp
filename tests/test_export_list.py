'''
Author: LetMeFly
Date: 2026-08-03 17:06:52
LastEditors: LetMeFly.xyz
LastEditTime: 2026-08-03 17:36:53
'''
from pathlib import Path
from livp_export import gen_export_list, ExportList


def create_files(tmp_path: Path, files: list[str]):
    for file in files:
        path = tmp_path / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test")


def exported_names(export_list: ExportList):
    return {
        *[f.exported_name for f in export_list.static_files],
        *[f.livp_name for f in export_list.dynamic_files],
    }


def test_basic_pair(tmp_path):
    create_files(
        tmp_path,
        [
            "a.jpg",
            "a.mov",
        ],
    )

    result = gen_export_list(tmp_path, [])

    assert len(result.dynamic_files) == 1
    assert result.dynamic_files[0].static_name == "a.jpg"
    assert result.dynamic_files[0].dynamic_name == "a.mov"
    assert result.dynamic_files[0].livp_name == "a.livp"


def test_unpaired_static_export(tmp_path):
    create_files(
        tmp_path,
        [
            "a.jpg",
        ],
    )

    result = gen_export_list(tmp_path, [])

    assert len(result.static_files) == 1
    assert result.static_files[0].original_name == "a.jpg"
    assert result.static_files[0].exported_name == "a.jpg"


def test_unpaired_dynamic_export(tmp_path):
    create_files(
        tmp_path,
        [
            "a.mov",
        ],
    )

    result = gen_export_list(tmp_path, [])

    assert len(result.static_files) == 1
    assert result.static_files[0].exported_name == "a.mov"


# fix by LetMeFly
def test_multiple_dynamic_files(tmp_path):
    create_files(
        tmp_path,
        [
            "a.jpg",
            "a.mov",
            "a.mp4",
        ],
    )

    result = gen_export_list(tmp_path, [])
    exported_names_set = exported_names(result)

    assert exported_names_set == { "a.livp", "a.mp4" } or \
        exported_names_set == { "a.livp", "a.mov" }


def test_case_sensitive_filename_should_not_pair(tmp_path):
    """
    macOS 文件系统可能大小写不敏感，
    但是业务逻辑应该区分文件名大小写。
    """
    create_files(
        tmp_path,
        [
            "a.jpg",
            "A.mov",
        ],
    )

    result = gen_export_list(tmp_path, [])

    assert exported_names(result) == {
        "a.jpg",
        "A.mov",
    }


def test_case_preserve_export_name(tmp_path):
    """
    输入:
        IMG.JPG + IMG.MOV

    输出:
        IMG.livp

    不应该变成:
        img.livp
    """
    create_files(
        tmp_path,
        [
            "IMG.JPG",
            "IMG.MOV",
        ],
    )

    result = gen_export_list(tmp_path, [])

    assert result.dynamic_files[0].livp_name == "IMG.livp"


def test_duplicate_output_name(tmp_path):
    create_files(
        tmp_path,
        [
            "a.jpg",
            "b/a.jpg",
        ],
    )

    result = gen_export_list(tmp_path, [])

    assert exported_names(result) == {
        "a.jpg",
        "a_1.jpg",
    }

# # 很多测试场景下这两个文件不会同时存在。
# def test_same_name_different_case_conflict(tmp_path):
#     create_files(
#         tmp_path,
#         [
#             "a.jpg",
#             "A.jpg",
#         ],
#     )

#     result = gen_export_list(tmp_path, [])

#     assert exported_names(result) == {
#         "a.jpg",
#         "A_1.jpg",
#     }


def test_exclude_prefix(tmp_path):
    create_files(
        tmp_path,
        [
            ".hidden/a.jpg",
            "_exported/b.jpg",
            "normal/c.jpg",
        ],
    )

    result = gen_export_list(
        tmp_path,
        [".", "_exported"],
    )

    assert exported_names(result) == {
        "c.jpg",
    }


def test_nested_directory(tmp_path):
    create_files(
        tmp_path,
        [
            "a/b/c.jpg",
            "a/b/c.mov",
        ],
    )

    result = gen_export_list(tmp_path, [])

    assert result.dynamic_files[0].path == tmp_path / "a/b"
