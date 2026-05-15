# 数据库配置说明

## 概述

本项目使用 MySQL 8.0+ 或 MariaDB 10.6+ 作为数据库。

## 安装 MySQL

### macOS
- Homebrew (推荐)

```bash
# 安装 MySQL
brew install mysql

# 启动 MySQL 服务
brew services start mysql
```

### Docker (可选)
```bash
# 拉取 MySQL 镜像
docker run --name palmmicro-mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=yourpassword -d mysql:8.0
```

## 配置数据库

### 1. 创建数据库用户

```bash
# 登录 MySQL
mysql -u root -p
```

```sql
-- 创建数据库和用户
CREATE USER IF NOT EXISTS 'palmmicro'@'localhost' IDENTIFIED BY 'your_secure_password';
CREATE DATABASE IF NOT EXISTS palmmicro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON palmmicro.* TO 'palmmicro'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 配置环境变量

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的数据库信息：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=palmmicro
DB_PASSWORD=your_secure_password
DB_NAME=palmmicro

# Flask 配置
SECRET_KEY=your_secret_key_change_this_in_production
DEBUG=True
```

## 初始化数据库

### 方式一：使用 SQL 脚本（推荐）

```bash
mysql -u palmmicro -p palmmicro < scripts/init_db.sql
```

### 方式二：使用 Python 脚本

```bash
# 安装依赖
pip install -r requirements.txt

# 运行初始化脚本
python scripts/init_db.py
```

## 验证数据库

```sql
-- 检查数据库
USE palmmicro;
SHOW TABLES;
```

## 数据迁移（如果需要从 PHP 项目）

如果你需要从原始 PHP 项目迁移数据，请参考：

1. 导出原数据库的数据
2. 使用工具（如 `mysqldump`）导出数据
3. 导入到新数据库

## 常用 MySQL 命令

```bash
# 备份数据库
mysqldump -u palmmicro -p palmmicro > backup.sql

# 恢复备份
mysql -u palmmicro -p palmmicro < backup.sql

# 连接到数据库
mysql -u palmmicro -p palmmicro
```
