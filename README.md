<!--
 * @Author: LetMeFly
 * @Date: 2026-07-07 17:31:31
 * @LastEditors: LetMeFly.xyz
 * @LastEditTime: 2026-07-07 17:38:19
-->
# 2livp

把静态图(.heic)+动态视频(.mov)打包为百度网盘/一刻相册可以识别的.livp格式live图。

## livp格式简介

livp格式并非Apple官方格式，而是互联网厂商为了适配苹果系统的live图而推出的格式。其本质是静态图(.heic)+动态视频(.mov)的zip压缩包。

但是你直接把这两个文件给zip的话就会发现很多软件无法识别，研究了下百度系产品发现其支持的zip压缩需要满足以下几点：

1. 不压缩（别扭吗？不别扭）。`zip`命令添加参数`-0`代表只打包不做压缩，保持原始字节。
2. 去掉额外的文件属性（eXclude extra file attributes）。`zip`命令添加参数`-X`代表 不保存文件的Unix UID/GID等信息。
3. 注释。还需要使用`-z`参数给`.zip`文件添加形如`0002000000300022175F0003002217BE003D8A51313030304C495650`的注释，用来快速获取原始文件数据在zip文件中的位置信息。

至于*注释*是什么含义？*注释*一共有以下几部分组成：

```
0002 00000030 000E26AB 0003 000E270A 004B806E 313030304C495650
0002 00000030 0010B331 0003 0010B390 004208DB 313030304C495650
part1  part2    part3  part4  part5   part6       part7
```

+ part1: 0002
+ part2: 00000030
+ part3: heic字节数(16进制)
+ part4: 0003
+ part5: part3+(30+静态图文件名长度)+(30+动态图文件名长度)，目前来看其中**静态图文件名长度必须是18**
+ part6: mov字节数(16进制)
+ part7: 313030304C495650(ASCII含义为1000LIVP)

part3和part6的8位的字节数最大约 $$2^{4\times 8}$$ 字节也就是大约4 GiB。

part1、part2、part4、part7都为固定值，part7的ASCII含义为1000LIVP。

```python
hex_str = "313030304C495650"
bytes_obj = bytes.fromhex(hex_str)
ascii_str = bytes_obj.decode("ascii")
print(ascii_str)  # 1000LIVP
```

## 更详细原理描述

请参考我的文章《[iOS：压缩和解压live图(.livp)——百度一刻相册+百度网盘识别支持](https://blog.letmefly.xyz/2026/07/04/Other-iOS-zipAndUnzipingLivp-BaiduYikePhoto/)》

## Mac/iOS系统上的live图方案（以及传输到Windows上）

iOS拍摄的live图如果想通过iCloud之外的方式同步到其他电脑/设备，主要有两个地方可以设置：

1. 数据线传输时：`iPhone -> 设置(settings) -> 应用(Apps) -> 照片(photos) -> 最下面的“传输到Mac或PC”(Transfer to Mac or PC) -> 保留原片(Keep Originals)`
2. AirDrop时：`分享 -> 选项(Options) -> 打开“所有照片数据”(All Photos Data)`

这样分享一张照片会在电脑上得到一个文件夹。

## 将一个文件夹下所有的live图文件夹们打包成.livp文件的脚本

将手机上一堆照片传输到电脑上后，会得到一个个如`IMG_5526`的文件夹。

将这些文件夹所在的文件夹路径记下来（如果在下载文件夹下则路径为`~/Downloads`），star并clone本仓库，运行命令`python livp2.py 照片文件夹所在路径`命令，即可在`照片文件夹所在路径/exported`文件夹下找到一个个导出的照片文件，有的是静态图有的是live图，直接拖拽到百度网盘或一刻相册即可直接上传。
