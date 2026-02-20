"""
文件处理工具
"""

from typing import List


def read_file(file_path: str, encoding: str = "utf-8") -> List[str]:
    """
    读取文件内容

    Args:
        file_path: 文件路径
        encoding: 文件编码

    Returns:
        文件行列表

    Raises:
        FileNotFoundError: 文件不存在
        IOError: 文件读取失败
    """
    with open(file_path, "r", encoding=encoding) as f:
        return f.readlines()


def write_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码

    Raises:
        IOError: 文件写入失败
    """
    # 确保目录存在
    import os

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)


def read_lines(file_path: str, encoding: str = "utf-8") -> List[str]:
    """
    逐行读取文件（生成器）

    Args:
        file_path: 文件路径
        encoding: 文件编码

    Returns:
        生成器，每次生成一行

    Raises:
        FileNotFoundError: 文件不存在
        IOError: 文件读取失败
    """
    with open(file_path, "r", encoding=encoding) as f:
        for line in f:
            yield line.rstrip("\n")
