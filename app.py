"""
가계부 웹 애플리케이션
Python Streamlit을 사용한 가계부 관리 시스템

주요 기능:
1. 가계부 항목 추가/수정/삭제
2. 기간별 품목별 지출량 그래프/표 표시
3. 키워드 기반 품목 추천
4. AI 분석 기능
5. 필수 항목 검증
"""

import streamlit as st
import pandas as pd
import plotly.express as px  # pyright: ignore[reportMissingImports]
import plotly.graph_objects as go  # pyright: ignore[reportMissingImports]
from datetime import datetime, date
import json
import os

# 페이지 설정
st.set_page_config(
    page_title="가계부 관리 시스템",
    page_icon="💰",
    layout="wide"
)

# 데이터 파일 경로
DATA_FILE = "household_data.json"

# 품목 카테고리 및 키워드 매핑
CATEGORY_KEYWORDS = {
    "식비": ["음식", "식당", "배달", "카페", "커피", "점심", "저녁", "아침", "간식", "치킨", "피자", "햄버거"],
    "교통비": ["버스", "지하철", "택시", "기차", "주유", "주차", "통행료", "교통", "이동"],
    "쇼핑": ["옷", "신발", "가방", "화장품", "의류", "쇼핑", "온라인", "마켓"],
    "생활비": ["전기", "가스", "수도", "인터넷", "통신", "관리비", "공과금"],
    "의료": ["병원", "약국", "의료", "치과", "검진", "약"],
    "교육": ["학원", "책", "강의", "교육", "학습", "교재"],
    "오락": ["영화", "게임", "놀이", "취미", "여가", "콘서트"],
    "기타": []
}

def parse_date_series(series: pd.Series) -> pd.Series:
    """
    날짜 형식을 일관되게 변환합니다.
    서로 다른 문자열 포맷이 섞여 있어도 파싱할 수 있도록 cache를 비활성화합니다.
    """
    if series.empty:
        return series
    return pd.to_datetime(series, errors='coerce', cache=False)

def load_data():
    """저장된 가계부 데이터를 불러옵니다."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                if not df.empty and '날짜' in df.columns:
                    df['날짜'] = parse_date_series(df['날짜'])
                return df
        except:
            return pd.DataFrame(columns=['날짜', '품목', '제품명', '가격', '개수', '개당가격', '전체가격'])
    return pd.DataFrame(columns=['날짜', '품목', '제품명', '가격', '개수', '개당가격', '전체가격'])

def save_data(df):
    """가계부 데이터를 파일에 저장합니다."""
    if not df.empty:
        df_dict = df.to_dict('records')
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(df_dict, f, ensure_ascii=False, indent=2, default=str)
    else:
        # 빈 데이터프레임일 경우 빈 파일 생성
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)

def recommend_category(product_name):
    """
    제품명의 키워드를 기반으로 품목을 추천합니다.
    키워드 매칭 점수를 계산하여 가장 높은 점수의 품목을 반환합니다.
    """
    if not product_name:
        return "기타"
    
    product_lower = product_name.lower()
    scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in product_lower:
                score += 1
        scores[category] = score
    
    # 가장 높은 점수의 카테고리 반환
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "기타"

def validate_input(date_input, category, product_name, price, quantity):
    """
    필수 항목이 모두 입력되었는지 검증합니다.
    """
    errors = []
    if not date_input:
        errors.append("구매 날짜")
    if not category:
        errors.append("품목")
    if not product_name:
        errors.append("제품명")
    if not price or price <= 0:
        errors.append("가격")
    
    return errors

def calculate_price(price, quantity, price_type):
    """
    가격을 계산합니다.
    price_type: 'unit' (개당가격 입력) 또는 'total' (전체가격 입력)
    """
    if price_type == 'unit':
        # 개당가격이 입력된 경우
        unit_price = price
        total_price = unit_price * quantity if quantity > 0 else unit_price
        return unit_price, total_price
    else:
        # 전체가격이 입력된 경우
        total_price = price
        unit_price = total_price / quantity if quantity > 0 else total_price
        return unit_price, total_price

def analyze_expenditure(df, start_date, end_date, category_filter=None):
    """
    특정 기간의 지출을 분석합니다.
    """
    if df.empty:
        return "데이터가 없습니다."
    
    # 날짜 필터링
    df['날짜'] = parse_date_series(df['날짜'])
    filtered_df = df[(df['날짜'] >= pd.to_datetime(start_date)) & 
                     (df['날짜'] <= pd.to_datetime(end_date))]
    
    if filtered_df.empty:
        return "선택한 기간에 데이터가 없습니다."
    
    # 품목 필터링
    if category_filter:
        filtered_df = filtered_df[filtered_df['품목'] == category_filter]
    
    if filtered_df.empty:
        return "선택한 조건에 맞는 데이터가 없습니다."
    
    # 분석 결과 생성
    total_expenditure = filtered_df['전체가격'].sum()
    avg_expenditure = filtered_df['전체가격'].mean()
    transaction_count = len(filtered_df)
    
    # 품목별 지출
    category_expenditure = filtered_df.groupby('품목')['전체가격'].sum().sort_values(ascending=False)
    
    # 개별 제품 구매 빈도
    product_frequency = filtered_df['제품명'].value_counts()
    
    result = f"""
**기간**: {start_date} ~ {end_date}
**총 지출**: {total_expenditure:,.0f}원
**평균 지출**: {avg_expenditure:,.0f}원
**거래 횟수**: {transaction_count}회

**품목별 지출**:
"""
    for cat, amount in category_expenditure.items():
        percentage = (amount / total_expenditure) * 100
        result += f"- {cat}: {amount:,.0f}원 ({percentage:.1f}%)\n"
    
    result += f"\n**자주 구매한 제품 (상위 5개)**:\n"
    for product, count in product_frequency.head(5).items():
        result += f"- {product}: {count}회\n"
    
    return result

def ai_analysis(df, start_date, end_date, user_query):
    """
    사용자 쿼리를 기반으로 AI 분석을 수행합니다.
    """
    if df.empty:
        return "데이터가 없습니다."
    
    # 날짜 필터링
    df['날짜'] = parse_date_series(df['날짜'])
    filtered_df = df[(df['날짜'] >= pd.to_datetime(start_date)) & 
                     (df['날짜'] <= pd.to_datetime(end_date))]
    
    if filtered_df.empty:
        return "선택한 기간에 데이터가 없습니다."
    
    # 이전 기간과 비교 (현재 기간의 절반 길이만큼 이전 기간)
    period_days = max((pd.to_datetime(end_date) - pd.to_datetime(start_date)).days, 1)
    prev_start = pd.to_datetime(start_date) - pd.Timedelta(days=period_days)
    prev_end = pd.to_datetime(start_date)
    
    prev_df = df[(df['날짜'] >= prev_start) & (df['날짜'] < prev_end)]
    
    result_sections = []
    query_lower = user_query.lower()
    
    wants_trend = any(keyword in query_lower for keyword in ["경향", "추세", "변화", "증감", "비교", "추이", "증가", "감소"])
    wants_category_detail = any(keyword in query_lower for keyword in ["지출", "항목", "카테고리"]) or any(cat.lower() in query_lower for cat in CATEGORY_KEYWORDS)
    wants_frequency = any(keyword in query_lower for keyword in ["빈도", "낱개", "개별", "자주", "횟수"])
    wants_feedback = any(keyword in query_lower for keyword in ["피드백", "추천", "조언", "절감", "개선", "인사이트"])
    
    # 기본 경향 분석
    current_total = filtered_df['전체가격'].sum()
    current_days = max((filtered_df['날짜'].max() - filtered_df['날짜'].min()).days + 1, 1)
    daily_avg = current_total / current_days
    
    trend_summary = f"기간 총 지출은 {current_total:,.0f}원이며 일일 평균은 약 {daily_avg:,.0f}원입니다."
    if not prev_df.empty:
        prev_total = prev_df['전체가격'].sum()
        if prev_total > 0:
            total_change = (current_total - prev_total) / prev_total * 100
            direction = "증가" if total_change > 0 else "감소"
            trend_summary += f" 이전 기간 대비 {abs(total_change):.1f}% {direction}했습니다."
        else:
            trend_summary += " 이전 기간에는 지출이 없었습니다."
    else:
        trend_summary += " 비교 가능한 이전 기간 데이터가 없습니다."
    
    result_sections.append(("지출 경향 요약", trend_summary))
    
    # 품목 관련 상세 분석
    current_category_exp = filtered_df.groupby('품목')['전체가격'].sum().sort_values(ascending=False)
    category_focus = []
    
    categories_requested = [cat for cat in CATEGORY_KEYWORDS if cat.lower() in query_lower]
    focus_categories = categories_requested if categories_requested else list(current_category_exp.index)
    
    prev_category_exp = prev_df.groupby('품목')['전체가격'].sum() if not prev_df.empty else pd.Series(dtype=float)
    
    if focus_categories:
        for category in focus_categories:
            if category not in current_category_exp:
                continue
            current_amount = current_category_exp[category]
            share = (current_amount / current_total * 100) if current_total > 0 else 0
            prev_amount = prev_category_exp.get(category, 0) if not prev_category_exp.empty else 0
            if prev_amount > 0:
                change = (current_amount - prev_amount) / prev_amount * 100
                direction = "증가" if change > 0 else "감소"
                category_focus.append(f"{category}: {current_amount:,.0f}원, 비중 {share:.1f}%, 이전 기간 대비 {abs(change):.1f}% {direction}")
            elif not prev_df.empty:
                category_focus.append(f"{category}: {current_amount:,.0f}원, 비중 {share:.1f}%, 이전 기간 대비 신규 지출")
            else:
                category_focus.append(f"{category}: {current_amount:,.0f}원, 비중 {share:.1f}%")
        
        if category_focus and (wants_category_detail or categories_requested):
            result_sections.append(("품목별 상세 분석", "\n".join(category_focus[:5])))
    
    # 상위 지출 및 빈도
    top_categories = current_category_exp.head(3)
    top_items = filtered_df.groupby('제품명').agg(
        총지출=('전체가격', 'sum'),
        구매횟수=('제품명', 'count'),
        평균개수=('개수', 'mean')
    ).sort_values(by='총지출', ascending=False).head(5)
    
    habit_lines = []
    if not top_categories.empty:
        top_cat = top_categories.index[0]
        top_cat_share = (top_categories.iloc[0] / current_total * 100) if current_total > 0 else 0
        habit_lines.append(f"가장 큰 비중은 `{top_cat}`으로 총 지출의 {top_cat_share:.1f}%를 차지합니다.")
    
    if wants_frequency:
        current_single = len(filtered_df[filtered_df['개수'] == 1])
        current_total_transactions = len(filtered_df)
        current_ratio = (current_single / current_total_transactions * 100) if current_total_transactions > 0 else 0
        if not prev_df.empty:
            prev_single = len(prev_df[prev_df['개수'] == 1])
            prev_total_transactions = len(prev_df)
            prev_ratio = (prev_single / prev_total_transactions * 100) if prev_total_transactions > 0 else 0
            change = current_ratio - prev_ratio
            direction = "증가" if change > 0 else "감소"
            habit_lines.append(f"낱개 구매 비중은 {current_ratio:.1f}%로 이전 기간 대비 {abs(change):.1f}% {direction}했습니다.")
        else:
            habit_lines.append(f"낱개 구매 비중은 {current_ratio:.1f}%입니다.")
    
    if not top_items.empty and (wants_frequency or wants_category_detail or wants_trend):
        items_summary = ", ".join([f"{row.Index}({row.구매횟수}회, {row.총지출:,.0f}원)" for row in top_items.itertuples()])
        habit_lines.append(f"주요 구매 품목: {items_summary}")
    
    if habit_lines:
        result_sections.append(("소비 패턴 관찰", "\n".join(habit_lines)))
    
    # 피드백 및 권장 사항
    feedback_lines = []
    if wants_feedback or True:
        # Identify categories with significant increase or high share
        if current_total > 0:
            for category, amount in current_category_exp.items():
                share = amount / current_total * 100
                if share >= 30:
                    feedback_lines.append(f"`{category}` 비중이 {share:.1f}%로 높습니다. 해당 지출의 필요성과 대체 가능성을 검토해 보세요.")
                if not prev_df.empty:
                    prev_amount = prev_category_exp.get(category, 0) if not prev_category_exp.empty else 0
                    if prev_amount > 0:
                        change = (amount - prev_amount) / prev_amount * 100
                        if change >= 20:
                            feedback_lines.append(f"`{category}` 지출이 이전 기간 대비 {change:.1f}% 증가했습니다. 원인을 점검하고 예산 한도를 설정하는 것이 좋습니다.")
        if daily_avg > 0:
            feedback_lines.append(f"일평균 지출 {daily_avg:,.0f}원에 맞춰 주간/월간 예산을 재조정하거나 지출 알림을 설정하면 관리에 도움이 됩니다.")
        if not feedback_lines:
            feedback_lines.append("현재 지출 패턴은 안정적입니다. 다만 대규모 지출이 발생한 품목이 있는지 주기적으로 점검하세요.")
        result_sections.append(("개선 제안", "\n".join(dict.fromkeys(feedback_lines))))
    
    formatted_sections = []
    for title, content in result_sections:
        if content:
            formatted_sections.append(f"**{title}**\n{content}")
    
    return "\n\n".join(formatted_sections) if formatted_sections else "분석할 수 있는 데이터가 부족합니다. 더 구체적인 질문을 해주세요."

# 세션 상태 초기화
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# 메인 타이틀
st.title("💰 가계부 관리 시스템")

# 사이드바 - 메뉴
st.sidebar.title("메뉴")
menu = st.sidebar.radio(
    "선택하세요",
    ["가계부 입력", "가계부 목록", "통계 및 그래프", "AI 분석"]
)

# 1. 가계부 입력
if menu == "가계부 입력":
    st.header("📝 가계부 항목 추가")
    
    col1, col2 = st.columns(2)
    
    with col1:
        purchase_date = st.date_input("구매 날짜 *", value=date.today())
        product_name = st.text_input("제품명 *", placeholder="예: 치킨, 버스카드 충전 등")
        
        # 제품명 입력 시 품목 추천
        if product_name:
            recommended_category = recommend_category(product_name)
            st.info(f"💡 추천 품목: **{recommended_category}**")
        
        category = st.selectbox(
            "품목 *",
            options=["식비", "교통비", "쇼핑", "생활비", "의료", "교육", "오락", "기타"],
            index=7 if not product_name else list(CATEGORY_KEYWORDS.keys()).index(recommended_category) if recommended_category in CATEGORY_KEYWORDS else 7
        )
    
    with col2:
        price_type = st.radio(
            "가격 입력 방식",
            ["개당 가격", "전체 가격"],
            horizontal=True
        )
        
        price = st.number_input(
            f"{'개당 가격' if price_type == '개당 가격' else '전체 가격'} *",
            min_value=0.0,
            value=0.0,
            step=100.0
        )
        
        quantity = st.number_input(
            "개수 *",
            min_value=1,
            value=1,
            step=1
        )
    
    # 가격 계산 미리보기
    if price > 0 and quantity > 0:
        if price_type == '개당 가격':
            unit_price = price
            total_price = unit_price * quantity
        else:
            total_price = price
            unit_price = total_price / quantity
        
        st.info(f"💰 개당 가격: {unit_price:,.0f}원 | 전체 가격: {total_price:,.0f}원")
    
    # 추가 버튼
    if st.button("✅ 항목 추가", type="primary"):
        # 필수 항목 검증
        validation_errors = validate_input(
            purchase_date, category, product_name, price, quantity
        )
        
        if validation_errors:
            st.error(f"❌ 필수 항목이 입력되지 않았습니다: {', '.join(validation_errors)}")
        else:
            # 가격 계산
            unit_price, total_price = calculate_price(
                price, quantity, 'unit' if price_type == '개당 가격' else 'total'
            )
            
            # 새 항목 추가
            new_row = pd.DataFrame({
                '날짜': [purchase_date],
                '품목': [category],
                '제품명': [product_name],
                '가격': [price],
                '개수': [quantity],
                '개당가격': [unit_price],
                '전체가격': [total_price]
            })
            
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            st.session_state.df['날짜'] = parse_date_series(st.session_state.df['날짜'])
            save_data(st.session_state.df)
            st.success("✅ 항목이 추가되었습니다!")
            st.rerun()

# 2. 가계부 목록
elif menu == "가계부 목록":
    st.header("📋 가계부 목록")
    
    if st.session_state.df.empty:
        st.info("📭 아직 등록된 항목이 없습니다.")
    else:
        # 필터 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_filter = st.checkbox("날짜 필터 적용")
            if date_filter:
                try:
                    df_dates = parse_date_series(st.session_state.df['날짜'])
                    min_date = df_dates.min().date() if not df_dates.empty else date.today()
                    max_date = df_dates.max().date() if not df_dates.empty else date.today()
                except:
                    min_date = date.today()
                    max_date = date.today()
                start_date_filter = st.date_input("시작 날짜", value=min_date)
                end_date_filter = st.date_input("종료 날짜", value=max_date)
        
        with col2:
            categories = ["전체"] + list(st.session_state.df['품목'].unique()) if not st.session_state.df.empty else ["전체"]
            selected_category = st.selectbox("품목 필터", categories)
        
        with col3:
            search_product = st.text_input("제품명 검색", placeholder="제품명으로 검색...")
        
        # 데이터 필터링
        filtered_df = st.session_state.df.copy()
        if not filtered_df.empty:
            filtered_df['날짜'] = parse_date_series(filtered_df['날짜'])
        
        if date_filter and not filtered_df.empty:
            filtered_df = filtered_df[
                (filtered_df['날짜'] >= pd.to_datetime(start_date_filter)) &
                (filtered_df['날짜'] <= pd.to_datetime(end_date_filter))
            ]
        
        if selected_category != "전체" and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df['품목'] == selected_category]
        
        if search_product and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df['제품명'].str.contains(search_product, case=False, na=False)]
        
        # 표시
        if filtered_df.empty:
            st.info("📭 필터 조건에 맞는 항목이 없습니다.")
        else:
            # 표시용 데이터프레임 (인덱스 포함)
            display_df = filtered_df.copy()
            display_df['날짜'] = parse_date_series(display_df['날짜']).dt.strftime('%Y-%m-%d')
            display_df = display_df[['날짜', '품목', '제품명', '개수', '개당가격', '전체가격']]
            display_df.columns = ['날짜', '품목', '제품명', '개수', '개당가격(원)', '전체가격(원)']
            
            # 숫자 포맷팅
            display_df['개당가격(원)'] = display_df['개당가격(원)'].apply(lambda x: f"{x:,.0f}")
            display_df['전체가격(원)'] = display_df['전체가격(원)'].apply(lambda x: f"{x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True)
            
            # 통계 요약
            total_amount = filtered_df['전체가격'].sum()
            st.metric("총 지출액", f"{total_amount:,.0f}원")
            
            # 삭제 기능
            st.subheader("항목 삭제")
            if not filtered_df.empty:
                delete_indices = st.multiselect(
                    "삭제할 항목 선택 (인덱스)",
                    options=filtered_df.index.tolist(),
                    format_func=lambda x: f"{x}: {filtered_df.loc[x, '제품명']} - {filtered_df.loc[x, '전체가격']:,.0f}원"
                )
                
                if st.button("🗑️ 선택한 항목 삭제", type="secondary"):
                    if delete_indices:
                        st.session_state.df = st.session_state.df.drop(delete_indices)
                        st.session_state.df = st.session_state.df.reset_index(drop=True)
                        save_data(st.session_state.df)
                        st.success("✅ 항목이 삭제되었습니다!")
                        st.rerun()

# 3. 통계 및 그래프
elif menu == "통계 및 그래프":
    st.header("📊 통계 및 그래프")
    
    if st.session_state.df.empty:
        st.info("📭 통계를 표시할 데이터가 없습니다.")
    else:
        # 기간 선택
        col1, col2 = st.columns(2)
        with col1:
            df_dates = parse_date_series(st.session_state.df['날짜'])
            start_date = st.date_input(
                "시작 날짜",
                value=df_dates.min().date() if not df_dates.empty else date.today()
            )
        with col2:
            end_date = st.date_input(
                "종료 날짜",
                value=df_dates.max().date() if not df_dates.empty else date.today()
            )
        
        # 품목 선택
        categories = ["전체"] + list(st.session_state.df['품목'].unique()) if not st.session_state.df.empty else ["전체"]
        selected_category = st.selectbox("품목 선택", categories)
        
        # 데이터 필터링
        filtered_df = st.session_state.df.copy()
        filtered_df['날짜'] = parse_date_series(filtered_df['날짜'])
        filtered_df = filtered_df[
            (filtered_df['날짜'] >= pd.to_datetime(start_date)) &
            (filtered_df['날짜'] <= pd.to_datetime(end_date))
        ]
        
        if selected_category != "전체":
            filtered_df = filtered_df[filtered_df['품목'] == selected_category]
        
        if filtered_df.empty:
            st.info("📭 선택한 조건에 맞는 데이터가 없습니다.")
        else:
            # 표 형식 표시
            st.subheader("📋 지출 내역 표")
            display_df = filtered_df[['날짜', '품목', '제품명', '개수', '전체가격']].copy()
            display_df['날짜'] = display_df['날짜'].dt.strftime('%Y-%m-%d')
            display_df.columns = ['날짜', '품목', '제품명', '개수', '지출액(원)']
            display_df['지출액(원)'] = display_df['지출액(원)'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(display_df, use_container_width=True)
            
            # 그래프
            st.subheader("📈 지출 그래프")
            
            # 1. 날짜별 지출 추이
            daily_expenditure = filtered_df.groupby(filtered_df['날짜'].dt.date)['전체가격'].sum().reset_index()
            daily_expenditure.columns = ['날짜', '지출액']
            
            fig1 = px.line(
                daily_expenditure,
                x='날짜',
                y='지출액',
                title=f"{selected_category} 일별 지출 추이",
                markers=True
            )
            fig1.update_layout(xaxis_title="날짜", yaxis_title="지출액 (원)")
            st.plotly_chart(fig1, use_container_width=True)
            
            # 2. 품목별 지출 파이 차트
            if selected_category == "전체":
                category_expenditure = filtered_df.groupby('품목')['전체가격'].sum().reset_index()
                category_expenditure.columns = ['품목', '지출액']
                
                fig2 = px.pie(
                    category_expenditure,
                    values='지출액',
                    names='품목',
                    title="품목별 지출 비율"
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # 3. 품목별 지출 막대 그래프
            category_expenditure = filtered_df.groupby('품목')['전체가격'].sum().sort_values(ascending=False).reset_index()
            category_expenditure.columns = ['품목', '지출액']
            
            fig3 = px.bar(
                category_expenditure,
                x='품목',
                y='지출액',
                title="품목별 지출액",
                text='지출액'
            )
            fig3.update_traces(texttemplate='%{text:,.0f}원', textposition='outside')
            fig3.update_layout(xaxis_title="품목", yaxis_title="지출액 (원)")
            st.plotly_chart(fig3, use_container_width=True)
            
            # 통계 요약
            st.subheader("📊 통계 요약")
            col1, col2, col3, col4 = st.columns(4)
            
            total_expenditure = filtered_df['전체가격'].sum()
            avg_expenditure = filtered_df['전체가격'].mean()
            max_expenditure = filtered_df['전체가격'].max()
            transaction_count = len(filtered_df)
            
            with col1:
                st.metric("총 지출액", f"{total_expenditure:,.0f}원")
            with col2:
                st.metric("평균 지출액", f"{avg_expenditure:,.0f}원")
            with col3:
                st.metric("최대 지출액", f"{max_expenditure:,.0f}원")
            with col4:
                st.metric("거래 횟수", f"{transaction_count}회")

# 4. AI 분석
elif menu == "AI 분석":
    st.header("🤖 AI 분석")
    
    if st.session_state.df.empty:
        st.info("📭 분석할 데이터가 없습니다.")
    else:
        # 기간 선택
        col1, col2 = st.columns(2)
        with col1:
            try:
                df_dates = parse_date_series(st.session_state.df['날짜'])
                min_date = df_dates.min().date() if not df_dates.empty else date.today()
            except:
                min_date = date.today()
            start_date = st.date_input("분석 시작 날짜", value=min_date, key="ai_start")
        with col2:
            try:
                df_dates = parse_date_series(st.session_state.df['날짜'])
                max_date = df_dates.max().date() if not df_dates.empty else date.today()
            except:
                max_date = date.today()
            end_date = st.date_input("분석 종료 날짜", value=max_date, key="ai_end")
        
        # 사용자 쿼리 입력
        user_query = st.text_area(
            "분석 요청",
            placeholder="예: A항목 관련 지출과 낱개 제품 구매 빈도를 분석해줘",
            height=100
        )
        
        if st.button("🔍 분석 실행", type="primary"):
            if user_query:
                # 기본 분석 결과
                basic_analysis = analyze_expenditure(
                    st.session_state.df,
                    start_date,
                    end_date
                )
                
                st.subheader("📊 기본 분석 결과")
                st.markdown(basic_analysis)
                
                # AI 분석 결과
                ai_result = ai_analysis(
                    st.session_state.df,
                    start_date,
                    end_date,
                    user_query
                )
                
                st.subheader("🤖 AI 분석 결과")
                st.markdown(ai_result)
            else:
                st.warning("⚠️ 분석 요청을 입력해주세요.")

# 하단 정보
st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 사용 방법")
st.sidebar.markdown("""
1. **가계부 입력**: 지출 내역을 추가합니다
2. **가계부 목록**: 저장된 내역을 확인/삭제합니다
3. **통계 및 그래프**: 기간별/품목별 통계를 확인합니다
4. **AI 분석**: 데이터를 분석합니다
""")

