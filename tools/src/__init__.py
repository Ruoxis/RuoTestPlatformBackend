# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：__init__.py
@Time ：2025/9/15 8:15
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from collections import defaultdict

from typing import List, Dict


def compare_json_data(list1: List[Dict], list2: List[Dict]) -> List[Dict]:
    """
    对比两组JSON数据的差异，支持重复Code的记录比较

    Args:
        list1: 第一组JSON数据
        list2: 第二组JSON数据

    Returns:
        差异结果的详细列表
    """
    differences = []

    # 构建按Code分组的字典，处理重复Code的情况
    dict1 = defaultdict(list)
    dict2 = defaultdict(list)

    for item in list1:
        code = item.get('Code', '')
        dict1[code].append(item)

    for item in list2:
        code = item.get('Code', '')
        dict2[code].append(item)

    # 找出所有唯一的Code
    all_codes = set(dict1.keys()) | set(dict2.keys())

    for code in sorted(all_codes):
        items1 = dict1.get(code, [])
        items2 = dict2.get(code, [])

        # 统计每个Code在两个列表中的出现次数
        count1 = len(items1)
        count2 = len(items2)

        if count1 == 0:
            # 只在第二组中存在
            for item in items2:
                differences.append({
                    'type': '只在第二组中存在',
                    'code': code,
                    'name': item.get('Name', ''),
                    'data': item
                })
        elif count2 == 0:
            # 只在第一组中存在
            for item in items1:
                differences.append({
                    'type': '只在第一组中存在',
                    'code': code,
                    'name': item.get('Name', ''),
                    'data': item
                })
        else:
            # 两个列表都有这个Code，需要详细比较
            # 找出数量差异
            if count1 != count2:
                differences.append({
                    'type': '数量不同',
                    'code': code,
                    'name': items1[0].get('Name', '') if items1 else items2[0].get('Name', ''),
                    'count_info': {
                        '第一组数量': count1,
                        '第二组数量': count2
                    }
                })

            # 比较相同数量的记录
            min_count = min(count1, count2)
            for i in range(min_count):
                item1 = items1[i]
                item2 = items2[i]
                field_diffs = {}

                all_fields = set(item1.keys()) | set(item2.keys())
                for field in all_fields:
                    val1 = item1.get(field)
                    val2 = item2.get(field)
                    if val1 != val2:
                        field_diffs[field] = {'第一组': val1, '第二组': val2}

                if field_diffs:
                    differences.append({
                        'type': '内容不同',
                        'code': code,
                        'index': i + 1,  # 记录是第几个重复项
                        'name': item1.get('Name', ''),
                        'differences': field_diffs
                    })

    return differences


def print_differences(differences: List[Dict]):
    """
    以友好的格式打印差异结果
    """
    if not differences:
        print("✅ 两组数据完全相同")
        return

    print(f"📊 发现 {len(differences)} 处差异:")
    print("=" * 80)

    for i, diff in enumerate(differences, 1):
        print(f"\n{i}. {diff['type'].upper()}")
        print(f"   代码: {diff['code']}")
        print(f"   名称: {diff['name']}")

        if diff['type'] == '内容不同' and 'index' in diff:
            print(f"   序号: 第{diff['index']}个重复项")

        if 'count_info' in diff:
            print(f"   数量: 第一组={diff['count_info']['第一组数量']}, 第二组={diff['count_info']['第二组数量']}")

        if 'differences' in diff:
            print("   具体差异:")
            for field, values in diff['differences'].items():
                print(f"     {field}: {values['第一组']} ←→ {values['第二组']}")

        print("-" * 40)


def get_difference_summary(differences: List[Dict]) -> Dict:
    """
    获取差异统计摘要
    """
    summary = {
        'total_differences': len(differences),
        'only_in_list1': 0,
        'only_in_list2': 0,
        'count_differences': 0,
        'content_differences': 0
    }

    for diff in differences:
        if diff['type'] == '只在第一组中存在':
            summary['only_in_list1'] += 1
        elif diff['type'] == '只在第二组中存在':
            summary['only_in_list2'] += 1
        elif diff['type'] == '数量不同':
            summary['count_differences'] += 1
        elif diff['type'] == '内容不同':
            summary['content_differences'] += 1

    return summary


# 使用示例

if __name__ == '__main__':
    pass
    a = [
        {'StockUpType': 1, 'Code': 'SAA10265', 'Name': '18mm铝康板左侧板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 250.0, 'Length': 350.0, 'Quantity': 1.0, 'Remark': '内进18K，上12，下12不锣通',
         'EdgeBanding': '四K△,K1'},
        {'StockUpType': 1, 'Code': 'SAA10266', 'Name': '18mm铝康板右侧板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 250.0, 'Length': 350.0, 'Quantity': 1.0, 'Remark': '内进18K，上12，下12不锣通',
         'EdgeBanding': '四K△,K1'},
        {'StockUpType': 1, 'Code': 'SAE10245', 'Name': '18mm铝康板顶板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 249.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '内进18K',
         'EdgeBanding': '四K△,K1'},
        {'StockUpType': 1, 'Code': 'SAE10246', 'Name': '18mm铝康板底板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 229.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '内进18K',
         'EdgeBanding': '四K△,K1'},
        {'StockUpType': 3, 'Code': 'CH00005431', 'Name': '三合一(铝康板专用)', 'Color': '', 'Height': 41.0,
         'Width': 12.0, 'Length': 12.5, 'Quantity': 16.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH10700003_967', 'Name': '12mm饰盖贴(臻灰_967)', 'Color': '967', 'Height': 0.5,
         'Width': 12.0, 'Length': 12.0, 'Quantity': 16.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH19900076', 'Name': '吊柜锚栓φ8*65', 'Color': '', 'Height': 8.0, 'Width': 8.0,
         'Length': 65.0, 'Quantity': 6.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH20110021', 'Name': '沉头自攻螺钉5*80', 'Color': '', 'Height': 0.0, 'Width': 8.0,
         'Length': 50.0, 'Quantity': 6.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH60800008', 'Name': '掩门防撞胶粒(100粒/片，100片/包)', 'Color': '', 'Height': 0.0,
         'Width': 0.0, 'Length': 0.0, 'Quantity': 2.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH20320007', 'Name': '8*30木塞', 'Color': '', 'Height': 8.0, 'Width': 8.0,
         'Length': 30.0, 'Quantity': 8.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH40300016', 'Name': '百隆迷你上翻门20K2C00(轻型)', 'Color': '', 'Height': 45.0,
         'Width': 187.0, 'Length': 300.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'SAM10523', 'Name': '18mm铝康板斜直封边拉手上翻门', 'Color': '1050AMAL',
         'Height': 18.0, 'Width': 344.0, 'Length': 1197.0, 'Quantity': 1.0,
         'Remark': '1右，按0，0，0，0，0，0打孔，上翻门做法，1H斜直边锣拉手槽，左1，右1不锣通', 'EdgeBanding': '四△,K3'},
        {'StockUpType': 1, 'Code': 'SAH00106', 'Name': '斜边拉手(铝康板专用)(切割)', 'Color': '', 'Height': 8.7,
         'Width': 24.4, 'Length': 1195.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'CH00005437', 'Name': '斜边拉手饰盖-左(铝康板专用)', 'Color': '', 'Height': 6.0,
         'Width': 16.0, 'Length': 20.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'CH00005438', 'Name': '斜边拉手饰盖-右(铝康板专用)', 'Color': '', 'Height': 6.0,
         'Width': 16.0, 'Length': 20.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'SAC10077', 'Name': '10mm铝康板背板', 'Color': '1051AMAL', 'Height': 10.0,
         'Width': 1174.0, 'Length': 324.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'SAG10048', 'Name': '18mm铝康板拉板', 'Color': '1051AMAL', 'Height': 18.0,
         'Width': 70.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四△'},
        {'StockUpType': 1, 'Code': 'SAG10048', 'Name': '18mm铝康板拉板', 'Color': '1051AMAL', 'Height': 18.0,
         'Width': 70.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四△'},
        {'StockUpType': 1, 'Code': 'SAM10523', 'Name': '18mm铝康板斜直封边拉手上翻门', 'Color': '1050AMAL',
         'Height': 18.0, 'Width': 347.0, 'Length': 1200.0, 'Quantity': 1.0,
         'Remark': '1右，按0，0，0，0，0，0打孔，上翻门做法，1H斜直边锣拉手槽，左1，右1不锣通', 'EdgeBanding': '四△,K3'},
        {'StockUpType': 1, 'Code': 'SAH00106', 'Name': '斜边拉手(铝康板专用)(切割)', 'Color': '', 'Height': 8.7,
         'Width': 24.4, 'Length': 1198.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'CH00005437', 'Name': '斜边拉手饰盖-左(铝康板专用)', 'Color': '', 'Height': 6.0,
         'Width': 16.0, 'Length': 20.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'CH00005438', 'Name': '斜边拉手饰盖-右(铝康板专用)', 'Color': '', 'Height': 6.0,
         'Width': 16.0, 'Length': 20.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH40300015', 'Name': '百隆迷你上翻门20K2E00(重型)', 'Color': '', 'Height': 45.0,
         'Width': 187.0, 'Length': 300.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH60800008', 'Name': '掩门防撞胶粒(100粒/片，100片/包)', 'Color': '', 'Height': 0.0,
         'Width': 0.0, 'Length': 0.0, 'Quantity': 2.0, 'Remark': '', 'EdgeBanding': ''}]
    b = [
        {'StockUpType': 1, 'Code': 'SAA10265', 'Name': '18mm铝康板左侧板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 250.0, 'Length': 350.0, 'Quantity': 1.0, 'Remark': '内进18K，上12，下12不锣通',
         'EdgeBanding': '四K△,K1'},
        {'StockUpType': 1, 'Code': 'SAA10266', 'Name': '18mm铝康板右侧板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 250.0, 'Length': 350.0, 'Quantity': 1.0, 'Remark': '内进18K，上12，下12不锣通',
         'EdgeBanding': '四K△,K1'},
        {'StockUpType': 1, 'Code': 'SAE10246', 'Name': '18mm铝康板底板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 229.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '内进18K',
         'EdgeBanding': '四K△,K1'},
        {'StockUpType': 1, 'Code': 'SAE10245', 'Name': '18mm铝康板顶板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 249.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '内进18K',
         'EdgeBanding': '四K△,K1'},
        {'StockUpType': 1, 'Code': 'SAE10246', 'Name': '18mm铝康板底板(10mm背板槽)', 'Color': '1051AMAL',
         'Height': 18.0, 'Width': 229.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '内进18K',
         'EdgeBanding': '四K△,K1'},

        {'StockUpType': 3, 'Code': 'CH10700003_967', 'Name': '12mm饰盖贴(臻灰_967)', 'Color': '967', 'Height': 0.5,
         'Width': 12.0, 'Length': 12.0, 'Quantity': 16.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH19900076', 'Name': '吊柜锚栓φ8*65', 'Color': '', 'Height': 8.0, 'Width': 8.0,
         'Length': 65.0, 'Quantity': 6.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH00005431', 'Name': '三合(铝康板专用)', 'Color': '', 'Height': 41.0,
         'Width': 12.0, 'Length': 12.5, 'Quantity': 16.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH20110021', 'Name': '沉头自攻螺钉5*80', 'Color': '', 'Height': 0.0, 'Width': 8.0,
         'Length': 50.0, 'Quantity': 6.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH60800008', 'Name': '掩门防撞胶粒(100粒/片，100片/包)', 'Color': '', 'Height': 0.0,
         'Width': 0.0, 'Length': 0.0, 'Quantity': 2.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH20320007', 'Name': '8*30木塞', 'Color': '', 'Height': 8.0, 'Width': 8.0,
         'Length': 30.0, 'Quantity': 8.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH40300016', 'Name': '百隆迷你上翻门20K2C00(轻型)', 'Color': '', 'Height': 45.0,
         'Width': 187.0, 'Length': 300.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'SAM10523', 'Name': '18mm铝康板斜直封边拉手上翻门', 'Color': '1050AMAL',
         'Height': 18.0, 'Width': 344.0, 'Length': 1197.0, 'Quantity': 1.0,
         'Remark': '1右，按0，0，0，0，0，0打孔，上翻门做法，1H斜直边锣拉手槽，左1，右1不锣通', 'EdgeBanding': '四△,K3'},
        {'StockUpType': 1, 'Code': 'SAH00106', 'Name': '斜边拉手(铝康板专用)(切割)', 'Color': '', 'Height': 8.7,
         'Width': 24.4, 'Length': 1195.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'CH00005437', 'Name': '斜边拉手饰盖-左(铝康板专用)', 'Color': '', 'Height': 6.0,
         'Width': 16.0, 'Length': 20.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'CH00005438', 'Name': '斜边拉手饰盖-右(铝康板专用)', 'Color': '', 'Height': 6.0,
         'Width': 16.0, 'Length': 20.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'SAC10077', 'Name': '10mm铝康板背板', 'Color': '1051AMAL', 'Height': 10.0,
         'Width': 1174.0, 'Length': 324.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'SAG10048', 'Name': '18mm铝康板拉板', 'Color': '1051AMAL', 'Height': 18.0,
         'Width': 70.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四△'},
        {'StockUpType': 1, 'Code': 'SAG10048', 'Name': '18mm铝康板拉板', 'Color': '1051AMAL', 'Height': 18.0,
         'Width': 70.0, 'Length': 1164.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四△'},
        {'StockUpType': 1, 'Code': 'SAM10523', 'Name': '18mm铝康板斜直封边拉手上翻门', 'Color': '1050AMAL',
         'Height': 18.0, 'Width': 347.0, 'Length': 1200.0, 'Quantity': 1.0,
         'Remark': '1右，按0，0，0，0，0，0打孔，上翻门做法，1H斜直边锣拉手槽，左1，右1不锣通', 'EdgeBanding': '四△,K3'},
        {'StockUpType': 1, 'Code': 'SAH00106', 'Name': '斜边拉手(铝康板专用)(切割)', 'Color': '', 'Height': 8.7,
         'Width': 24.4, 'Length': 1198.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'CH00005437', 'Name': '斜边拉手饰盖-左(铝康板专用)', 'Color': '', 'Height': 6.0,
         'Width': 16.0, 'Length': 20.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 1, 'Code': 'CH00005438', 'Name': '斜边拉手饰盖-右(铝康板专用)', 'Color': '', 'Height': 6.0,
         'Width': 16.0, 'Length': 21.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': 'CH40300015', 'Name': '百隆迷你上翻门20K2E00(重型)', 'Color': '', 'Height': 45.0,
         'Width': 187.0, 'Length': 301.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': '', 'Name': '掩门防撞胶粒(100粒/片，100片/包)', 'Color': '', 'Height': 0.0,
         'Width': 0.0, 'Length': 0.0, 'Quantity': 2.0, 'Remark': '', 'EdgeBanding': ''},
        {'StockUpType': 3, 'Code': '', 'Name': '掩门防撞胶粒(100粒/片，100片/包)', 'Color': '', 'Height': 0.0,
         'Width': 0.0, 'Length': 0.0, 'Quantity': 2.0, 'Remark': '', 'EdgeBanding': ''}
    ]

    diff_results = compare_json_data(a, b)

    # 打印详细差异
    print_differences(diff_results)

    # 获取统计摘要
    summary = get_difference_summary(diff_results)
    print(summary)
    print(f"\n📈 差异统计:")
    print(f"   总差异数: {summary['total_differences']}")
    print(f"   只在第一组中: {summary['only_in_list1']}")
    print(f"   只在第二组中: {summary['only_in_list2']}")
    print(f"   数量差异: {summary['count_differences']}")
    print(f"   内容差异: {summary['content_differences']}")
