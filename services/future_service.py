from typing import Dict, List


CAREER_MAP = {
    "01": ["哲学研究助理", "公共政策研究员", "高校行政与思政相关岗位"],
    "02": ["经济分析师", "金融数据分析助理", "商业研究员"],
    "03": ["法务助理", "合规专员", "公共事务与政策岗位"],
    "04": ["教育产品专员", "教学管理岗位", "学习与培训发展岗位"],
    "05": ["文学编辑", "内容策划", "品牌传播与新媒体岗位"],
    "06": ["历史文化传播岗位", "文博机构助理", "文化内容研究岗位"],
    "07": ["理工科研究助理", "数据分析岗位", "科研支持岗位"],
    "08": ["软件开发", "产品经理", "算法/测试/数据相关岗位"],
    "09": ["农林科技推广", "食品与生物方向助理岗位", "乡村振兴相关岗位"],
    "10": ["医学信息分析", "医疗管理支持岗位", "健康服务相关岗位"],
    "11": ["国防科技支持岗位", "安全与应急管理方向", "军事理论研究支持"],
    "12": ["运营管理", "商业分析", "人力资源/供应链/咨询方向岗位"],
    "13": ["视觉设计", "数字媒体设计", "创意策划与艺术传播岗位"],
}

CATEGORY_NAME_MAP = {
    "01": "哲学",
    "02": "经济学",
    "03": "法学",
    "04": "教育学",
    "05": "文学",
    "06": "历史学",
    "07": "理学",
    "08": "工学",
    "09": "农学",
    "10": "医学",
    "11": "军事学",
    "12": "管理学",
    "13": "艺术学",
}


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def score_to_level(score: float) -> str:
    if score >= 85:
        return "优势明显"
    elif score >= 70:
        return "基础较好"
    elif score >= 55:
        return "具备潜力"
    return "需重点准备"


def get_target_category_name(target_major_code: str) -> str:
    target_major_code = str(target_major_code).strip()
    if len(target_major_code) < 2:
        return "未知门类"
    return CATEGORY_NAME_MAP.get(target_major_code[:2], "未知门类")


def get_career_recommendations(target_major_code: str) -> List[str]:
    target_major_code = str(target_major_code).strip()
    if len(target_major_code) < 2:
        return ["请先填写有效的目标专业代码"]

    category_code = target_major_code[:2]
    return CAREER_MAP.get(category_code, ["当前暂未匹配到明确职业方向，建议补充目标专业信息"])


def calculate_future_readiness(
    academic_score: float,
    consumption_score: float,
    health_score: float,
    psychology_score: float,
    similarity_score: float,
) -> float:
    readiness = (
        0.35 * similarity_score +
        0.30 * academic_score +
        0.20 * psychology_score +
        0.10 * health_score +
        0.05 * consumption_score
    )
    return round(clamp(readiness), 1)


def build_future_report(
    academic_score: float,
    consumption_score: float,
    health_score: float,
    psychology_score: float,
    similarity_score: float,
    readiness_score: float,
    current_major_code: str,
    target_major_code: str,
    future_details: List[str],
) -> str:
    target_category_name = get_target_category_name(target_major_code)
    career_list = get_career_recommendations(target_major_code)

    strengths = []
    weaknesses = []

    score_map = {
        "学业基础": academic_score,
        "心理状态": psychology_score,
        "身体状态": health_score,
        "资源管理能力": consumption_score,
    }

    for key, value in score_map.items():
        if value >= 80:
            strengths.append(key)
        elif value < 60:
            weaknesses.append(key)

    strengths_text = "、".join(strengths) if strengths else "当前暂未形成特别突出的单项优势"
    weaknesses_text = "、".join(weaknesses) if weaknesses else "当前整体短板不明显"

    similarity_level = score_to_level(similarity_score)
    readiness_level = score_to_level(readiness_score)
    detail_text = "；".join(future_details) if future_details else "暂无专业相似度细节说明"

    action_advice = []
    if academic_score < 70:
        action_advice.append("优先提升专业基础课程和核心能力")
    if psychology_score < 70:
        action_advice.append("优先稳定心理状态，减少压力对发展选择的影响")
    if health_score < 70:
        action_advice.append("改善作息和身体状态，保证持续投入的精力")
    if similarity_score < 60:
        action_advice.append("目标方向与当前专业距离较大，建议先补跨专业基础")
    elif similarity_score >= 80:
        action_advice.append("目标方向与当前专业契合度较高，可以尽快进入深化准备阶段")

    if not action_advice:
        action_advice.append("继续巩固现有优势，开始聚焦项目、实习和职业探索")

    return (
        f"你的目标发展方向属于{target_category_name}门类。当前专业代码为 {current_major_code}，"
        f"目标专业代码为 {target_major_code}。从专业相似度来看，你与目标方向的匹配程度为 {similarity_score} 分，"
        f"整体属于“{similarity_level}”；结合学业、心理、身体和资源管理状态综合计算后的未来发展准备度为 {readiness_score} 分，"
        f"整体属于“{readiness_level}”。目前你的核心优势主要体现在：{strengths_text}；当前需要优先补足的方面为：{weaknesses_text}。"
        f"从职业方向上看，当前较适合优先关注的路径包括：{career_list[0]}、{career_list[1]}、{career_list[2]}。"
        f"专业相似度分析细节为：{detail_text}。"
        f"建议你下一阶段重点行动为：{'；'.join(action_advice)}。"
    )


def build_future_result(
    current_major_code: str,
    target_major_code: str,
    similarity_result: Dict,
    academic_score: float,
    consumption_score: float,
    health_score: float,
    psychology_score: float,
) -> Dict:
    similarity_score = float(similarity_result.get("score", 0))
    future_details = similarity_result.get("details", [])
    readiness_score = calculate_future_readiness(
        academic_score=academic_score,
        consumption_score=consumption_score,
        health_score=health_score,
        psychology_score=psychology_score,
        similarity_score=similarity_score,
    )
    career_recommendations = get_career_recommendations(target_major_code)
    target_category_name = get_target_category_name(target_major_code)

    future_report_text = build_future_report(
        academic_score=academic_score,
        consumption_score=consumption_score,
        health_score=health_score,
        psychology_score=psychology_score,
        similarity_score=similarity_score,
        readiness_score=readiness_score,
        current_major_code=current_major_code,
        target_major_code=target_major_code,
        future_details=future_details,
    )

    return {
        "score": similarity_score,
        "details": future_details,
        "readiness_score": readiness_score,
        "career_recommendations": career_recommendations,
        "future_report_text": future_report_text,
        "target_category_name": target_category_name,
    }