#!/usr/bin/env python3
"""
Typora 激活脚本 - 新版本支持
基于 JavaScript 文件修改的激活方法
支持 Windows 和 macOS
"""

import os
import sys
import shutil
import re
import platform
from pathlib import Path
from loguru import logger


class TyporaActivator:
    def __init__(self):
        self.system = platform.system()
        self.typora_paths = self._get_typora_paths()
        self.backup_suffix = ".backup"
        
    def _get_typora_paths(self):
        """获取不同系统下的 Typora 安装路径"""
        if self.system == "Darwin":  # macOS
            return [
                "/Applications/Typora.app/Contents/Resources/TypeMark",
                "/Applications/Typora.app/Contents/Resources"
            ]
        elif self.system == "Windows":
            return [
                "C:\\Program Files\\Typora",
                "C:\\Program Files (x86)\\Typora",
                os.path.expanduser("~\\AppData\\Local\\Programs\\Typora")
            ]
        elif self.system == "Linux":
            return [
                "/usr/share/typora",
                "/opt/typora",
                os.path.expanduser("~/.local/share/typora")
            ]
        else:
            return []
    
    def find_typora_installation(self):
        """查找 Typora 安装目录"""
        logger.info(f"在 {self.system} 系统上查找 Typora 安装目录...")
        
        for base_path in self.typora_paths:
            if os.path.exists(base_path):
                # 查找 resources 目录下的文件结构
                possible_paths = [
                    os.path.join(base_path, "resources", "page-dist", "static", "js"),
                    os.path.join(base_path, "page-dist", "static", "js"),
                    os.path.join(base_path, "resources", "app.asar.unpacked", "page-dist", "static", "js")
                ]
                
                for js_path in possible_paths:
                    if os.path.exists(js_path):
                        logger.info(f"找到 Typora JavaScript 目录: {js_path}")
                        return js_path
        
        return None
    
    def find_license_file(self, js_dir):
        """查找 LicenseIndex 文件"""
        logger.info(f"在目录中查找 LicenseIndex 文件: {js_dir}")
        
        # 查找符合模式的文件
        patterns = [
            "LicenseIndex.*.chunk.js",
            "LicenseIndex.*.js", 
            "*LicenseIndex*.js",
            "*license*.js"
        ]
        
        for pattern in patterns:
            files = list(Path(js_dir).glob(pattern))
            if files:
                license_file = str(files[0])
                logger.info(f"找到许可证文件: {license_file}")
                return license_file
        
        # 如果没找到，列出所有 js 文件让用户选择
        js_files = list(Path(js_dir).glob("*.js"))
        if js_files:
            logger.warning("未找到标准的 LicenseIndex 文件，以下是可用的 JS 文件:")
            for i, file in enumerate(js_files):
                logger.info(f"{i+1}. {file.name}")
        
        return None
    
    def backup_file(self, file_path):
        """备份原始文件"""
        backup_path = file_path + self.backup_suffix
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
            logger.info(f"已备份原始文件: {backup_path}")
        else:
            logger.info(f"备份文件已存在: {backup_path}")
        return backup_path
    
    def modify_license_file(self, file_path):
        """修改许可证文件实现激活"""
        logger.info(f"开始修改许可证文件: {file_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找目标字符串
            target_pattern = r'e\.hasActivated="true"==e\.hasActivated'
            replacement = 'e.hasActivated="true"=="true"'
            
            # 尝试多种可能的模式
            patterns_and_replacements = [
                (r'e\.hasActivated="true"==e\.hasActivated', 'e.hasActivated="true"=="true"'),
                (r'hasActivated="true"==\w+\.hasActivated', 'hasActivated="true"=="true"'),
                (r'(\w+)\.hasActivated="true"==\1\.hasActivated', r'\1.hasActivated="true"=="true"'),
                # 更通用的模式
                (r'(\w+\.)?hasActivated="true"==(\w+\.)?hasActivated', r'\1hasActivated="true"=="true"'),
            ]
            
            modified = False
            for pattern, replacement in patterns_and_replacements:
                if re.search(pattern, content):
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        content = new_content
                        modified = True
                        logger.success(f"成功应用模式: {pattern}")
                        break
            
            if not modified:
                # 如果没有找到标准模式，尝试更宽泛的搜索
                logger.warning("未找到标准激活模式，尝试搜索相关代码...")
                
                # 搜索可能的激活相关代码
                activation_patterns = [
                    r'hasActivated',
                    r'activated',
                    r'license',
                    r'registered'
                ]
                
                for pattern in activation_patterns:
                    matches = re.findall(f'.*{pattern}.*', content, re.IGNORECASE)
                    if matches:
                        logger.info(f"找到可能相关的代码 (模式: {pattern}):")
                        for match in matches[:3]:  # 只显示前3个匹配
                            logger.info(f"  {match[:100]}...")
                
                logger.error("无法找到可修改的激活代码，可能需要手动分析文件")
                return False
            
            # 写入修改后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.success("文件修改完成！")
            return True
            
        except Exception as e:
            logger.error(f"修改文件时发生错误: {e}")
            return False
    
    def restore_backup(self, file_path):
        """恢复备份文件"""
        backup_path = file_path + self.backup_suffix
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            logger.info(f"已恢复备份文件: {file_path}")
            return True
        else:
            logger.error(f"备份文件不存在: {backup_path}")
            return False
    
    def modify_popup_prevention(self, typora_base_dir):
        """可选：阻止激活弹窗"""
        logger.info("尝试阻止激活弹窗...")
        
        # 查找 license.html 文件
        possible_paths = [
            os.path.join(typora_base_dir, "resources", "page-dist", "license.html"),
            os.path.join(typora_base_dir, "page-dist", "license.html")
        ]
        
        for license_html_path in possible_paths:
            if os.path.exists(license_html_path):
                try:
                    # 备份
                    self.backup_file(license_html_path)
                    
                    # 读取并修改
                    with open(license_html_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 在 </body> 前添加自动关闭脚本
                    if '<script>window.close()</script>' not in content:
                        content = content.replace('</body>', '<script>window.close()</script>\n</body>')
                        
                        with open(license_html_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logger.success("已添加弹窗阻止代码")
                        return True
                    else:
                        logger.info("弹窗阻止代码已存在")
                        return True
                        
                except Exception as e:
                    logger.error(f"修改 license.html 失败: {e}")
        
        logger.warning("未找到 license.html 文件")
        return False
    
    def run(self):
        """运行激活脚本"""
        logger.info("=== Typora 激活脚本开始运行 ===")
        
        # 1. 查找 Typora 安装目录
        js_dir = self.find_typora_installation()
        if not js_dir:
            logger.error("未找到 Typora 安装目录！")
            logger.info("请确保 Typora 已正确安装")
            return False
        
        # 2. 查找许可证文件
        license_file = self.find_license_file(js_dir)
        if not license_file:
            logger.error("未找到许可证文件！")
            return False
        
        # 3. 备份原始文件
        self.backup_file(license_file)
        
        # 4. 修改许可证文件
        if not self.modify_license_file(license_file):
            logger.error("激活失败！")
            return False
        
        # 5. 可选：阻止弹窗
        typora_base = os.path.dirname(os.path.dirname(os.path.dirname(js_dir)))
        self.modify_popup_prevention(typora_base)
        
        logger.success("=== Typora 激活完成！===")
        logger.info("请重新启动 Typora 以查看激活效果")
        logger.info(f"如需恢复原始文件，运行: python {__file__} --restore '{license_file}'")
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Typora 激活脚本")
    parser.add_argument("--restore", help="恢复指定文件的备份")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 配置日志
    logger.remove()
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.add(sys.stderr, level=log_level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}")
    
    activator = TyporaActivator()
    
    if args.restore:
        # 恢复模式
        if activator.restore_backup(args.restore):
            logger.success("恢复完成！")
        else:
            logger.error("恢复失败！")
        return
    
    # 正常激活模式
    try:
        success = activator.run()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"发生未预期的错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()