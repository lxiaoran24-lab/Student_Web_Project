from similarity import MajorSimilarityCalculator

calculator = MajorSimilarityCalculator()


def calculate_major_similarity(current_code: str, target_code: str) -> dict:
    if not current_code or not target_code:
        return {
            "score": 0,
            "details": ["未填写专业代码"],
            "names": ("未知", "未知")
        }

    try:
        result = calculator.get_similarity(current_code, target_code)

        if isinstance(result, str):
            return {
                "score": 0,
                "details": [result],
                "names": ("未知", "未知")
            }

        return result

    except Exception as e:
        return {
            "score": 0,
            "details": [f"专业相似度计算失败：{str(e)}"],
            "names": ("未知", "未知")
        }