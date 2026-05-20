import pandas as pd
import re
import os

def snake_to_camel(snake_str):
    """将下划线命名转换为驼峰命名 (data_date -> dataDate)"""
    components = snake_str.split('_')
    # 处理空字符串或不包含下划线的情况
    if not components or not components[0]:
        return snake_str
    return components[0].lower() + ''.join(x.title() for x in components[1:])

def generate_java_pojo(excel_path, sheet_name, class_name):
    print(f"🚀 开始解析 Excel: {excel_path} | Sheet: {sheet_name}")
    
    # 核心：定义 SQL/Excel 数据类型到 Java 类型的映射字典
    type_mapping = {
        'VARCHAR': 'String',
        'CHAR': 'String',
        'TEXT': 'String',
        'INT': 'Integer',
        'BIGINT': 'Long',
        'DECIMAL': 'BigDecimal',
        'NUMERIC': 'BigDecimal',
        'DOUBLE': 'Double',
        'FLOAT': 'Float',
        'DATE': 'LocalDate',
        'DATETIME': 'LocalDateTime',
        'TIMESTAMP': 'Long' # 或者 LocalDateTime，视您的 Flink 处理习惯而定
    }

    try:
        # 读取 Excel。
        # 观察您的截图，真正的表头在第 3 行（索引为 2），所以我们跳过前两行。
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=2)
        
        # 清理数据：过滤掉“字段”列为空的行（忽略空行）
        df = df.dropna(subset=['字段'])
        
        # 开始拼接 Java 代码
        java_code = "import lombok.Data;\n"
        java_code += "import java.math.BigDecimal;\n"
        java_code += "import java.time.LocalDateTime;\n"
        java_code += "import java.time.LocalDate;\n\n"
        java_code += "/**\n * 自动生成的实体类\n * 来源 Sheet: " + sheet_name + "\n */\n"
        java_code += "@Data\n"
        java_code += f"public class {class_name} {{\n\n"

        # 遍历数据行
        for index, row in df.iterrows():
            # 提取并清理三个核心字段
            field_en = str(row['字段']).strip()
            field_cn = str(row['名称']).strip()
            data_type = str(row['数据类型']).strip().upper()
            
            if field_en == 'nan' or not field_en:
                continue

            # 处理数据类型中的长度，例如将 "VARCHAR(10)" 过滤为 "VARCHAR"
            clean_data_type = re.sub(r'\(.*?\)', '', data_type).strip()
            
            # 获取对应的 Java 类型，如果字典里没有，默认兜底使用 String
            java_type = type_mapping.get(clean_data_type, 'String')
            
            # 转换为驼峰命名
            camel_case_field = snake_to_camel(field_en)

            # 拼装带有注释的字段声明
            java_code += f"    /**\n     * {field_cn}\n     */\n"
            java_code += f"    private {java_type} {camel_case_field};\n\n"

        java_code += "}\n"
        
        # 将生成的代码写入 .java 文件
        output_file = f"{class_name}.java"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(java_code)
            
        print(f"✅ 成功生成 Java 文件: {os.path.abspath(output_file)}")
        print("-" * 40)
        print(java_code)
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")

if __name__ == "__main__":
    # 使用示例：请将这里的路径替换为您真实的 Excel 路径
    FILE_PATH = "data_dict.xlsx" 
    SHEET_NAME = "Sheet1"        # 替换为真实的 Sheet 名称
    TARGET_CLASS_NAME = "GpsLabelVariable" # 您期望生成的 Java 类名

    # 如果要批量处理多个 Sheet，可以在这里加个 for 循环
    generate_java_pojo(FILE_PATH, SHEET_NAME, TARGET_CLASS_NAME)
