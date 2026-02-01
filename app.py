import json
import streamlit as st
from dotenv import load_dotenv

from upstage_client import UpstageClient, extract_text_from_solar_response
from schemas import ASSIGNMENT_SCHEMA, PROJECT_SCHEMA
from prompts import SYSTEM_AGENT, ASSIGNMENT_COACH, PM_COACH, REVIEWER

load_dotenv()
client = UpstageClient()

st.set_page_config(page_title="Doc2Plan Coach", layout="centered")
st.title("📄 Doc2Plan Coach (Prototype)")
st.write("문서(PDF)를 업로드하면 요구사항/마일스톤을 구조화하고, 개인 과제 코칭 + 팀 PM 계획을 생성합니다.")

uploaded = st.file_uploader("PDF 업로드", type=["pdf"])

# ✅ 세션 초기화 (KeyError 방지)
if "parsed_text" not in st.session_state:
    st.session_state["parsed_text"] = None
if "assignment_json" not in st.session_state:
    st.session_state["assignment_json"] = None
if "project_json" not in st.session_state:
    st.session_state["project_json"] = None

def _safe_json_dump(x):
    return json.dumps(x, ensure_ascii=False, indent=2)

if uploaded:
    file_bytes = uploaded.read()
    st.success(f"업로드 완료: {uploaded.name}")

    col1, col2 = st.columns(2)

    # ----------------------
    # 1) Document Parse
    # ----------------------
    with col1:
        if st.button("1) Document Parse 실행"):
            parsed = client.document_parse(file_bytes, uploaded.name)
            st.session_state["parsed_text"] = _safe_json_dump(parsed)
            st.info("Parse 완료. 이제 Information Extract를 실행하세요.")

    # ----------------------
    # 2) Extract - Assignment
    # ----------------------
    with col2:
        if st.button("2) Extract(과제 스키마)"):
            if not uploaded:
                st.warning("먼저 PDF를 업로드하세요.")
            else:
                try:
                    extracted = client.information_extract(
                        file_bytes=file_bytes,
                        filename=uploaded.name,
                        schema=ASSIGNMENT_SCHEMA,
                        mode="enhanced"
                    )
                    st.session_state["assignment_json"] = extracted
                    st.success("✅ IE(Information Extract)로 추출 완료!")
                except Exception as e:
                    st.warning(f"IE 실패 → Solar로 대체 추출합니다.\n\n에러: {e}")

                    # Solar fallback: parsed_text가 없으면 parse부터
                    if not st.session_state["parsed_text"]:
                        parsed = client.document_parse(file_bytes, uploaded.name)
                        st.session_state["parsed_text"] = json.dumps(parsed, ensure_ascii=False, indent=2)

                    fallback_prompt = f"""
        다음 문서 내용을 보고 JSON 스키마에 맞춰 값을 채워줘.
        - 근거 없으면 "근거 부족"
        - 반드시 JSON만 출력

        [스키마]
        {json.dumps(ASSIGNMENT_SCHEMA, ensure_ascii=False)}

        [문서]
        {st.session_state["parsed_text"]}
        """
                    out = client.solar_chat(
                        system="너는 문서에서 정보를 정확히 추출해 JSON으로만 답한다.",
                        user=fallback_prompt,
                        model="solar-pro"
                    )
                    st.session_state["assignment_json"] = out
                    st.success("✅ Solar로 대체 추출 완료!")



    # ----------------------
    # Parse 결과 표시
    # ----------------------
    if st.session_state["parsed_text"]:
        st.subheader("🧾 Document Parse 결과(요약용)")
        st.text_area("parsed_text", st.session_state["parsed_text"], height=180)

    tab1, tab2 = st.tabs(["✅ 개인 과제 코치", "👥 팀 PM 코치"])

    # ----------------------
    # Tab 1: Assignment Coach
    # ----------------------
    with tab1:
        st.subheader("1) 과제 JSON")
        if st.session_state["assignment_json"] is not None:
            try:
                content = st.session_state["assignment_json"]["choices"][0]["message"]["content"]
                st.json(json.loads(content))
            except Exception:
                st.json(st.session_state["assignment_json"])
        else:
            st.caption("아직 추출된 과제 JSON이 없습니다. 'Extract(과제 스키마)'를 눌러주세요.")

        if st.button("3) Solar로 체크리스트/계획 생성"):
            if st.session_state["assignment_json"] is None:
                st.warning("먼저 과제 JSON을 추출하세요.")
            else:
                prompt = ASSIGNMENT_COACH.format(
                    assignment_json=_safe_json_dump(st.session_state["assignment_json"])
                )
                out = client.solar_chat(system=SYSTEM_AGENT, user=prompt)
                st.subheader("Solar 출력")
                st.write(extract_text_from_solar_response(out))

        st.subheader("2) 내 초안 피드백")
        draft = st.text_area("초안/설명/계획/코드 설계 등을 붙여넣기", height=160)
        if st.button("초안 피드백 받기(과제 기준)"):
            if st.session_state["assignment_json"] is None:
                st.warning("먼저 과제 JSON을 추출하세요.")
            elif not draft.strip():
                st.warning("초안을 입력하세요.")
            else:
                prompt = REVIEWER.format(
                    criteria_json=_safe_json_dump(st.session_state["assignment_json"]),
                    draft=draft.strip(),
                )
                out = client.solar_chat(system=SYSTEM_AGENT, user=prompt)
                st.subheader("Solar 피드백")
                st.write(extract_text_from_solar_response(out))

    # ----------------------
    # Tab 2: PM Coach
    # ----------------------
    with tab2:
        st.subheader("0) 팀 정보")
        team_size = st.number_input("팀 인원", min_value=2, max_value=10, value=4, step=1)
        duration = st.text_input("기간(예: 4주, 6주, 1개월)", value="4주")

        st.divider()

        if st.button("2) Extract(프로젝트 스키마)"):
            if not uploaded:
                st.warning("먼저 PDF를 업로드하세요.")
            else:
                try:
                    extracted = client.information_extract(
                        file_bytes=file_bytes,
                        filename=uploaded.name,
                        schema=PROJECT_SCHEMA,
                        mode="enhanced"
                    )
                    st.session_state["project_json"] = extracted
                    st.success("✅ IE(Information Extract)로 프로젝트 스키마 추출 완료!")
                except Exception as e:
                    st.warning(f"IE 실패 → Solar로 대체 추출합니다.\n\n에러: {e}")

                    # Solar fallback: parsed_text가 없으면 parse부터
                    if not st.session_state["parsed_text"]:
                        parsed = client.document_parse(file_bytes, uploaded.name)
                        st.session_state["parsed_text"] = json.dumps(parsed, ensure_ascii=False, indent=2)

                    fallback_prompt = f"""
        다음 문서 내용을 보고 JSON 스키마에 맞춰 값을 채워줘.
        - 근거 없으면 "근거 부족"
        - 반드시 JSON만 출력

        [스키마]
        {json.dumps(PROJECT_SCHEMA, ensure_ascii=False)}

        [문서]
        {st.session_state["parsed_text"]}
        """
                    out = client.solar_chat(
                        system="너는 문서에서 정보를 정확히 추출해 JSON으로만 답한다.",
                        user=fallback_prompt,
                        model="solar-pro"
                    )
                    st.session_state["project_json"] = out
                    st.success("✅ Solar로 프로젝트 스키마 대체 추출 완료!")

        st.subheader("1) 프로젝트 JSON")

        if st.session_state["project_json"] is not None:
            try:
                content = st.session_state["project_json"]["choices"][0]["message"]["content"]
                st.json(json.loads(content))
            except Exception:
                st.json(st.session_state["project_json"])
        else:
            st.caption("아직 추출된 프로젝트 JSON이 없습니다. 'Extract(프로젝트 스키마)'를 눌러주세요.")


        if st.button("3) Solar로 역할/일정/리스크 생성"):
            if st.session_state["project_json"] is None:
                st.warning("먼저 프로젝트 JSON을 추출하세요.")
            else:
                prompt = PM_COACH.format(
                    project_json=_safe_json_dump(st.session_state["project_json"]),
                    team_size=team_size,
                    duration=duration,
                )
                out = client.solar_chat(system=SYSTEM_AGENT, user=prompt)
                st.subheader("Solar 출력")
                st.write(extract_text_from_solar_response(out))
