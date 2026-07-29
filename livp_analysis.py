# 批量分析livp文件样本是否符合逆向结果
# Mainly by ChatGPT

import zipfile
from pathlib import Path


IMAGE_EXT = (
    ".jpg",
    ".jpeg",
    ".heic",
    ".heif",
)

VIDEO_EXT = (
    ".mov",
    ".mp4",
)


def parse_comment(comment: bytes):

    text = comment.decode(
        "ascii",
        errors="replace"
    )

    if len(text) < 48:
        return {}

    return {
        "part1": text[0:4],
        "part2": int(text[4:12], 16),
        "part3": int(text[12:20], 16),
        "part4": text[20:24],
        "part5": int(text[24:32], 16),
        "part6": int(text[32:40], 16),
        "part7": text[40:],
    }


def check_yesno(v):
    return "PASS" if v else "FAIL"


def analyze(zip_path):

    result = {
        "filename": zip_path.name,
        "zip_comment": "",

        "part1": "",
        "part2": "",
        "part3": "",
        "part4": "",
        "part5": "",
        "part6": "",
        "part7": "",

        "static": "",
        "video": "",
        "unknown": "",

        "static_size": "",
        "video_size": "",

        "cd_order": "",

        "static_cd_entry1": "",

        "check_part2_filename": "",
        "check_part3_size": "",
        "check_part5_offset": "",
        "check_part6_size": "",
        "check_part7_magic": "",

        "comment_check": "",
    }


    with zipfile.ZipFile(zip_path, "r") as z:

        result["zip_comment"] = (
            z.comment
            .decode(
                "ascii",
                errors="replace"
            )
        )

        parts = parse_comment(z.comment)

        if parts:
            result.update(parts)


        infos = z.infolist()

        cd_names = []

        unknown = []

        static_info = None
        video_info = None


        for idx, info in enumerate(infos, start=1):

            name = info.filename

            cd_names.append(
                f"{idx}:{name}"
            )

            lower = name.lower()


            if lower.endswith(IMAGE_EXT):

                result["static"] = name
                static_info = info


            elif lower.endswith(VIDEO_EXT):

                result["video"] = name
                video_info = info


            else:
                unknown.append(name)



        result["unknown"] = ",".join(unknown)

        result["cd_order"] = (
            "<br>".join(cd_names)
        )


        if static_info:

            result["static_size"] = (
                static_info.file_size
            )

            result["static_cd_entry1"] = (
                "YES"
                if infos[0].filename
                == static_info.filename
                else "NO"
            )


        if video_info:

            result["video_size"] = (
                video_info.file_size
            )


        #
        # 验证
        #

        checks = []


        if parts and static_info:

            ok = (
                parts["part2"]
                ==
                30 + len(static_info.filename)
            )

            result["check_part2_filename"] = (
                check_yesno(ok)
            )

            checks.append(ok)


            ok = (
                parts["part3"]
                ==
                static_info.file_size
            )

            result["check_part3_size"] = (
                check_yesno(ok)
            )

            checks.append(ok)


        if parts and static_info and video_info:

            ok = (
                parts["part5"]
                ==
                parts["part3"]
                +
                (
                    30
                    +
                    len(static_info.filename)
                )
                +
                (
                    30
                    +
                    len(video_info.filename)
                )
            )

            result["check_part5_offset"] = (
                check_yesno(ok)
            )

            checks.append(ok)


            ok = (
                parts["part6"]
                ==
                video_info.file_size
            )

            result["check_part6_size"] = (
                check_yesno(ok)
            )

            checks.append(ok)



        if parts:

            ok = (
                parts["part7"]
                ==
                "1000LIVP".encode("ascii").hex().upper()  # HERE FIX BY LETMEFLY
            )
            # print(parts["part7"])
            # print("1000LIVP".encode("ascii").hex().upper())

            result["check_part7_magic"] = (
                check_yesno(ok)
            )

            checks.append(ok)


        if checks:
            result["comment_check"] = (
                "PASS"
                if all(checks)
                else "FAIL"
            )


    return result



def md_escape(v):

    return (
        str(v)
        .replace("|", "\\|")
        .replace("\n", "<br>")
    )


def main():

    rows = []

    for p in sorted(
        Path(".").glob("*.zip")
    ):

        print(
            "Analyzing",
            p
        )

        rows.append(
            analyze(p)
        )


    headers = [

        "文件名",
        "zip comment",

        "part1",
        "part2",
        "part3",
        "part4",
        "part5",
        "part6",
        "part7",

        "静态图",
        "动态视频",

        "静态大小",
        "视频大小",

        "Central Directory顺序",

        "静态是否CD Entry #1",

        "part2文件名验证",
        "part3大小验证",
        "part5 offset验证",
        "part6大小验证",
        "part7 magic验证",

        "comment整体验证",
    ]


    with open(
        "livp_analysis.md",
        "w",
        encoding="utf-8"
    ) as f:


        f.write(
            "# LIVP分析结果\n\n"
        )


        f.write(
            "| "
            +
            " | ".join(headers)
            +
            " |\n"
        )

        f.write(
            "| "
            +
            " | ".join(
                ["---"] * len(headers)
            )
            +
            " |\n"
        )


        for r in rows:

            values = [

                r["filename"],
                r["zip_comment"],

                r["part1"],
                r["part2"],
                r["part3"],
                r["part4"],
                r["part5"],
                r["part6"],
                r["part7"],

                r["static"],
                r["video"],

                r["static_size"],
                r["video_size"],

                r["cd_order"],

                r["static_cd_entry1"],

                r["check_part2_filename"],
                r["check_part3_size"],
                r["check_part5_offset"],
                r["check_part6_size"],
                r["check_part7_magic"],

                r["comment_check"],
            ]


            f.write(
                "| "
                +
                " | ".join(
                    md_escape(x)
                    for x in values
                )
                +
                " |\n"
            )


if __name__ == "__main__":
    main()