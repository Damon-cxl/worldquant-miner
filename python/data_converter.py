import json
import os
import sys
# 修复导入语句，确保zdb目录在Python路径中
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入所需模块
from zdb import db_operations

def convert_table_to_data_structure(file_path):
    """
    从文本文件中读取表格数据并转换为结构化数据集合
    
    Args:
        file_path: 表格数据文本文件路径
        
    Returns:
        list: 转换后的结构化数据列表
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件格式不正确
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 从文本文件中读取表格数据
    with open(file_path, 'r', encoding='utf-8') as f:
        table_data = f.read()
    
    lines = table_data.strip().split('\n')
    
    # 验证文件格式
    if len(lines) < 3:
        raise ValueError("文件格式不正确，需要包含表头、分割线和至少一行数据")
    
    # 解析表头
    headers = [h.strip() for h in lines[0].split('|')]
    
    # 跳过分割线
    data_lines = lines[2:]
    
    result_data = []
    
    for line_num, line in enumerate(data_lines, start=3):  # 行号从3开始（跳过表头和分割线）
        if not line.strip():
            continue
        
        values = [v.strip() for v in line.split('|') if v.strip() != '']
        
        # 验证每行数据的列数
        if len(values) < 3:  # 至少需要原始字段、一个相似度字段和一个相似分
            print(f"警告: 第{line_num}行数据格式不正确，跳过该行")
            continue
        
        try:

            # 处理Top1到Top10的数据
            for i in range(1, min(20, len(values)), 2):  # 防止索引越界
                rank = (i + 1) // 2  # 计算当前是Top几
                if i + 1 < len(values):
                    row_data = {}
                    row_data['origin'] = values[0]
                    similarity_name = values[i]
                    try:
                        similarity_score = float(values[i + 1]) if values[i + 1] else None
                    except ValueError:
                        print(f"警告: 第{line_num}行Top{rank}相似分格式不正确，跳过该值：{values[i + 1]}")
                        similarity_score = None
                    
                    row_data['sim_field'] = similarity_name
                    row_data['sim'] = similarity_score
                    result_data.append(row_data)
        except Exception as e:
            print(f"警告: 处理第{line_num}行时出错: {str(e)}，跳过该行")
    
    if not result_data:
        raise ValueError("未找到有效数据，请检查文件格式")
    
    return result_data

def main():
    """
    主函数，处理命令行参数并执行数据转换
    """
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 默认文件路径（使用绝对路径）
    default_input_file = os.path.join(script_dir, 'similarity_data.txt')
    default_output_file = os.path.join(script_dir, 'similarity_data.json')
    
    # 处理命令行参数
    input_file = default_input_file
    output_file = default_output_file
    
    # 如果用户提供了命令行参数，需要判断是相对路径还是绝对路径
    if len(sys.argv) > 1:
        # 如果用户提供的是相对路径，则相对于脚本所在目录
        if not os.path.isabs(sys.argv[1]):
            input_file = os.path.join(script_dir, sys.argv[1])
        else:
            input_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        # 如果用户提供的是相对路径，则相对于脚本所在目录
        if not os.path.isabs(sys.argv[2]):
            output_file = os.path.join(script_dir, sys.argv[2])
        else:
            output_file = sys.argv[2]
    
    print(f"正在从文件读取数据: {input_file}")
    
    try:
        # 转换数据
        data_collection = convert_table_to_data_structure(input_file)
        
        # 保存到数据库
        try:
            db_ops = db_operations.DataBaseOp()
            if db_ops.batch_save_similar_fields(data_collection):
                print(f"数据成功保存到数据库")
            else:
                print(f"警告: 数据保存到数据库失败")
        except Exception as db_error:
            print(f"数据库操作错误: {str(db_error)}")
            # 即使数据库操作失败，也继续保存到文件
        
        # # 打印转换后的数据
        # print("转换后的数据集合:")
        # print(json.dumps(data_collection, ensure_ascii=False, indent=2))
        
        # # 将数据保存到文件
        # with open(output_file, 'w', encoding='utf-8') as f:
        #     json.dump(data_collection, f, ensure_ascii=False, indent=2)
        
        # print(f"\n数据已成功保存到: {output_file}")
        print(f"总共转换了 {len(data_collection)} 条记录")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()