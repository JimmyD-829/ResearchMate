import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

conn = sqlite3.connect('researchmate.db')
cursor = conn.cursor()

print('检查数据库表...')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'现有表: {tables}')

if ('users',) in tables:
    print('\n检查用户...')
    cursor.execute("SELECT id, email FROM users WHERE email = ?", ('dongjiming189@163.com',))
    user = cursor.fetchone()
    
    if user:
        user_id, email = user
        hashed_pwd = pwd_context.hash('Test123456')
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_pwd, user_id))
        conn.commit()
        print(f'✅ 密码已重置: {email}')
        print(f'   用户ID: {user_id}')
    else:
        print('❌ 用户不存在，正在创建...')
        hashed_pwd = pwd_context.hash('Test123456')
        cursor.execute("INSERT INTO users (id, email, password_hash, nickname) VALUES (?, ?, ?, ?)",
                       ('user_001', 'dongjiming189@163.com', hashed_pwd, '演示用户'))
        conn.commit()
        print('✅ 用户已创建')
else:
    print('❌ users表不存在！需要先初始化数据库')

conn.close()
