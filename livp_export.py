'''
Author: LetMeFly
Date: 2026-08-01 15:12:04
LastEditors: LetMeFly.xyz
LastEditTime: 2026-08-03 16:57:02
Description: still 古法编程
Description: 没livp_maker.py美观
'''
import os
import argparse
from pathlib import Path
import uuid
from dataclasses import dataclass, field, asdict
from pprint import pprint
import livp_maker


SUPPORTED_STATIC_EXTS = [".jpg", ".jpeg", ".heic"]
SUPPORTED_DYNAMIC_EXTS = [".mov", ".mp4"]
IS_DEBUG = False
IS_TEST = False


# 导出方式
@dataclass
class ExportList:
    # 要直接导出的文件
    @dataclass
    class StaticFile:
        path: Path
        original_name: str
        exported_name: str
    
    # 要合并为live图的2个文件
    @dataclass
    class DynamicFile:
        path: Path
        static_name: str
        dynamic_name: str
        livp_name: str
    
    static_files: list[StaticFile] = field(default_factory=list)
    dynamic_files: list[DynamicFile] = field(default_factory=list)


# 当前目录下有哪些文件
"""
{
    "image_123": {
        static: [
            "image_123.jpg",
            "image_123.jPg"
        ],
        dynamic: [
            "image_123.mov"
            "image_123.mp4"
        ],
        other: [
            "image_123.txt"
        ]
    },
    "IMAGE_123": {
        static: [
            "IMAGE_123.jpg"
        ],
        dynamic: [],
        other: []
    }
}
"""
type FilesStemSuffix = dict[str, FileGroup]
@dataclass
class FileGroup:
    static: list[str] = field(default_factory=list)
    dynamic: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)


def gen_unique_export_name(export_names: set[str], filename: str, filetype: str) -> str:
    name = filename + "." + filetype if filetype else filename
    if name not in export_names:
        return name
    index = 1
    while True:
        name = f"{filename}_{index}"
        if filetype:
            name += "." + filetype
        if name.casefold() not in export_names:
            return name
        index += 1


def gen_export_list(src: Path, exclude_prefixes: list[str]) -> ExportList:
    export_list = ExportList()
    exported_names = set()
    for root, dirs, files_original in os.walk(src):
        # 排除指定前缀的文件夹
        dirs[:] = [d for d in dirs if not any(d.startswith(prefix) for prefix in exclude_prefixes)]
        files_original = [f for f in files_original if not any(f.startswith(prefix) for prefix in exclude_prefixes)]
        # 转为以 stem 为 key 的字典
        files: FilesStemSuffix = {}
        for file in files_original:
            stem, ext = os.path.splitext(file)
            files.setdefault(stem, FileGroup())
            if ext.lower() in SUPPORTED_STATIC_EXTS:
                files[stem].static.append(file)
            elif ext.lower() in SUPPORTED_DYNAMIC_EXTS:
                files[stem].dynamic.append(file)
            else:
                files[stem].other.append(file)
        
        # 开始配对、生成导出列表
        for stem, group in files.items():
            num_static, num_dynamic = len(group.static), len(group.dynamic)
            num_less = min(num_static, num_dynamic)
            for i in range(num_less):
                live_static = group.static[i]
                live_dynamic = group.dynamic[i]
                livp_name = gen_unique_export_name(exported_names, stem, "livp")
                exported_names.add(livp_name.casefold())  # Windows和Mac的文件系统大小写不敏感
                export_list.dynamic_files.append(
                    ExportList.DynamicFile(
                        path=Path(root),
                        static_name=live_static,
                        dynamic_name=live_dynamic,
                        livp_name=livp_name
                    )
                )
            if num_static <= num_dynamic:
                others = group.dynamic[num_less:] + group.other
            else:
                others = group.static[num_less:] + group.other
            for other in others:
                _, ext = os.path.splitext(other)
                other_name = gen_unique_export_name(exported_names, stem, ext.lstrip("."))
                exported_names.add(other_name.casefold())  # Windows和Mac默认APFS的文件系统大小写不敏感
                export_list.static_files.append(
                    ExportList.StaticFile(
                        path=Path(root),
                        original_name=other,
                        exported_name=other_name
                    )
                )
    return export_list


def gen_output_dir(src: Path, dst: Path | None) -> Path:
    if dst:
        os.makedirs(
            dst,
            exist_ok=True
        )
        return dst

    base = src / "_exported"
    if not base.exists():
        os.makedirs(base)
        return base

    while True:
        # 假设不会有过多过多的已存在文件夹
        name = "_exported_" + uuid.uuid4().hex[:8]
        path = src / name
        if not path.exists():
            os.makedirs(path)
            return path


def export(export_list: ExportList, dst_dir: Path):
    for static_file in export_list.static_files:
        src = static_file.path / static_file.original_name
        dst = dst_dir / static_file.exported_name
        try:
            os.link(src, dst)
        except Exception as e:
            print(f"硬链接失败，尝试复制文件：{src} -> {dst}，错误：{e}")
            try:
                import shutil
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"复制文件失败：{src} -> {dst}，错误：{e}")

    for dynamic_file in export_list.dynamic_files:
        src_static = dynamic_file.path / dynamic_file.static_name
        src_dynamic = dynamic_file.path / dynamic_file.dynamic_name
        dst_livp = dst_dir / dynamic_file.livp_name
        try:
            livp_maker.main(src_static, src_dynamic, dst_livp)
        except Exception as e:
            print(f"生成livp失败：{src_static}, {src_dynamic} -> {dst_livp}，错误：{e}")


class TestInputGenerator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.files = [
            "test001.jpg", "test001.mov",  # -> livp
            "test002.jpeg", "test002.mp4",  # -> livp
            "test003.heic", "test003.mov",  # -> livp
            "test004.jpg",  # -> jpg
            "test005.mp4",  # -> mp4
            "test006.txt",  # -> txt
            "test007.jpg", "test007.mov", "test007.mp4",  # -> livp + mp4/mov
            ".DS_Store_test008",  # -> 排除
            "_exported_test/test009.jpg",  # -> 排除
            "a/test010.jpg", "a/test010.mov",  # -> livp
            "b/test011.jpg", "b/test011.mp4", "b/test011",  # -> livp + test011
            "c/a/test012.jpg", "c/a/test012.mov",  # -> livp
            "d/test013.jpg", "e/test013.jpg",  # -> test013.jpg + test013_1.jpg
            "f/test014.jpg", "f/test014.mov", "g/test014.jpg", "g/test014.mov",  # -> test014.livp + test014_1.livp
            "test015_withoutextension",  # -> test015_withoutextension
            "test016_upper.JPG", "test016_upper.MOV",  # -> test016_upper.livp
            "test017_IMG_6229.JPEG", "test017_IMG_6229.MP4",  # -> test017_IMG_6229.livp
            "tesT018-tEst.jPg", "tesT018-tEst.mOv",  # -> tesT018-tEst.livp
            "test019-中文.jpg", "test019-中文.mov",  # -> test019-中文.livp
            "test020_shouldNotBePaired.jpg", "test020_shouldnotbepaired.mov",  # -> test020_shouldNotBePaired.jpg + test020_shouldnotbepaired.mov
        ]
        self.expected_files = set([
            "test001.livp",
            "test002.livp",
            "test003.livp",
            "test004.jpg",
            "test005.mp4",
            "test006.txt",
            "test007.livp", "test007.mp4",
            "test010.livp",
            "test011.livp", "test011",
            "test012.livp",
            "test013.jpg", "test013_1.jpg",
            "test014.livp", "test014_1.livp",
            "test015_withoutextension",
            "test016_upper.livp",
            "test017_IMG_6229.livp",
            "tesT018-tEst.livp",
            "test019-中文.livp",
            "test020_shouldNotBePaired.jpg", "test020_shouldnotbepaired.mov",
        ])
        self._gen_test_input_dir()
    
    @staticmethod
    def input_dirname() -> Path:
        return Path("test_input")
    
    def _gen_test_input_dir(self):
        os.makedirs(
            self.input_dirname(),
            exist_ok=True
        )
        for file in self.files:
            path = self.input_dirname() / file
            if os.path.exists(path):
                continue
            print(f"生成测试文件：{path}")
            os.makedirs(
                path.parent,
                exist_ok=True
            )
            with open(path, "wb") as f:
                f.write(b"test")
    
    def assert_expected_files(self, export_list: ExportList):
        really_exported_files = set(
            [f.exported_name for f in export_list.static_files] +
            [f.livp_name for f in export_list.dynamic_files]
        )
        assert really_exported_files == self.expected_files, \
            f"导出文件不符合预期，\n" + \
            f"预期：{self.expected_files}\n" + \
            f"实际：{really_exported_files}\n" + \
            f"差异：{really_exported_files.difference(self.expected_files)}\n"
    

def init_args() -> tuple[Path, Path, list[str]]:
    global IS_DEBUG
    global IS_TEST
    parser = argparse.ArgumentParser(
        description=(
            "递归导出一个文件夹下的所有文件，若能合并转为live图则转换\n\n"
            "  - 若同一文件夹下存在同名的静态图片和动态视频，则将其合并为live图导出(同时存在多种可能组合则按先组合先消除原则)\n"
            "  - 否则将其单独导出(默认硬链接的方式导出，失败再复制)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "input",
        type=Path,
        metavar="INPUT_DIR",
        help="输入文件夹路径"
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="OUTPUT_DIR",
        help="输出文件夹路径，默认输入文件夹/_exported{_random_suffix}"
    )
    default_exclude_prefixes = [".", "_exported"]
    parser.add_argument(
        "--exclude-prefix",
        action="append",
        default=[],
        help="排除的前缀文件夹名，默认排除 “" + "”、“".join(default_exclude_prefixes) + "” 开头的文件夹"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="启用测试模式 | 测试模式下不依据input变量，而是自己生成一个测试文件夹"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.1.0"
    )

    args = parser.parse_args()

    IS_TEST = args.test
    src = args.input.resolve() if not IS_TEST else TestInputGenerator.input_dirname().resolve()
    if not src.is_dir() and not IS_TEST:
        parser.error(f"{src} 不是目录")
    dst = gen_output_dir(src, args.output)
    exclude_prefixes = args.exclude_prefix or default_exclude_prefixes
    IS_DEBUG = IS_TEST | args.debug
    return src, dst, exclude_prefixes


if __name__ == "__main__":
    src, dst, exclude_prefixes = init_args()
    if IS_TEST:
        test_input_generator = TestInputGenerator()
    export_list = gen_export_list(src, exclude_prefixes)
    if IS_DEBUG:
        pprint(asdict(export_list))
    if IS_TEST:  # 测试模式下不真的导出文件
        test_input_generator.assert_expected_files(export_list)
        print("测试通过")
        exit(0)
    export(export_list, dst)
