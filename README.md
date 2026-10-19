# 基于 MongoDB 的问卷系统

## 一、项目简介

本项目是“当代数据管理系统”课程大作业，使用 Python、Flask 和 MongoDB 实现一个简化的在线问卷系统。

系统支持用户注册与登录、创建和管理问卷、配置题目及校验规则、发布问卷、通过分享链接填写问卷、设置条件跳转、提交答卷以及查看统计结果。

## 二、主要功能

- **用户管理：** 用户注册、登录、退出登录和当前登录状态查询。
- **问卷管理：** 创建问卷、查看本人创建的问卷、发布问卷、关闭问卷和设置截止时间。
- **题目管理：** 支持单选题、多选题、文本填空题和数字填空题。
- **输入校验：** 支持必填校验、选项校验、多选数量限制、文本长度限制、数字范围限制和整数校验。
- **条件跳转：** 支持单选题、多选题和数字填空题的条件跳转。
- **答卷提交：** 校验答题内容及跳转路径，并保存有效答卷。
- **结果统计：** 支持单选题选项计数、多选题选项计数、文本答案展示和数字题统计。

## 三、技术与运行环境

| 项目 | 使用技术 |
|---|---|
| 开发语言 | Python |
| 后端框架 | Flask |
| 数据库 | MongoDB |
| Python 数据库驱动 | PyMongo |
| 配置管理 | python-dotenv |
| 密码哈希处理 | Werkzeug |
| 自动化测试 | pytest |

开发环境使用 Python 3.14.7、MongoDB Server 8.3.11。其他版本的兼容性需要根据实际环境验证。

本项目使用 MongoDB 保存业务数据，不使用关系型数据库作为业务数据存储。

## 四、项目目录

```text
mongodb_survey_system/
├── app/
│   ├── models/          # 模型相关模块
│   ├── routes/          # 用户、问卷、题目和答卷接口
│   ├── services/        # 业务服务模块
│   ├── static/          # 静态资源
│   ├── templates/       # 页面模板
│   ├── db.py            # MongoDB 连接配置
│   ├── init_db.py       # 集合和索引初始化
│   └── __init__.py      # Flask 应用初始化
├── docs/                # 项目文档、测试用例、完成报告和 AI 使用日志
├── tests/               # 自动化测试代码
├── scripts/             # 辅助脚本及说明
├── instance/            # 实例目录
├── .env                 # 本地环境配置，不应提交真实密钥
├── .env.example         # 环境配置模板
├── requirements.txt     # Python 依赖清单
├── run.py               # 应用启动入口
└── README.md            # 项目说明与运行指南
```

## 五、运行前准备

运行本项目需要：

1. 已安装 Python。
2. 已安装 MongoDB，并准备好 MongoDB 数据目录。
3. 已安装项目依赖。
4. 已配置项目根目录下的 `.env` 文件。

以下启动命令中的 MongoDB 安装路径和数据目录来自本项目当前开发环境。如果其他电脑的安装位置不同，需要修改对应路径。

## 六、安装与配置

### 6.1 进入项目目录

在 VS Code 终端或 PowerShell 中执行：

```powershell
cd C:\Users\10245\Desktop\mongodb_survey_system
```

如果项目放在其他位置，请替换为实际路径。

### 6.2 创建或激活 Python 虚拟环境

如果项目中的 `.venv` 已经存在，执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果还没有虚拟环境，执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

激活成功后，终端命令提示符前通常会出现 `(.venv)`。

### 6.3 安装项目依赖

在项目根目录执行：

```powershell
python -m pip install -r requirements.txt
```

如果安装失败，应先检查 Python、网络和依赖版本，再根据具体错误处理。

### 6.4 配置 `.env` 文件

项目使用 `python-dotenv` 加载环境变量。请在项目根目录中准备 `.env` 文件，使它与 `run.py` 位于同一层。

`.env.example` 是配置模板。如果 `.env` 不存在，可以复制模板后再编辑：

```powershell
Copy-Item .env.example .env
```

如果 `.env` 已经存在，不要重复覆盖，以免丢失已有配置。

配置格式如下：

```dotenv
SECRET_KEY=替换为本地开发密钥
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB_NAME=survey_system
```

各配置项的含义如下：

| 配置项 | 作用 | 当前开发环境的设置 |
|---|---|---|
| `SECRET_KEY` | Flask 会话等功能使用的签名密钥 | 本地开发密钥 |
| `MONGO_URI` | 指定 MongoDB 服务的连接地址 | `mongodb://127.0.0.1:27017` |
| `MONGO_DB_NAME` | 指定项目使用的数据库名称 | `survey_system` |

**注意事项：**

- `MONGO_URI` 中的 `127.0.0.1` 表示本机，`27017` 是本项目使用的 MongoDB 端口。
- `MONGO_DB_NAME` 指定的是数据库名称，不是 MongoDB 数据文件的保存路径。
- `SECRET_KEY` 应替换为自行生成的随机密钥，不要将真实密钥上传到公开代码仓库。
- `.env` 包含本地配置，应避免提交；提交时应提供 `.env.example` 作为配置模板。
- `app/db.py` 在创建 MongoDB 客户端时会读取 `MONGO_URI` 和 `MONGO_DB_NAME`，并使用这些配置建立数据库连接。

### 6.5 MongoDB 数据目录说明

本项目开发环境使用的 MongoDB 数据目录为：

```text
D:\MongoDB\data\db
```

该目录保存 MongoDB 数据文件。启动 MongoDB 时，`--dbpath` 参数指定数据目录；它与 `.env` 中的 `MONGO_URI` 作用不同。

请确保数据目录已经存在。不要为了重新运行项目而删除该目录，因为其中可能保存已有数据库数据。

## 七、启动系统

建议使用三个终端：

- **终端 1：** 启动 MongoDB。
- **终端 2：** 启动 Flask 后端。
- **终端 3：** 执行数据库初始化、测试和其他管理命令。

### 7.1 启动 MongoDB

在终端 1 中执行：

```powershell
& "D:\MongoDB\Server\8.3\bin\mongod.exe" --dbpath "D:\MongoDB\data\db" --port 27017
```

如果 MongoDB 的安装路径或数据目录不同，请替换为本机的实际路径。

启动后保持终端运行，不要关闭，也不要在该终端继续执行其他命令。

### 7.2 初始化数据库集合和索引

首次配置项目，或者需要重新确认数据库结构时，在终端 3 中执行：

```powershell
.\.venv\Scripts\Activate.ps1
python -m app.init_db
```

该脚本会检查并创建项目所需的集合：

- `users`：用户信息。
- `surveys`：问卷信息。
- `questions`：题目信息。
- `responses`：答卷信息。

同时创建用户名称唯一索引、问卷分享码唯一索引、问卷创建者与创建时间索引、题目顺序唯一索引、答卷查询索引，以及可选提交标识的稀疏唯一索引。

集合和索引初始化由 `app/init_db.py` 单独执行；`app/__init__.py` 的 `create_app()` 不会自动调用该初始化脚本。

如果已有数据，初始化前不要随意删除集合。重新执行初始化前，也应确认现有数据与索引没有冲突。

### 7.3 启动 Flask 后端

在终端 2 中进入项目根目录，激活虚拟环境并启动应用：

```powershell
.\.venv\Scripts\Activate.ps1
python run.py
```

如果虚拟环境已经激活，直接执行：

```powershell
python run.py
```

应用默认监听：

```text
http://127.0.0.1:5000
```

保持 Flask 终端运行。开发服务器用于本机开发和测试，不应直接作为生产环境服务器使用。

### 7.4 检查服务状态

在浏览器中访问：

```text
http://127.0.0.1:5000/health
```

正常情况下，健康检查接口返回 HTTP 200，并包含类似以下字段：

```json
{
  "status": "ok",
  "mongodb": "connected",
  "database": "survey_system"
}
```

该接口用于检查 Flask 应用能否连接 MongoDB。如果返回服务不可用，应检查 MongoDB 是否正在运行、连接地址是否正确以及数据库配置是否匹配。

## 八、运行自动化测试

确认 MongoDB 服务正常，并且虚拟环境已激活。在项目根目录执行：

```powershell
python -m pytest tests/test_api.py -v
```

自动化测试覆盖以下内容：

- 健康检查接口。
- 用户注册、登录和当前登录状态。
- 重复注册校验。
- 未登录用户访问问卷管理接口。
- 创建问卷、创建题目、发布问卷和分享访问。
- 题目选项校验。
- 答卷提交与统计。
- 非法答案拦截。
- 单选题条件跳转。

开发过程中最近一次记录的测试结果为 9 项全部通过。重新运行时，应以实际测试输出为准。

**测试数据库注意事项：**

自动化测试使用独立的 `survey_system_test` 数据库，与日常开发使用的 `survey_system` 数据库分开。运行测试前应检查测试配置，确保测试操作不会连接到需要保留的正式数据。

## 九、主要接口模块

| 接口模块 | 主要功能 |
|---|---|
| `/api/auth` | 用户注册、登录、退出登录、查询当前登录状态 |
| `/api/surveys` | 创建问卷、查询问卷列表、发布、关闭、设置截止时间、统计和分享访问 |
| `/api/surveys/<survey_id>/questions` | 查询、创建、修改和删除题目 |
| `/api/responses/<share_code>` | 提交问卷答卷 |

以上是接口模块的概览。具体请求方法、参数、返回字段、状态码和错误处理规则，以项目实际接口实现及详细 API 文档为准。

## 十、相关文档

项目详细文档位于 `docs/` 目录：

- `项目文档.md`：系统说明、数据库设计、API 说明和关键逻辑说明。
- `测试用例.md`：测试步骤、输入、预期输出、实际输出和测试结果。
- `项目完成报告.md`：项目目标、系统设计、MongoDB 设计、跳转设计、校验设计、AI 使用过程、测试结果、遇到的问题及解决方法。
- `AI使用日志.md`：AI 工具、实际提示词、生成结果、是否修改以及人工修改情况。

自动化测试代码位于 `tests/test_api.py`。测试运行方法也可参考 `tests/README.md`。
