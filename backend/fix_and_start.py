import subprocess
import time
import requests
import sys

print("=" * 60)
print("🔧 ResearchMate 一键修复脚本")
print("=" * 60)

# 1. 删除旧数据库
print("\n1️⃣  清理旧数据库...")
import os
db_path = "researchmate.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"   ✅ 已删除: {db_path}")
else:
    print(f"   ℹ️  数据库不存在，跳过删除")

# 2. 启动后端服务（在后台）
print("\n2️⃣  启动后端服务...")
backend_process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# 等待后端启动
print("   ⏳ 等待后端启动...")
time.sleep(5)

# 检查后端是否启动成功
try:
    response = requests.get("http://127.0.0.1:8000/health", timeout=5)
    if response.status_code == 200:
        print("   ✅ 后端启动成功！")
    else:
        print(f"   ❌ 后端启动异常: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ 后端连接失败: {e}")
    backend_process.terminate()
    sys.exit(1)

# 3. 注册/更新用户
print("\n3️⃣  创建测试用户...")
register_data = {
    "email": "dongjiming189@163.com",
    "password": "Test123456",
    "nickname": "演示用户"
}

try:
    # 尝试注册
    response = requests.post(
        "http://127.0.0.1:8000/api/auth/register",
        json=register_data,
        timeout=10
    )
    
    if response.status_code == 201:
        print("   ✅ 用户注册成功！")
        user_info = response.json()
        print(f"   📧 邮箱: {user_info.get('email')}")
        print(f"   👤 昵称: {user_info.get('nickname')}")
    elif response.status_code == 400 and "already registered" in response.text:
        print("   ℹ️  用户已存在，尝试登录验证...")
        
        # 测试登录
        login_response = requests.post(
            "http://127.0.0.1:8000/api/auth/login",
            json={"email": register_data["email"], "password": register_data["password"]},
            timeout=10
        )
        
        if login_response.status_code == 200:
            print("   ✅ 登录验证成功！")
        else:
            print(f"   ❌ 登录失败: {login_response.text}")
    else:
        print(f"   ❌ 注册失败: {response.status_code} - {response.text}")

except Exception as e:
    print(f"   ❌ 操作失败: {e}")

# 4. 验证登录
print("\n4️⃣  验证登录功能...")
try:
    login_response = requests.post(
        "http://127.0.0.1:8000/api/auth/login",
        json={"email": register_data["email"], "password": register_data["password"]},
        timeout=10
    )
    
    if login_response.status_code == 200:
        data = login_response.json()
        print("   ✅ 登录测试成功！")
        print(f"   🔑 Token: {data.get('access_token', 'N/A')[:20]}...")
        print(f"   👤 用户: {data.get('user', {}).get('nickname', 'N/A')}")
    else:
        print(f"   ❌ 登录测试失败: {login_response.status_code} - {login_response.text}")

except Exception as e:
    print(f"   ❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("✨ 修复完成！")
print("=" * 60)
print("\n📝 登录信息:")
print(f"   📧 邮箱: dongjiming189@163.com")
print(f"   🔑 密码: Test123456")
print(f"\n🌐 访问地址: http://localhost:3000/login")
print("\n💡 提示: 后端服务正在后台运行 (PID:", backend_process.pid, ")")
print("   按 Ctrl+C 停止后端服务")

# 保持脚本运行，直到用户按Ctrl+C
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n🛑 正在停止后端服务...")
    backend_process.terminate()
    print("✅ 后端服务已停止")
