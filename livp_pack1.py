"""
livp_pack1.py

将一个静态图 + 一个动态图打包为可识别的 .livp 文件。

支持：

静态图：
    *.jpeg
    *.jpg
    *.heic
    *.HEIC.heic

动态图：
    *.mov


生成规则：

ZIP:
    - 不压缩
    - 不保存 extra attributes
    - Central Directory:
        静态图
        动态图

ZIP comment:

    part1 part2 part3 part4 part5 part6 part7

其中：

part1:
    静态类型
        heic = 0002
        jpeg = 0005

part2:
    30 + 静态文件名长度

part3:
    静态文件大小

part4:
    mov
        0003

part5:
    静态 offset + 30 + static_name_len
               + 30 + dynamic_name_len

part6:
    动态文件大小

part7:
    1000LIVP ASCII hex
"""


import argparse
import os
import struct
import subprocess
import tempfile
import shutil


MAGIC = "313030304C495650"


STATIC_TYPES = {
    ".heic": "0002",
    ".jpeg": "0005",
    ".jpg": "0005",
}


def detect_static_type(filename):
    """
    判断静态图片类型
    """

    lower = filename.lower()

    if lower.endswith(".heic"):
        return "0002"

    if lower.endswith(".jpeg") or lower.endswith(".jpg"):
        return "0005"

    raise ValueError(
        f"不支持的静态图片类型: {filename}"
    )


def check_inputs(static, dynamic):

    if not os.path.isfile(static):
        raise FileNotFoundError(static)

    if not os.path.isfile(dynamic):
        raise FileNotFoundError(dynamic)

    if not dynamic.lower().endswith(".mov"):
        raise ValueError(
            "动态图必须为 mov"
        )


def check_filename_rule(static, dynamic):

    """
    软规范：

    xxx.xxx.jpeg
    xxx.xxx.mov

    去掉最后扩展名后必须一致
    """

    s = os.path.basename(static)
    d = os.path.basename(dynamic)

    s_prefix = os.path.splitext(s)[0]
    d_prefix = os.path.splitext(d)[0]

    if s_prefix != d_prefix:
        raise ValueError(
            "静态图和动态图文件名主体不一致:\n"
            f"{s}\n{d}"
        )


def build_comment(static, dynamic):

    static_name = os.path.basename(static)
    dynamic_name = os.path.basename(dynamic)

    static_type = detect_static_type(static)

    static_size = os.path.getsize(static)
    dynamic_size = os.path.getsize(dynamic)


    # Local File Header 固定30字节
    static_name_len = len(
        static_name.encode("utf-8")
    )

    dynamic_name_len = len(
        dynamic_name.encode("utf-8")
    )


    # static offset
    #
    # 第一个文件永远 offset 0
    #

    static_offset = 0


    part2 = 30 + static_name_len


    #
    # dynamic Local Header offset:
    #
    # static local header
    # + static data
    #

    dynamic_offset = (
        static_offset
        + 30
        + static_name_len
        + static_size
    )


    part5 = (
        dynamic_offset
        + 30
        + dynamic_name_len
    )


    parts = [
        static_type,
        f"{part2:08X}",
        f"{static_size:08X}",
        "0003",
        f"{part5:08X}",
        f"{dynamic_size:08X}",
        MAGIC,
    ]


    return "".join(parts)



def create_zip(static, dynamic, output):

    """
    使用系统 zip 创建基础包

    注意：
    不能用 Python zipfile
    """

    with tempfile.TemporaryDirectory() as tmp:

        temp_zip = os.path.join(
            tmp,
            "tmp.zip"
        )


        #
        # -0:
        #   store only
        #
        # -X:
        #   exclude extra attributes
        #

        cmd = [
            "zip",
            "-0",
            "-X",
            temp_zip,
            os.path.basename(static),
            os.path.basename(dynamic),
        ]


        subprocess.run(
            cmd,
            cwd=os.path.dirname(static),
            check=True,
            stdout=subprocess.DEVNULL,
        )


        #
        # 写入 comment
        #

        comment = build_comment(
            static,
            dynamic
        )


        with open(temp_zip, "rb") as f:
            data = f.read()


        #
        # ZIP End Of Central Directory:
        #
        # signature:
        # 4 bytes
        #
        # comment length:
        # offset +20
        #

        eocd = data.rfind(
            b"PK\x05\x06"
        )

        if eocd < 0:
            raise RuntimeError(
                "不是有效zip"
            )


        old_len = struct.unpack(
            "<H",
            data[eocd+20:eocd+22]
        )[0]


        #
        # 去掉旧comment
        #

        data = (
            data[:eocd+20]
            +
            struct.pack(
                "<H",
                len(comment)
            )
            +
            data[eocd+22+old_len:]
        )


        data += comment.encode(
            "ascii"
        )


        with open(output, "wb") as f:
            f.write(data)



def main():

    parser = argparse.ArgumentParser(
        description=
        "将静态图+动态图打包为 livp"
    )


    parser.add_argument(
        "static",
        help="静态图片"
    )

    parser.add_argument(
        "dynamic",
        help="动态图 mov"
    )

    parser.add_argument(
        "output",
        help="输出 .livp"
    )


    args = parser.parse_args()


    check_inputs(
        args.static,
        args.dynamic
    )


    check_filename_rule(
        args.static,
        args.dynamic
    )


    if not args.output.endswith(".livp"):
        raise ValueError(
            "输出文件必须为 .livp"
        )


    create_zip(
        args.static,
        args.dynamic,
        args.output
    )


    print(
        "完成:",
        args.output
    )


if __name__ == "__main__":
    main()