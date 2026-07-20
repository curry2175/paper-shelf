from __future__ import annotations

import time
from functools import lru_cache

from django.conf import settings
from google import genai
from pydantic import BaseModel, Field


class PaperSummarySchema(BaseModel):
    research_question: str = Field(
        description="핵심 연구 질문을 쉬운 한국어로 설명"
    )
    why_it_matters: str = Field(
        description="왜 중요한 연구인지 쉬운 한국어로 설명"
    )
    study_design: str = Field(description="연구 설계와 방법")
    study_population: str = Field(description="대상, 표본 수, 주요 특성")
    main_results: list[str] = Field(description="핵심 결과 1~4개")
    easy_explanation: str = Field(
        description="결과의 의미를 초보자가 이해하기 쉽게 설명"
    )
    limitations: list[str] = Field(description="초록에서 확인되는 한계 1~3개")
    beginner_takeaway: str = Field(description="한 문장 핵심 요약")
    difficult_terms: list[str] = Field(
        description="용어: 쉬운 설명 형식, 최대 5개"
    )


@lru_cache(maxsize=1)
def get_client():
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(".env 파일에 GEMINI_API_KEY를 입력해주세요.")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def summarize_abstract(
    title: str, abstract: str, journal: str = ""
) -> PaperSummarySchema:
    if not abstract.strip():
        raise ValueError("이 논문에는 PubMed Abstract가 없습니다.")

    prompt = f"""
너는 의학 연구를 처음 시작하는 학생에게 논문을 설명하는 교육 도우미다.
아래 제목과 PubMed Abstract에 적힌 정보만 사용해 한국어로 답하라.

규칙:
1. Abstract에 없는 내용을 만들지 않는다.
2. 숫자, 표본 수, 효과크기, 신뢰구간, p-value를 바꾸지 않는다.
3. 상관관계를 인과관계로 표현하지 않는다.
4. 결론을 과장하지 않는다.
5. 전문을 읽은 것처럼 추가 정보를 만들지 않는다.
6. 확인되지 않으면 '초록에서 확인되지 않음'이라고 쓴다.
7. 개인 진단이나 치료 조언을 하지 않는다.

논문 제목: {title}
저널: {journal}

PubMed Abstract:
{abstract}
""".strip()

    last_error = None
    for attempt in range(1, settings.GEMINI_MAX_RETRIES + 1):
        try:
            interaction = get_client().interactions.create(
                model=settings.GEMINI_MODEL,
                input=prompt,
                store=False,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": PaperSummarySchema.model_json_schema(),
                },
            )
            if not interaction.output_text:
                raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")
            return PaperSummarySchema.model_validate_json(
                interaction.output_text
            )
        except Exception as exc:
            last_error = exc
            if attempt < settings.GEMINI_MAX_RETRIES:
                time.sleep(2**attempt)

    raise RuntimeError(f"Gemini 요약에 실패했습니다: {last_error}")
