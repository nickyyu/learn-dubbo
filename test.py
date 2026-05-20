import pandas as pd
import math
import os

def generate_mysql_ddl(excel_path, sheet_name, table_name, table_comment, primary_keys=None):
    """
    解析 Excel 数据字典并生成 MySQL 物理建表语句
    """
    print(f"🚀 开始解析 Excel: {excel_path} | Sheet: {sheet_name}")
    
    try:
        # 读取 Excel，截图显示表头在第 3 行（索引为 2）
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=2)
        
        # 过滤掉“字段”列为空的行（忽略空行）
        df = df.dropna(subset=['字段'])
        
        # 拼接 SQL 头
        sql_code = f"CREATE TABLE `{table_name}` (\n"
        
        columns_sql = []
        # 遍历数据行
        for index, row in df.iterrows():
            # 提取信息
            field_en = str(row['字段']).strip()
            field_cn = str(row['名称']).strip()
            
            # 如果遇到空行则跳过
            if field_en == 'nan' or not field_en:
                continue
                
            # 处理数据类型和长度
            data_type = str(row.get('数据类型', 'VARCHAR')).strip().upper()
            length = row.get('长度', '')
            
            # 智能组装数据类型（比如 VARCHAR + 10 -> VARCHAR(10)）
            # 如果类型里本身不带括号，且长度列有值，则拼接长度
            if pd.notna(length) and str(length).strip() != '' and '(' not in data_type:
                try:
                    # 处理 Excel 读取数字可能变成 10.0 的情况
                    len_int = int(float(length))
                    final_type = f"{data_type}({len_int})"
                except ValueError:
                    final_type = data_type
            else:
                final_type = data_type
            
            # 对于数值类型如果没有指定长度，给定默认的类型展示
            if final_type == 'INT':
                final_type = 'INT(11)' 
                
            # 处理注释中的单引号（防止 SQL 语法报错）
            safe_comment = field_cn.replace("'", "\\'")
            
            # 拼接单行字段定义
            column_def = f"  `{field_en}` {final_type} COMMENT '{safe_comment}'"
            columns_sql.append(column_def)

        # 处理主键约束
        if primary_keys and len(primary_keys) > 0:
            pk_str = ", ".join([f"`{pk}`" for pk in primary_keys])
            columns_sql.append(f"  PRIMARY KEY ({pk_str})")

        # 将字段列表通过 ",\n" 拼接，并加入到最终的 SQL 中
        sql_code += ",\n".join(columns_sql)
        sql_code += "\n"
        
        # 拼接 SQL 尾部属性表征
        sql_code += f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='{table_comment}';\n"
        
        # 将生成的建表语句写入 .sql 文件
        output_file = f"{table_name}.sql"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(sql_code)
            
        print(f"✅ 成功生成建表 SQL 文件: {os.path.abspath(output_file)}")
        print("-" * 50)
        print(sql_code)
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")

if __name__ == "__main__":
    # ======== 配置区 ========
    FILE_PATH = "data_dict.xlsx"   # 替换为您 Excel 文件的真实路径
    SHEET_NAME = "Sheet1"          # 替换为真实的 Sheet 名称
    
    # 目标表的元数据
    TABLE_NAME = "bd_gps_lbl_pl"
    TABLE_COMMENT = "GPS变量标签"
    
    # 指定主键（如果截图中的前两个带有复选框代表是主键，则填入这里）
    PRIMARY_KEYS = ["data_date", "geohash"] 
    # =======================

    # 执行生成
    generate_mysql_ddl(FILE_PATH, SHEET_NAME, TABLE_NAME, TABLE_COMMENT, PRIMARY_KEYS)
