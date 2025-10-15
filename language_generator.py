#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书多语言文档自动生成Dart多语言文件工具

支持从飞书多维表格或文档中提取多语言数据，并生成对应的JSON文件和Dart代码
"""

import json
import os
import sys
from typing import Dict
from dataclasses import dataclass
import argparse

@dataclass
class LanguageConfig:
    """语言配置"""
    code: str  # 语言代码，如 'zh', 'en', 'ja'
    name: str  # 语言名称，如 '中文', 'English', '日本語'
    file_name: str  # 文件名，如 'intl_zh.arb'


# arb保存的路径,配合flutter intl使用再好不过
ARB_DIR = "lib/l10n"
# 支持的语言配置,根据language.csv中的内容修改
LANGUAGES = {
    "zh": LanguageConfig("zh", "中文", "intl_zh.arb"),
    "en": LanguageConfig("en", "英语", "intl_en.arb"),
    "ja": LanguageConfig("ja", "日语", "intl_ja.arb"),
    "ko": LanguageConfig("ko", "韩语", "intl_ko.arb"),
    "tr": LanguageConfig("tr", "土耳其语", "intl_tr.arb"),
}

class FeishuI18nGenerator:
    """飞书多语言生成器"""
    
    def __init__(self):
        os.makedirs(ARB_DIR, exist_ok=True)
    
    def parse_csv_data(self, csv_content: str) -> Dict[str, Dict[str, str]]:
        """解析CSV格式的多语言数据"""
        import csv
        from io import StringIO
        
        # 处理BOM
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]
        
        # 使用csv模块正确解析CSV
        csv_reader = csv.reader(StringIO(csv_content))
        rows = list(csv_reader)
        
        if len(rows) < 2:
            raise ValueError("CSV数据至少需要包含标题行和一行数据")
        
        # 解析标题行，过滤空列
        headers = [h.strip() for h in rows[0] if h.strip()]
        
        # 检查是否包含key列
        if 'key' not in headers:
            raise ValueError("CSV必须包含'key'列")
        
        key_index = headers.index('key')
        
        # 找到语言列 - 直接匹配语言代码
        language_columns = {}
        for i, header in enumerate(headers):
            if header.lower() == 'key':
                continue
            # 直接匹配语言代码
            if header.lower() in LANGUAGES:
                language_columns[header.lower()] = i
        
        if not language_columns:
            raise ValueError("未找到任何支持的语言列")
        
        # 解析数据
        result = {}
        for row in rows[1:]:
            if not row or len(row) <= key_index:
                continue
                
            key = row[key_index].strip()
            if not key:
                continue
                
            result[key] = {}
            for lang_code, col_index in language_columns.items():
                if col_index < len(row):
                    value = row[col_index].strip()
                    # 清理值中的引号和换行符
                    value = value.replace('\\n', '\n').replace('\\"', '"')
                    result[key][lang_code] = value
        
        return result
    
    def generate_json_files(self, i18n_data: Dict[str, Dict[str, str]]) -> None:
        """生成JSON格式的多语言文件"""
        print("正在生成JSON文件...")
        
        for lang_code, lang_config in LANGUAGES.items():
            file_path = os.path.join(ARB_DIR, lang_config.file_name)
            lang_data = {}
            
            # 收集该语言的所有键值对
            for key, translations in i18n_data.items():
                if lang_code in translations and translations[lang_code]:
                    lang_data[key] = translations[lang_code]
            
            # 保存JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(lang_data, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ 生成 {lang_config.file_name} ({len(lang_data)} 个键值对)")
    
    def validate_data(self, i18n_data: Dict[str, Dict[str, str]]) -> None:
        """验证多语言数据"""
        print("正在验证数据...")
        
        # 统计信息
        total_keys = len(i18n_data)
        language_counts = {lang: 0 for lang in LANGUAGES.keys()}
        
        for key, translations in i18n_data.items():
            for lang_code in LANGUAGES.keys():
                if lang_code in translations and translations[lang_code]:
                    language_counts[lang_code] += 1
        
        print(f"  总键数: {total_keys}")
        for lang_code, count in language_counts.items():
            lang_name = LANGUAGES[lang_code].name
            print(f"  {lang_name} ({lang_code}): {count} 个键值对")
        
        # 检查缺失的翻译
        missing_translations = []
        for key, translations in i18n_data.items():
            for lang_code in LANGUAGES.keys():
                if lang_code not in translations or not translations[lang_code]:
                    missing_translations.append((key, lang_code))
        
        if missing_translations:
            print(f"\n  ⚠️ 发现 {len(missing_translations)} 个缺失的翻译:")
            for key, lang_code in missing_translations[:10]:  # 只显示前10个
                lang_name = LANGUAGES[lang_code].name
                print(f"    {key} -> {lang_name}")
            if len(missing_translations) > 10:
                print(f"    ... 还有 {len(missing_translations) - 10} 个")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="飞书多语言文档自动生成工具")
    parser.add_argument("csv", help="CSV文件路径")
    
    args = parser.parse_args()
    
    generator = FeishuI18nGenerator()
    
    try:
        # 解析CSV数据
        print(f"正在解析CSV文件: {args.csv}")
        with open(args.csv, 'r', encoding='utf-8') as f:
            i18n_data = generator.parse_csv_data(f.read())
        
        # 验证数据
        generator.validate_data(i18n_data)
        
        # 生成文件
        generator.generate_json_files(i18n_data)
        
        print("\n✅ 多语言文件生成完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
