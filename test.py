import json

def to_camel_case(snake_str):
    """将下划线命名 (snake_case) 转换为驼峰命名 (camelCase)"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def capitalize_first(s):
    """首字母大写，用于生成类名"""
    return s[0].upper() + s[1:] if s else s

class JavaEntityGenerator:
    def __init__(self):
        # 存储解析出的所有类及其字段：{ 类名: [(数据类型, 字段名)] }
        self.classes = {}

    def parse(self, class_name, data):
        """递归解析 JSON 字典并提取字段类型"""
        fields = []
        for key, value in data.items():
            java_type = self._get_java_type(key, value)
            camel_key = to_camel_case(key)
            fields.append((java_type, camel_key))
        # 保存当前类的结构
        self.classes[class_name] = fields

    def _get_java_type(self, key, value):
        """根据 Python 数据类型映射到对应的 Java 数据类型"""
        if isinstance(value, str):
            return "String"
        elif isinstance(value, bool): # 注意：在 Python 中 bool 是 int 的子类，必须先判断 bool
            return "Boolean"
        elif isinstance(value, int):
            return "Integer"
        elif isinstance(value, float):
            return "Double"
        elif isinstance(value, dict):
            # 处理嵌套对象：生成一个新的类
            nested_class_name = capitalize_first(to_camel_case(key))
            self.parse(nested_class_name, value) # 递归解析内部类
            return nested_class_name
        elif isinstance(value, list):
            # 处理数组：尝试获取泛型类型
            if len(value) > 0:
                # 尝试去掉复数的 's' 作为泛型类名，或者加上 'Item'
                singular_key = key[:-1] if key.endswith('s') else key + "Item"
                elem_type = self._get_java_type(singular_key, value[0])
                return f"List<{elem_type}>"
            else:
                return "List<Object>"
        else:
            return "Object"

    def generate_code(self, use_lombok=True):
        """将解析后的数据结构拼装成 Java 代码"""
        code_lines = []
        
        if use_lombok:
            code_lines.append("import lombok.Data;\n")
        code_lines.append("import java.util.List;\n")
        
        # 遍历生成所有实体类（包含主类和嵌套类）
        for cls_name, fields in self.classes.items():
            if use_lombok:
                code_lines.append("@Data")
            code_lines.append(f"public class {cls_name} {{")
            
            # 生成属性字段
            for java_type, field_name in fields:
                code_lines.append(f"    private {java_type} {field_name};")
            
            # 如果不使用 Lombok，则生成标准的 Getter 和 Setter
            if not use_lombok:
                code_lines.append("")
                for java_type, field_name in fields:
                    capitalized_field = capitalize_first(field_name)
                    # Getter
                    code_lines.append(f"    public {java_type} get{capitalized_field}() {{")
                    code_lines.append(f"        return {field_name};")
                    code_lines.append("    }")
                    # Setter
                    code_lines.append(f"    public void set{capitalized_field}({java_type} {field_name}) {{")
                    code_lines.append(f"        this.{field_name} = {field_name};")
                    code_lines.append("    }")

            code_lines.append("}\n")
        
        return "\n".join(code_lines)

def json_to_java(json_str, root_class_name="RootEntity", use_lombok=True):
    """入口函数"""
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return "错误: 最外层 JSON 必须是一个 Object ({})。"
        
        generator = JavaEntityGenerator()
        generator.parse(root_class_name, data)
        return generator.generate_code(use_lombok)
    except json.JSONDecodeError as e:
        return f"JSON 解析失败: {e}"

# ================= 测试与运行 =================
if __name__ == '__main__':
    # 你可以在这里替换成你的 JSON 字符串
    sample_json = """
    {
        "user_id": 1001,
        "user_name": "张三",
        "is_active": true,
        "score": 98.5,
        "address": {
            "province": "Guangdong",
            "city": "Shenzhen",
            "zip_code": 518000
        },
        "orders": [
            {
                "order_id": "ORD-001",
                "amount": 250.0
            }
        ],
        "tags": ["VIP", "New"]
    }
    """
    
    # 运行并打印生成的 Java 代码
    java_code = json_to_java(sample_json, root_class_name="UserInfo", use_lombok=True)
    print(java_code)