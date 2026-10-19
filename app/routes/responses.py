import math
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, session

from app.db import db


responses_bp = Blueprint(
    "responses",
    __name__,
    url_prefix="/api/responses",
)


def answer_is_empty(answer):
    """判断答案是否为空。"""
    return (
        answer is None
        or answer == ""
        or (isinstance(answer, list) and len(answer) == 0)
    )


def is_number(value):
    """只接受有限的数字，不接受布尔值。"""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def answer_is_valid(question, answer):
    """检查单道题答案的类型、必填要求和校验规则。"""
    question_type = question.get("type")
    required = question.get("required", False)
    validation = question.get("validation", {})

    if answer_is_empty(answer):
        if required:
            return False, "此题为必填题，不能留空"
        return True, ""

    if not isinstance(validation, dict):
        validation = {}

    if question_type == "single_choice":
        if not isinstance(answer, str):
            return False, "单选题答案必须是字符串"

        valid_options = {
            option.get("option_id")
            for option in question.get("options", [])
        }

        if answer not in valid_options:
            return False, "单选题答案不在可选范围内"

    elif question_type == "multiple_choice":
        if not isinstance(answer, list):
            return False, "多选题答案必须是数组"

        valid_options = {
            option.get("option_id")
            for option in question.get("options", [])
        }

        if any(
            not isinstance(option_id, str)
            or option_id not in valid_options
            for option_id in answer
        ):
            return False, "多选题包含无效选项"

        if len(set(answer)) != len(answer):
            return False, "多选题不能重复选择同一选项"

        count = len(answer)
        min_selections = validation.get("min_selections")
        max_selections = validation.get("max_selections")
        exact_selections = validation.get("exact_selections")

        if (
            min_selections is not None
            and count < min_selections
        ):
            return False, f"此题至少需要选择 {min_selections} 个选项"

        if (
            max_selections is not None
            and count > max_selections
        ):
            return False, f"此题最多只能选择 {max_selections} 个选项"

        if (
            exact_selections is not None
            and count != exact_selections
        ):
            return False, f"此题必须选择恰好 {exact_selections} 个选项"

    elif question_type == "text":
        if not isinstance(answer, str):
            return False, "文本题答案必须是字符串"

        min_length = validation.get("min_length")
        max_length = validation.get("max_length")
        answer_length = len(answer)

        if min_length is not None and answer_length < min_length:
            return False, f"回答至少需要 {min_length} 个字符"

        if max_length is not None and answer_length > max_length:
            return False, f"回答不能超过 {max_length} 个字符"

    elif question_type == "numeric":
        if not is_number(answer):
            return False, "数值题答案必须是有限数字"

        min_value = validation.get("min_value")
        max_value = validation.get("max_value")
        integer = validation.get("integer", False)

        if min_value is not None and answer < min_value:
            return False, f"数值不能小于 {min_value}"

        if max_value is not None and answer > max_value:
            return False, f"数值不能大于 {max_value}"

        if integer and not float(answer).is_integer():
            return False, "此题必须填写整数"

    else:
        return False, "暂不支持此题型"

    return True, ""


def jump_rule_matches(question, answer, rule):
    """判断当前答案是否满足一条跳转规则。"""
    if answer_is_empty(answer):
        return False

    question_type = question.get("type")

    if question_type == "single_choice":
        return answer == rule.get("option_id")

    if question_type == "multiple_choice":
        return rule.get("option_id") in answer

    if question_type == "numeric":
        if not is_number(answer):
            return False

        value = rule.get("value")
        operator = rule.get("operator")

        if not is_number(value):
            return False

        comparisons = {
            "eq": answer == value,
            "ne": answer != value,
            "gt": answer > value,
            "gte": answer >= value,
            "lt": answer < value,
            "lte": answer <= value,
        }

        return comparisons.get(operator, False)

    return False


def get_active_question_ids(questions, received_answers):
    """
    根据答案和跳转规则，计算本次答卷中应该作答的题目。

    跳转目标必须是当前题之后的题目。
    没有触发跳转规则时，按原顺序继续。
    """
    question_ids = [
        str(question["_id"])
        for question in questions
    ]

    question_by_id = {
        str(question["_id"]): question
        for question in questions
    }

    position_by_id = {
        question_id: index
        for index, question_id in enumerate(question_ids)
    }

    active_ids = []
    index = 0

    while index < len(questions):
        question = questions[index]
        question_id = str(question["_id"])

        active_ids.append(question_id)

        answer = received_answers.get(question_id)
        jump_rules = question.get("jump_rules", [])

        target_index = None

        if isinstance(jump_rules, list):
            for rule in jump_rules:
                if not isinstance(rule, dict):
                    continue

                if not jump_rule_matches(question, answer, rule):
                    continue

                target_id = rule.get("target_question_id")

                if target_id not in question_by_id:
                    continue

                candidate_index = position_by_id[target_id]

                # 只允许跳转到当前题之后的题目。
                if candidate_index <= index:
                    continue

                target_index = candidate_index
                break

        if target_index is not None:
            index = target_index
        else:
            index += 1

    return active_ids


@responses_bp.post("/<share_code>")
def submit_response(share_code):
    """登录用户通过问卷分享码提交答案。"""
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "请先登录再提交问卷"}), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "请求内容必须是 JSON 对象"}), 400

    answers = data.get("answers")

    if not isinstance(answers, list):
        return jsonify({"error": "answers 必须是数组"}), 400

    survey = db.surveys.find_one({
        "share_code": share_code,
        "status": "published",
    })

    if survey is None:
        return jsonify({
            "error": "问卷不存在、尚未发布或已经关闭"
        }), 404

    now = datetime.now(timezone.utc)
    deadline = survey.get("deadline")

    if deadline is not None:
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if deadline <= now:
            return jsonify({"error": "问卷已超过截止时间"}), 403

    questions = list(
        db.questions.find({
            "survey_id": str(survey["_id"]),
        }).sort("order", 1)
    )

    question_by_id = {
        str(question["_id"]): question
        for question in questions
    }

    received_answers = {}

    for item in answers:
        if not isinstance(item, dict):
            return jsonify({
                "error": "每个答案必须是 JSON 对象"
            }), 400

        question_id = item.get("question_id")

        if not isinstance(question_id, str):
            return jsonify({
                "error": "每个答案都必须提供 question_id"
            }), 400

        if question_id not in question_by_id:
            return jsonify({
                "error": "答案包含不属于此问卷的题目"
            }), 400

        if question_id in received_answers:
            return jsonify({
                "error": "同一道题不能重复提交"
            }), 400

        if "answer" not in item:
            return jsonify({
                "error": "每个答案都必须提供 answer 字段"
            }), 400

        received_answers[question_id] = item["answer"]

    # 根据答案计算实际应该作答的题目。
    active_question_ids = get_active_question_ids(
        questions,
        received_answers,
    )
    active_question_id_set = set(active_question_ids)

    # 不允许提交已经被跳过的题目的答案。
    for question_id in received_answers:
        if question_id not in active_question_id_set:
            return jsonify({
                "error": "答案包含根据条件跳转应被跳过的题目",
                "question_id": question_id,
            }), 400

    # 只校验当前答题路径中应该作答的题目。
    for question_id in active_question_ids:
        question = question_by_id[question_id]
        answer = received_answers.get(question_id)

        valid, message = answer_is_valid(question, answer)

        if not valid:
            return jsonify({
                "error": message,
                "question_id": question_id,
            }), 400

    # 仅保存当前答题路径中有效的答案。
    stored_answers = [
        {
            "question_id": question_id,
            "answer": received_answers[question_id],
        }
        for question_id in active_question_ids
        if question_id in received_answers
    ]

    response_document = {
        "survey_id": str(survey["_id"]),
        "respondent_id": (
            None if survey.get("anonymous", False) else user_id
        ),
        "answers": stored_answers,
        "submitted_at": now,
    }

    result = db.responses.insert_one(response_document)

    return jsonify({
        "message": "答卷提交成功",
        "response_id": str(result.inserted_id),
        "survey_id": str(survey["_id"]),
        "submitted_at": now.isoformat(),
    }), 201
