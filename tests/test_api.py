import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from pymongo import MongoClient


# 必须在导入应用代码前指定测试数据库。
os.environ["MONGO_DB_NAME"] = "survey_system_test"
os.environ["SECRET_KEY"] = "pytest-test-secret-key"


from app import create_app
from app.db import db
from app.init_db import create_collections, create_indexes


@pytest.fixture
def client():
    """每个测试前清理独立测试库，并创建 Flask 测试客户端。"""
    create_collections()
    create_indexes()

    for name in ("users", "surveys", "questions", "responses"):
        db[name].delete_many({})

    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "pytest-test-secret-key"

    with app.test_client() as test_client:
        yield test_client

    for name in ("users", "surveys", "questions", "responses"):
        db[name].delete_many({})


def register_and_login(client):
    """注册唯一测试用户并登录。"""
    username = "pytest_" + uuid.uuid4().hex[:12]
    password = "TestPass123!"

    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 201, response.get_json()

    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.get_json()

    return username


def create_survey(client, title="自动化测试问卷"):
    response = client.post(
        "/api/surveys",
        json={
            "title": title,
            "description": "pytest 自动化测试",
            "anonymous": False,
        },
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def add_question(client, survey_id, payload):
    response = client.post(
        f"/api/surveys/{survey_id}/questions",
        json=payload,
    )
    return response


def publish_survey(client, survey_id):
    response = client.post(f"/api/surveys/{survey_id}/publish")
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def test_health_endpoint():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_register_login_and_current_user(client):
    username = register_and_login(client)

    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.get_json()["logged_in"] is True
    assert response.get_json()["username"] == username

    response = client.post("/api/auth/logout")
    assert response.status_code == 200

    response = client.get("/api/auth/me")
    assert response.get_json()["logged_in"] is False


def test_duplicate_registration_is_rejected(client):
    username = "duplicate_" + uuid.uuid4().hex[:10]
    payload = {"username": username, "password": "TestPass123!"}

    first = client.post("/api/auth/register", json=payload)
    second = client.post("/api/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_survey_requires_login(client):
    response = client.post(
        "/api/surveys",
        json={"title": "未登录问卷"},
    )
    assert response.status_code == 401


def test_create_question_publish_and_access_share_link(client):
    register_and_login(client)
    survey = create_survey(client)
    survey_id = survey["survey_id"]

    question_response = add_question(
        client,
        survey_id,
        {
            "title": "你最喜欢哪种数据库？",
            "type": "single_choice",
            "required": True,
            "options": ["MongoDB", "MySQL"],
        },
    )
    assert question_response.status_code == 201
    question = question_response.get_json()
    assert question["options"][0]["option_id"] == "1"

    published = publish_survey(client, survey_id)
    assert published["status"] == "published"

    share_code = published["share_code"]
    public_response = client.get(f"/api/surveys/share/{share_code}")

    assert public_response.status_code == 200
    assert public_response.get_json()["title"] == survey["title"]
    assert len(public_response.get_json()["questions"]) == 1


def test_question_validation_rejects_duplicate_options(client):
    register_and_login(client)
    survey = create_survey(client)

    response = add_question(
        client,
        survey["survey_id"],
        {
            "title": "重复选项测试",
            "type": "single_choice",
            "options": ["相同", "相同"],
        },
    )

    assert response.status_code == 400
    assert "不能重复" in response.get_json()["error"]


def test_submission_and_statistics(client):
    register_and_login(client)
    survey = create_survey(client, "答卷统计测试")

    question_specs = [
        {
            "title": "选择数据库",
            "type": "single_choice",
            "required": True,
            "options": ["MongoDB", "MySQL"],
        },
        {
            "title": "使用过哪些数据库",
            "type": "multiple_choice",
            "required": True,
            "options": ["MongoDB", "MySQL", "PostgreSQL"],
            "validation": {"min_selections": 1, "max_selections": 2},
        },
        {
            "title": "使用感受",
            "type": "text",
            "required": True,
            "validation": {"min_length": 2, "max_length": 100},
        },
        {
            "title": "打分",
            "type": "numeric",
            "required": True,
            "validation": {
                "min_value": 1,
                "max_value": 10,
                "integer": True,
            },
        },
    ]

    question_ids = []
    for spec in question_specs:
        response = add_question(client, survey["survey_id"], spec)
        assert response.status_code == 201, response.get_json()
        question_ids.append(response.get_json()["question_id"])

    published = publish_survey(client, survey["survey_id"])
    share_code = published["share_code"]

    submission = client.post(
        f"/api/responses/{share_code}",
        json={
            "answers": [
                {"question_id": question_ids[0], "answer": "1"},
                {"question_id": question_ids[1], "answer": ["1", "2"]},
                {"question_id": question_ids[2], "answer": "使用起来比较灵活"},
                {"question_id": question_ids[3], "answer": 8},
            ]
        },
    )
    assert submission.status_code == 201, submission.get_json()

    stats_response = client.get(
        f"/api/surveys/{survey['survey_id']}/stats"
    )
    assert stats_response.status_code == 200

    stats = stats_response.get_json()
    assert stats["response_count"] == 1
    assert stats["questions"][0]["options"][0]["count"] == 1
    assert stats["questions"][1]["options"][0]["count"] == 1
    assert stats["questions"][2]["answers"] == ["使用起来比较灵活"]
    assert stats["questions"][3]["average"] == 8


def test_invalid_answers_are_rejected(client):
    register_and_login(client)
    survey = create_survey(client, "答案校验测试")

    question_response = add_question(
        client,
        survey["survey_id"],
        {
            "title": "1 到 10 的整数",
            "type": "numeric",
            "required": True,
            "validation": {
                "min_value": 1,
                "max_value": 10,
                "integer": True,
            },
        },
    )
    assert question_response.status_code == 201
    question_id = question_response.get_json()["question_id"]

    published = publish_survey(client, survey["survey_id"])

    response = client.post(
        f"/api/responses/{published['share_code']}",
        json={
            "answers": [
                {"question_id": question_id, "answer": 11}
            ]
        },
    )

    assert response.status_code == 400
    assert "不能大于 10" in response.get_json()["error"]


def test_single_choice_jump_skips_intermediate_question(client):
    register_and_login(client)
    survey = create_survey(client, "条件跳转测试")
    survey_id = survey["survey_id"]

    first = add_question(
        client,
        survey_id,
        {
            "title": "是否使用过 MongoDB？",
            "type": "single_choice",
            "required": True,
            "options": ["使用过", "没使用过"],
        },
    )
    assert first.status_code == 201, first.get_json()
    first_id = first.get_json()["question_id"]

    second = add_question(
        client,
        survey_id,
        {
            "title": "中间题",
            "type": "text",
            "required": True,
        },
    )
    assert second.status_code == 201, second.get_json()
    second_id = second.get_json()["question_id"]

    third = add_question(
        client,
        survey_id,
        {
            "title": "跳转目标题",
            "type": "text",
            "required": True,
        },
    )
    assert third.status_code == 201, third.get_json()
    third_id = third.get_json()["question_id"]

    update = client.put(
        f"/api/surveys/{survey_id}/questions/{first_id}",
        json={
            "title": "是否使用过 MongoDB？",
            "type": "single_choice",
            "required": True,
            "options": ["使用过", "没使用过"],
            "jump_rules": [
                {
                    "option_id": "1",
                    "target_question_id": third_id,
                }
            ],
        },
    )
    assert update.status_code == 200, update.get_json()

    published = publish_survey(client, survey_id)
    share_code = published["share_code"]

    # 选择“使用过”：从第一题跳到第三题，第二题应被跳过。
    valid_submission = client.post(
        f"/api/responses/{share_code}",
        json={
            "answers": [
                {"question_id": first_id, "answer": "1"},
                {"question_id": third_id, "answer": "目标回答"},
            ]
        },
    )
    assert valid_submission.status_code == 201, valid_submission.get_json()

    # 如果仍然提交被跳过的第二题，服务端应拒绝。
    invalid_submission = client.post(
        f"/api/responses/{share_code}",
        json={
            "answers": [
                {"question_id": first_id, "answer": "1"},
                {"question_id": second_id, "answer": "不应填写"},
                {"question_id": third_id, "answer": "目标回答"},
            ]
        },
    )
    assert invalid_submission.status_code == 400
    assert "应被跳过" in invalid_submission.get_json()["error"]
