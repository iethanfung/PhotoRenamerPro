import pandas as pd
import re
from loguru import logger


class ExcelEngine:
    def __init__(self):
        self.df = None
        self.lookup_map = {}  # RelNo (str_4_digits) -> Row Data (dict)

    def load_excel(self, path, header_map):
        """
        :param path: Excel 文件路径
        :param header_map: 字典，映射 {标准列名: Excel实际列名}
        """
        try:
            # 1. 读取 Excel，强制所有内容为字符串
            # keep_default_na=False 防止将 'NA' 识别为空值
            self.df = pd.read_excel(path, dtype=str, keep_default_na=False)

            # 2. 强力清洗表头：去除前后空格
            self.df.columns = self.df.columns.str.strip()

            # 3. 获取用户配置的列名
            rel_col_name = header_map.get("Rel_No", "No#").strip()

            # 4. 检查列是否存在
            if rel_col_name not in self.df.columns:
                available_cols = " | ".join(self.df.columns.tolist())
                error_msg = (
                    f"❌ 错误：在 Excel 中找不到名为 '{rel_col_name}' 的列！\n"
                    f"----------------------------------\n"
                    f"Excel 实际检测到的列名:\n[{available_cols}]\n"
                    f"----------------------------------\n"
                    f"请检查 [Settings] -> [Mapping] 中的配置是否与上方完全一致（区分大小写）。"
                )
                logger.error(error_msg)
                return False, error_msg

            # 5. 建立多重索引 (核心修复逻辑)
            self.lookup_map = {}
            count = 0

            for idx, row in self.df.iterrows():
                raw_val = str(row[rel_col_name]).strip()

                # 跳过无效行
                if not raw_val or raw_val.lower() in ['nan', 'none', '']:
                    continue

                # === 数据清洗 ===
                # 修复 Case 1: "154.0" -> "154" (浮点数转字符串残留)
                if raw_val.endswith(".0"):
                    raw_val = raw_val[:-2]

                # 准备一组可能的 Key，确保无论文件名怎么写都能命中
                keys_to_add = set()
                keys_to_add.add(raw_val)  # 原始值 (如 "154")

                # 如果是数字，生成补零版本
                if raw_val.isdigit():
                    keys_to_add.add(raw_val.zfill(4))  # "0154"
                    keys_to_add.add(str(int(raw_val)))  # "154" (去零)

                # 构建行数据字典
                row_data = row.to_dict()

                # 注入标准列名 (Build, Test 等)
                for std_key, excel_key in header_map.items():
                    clean_excel_key = excel_key.strip()
                    # 同样处理 .0 问题
                    val = str(row_data.get(clean_excel_key, "UNKNOWN")).strip()
                    if val.endswith(".0"):
                        val = val[:-2]
                    row_data[std_key] = val

                # 将这一行数据绑定到所有可能的 Key 上
                for k in keys_to_add:
                    self.lookup_map[k] = row_data

                count += 1

            # 打印调试信息 (你可以在 PyCharm 的 Run 窗口看到)
            sample_keys = list(self.lookup_map.keys())[:10]
            logger.info(f"✅ Excel 加载成功！有效数据行数: {count}")
            logger.info(f"🔍 索引库示例 (文件名包含这些数字才能识别): {sample_keys}")

            return True, f"成功加载 {count} 行数据"

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"Excel Load Error: {error_detail}")
            return False, f"Excel 读取失败: {str(e)}"

    def get_unit_info(self, rel_no):
        """返回 Unit 信息字典"""
        if not rel_no:
            return None

        rel_no = str(rel_no).strip()

        # 1. 直接匹配
        if rel_no in self.lookup_map:
            return self.lookup_map[rel_no]

        # 2. 尝试补全4位匹配 (针对文件名是 65，Excel是 0065)
        if rel_no.isdigit():
            padded = rel_no.zfill(4)
            if padded in self.lookup_map:
                return self.lookup_map[padded]

        return None