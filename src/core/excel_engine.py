import pandas as pd
import re
from loguru import logger


class ExcelEngine:
    def __init__(self):
        self.df = None
        # 查找字典：RelNo (纯数字/原始值) -> [RowData1, RowData2...]
        self.lookup_map = {}

    def load_excel(self, path, header_map):
        """
        加载 CSV 文件并建立智能索引
        """
        try:
            # 1. 读取 CSV (尝试多种编码，防止乱码)
            try:
                self.df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding='utf-8')
            except UnicodeDecodeError:
                logger.warning("UTF-8 解码失败，尝试 GBK...")
                self.df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding='gbk')

            # 2. 清理表头：去除空格
            self.df.columns = self.df.columns.str.strip()

            # 3. 获取 Rel No 列名
             #这里定义可能的rel no的表头写法
            possible_keys = ["Rel No.", "Rel No", "Rel#", "Rel", "No#"]
            rel_col_name = None
            for key in possible_keys:
                if key in header_map:
                    rel_col_name = header_map[key].strip()
                    break

            if rel_col_name is None:
                # 如果都没有找到，使用默认值
                rel_col_name = "No#"


            # 4. 验证列是否存在
            if rel_col_name not in self.df.columns:
                logger.error(f"列名 '{rel_col_name}' 不存在！CSV 列名: {self.df.columns.tolist()}")
                return False, f"找不到列: {rel_col_name}"

            # 5. 建立智能索引
            self.lookup_map = {}
            count = 0

            for idx, row in self.df.iterrows():
                # 获取原始机台号 (例如 "rel4817", "no.4088", "154")
                raw_val = str(row[rel_col_name]).strip()

                if not raw_val or raw_val.lower() in ['nan', '']:
                    continue

                # 生成所有可能的 Key
                keys_to_add = set()
                keys_to_add.add(raw_val)  # 1. 添加原始值

                # 2. 提取纯数字作为通用 Key (V4.0 核心优化)
                # 这样文件名里的 "4817" 就能找到 CSV 里的 "rel4817"
                nums = re.findall(r'\d+', raw_val)
                if nums:
                    # 通常取最长的一段数字作为核心 ID
                    core_num = max(nums, key=len)
                    keys_to_add.add(core_num)  # "4817"
                    keys_to_add.add(core_num.zfill(4))  # "0065" (如果数字短)
                    keys_to_add.add(str(int(core_num)))  # "65" (去零)

                # 准备行数据
                row_data = row.to_dict()
                # 注入标准键 (Build, Test 等)
                for std_key, excel_key in header_map.items():
                    clean_k = excel_key.strip()
                    val = str(row_data.get(clean_k, "UNKNOWN")).strip()
                    row_data[std_key] = val

                # === 存入字典 ===
                for k in keys_to_add:
                    if k not in self.lookup_map:
                        self.lookup_map[k] = []
                    # 避免同一行重复添加
                    if row_data not in self.lookup_map[k]:
                        self.lookup_map[k].append(row_data)

                    # 调试日志
                    # if "154" in k:
                    #     logger.debug(f"索引绑定: Key={k} -> Test={row_data.get('Test')}")

                count += 1

            logger.info(f"✅ CSV 加载完毕。有效行数: {count}。索引库大小: {len(self.lookup_map)}")
            return True, f"加载成功: {count} 行"

        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            return False, str(e)

    def get_unit_info(self, rel_no, target_test=None):
        """
        返回 Unit 信息列表。
        """
        if not rel_no: return None

        rel_no = str(rel_no).strip()
        candidates = []

        # 1. 直接查找
        if rel_no in self.lookup_map:
            candidates = self.lookup_map[rel_no]

        # 2. 尝试补零查找 (兼容文件名 65 -> CSV 0065)
        elif rel_no.isdigit():
            padded = rel_no.zfill(4)
            if padded in self.lookup_map:
                candidates = self.lookup_map[padded]

        return candidates if candidates else None