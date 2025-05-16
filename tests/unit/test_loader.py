import io
from pathlib import Path
import sys
import os
import requests

sys.path.append(
    os.path.join(os.path.dirname(__file__), "../../")
)  # 添加 utils 目录到 PATH
from excel_processor import ExcelParser
from parallel_processor import process_all_documents
from traits.trait_types import true

import logging

config = {
    "document_settings": {
        "max_length": 1000,
        "min_length": 300,
        "sentence_integrity_weight": 8.0,
        "table_length_factor": 1.2,
    },
    "processing_options": {
        "debug_mode": true,
        "output_folder": "文件输出",
        "skip_existing": true,
    },
    "advanced_settings": {
        "min_split_score": 7,
        "heading_score_bonus": 10,
        "sentence_end_score_bonus": 6,
        "length_score_factor": 100,
        "search_window": 5,
        "heading_after_penalty": 12,
        "force_split_before_heading": true,
    },
    "performance_settings": {
        "parallel_processing": true,
        "num_workers": 0,
        "cache_size": 1024,
        "batch_size": 3,
    },
    "input_folder": "/Users/dalididilo/Documents/PythonProject/VerbaAurea/",
}


def test_minio_loader() -> None:
    total_files, processed_files, failed_files = process_all_documents(config)
    logging.info(
        f"####total_files:{total_files},processed_files:{processed_files},failed_files:{failed_files}"
    )


def test_insert_split_markers() -> None:
    # 导入处理模块
    from document_processor import insert_split_markers

    # response = requests.get("http://192.168.1.3:9003/neo4j-rag/T30A%E4%BA%A7%E5%93%81%E5%9B%BA%E5%AE%9AIP%E3%80%81%E4%BF%AE%E6%94%B9%E6%9C%8D%E5%8A%A1%E5%99%A8%E6%8C%87%E5%90%91%E6%93%8D%E4%BD%9C%E8%AF%B4%E6%98%8E.docx")
    response = requests.get("http://192.168.1.3:9003/neo4j-rag/test_docx.docx")
    binary_data = response.content  # 直接获取 bytes
    # 如果需要 IO[bytes] 对象（如用于某些 API 要求）
    io_bytes = io.BytesIO(binary_data)  # 封装成 IO[bytes]
    # 处理文件
    success = insert_split_markers(
        io_bytes,
        "/Users/dalididilo/Documents/PythonProject/VerbaAurea/文件输出/1235.docx",
        config,
    )
    logging.info(f"处理文档:{success}")


def test_excel_parse() -> None:
    excel_parse = ExcelParser()
    # path = Path(
    #     "/Users/dalididilo/Documents/PythonProject/VerbaAurea/磷酸铁锂原材料价格.csv"
    # )
    response = requests.get("http://192.168.1.3:9003/neo4j-rag/%E7%A3%B7%E9%85%B8%E9%93%81%E9%94%82%E5%8E%9F%E6%9D%90%E6%96%99%E4%BB%B7%E6%A0%BC.xlsx")
    binary_data = response.content  # 直接获取 bytes
    # 如果需要 IO[bytes] 对象（如用于某些 API 要求）
    io_bytes = io.BytesIO(binary_data)  # 封装成 IO[bytes]
    rep = excel_parse.parse(input_data=io_bytes)
    # breakpoint()
    for item in rep:
        logging.info(f"{item}\n")
