# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
@Project ：ui_test_backend
@File ：order_comparator
@Time ：2025/9/17 8:21
@Author ：11031840
@Motto: 理解しあうのはとても大事なことです。理解とは误解の総体に过ぎないと言う人もいますし
@describe： 
"""
from typing import List, Dict, Set, Optional, Any, Tuple
from collections import defaultdict
import json


class OrderComparator:
    def __init__(self, list1: List[Dict],
                 list2: List[Dict],
                 compare_fields: Optional[List[str]] = None,
                 key_field: str = 'Code',
                 name_field: str = 'Name',
                 exclude_fields: Optional[List[str]] = None,
                 sort_fields: Optional[List[str]] = None):
        """
        初始化比较器

        :param list1: 第一个数据列表
        :param list2: 第二个数据列表
        :param compare_fields: 指定要对比的字段列表，如果为None则对比所有字段
        :param key_field: 用于匹配记录的主键字段，默认为'Code'
        :param exclude_fields: 指定要排除对比的字段列表
        :param sort_fields: 指定用于排序的字段列表，用于处理相同主键的多条记录
        """
        self.list1 = list1
        self.list2 = list2
        self.compare_fields = compare_fields
        self.key_field = key_field
        self.exclude_fields = exclude_fields or []
        # 确定 compare_fields
        if compare_fields is None:
            # 自动推断：取 list1 和 list2 中所有字典的公共字段，排除 key_field 和 exclude_fields
            all_fields1 = set().union(*(d.keys() for d in list1 if isinstance(d, dict)))
            all_fields2 = set().union(*(d.keys() for d in list2 if isinstance(d, dict)))
            common_fields = all_fields1 & all_fields2
            self.compare_fields = [
                f for f in common_fields
                if f != key_field and f not in self.exclude_fields
            ]
        else:
            # 使用用户指定的字段，过滤掉 key_field 和 exclude_fields
            self.compare_fields = [
                f for f in compare_fields
                if f != key_field and f not in self.exclude_fields
            ]

        # 确定 sort_fields
        if sort_fields is not None:
            # 用户指定了排序字段，直接使用（过滤 key_field 和 exclude_fields）
            self.sort_fields = [
                f for f in sort_fields
                if f != key_field and f not in self.exclude_fields
            ]
        else:
            # 默认排序字段：使用 compare_fields 中的字段（通常已排除 key_field 和 exclude_fields）
            # 如果 compare_fields 为空，则使用 name_field（如果存在）
            if self.compare_fields:
                self.sort_fields = self.compare_fields.copy()
            elif name_field in (self.compare_fields + [key_field]):
                # 如果 name_field 是有效字段，可用作次级排序
                self.sort_fields = [name_field]
            else:
                # 最后兜底：按字典序排序或其他默认字段
                self.sort_fields = ['id'] if 'id' in self.compare_fields + [key_field, name_field] else []

        self.comparison_result = []
        self.name_field = name_field
        self.stats = {
            'total_differences': 0,
            'only_in_list1': 0,
            'only_in_list2': 0,
            'count_differences': 0,
            'content_differences': 0,
            'total_rows': max(len(self.list1), len(self.list2))
        }

    def _get_compare_fields(self, item1: Dict, item2: Dict) -> Set[str]:
        """获取需要对比的字段集合"""
        if self.compare_fields:
            # 如果有指定对比字段，则排除不需要对比的字段
            return set(self.compare_fields) - set(self.exclude_fields)

        # 如果没有指定对比字段，则使用两个记录的所有字段的并集，并排除不需要对比的字段
        all_fields = set(item1.keys()) if item1 else set()
        if item2:
            all_fields |= set(item2.keys())
        return all_fields - set(self.exclude_fields)

    def _compare_items(self, item1: Dict, item2: Dict) -> Dict:
        """比较两个具体的数据项"""
        compare_fields = self._get_compare_fields(item1, item2)
        field_diffs = {}

        for field in compare_fields:
            val1 = item1.get(field) if item1 else None
            val2 = item2.get(field) if item2 else None

            # 处理数值和字符串类型的比较
            if isinstance(val1, (int, float)) and isinstance(val2, str):
                try:
                    val2 = float(val2)
                except (ValueError, TypeError):
                    pass
            elif isinstance(val2, (int, float)) and isinstance(val1, str):
                try:
                    val1 = float(val1)
                except (ValueError, TypeError):
                    pass

            if val1 != val2:
                field_diffs[field] = {'list1': val1, 'list2': val2}

        return field_diffs

    def _get_key_value(self, item: Dict, idx: int) -> str:
        """获取记录的主键值，处理主键缺失的情况"""
        if item and self.key_field in item and item[self.key_field]:
            return str(item[self.key_field])
        return f"no_{self.key_field.lower()}_{idx}"

    def _get_name_value(self, item: Dict) -> str:
        """获取记录的显示名称"""
        if item:
            return item.get(self.name_field, '') or ''
        return ''

    def _get_stock_value(self, item: Dict) -> str:
        if item:
            return item.get("StockUpType", '') or ''
        return ''

    def _sort_items(self, items: List[Dict]) -> List[Dict]:
        """对相同主键的记录进行排序，以便正确比较"""
        if len(items) <= 1:
            return items

        def get_sort_key(item: Dict) -> Tuple:
            """生成排序键"""
            sort_key = []
            for field in self.sort_fields:
                value = item.get(field)
                # 统一处理数值和字符串类型的排序
                if isinstance(value, (int, float)):
                    sort_key.append(value)
                elif isinstance(value, str):
                    try:
                        sort_key.append(float(value))
                    except (ValueError, TypeError):
                        sort_key.append(value)
                else:
                    sort_key.append(value)
            return tuple(sort_key)

        try:
            return sorted(items, key=get_sort_key)
        except (TypeError, ValueError):
            # 如果排序失败，返回原始顺序
            return items

    def _compare_same_key_items(self, items1: List[Dict], items2: List[Dict], key: str) -> None:
        """比较相同主键的多条记录"""
        count1 = len(items1)
        count2 = len(items2)

        if count1 != count2:
            self.stats['count_differences'] += 1
            self.stats['total_differences'] += 1

            self.comparison_result.append({
                'key': key,
                'name': self._get_name_value(items1[0]) if items1 else self._get_name_value(items2[0]),
                'stockType': self._get_stock_value(items1[0]) if items1 else self._get_stock_value(items2[0]),
                'status': 'count_difference',
                'data1': {'count': count1, 'sample': items1[0] if items1 else None},
                'data2': {'count': count2, 'sample': items2[0] if items2 else None},
                'differences': {'count': f'{count1} vs {count2}'}
            })
            return

        # 对相同主键的记录进行排序
        sorted_items1 = self._sort_items(items1)
        sorted_items2 = self._sort_items(items2)

        # 比较排序后的记录
        for i, (item1, item2) in enumerate(zip(sorted_items1, sorted_items2)):
            field_diffs = self._compare_items(item1, item2)

            if field_diffs:
                self.stats['content_differences'] += 1
                self.stats['total_differences'] += 1

                self.comparison_result.append({
                    'key': key,
                    'name': self._get_name_value(item1),
                    'stockType': self._get_stock_value(item1),
                    'status': 'content_difference',
                    'data1': item1,
                    'data2': item2,
                    'differences': field_diffs,
                    'index': i + 1  # 记录是第几个重复项
                })
            else:
                # 完全相同的数据
                self.comparison_result.append({
                    'key': key,
                    'name': self._get_name_value(item1),
                    'stockType': self._get_stock_value(item1),
                    'status': 'identical',
                    'data1': item1,
                    'data2': item2,
                    'differences': {}
                })

    def compare_json_data(self) -> Dict:
        """
        对比两组JSON数据的差异，支持指定对比字段
        :return: 包含对比结果和统计信息的字典
        """
        # 构建按主键分组的字典
        dict1 = defaultdict(list)
        dict2 = defaultdict(list)

        # 处理第一组数据
        for idx, item in enumerate(self.list1):
            key = self._get_key_value(item, idx)
            dict1[key].append(item)

        # 处理第二组数据
        for idx, item in enumerate(self.list2):
            key = self._get_key_value(item, idx)
            dict2[key].append(item)

        # 找出所有唯一的主键值
        all_keys = set(dict1.keys()) | set(dict2.keys())

        # 准备对比结果
        for key in sorted(all_keys):
            items1 = dict1.get(key, [])
            items2 = dict2.get(key, [])

            if not items1:
                # 只在第二组中存在
                count2 = len(items2)
                self.stats['only_in_list2'] += count2
                self.stats['total_differences'] += count2

                for item in items2:
                    field_diffs = self._compare_items(None, item)
                    self.comparison_result.append({
                        'key': key,
                        'name': self._get_name_value(item),
                        'stockType': self._get_stock_value(item),
                        'status': 'only_in_list2',
                        'data1': None,
                        'data2': item,
                        'differences': field_diffs
                    })

            elif not items2:
                # 只在第一组中存在
                count1 = len(items1)
                self.stats['only_in_list1'] += count1
                self.stats['total_differences'] += count1

                for item in items1:
                    field_diffs = self._compare_items(item, None)
                    self.comparison_result.append({
                        'key': key,
                        'name': self._get_name_value(item),
                        'stockType': self._get_stock_value(item),
                        'status': 'only_in_list1',
                        'data1': item,
                        'data2': None,
                        'differences': field_diffs
                    })

            else:
                # 两个列表都有这个主键，需要详细比较
                self._compare_same_key_items(items1, items2, key)

        return {
            'comparison': self.comparison_result,
            'stats': self.stats
        }

    def get_detailed_stats(self) -> Dict:
        """获取更详细的统计信息"""
        detailed_stats = self.stats.copy()
        detailed_stats.update({
            'total_records_list1': len(self.list1),
            'total_records_list2': len(self.list2),
            'unique_keys_list1': len(set(self._get_key_value(item, i) for i, item in enumerate(self.list1))),
            'unique_keys_list2': len(set(self._get_key_value(item, i) for i, item in enumerate(self.list2))),
            'compared_fields': list(self.compare_fields) if self.compare_fields else 'all fields',
            'excluded_fields': list(self.exclude_fields),
            'sort_fields': list(self.sort_fields)
        })
        return detailed_stats


if __name__ == '__main__':
    # 测试示例
    a = [{'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 543.5,
          'Length': 565.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'},
         {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 531.5,
          'Length': 865.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'},
         {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 543.5,
          'Length': 865.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'}]

    b = [{'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 543.5,
          'Length': 565.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'},
         {'StockUpType': 1, 'Code': 'F10A1-1', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 543.5,
          'Length': 865.0, 'Quantity': 1.2, 'Remark': '', 'EdgeBanding': '四○'},
         {'StockUpType': 1, 'Code': 'F10A1-3', 'Name': '非标上固层', 'Color': 'BD907AG', 'Height': 18.0, 'Width': 531.5,
          'Length': 865.0, 'Quantity': 1.0, 'Remark': '', 'EdgeBanding': '四○'}]

    # 创建比较器实例
    comparator = OrderComparator(a, b, key_field="Code", name_field="Name")

    # 执行比较
    result = comparator.compare_json_data()
    print(result)
    print("比较结果:")
    for item in result['comparison']:
        print(f"Key: {item['key']}, Status: {item['status']}")
        if item['differences']:
            print(f"差异: {item['differences']}")

    print("\n统计信息:")
    print(comparator.get_detailed_stats())
