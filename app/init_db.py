from app.db import db


def create_collections():
    """创建项目所需的集合。"""
    required_collections = [
        "users",
        "surveys",
        "questions",
        "responses",
    ]

    existing_collections = set(db.list_collection_names())

    for name in required_collections:
        if name not in existing_collections:
            db.create_collection(name)
            print(f"已创建集合：{name}")
        else:
            print(f"集合已存在，跳过：{name}")


def create_indexes():
    """创建常用查询索引和唯一索引。"""

    # 用户名唯一，避免重复注册
    db.users.create_index(
        [("username", 1)],
        unique=True,
        name="uq_users_username",
    )

    # 问卷分享码唯一
    db.surveys.create_index(
        [("share_code", 1)],
        unique=True,
        name="uq_surveys_share_code",
    )

    # 查询某个用户创建的问卷
    db.surveys.create_index(
        [("creator_id", 1), ("created_at", -1)],
        name="idx_surveys_creator_created",
    )

    # 查询问卷题目，并保证同一问卷内的 order 不重复
    db.questions.create_index(
        [("survey_id", 1), ("order", 1)],
        unique=True,
        name="uq_questions_survey_order",
    )

    # 查询某份问卷的答卷和提交时间
    db.responses.create_index(
        [("survey_id", 1), ("submitted_at", -1)],
        name="idx_responses_survey_submitted",
    )

    # 仅对设置了 submission_key 的答卷执行唯一性约束
    db.responses.create_index(
        [("submission_key", 1)],
        unique=True,
        sparse=True,
        name="uq_responses_submission_key",
    )

    print("索引创建或检查完成。")


def main():
    print(f"正在初始化数据库：{db.name}")
    create_collections()
    create_indexes()
    print("数据库初始化完成。")


if __name__ == "__main__":
    main()
