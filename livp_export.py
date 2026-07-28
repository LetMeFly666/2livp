"""
livp_export.py

递归导出图片目录。

规则：

1.
如果一个目录中存在：

    xxx.jpeg.jpeg
    xxx.jpeg.mov

或者：

    xxx.HEIC.heic
    xxx.HEIC.mov

则：

    打包为 xxx.livp

    不导出原始两个文件。


2.
否则：

    导出目录中的所有文件。


输出：

默认：

    输入目录/_exported


如果存在：

    _exported_xxxxxxxx


所有文件直接放在输出目录：

    output/
        a.jpeg
        b.mov
        c.livp


文件冲突自动增加：

    _1
    _2


普通文件：

优先硬链接：

    os.link()

失败：

    shutil.copy2()
"""


import argparse
import os
import shutil
import subprocess
import uuid


STATIC_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".heic",
}


def is_static(filename):

    lower = filename.lower()

    return any(
        lower.endswith(x)
        for x in STATIC_EXTENSIONS
    )



def is_dynamic(filename):

    return filename.lower().endswith(
        ".mov"
    )



def exported_name(path):

    """
    解决同名文件

    xxx.jpg

    xxx_1.jpg
    xxx_2.jpg
    """

    if not os.path.exists(path):
        return path


    dirname = os.path.dirname(path)

    filename = os.path.basename(path)


    name, ext = os.path.splitext(filename)


    i = 1

    while True:

        new = os.path.join(
            dirname,
            f"{name}_{i}{ext}"
        )


        if not os.path.exists(new):
            return new

        i += 1



def safe_link(src, dst):

    """
    优先硬链接

    失败复制
    """

    try:

        os.link(
            src,
            dst
        )

    except OSError:

        shutil.copy2(
            src,
            dst
        )



def create_output_dir(src, user_output):

    if user_output:

        os.makedirs(
            user_output,
            exist_ok=True
        )

        return user_output


    base = os.path.join(
        src,
        "_exported"
    )


    if not os.path.exists(base):

        os.makedirs(base)

        return base


    while True:

        name = (
            "_exported_"
            +
            uuid.uuid4()
            .hex[:8]
        )


        path = os.path.join(
            src,
            name
        )


        if not os.path.exists(path):

            os.makedirs(path)

            return path



def find_live_pairs(files):

    """
    返回：

    [
        (
          static,
          mov
        )
    ]

    """

    statics = {}
    movs = {}


    for f in files:

        full = f


        base, ext = os.path.splitext(
            os.path.basename(f)
        )


        if is_static(f):

            statics[base] = full


        elif is_dynamic(f):

            movs[base] = full



    pairs = []


    for key in statics:

        if key in movs:

            pairs.append(
                (
                    statics[key],
                    movs[key]
                )
            )


    return pairs



def pack_live(static, mov, output):

    """
    调用脚本一
    """

    script = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "livp_pack.py"
    )


    subprocess.run(
        [
            "python3",
            script,
            static,
            mov,
            output,
        ],
        check=True
    )



def export_directory(src, output):

    """
    处理单个目录

    """

    files = []

    for name in os.listdir(src):

        path = os.path.join(
            src,
            name
        )

        if os.path.isfile(path):

            files.append(path)



    handled = set()


    #
    # 先处理 live pair
    #

    pairs = find_live_pairs(files)


    for static, mov in pairs:


        base = os.path.splitext(
            os.path.basename(static)
        )[0]


        out = exported_name(
            os.path.join(
                output,
                base + ".livp"
            )
        )


        print(
            "[LIVP]",
            static,
            "+",
            mov,
            "->",
            out
        )


        pack_live(
            static,
            mov,
            out
        )


        handled.add(
            static
        )

        handled.add(
            mov
        )



    #
    # 其他全部导出
    #

    for f in files:


        if f in handled:

            continue


        out = exported_name(
            os.path.join(
                output,
                os.path.basename(f)
            )
        )


        print(
            "[FILE]",
            f,
            "->",
            out
        )


        safe_link(
            f,
            out
        )



def main():

    parser = argparse.ArgumentParser(
        description=
        "递归导出图片并转换 live 图为 livp"
    )


    parser.add_argument(
        "input",
        help="输入目录"
    )


    parser.add_argument(
        "--output",
        help="输出目录"
    )


    args = parser.parse_args()



    src = os.path.abspath(
        args.input
    )


    if not os.path.isdir(src):

        raise ValueError(
            "输入必须是目录"
        )


    output = create_output_dir(
        src,
        args.output
    )


    print(
        "输出目录:",
        output
    )



    #
    # 递归遍历
    #

    for root, dirs, files in os.walk(src):


        #
        # 不扫描输出目录
        #

        if os.path.abspath(root) == os.path.abspath(output):

            continue



        paths = [
            os.path.join(root, x)
            for x in files
        ]


        if paths:

            export_directory(
                root,
                output
            )



    print(
        "完成"
    )



if __name__ == "__main__":
    main()

"""
run result:
python /Users/tisfy/Projects/2livp/livp_export.py . 
输出目录: /Users/tisfy/Downloads/1/_exported
[FILE] /Users/tisfy/Downloads/1/.DS_Store -> /Users/tisfy/Downloads/1/_exported/.DS_Store
[FILE] /Users/tisfy/Downloads/1/IMG_5114/IMG_5114.PNG -> /Users/tisfy/Downloads/1/_exported/IMG_5114.PNG
[FILE] /Users/tisfy/Downloads/1/1/.DS_Store -> /Users/tisfy/Downloads/1/_exported/.DS_Store_1
[FILE] /Users/tisfy/Downloads/1/1/2/某线上AI峰会电话.m4a -> /Users/tisfy/Downloads/1/_exported/某线上AI峰会电话.m4a
[LIVP] /Users/tisfy/Downloads/1/IMG_5120/IMG_5120.HEIC + /Users/tisfy/Downloads/1/IMG_5120/IMG_5120.MOV -> /Users/tisfy/Downloads/1/_exported/IMG_5120.livp
完成: /Users/tisfy/Downloads/1/_exported/IMG_5120.livp
"""
