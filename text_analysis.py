#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本分析模块
负责段落分析、语义结构识别、句子边界检测等
(2025-05 补丁：增强标题识别 looks_like_heading)
"""
import re
import functools
import jieba
import nltk
from nltk.tokenize import sent_tokenize
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

# ---------- NLTK 资源 ----------
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# ---------- 标题识别 ----------
DEFAULT_HEADING_REGEX = [
    r'^第[一二三四五六七八九十百千]+[章节]',      # 第一节 / 第二章
    r'^[一二三四五六七八九十]+[、\.]',          # 一、 / 二.
    r'^\d+(\.\d+)*\s*[\u4e00-\u9fff]{0,30}$', # 1. / 1.1 标题
    r'^[\(（][一二三四五六七八九十]+[\)）]',    # （二）/ (三)
    r'^[\(（]?\d+[\)）]'                       # (2) / （3）
]

def _compile_heading_patterns():
    """加载 config.json 中的自定义标题正则并编译"""
    try:
        from config_manager import load_config
        cfg = load_config()
        extra = cfg.get('advanced_settings', {}).get('custom_heading_regex', [])
    except Exception:
        extra = []
    patterns = DEFAULT_HEADING_REGEX + extra
    return [re.compile(pat) for pat in patterns]

_HEADING_PATTERNS = _compile_heading_patterns()

def looks_like_heading(text: str) -> bool:
    """依据内容判断是否像标题（样式或正则命中即为标题）"""
    if not text:
        return False
    # 过长或明显以句号等结束的视为正文
    if len(text) > 50 or text.endswith(('。', '！', '？', '.', '!', '?', '；', ';')):
        return False
    stripped = text.strip()
    for pat in _HEADING_PATTERNS:
        if pat.match(stripped):
            return True
    return False
# ------------------------------------------------------------------


@functools.lru_cache(maxsize=1024)
def is_sentence_boundary(text_before, text_after):
    """判断两段文本之间是否为句子边界"""
    if text_before.endswith(('。', '！', '？', '.', '!', '?', '；', ';')):
        return True
    combined_text = text_before + " " + text_after
    try:
        if any(u'\u4e00' <= c <= u'\u9fff' for c in combined_text):
            # 中文用 jieba
            sents = list(jieba.cut(combined_text))
            for i, w in enumerate(sents[:-1]):
                if w in ['。', '！', '？', '.', '!', '?', '；', ';']:
                    before_seg = ''.join(sents[:i+1])
                    if abs(len(before_seg) - len(text_before)) < 5:
                        return True
        else:
            sents = sent_tokenize(combined_text)
            for s in sents:
                if text_before.endswith(s) or text_after.startswith(s):
                    return True
    except:
        pass
    return False


def find_nearest_sentence_boundary(paragraphs_info, current_index, search_window=5):
    """寻找最近句子边界"""
    best = -1
    dist = 1e9
    # 向前
    for i in range(max(0, current_index-search_window), current_index+1):
        if i>0 and is_sentence_boundary(paragraphs_info[i-1]['text'], paragraphs_info[i]['text']):
            if current_index - i < dist:
                dist = current_index - i
                best = i
    # 向后
    for i in range(current_index+1, min(len(paragraphs_info), current_index+search_window+1)):
        if i>0 and is_sentence_boundary(paragraphs_info[i-1]['text'], paragraphs_info[i]['text']):
            if i - current_index < dist:
                dist = i - current_index
                best = i
    return best


# =================== 主入口：extract_elements_info ===================
def extract_elements_info(doc, table_length_factor=1.0, debug_mode=False):
    """
    按文档布局顺序抽出段落/表格等元素信息
    """
    elements = []
    para_idx = -1
    tbl_idx = -1

    paragraph_map = {p._element: p for p in doc.paragraphs}
    table_map = {t._element: t for t in doc.tables}

    for el in doc._element.body:
        # -------- 段落 --------
        if isinstance(el, CT_P):
            para_idx += 1
            p = paragraph_map[el]
            text = p.text.strip()

            is_heading = p.style.name.startswith(('Heading', '标题')) or looks_like_heading(text)
            is_list_item = text.startswith(('•', '-', '*')) or \
                (len(text) > 2 and text[0].isdigit() and text[1] in '.、)')
            ends_with_period = text.endswith(('。', '！', '？', '.', '!', '?', '；', ';'))

            elements.append({
                'type': 'para',
                'i_para': para_idx,
                'i_table': None,
                'text': text,
                'length': len(text),
                'is_heading': is_heading,
                'is_list_item': is_list_item,
                'ends_with_period': ends_with_period
            })

        # -------- 表格 --------
        elif isinstance(el, CT_Tbl):
            tbl_idx += 1
            tbl = table_map[el]
            texts = []
            for row in tbl.rows:
                for cell in row.cells:
                    if cell.text:
                        texts.append(cell.text.strip())
            tbl_text = ' '.join(texts)
            tbl_len = int(len(tbl_text) * table_length_factor)

            elements.append({
                'type': 'table',
                'i_para': None,
                'i_table': tbl_idx,
                'text': tbl_text,
                'length': tbl_len,
                'is_heading': False,
                'is_list_item': False,
                'ends_with_period': True
            })

    if debug_mode:
        tbl_cnt = tbl_idx + 1
        print(f"[extract] elements={len(elements)} (tables={tbl_cnt})")
    return elements
# ====================================================================


# 下面 analyze_document / identify_semantic_blocks 等辅助函数
# ---- 原逻辑保持不变，省略，若需请复制旧文件对应片段 ----
