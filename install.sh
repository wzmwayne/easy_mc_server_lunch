#!/bin/bash
# Easy MC Server Lunch 安装脚本
# 开发者: wzmwayne 和 iFlow CLI

set -e

echo "=========================================="
echo "  Easy MC Server Lunch 安装程序"
echo "  开发者: wzmwayne 和 iFlow CLI"
echo "=========================================="
echo ""

# 设置清华源
echo "配置清华源..."
export PKG_MIRROR="https://mirrors.tuna.tsinghua.edu.cn/termux"
sed -i 's|https://packages-cf.termux.dev|https://mirrors.tuna.tsinghua.edu.cn/termux|g' $PREFIX/etc/apt/sources.list 2>/dev/null || true
echo "✓ 清华源已配置"

# 更新包列表
echo "更新包列表..."
pkg update -y
echo "✓ 包列表已更新"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，正在安装..."
    pkg install python -y
else
    echo "✓ Python3 已安装: $(python3 --version)"
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装，正在安装..."
    pkg install python-pip -y
else
    echo "✓ pip3 已安装"
fi

# 配置pip清华源（临时）
echo ""
echo "配置pip清华源..."
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
echo "✓ pip清华源已配置"

# 从GitHub下载Python文件
echo ""
echo "从GitHub下载项目文件..."
REPO_URL="https://wzmwayne.github.io/easy_mc_server_lunch"

# 下载主程序
echo "正在下载 mc_server_manager.py..."
curl -fsSL "${REPO_URL}/mc_server_manager.py" -o mc_server_manager.py
echo "✓ mc_server_manager.py 下载完成"

# 下载模板文件
echo "正在下载模板文件..."
mkdir -p templates
curl -fsSL "${REPO_URL}/templates/index.html" -o templates/index.html
echo "✓ templates/index.html 下载完成"

# 安装Python依赖
echo ""
echo "正在安装Python依赖..."
pip3 install flask psutil --quiet
echo "✓ Python依赖安装完成"

# 检查Java
echo ""
echo "检查Java环境..."
if ! command -v java &> /dev/null; then
    echo "❌ Java 未安装，正在安装 JDK 17..."
    pkg install openjdk-17 -y
else
    echo "✓ Java 已安装: $(java -version 2>&1 | head -1)"
fi

# 创建启动脚本
echo ""
echo "创建启动脚本..."
cat > start.sh << 'EOF'
#!/bin/bash
# Easy MC Server Lunch 启动脚本

cd "$(dirname "$0")"
python3 mc_server_manager.py
EOF

chmod +x start.sh
echo "✓ 启动脚本创建完成: start.sh"

# 创建停止脚本
cat > stop.sh << 'EOF'
#!/bin/bash
# Easy MC Server Lunch 停止脚本

echo "正在停止服务器管理器..."
pkill -f "python3 mc_server_manager.py"
echo "✓ 服务器管理器已停止"
EOF

chmod +x stop.sh
echo "✓ 停止脚本创建完成: stop.sh"

echo ""
echo "=========================================="
echo "  安装完成！"
echo "=========================================="
echo ""
echo "使用方法："
echo "  启动: ./start.sh"
echo "  停止: ./stop.sh"
echo "  或者: python3 mc_server_manager.py"
echo ""
echo "访问地址: http://localhost:5000"
echo ""
echo "=========================================="