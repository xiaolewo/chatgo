#!/usr/bin/env python3
"""
Peewee迁移文件检查脚本
检查所有迁移文件中可能的字段重复问题
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple


def print_header(text):
    print(f"\n🔍 {text}")


def print_success(text):
    print(f"✅ {text}")


def print_warning(text):
    print(f"⚠️  {text}")


def print_error(text):
    print(f"❌ {text}")


def print_info(text):
    print(f"ℹ️  {text}")


class PeeweeMigrationChecker:
    def __init__(self, migrations_dir: str):
        self.migrations_dir = Path(migrations_dir)
        self.field_history: Dict[str, Dict[str, List[str]]] = (
            {}
        )  # table -> field -> [migration_files]
        self.potential_conflicts: List[Tuple[str, str, str, List[str]]] = []

    def scan_migration_files(self) -> List[Path]:
        """扫描所有迁移文件"""
        migration_files = []
        for file in self.migrations_dir.glob("*.py"):
            if file.name.startswith("00") and file.name != "__init__.py":
                migration_files.append(file)
        return sorted(migration_files)

    def extract_add_fields_operations(
        self, file_path: Path
    ) -> List[Tuple[str, List[str]]]:
        """从迁移文件中提取add_fields操作"""
        operations = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 查找add_fields调用
            add_fields_pattern = r'migrator\.add_fields\s*\(\s*["\'](\w+)["\']([^)]+)\)'
            matches = re.findall(add_fields_pattern, content, re.MULTILINE | re.DOTALL)

            for table_name, fields_part in matches:
                # 提取字段名
                field_names = []
                # 简单的字段名提取（可能需要更复杂的解析）
                field_matches = re.findall(r"(\w+)\s*=\s*pw\.\w+", fields_part)
                field_names.extend(field_matches)

                if field_names:
                    operations.append((table_name, field_names))

        except Exception as e:
            print_error(f"解析文件 {file_path} 时出错: {e}")

        return operations

    def analyze_migrations(self) -> None:
        """分析所有迁移文件"""
        print_header("扫描Peewee迁移文件")

        migration_files = self.scan_migration_files()
        print_info(f"找到 {len(migration_files)} 个迁移文件")

        for migration_file in migration_files:
            print_info(f"分析: {migration_file.name}")
            operations = self.extract_add_fields_operations(migration_file)

            for table_name, field_names in operations:
                if table_name not in self.field_history:
                    self.field_history[table_name] = {}

                for field_name in field_names:
                    if field_name not in self.field_history[table_name]:
                        self.field_history[table_name][field_name] = []
                    self.field_history[table_name][field_name].append(
                        migration_file.name
                    )

    def detect_conflicts(self) -> None:
        """检测潜在的字段冲突"""
        print_header("检测潜在的字段冲突")

        for table_name, fields in self.field_history.items():
            for field_name, migration_files in fields.items():
                if len(migration_files) > 1:
                    self.potential_conflicts.append(
                        (table_name, field_name, "重复添加字段", migration_files)
                    )
                    print_warning(
                        f"表 '{table_name}' 的字段 '{field_name}' 在多个迁移中被添加:"
                    )
                    for mf in migration_files:
                        print(f"    - {mf}")

    def check_specific_problematic_patterns(self) -> None:
        """检查特定的问题模式"""
        print_header("检查特定问题模式")

        migration_files = self.scan_migration_files()

        for migration_file in migration_files:
            try:
                with open(migration_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 检查是否有直接的add_fields而没有错误处理
                if "add_fields" in content and "try:" not in content:
                    print_warning(
                        f"{migration_file.name}: 使用add_fields但没有错误处理"
                    )

                # 检查是否有已知的问题字段
                problematic_fields = [
                    "share_id",
                    "timestamp",
                    "updated_at",
                    "created_at",
                ]
                for field in problematic_fields:
                    if f"{field}=" in content and "duplicate column" not in content:
                        print_warning(
                            f"{migration_file.name}: 添加了可能冲突的字段 '{field}'"
                        )

            except Exception as e:
                print_error(f"检查文件 {migration_file} 时出错: {e}")

    def generate_fixes(self) -> None:
        """生成修复建议"""
        print_header("修复建议")

        if not self.potential_conflicts:
            print_success("未发现明显的字段冲突")
            return

        print_info("建议的修复方案:")

        for table, field, issue_type, files in self.potential_conflicts:
            print(f"\n🔧 表: {table}, 字段: {field}")
            print(f"   问题: {issue_type}")
            print(f"   涉及文件: {', '.join(files)}")
            print("   建议修复:")
            print("   1. 在add_fields调用外添加try-except处理")
            print("   2. 捕获'duplicate column'错误并忽略")
            print("   3. 示例代码:")
            print("""
   try:
       migrator.add_fields(
           "{}", {}=pw.SomeField(...)
       )
   except Exception as e:
       if "duplicate column" in str(e).lower():
           print("⚠️  字段已存在，跳过添加")
       else:
           raise e
""".format(table, field))

    def run_full_check(self) -> None:
        """运行完整检查"""
        print_header("Peewee迁移完整性检查")

        if not self.migrations_dir.exists():
            print_error(f"迁移目录不存在: {self.migrations_dir}")
            return

        self.analyze_migrations()
        self.detect_conflicts()
        self.check_specific_problematic_patterns()
        self.generate_fixes()

        print_header("检查完成")
        if self.potential_conflicts:
            print_warning(f"发现 {len(self.potential_conflicts)} 个潜在冲突")
        else:
            print_success("所有迁移文件看起来正常")


def main():
    """主函数"""
    print("🔧 Peewee迁移检查工具")

    # 检查迁移目录
    migrations_dir = "backend/open_webui/internal/migrations"

    if not os.path.exists(migrations_dir):
        print_error(f"迁移目录不存在: {migrations_dir}")
        return

    # 运行检查
    checker = PeeweeMigrationChecker(migrations_dir)
    checker.run_full_check()

    print_header("推荐的后续行动")
    print("1. 修复发现的冲突迁移文件")
    print("2. 运行数据库测试验证修复效果")
    print("3. 更新其他相似的迁移文件")


if __name__ == "__main__":
    main()
