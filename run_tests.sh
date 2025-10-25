#!/bin/bash
# 自动化测试运行脚本

echo "======================================================================"
echo "              笔记应用 - 自动化测试套件                              "
echo "======================================================================"
echo ""

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到Python环境"
    exit 1
fi

echo "✅ Python版本:"
python --version
echo ""

# 检查必要的依赖
echo "📦 检查依赖包..."
REQUIRED_PACKAGES=("flask" "flask_sqlalchemy" "flask_login" "flask_wtf" "pillow")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    python -c "import $package" 2>/dev/null
    if [ $? -ne 0 ]; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo "❌ 缺少以下依赖包: ${MISSING_PACKAGES[*]}"
    echo "请运行: pip install ${MISSING_PACKAGES[*]}"
    exit 1
fi

echo "✅ 所有依赖包已安装"
echo ""

# 生成测试数据
echo "======================================================================"
echo "步骤 1/3: 生成测试数据"
echo "======================================================================"
python test_data_generator.py
echo ""

# 运行测试
echo "======================================================================"
echo "步骤 2/3: 运行自动化测试"
echo "======================================================================"
python test_app.py

TEST_RESULT=$?

# 清理测试数据（可选）
echo ""
echo "======================================================================"
echo "步骤 3/3: 清理测试数据"
echo "======================================================================"
read -p "是否清理测试文件? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python -c "from test_data_generator import TestDataGenerator; TestDataGenerator().cleanup()"
    echo "✅ 测试文件已清理"
else
    echo "ℹ️  测试文件保留在 test_files/ 目录"
fi

echo ""
echo "======================================================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ 所有测试通过！"
else
    echo "❌ 部分测试失败，请查看上方错误信息"
fi
echo "======================================================================"

exit $TEST_RESULT