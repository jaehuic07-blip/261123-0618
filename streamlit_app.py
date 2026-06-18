import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Rectangle
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import io
from datetime import datetime
import os

# ==================== 한글 폰트 설정 ====================
# 프로젝트 폴더의 fonts 폴더에서 한글 폰트 로드
font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'NotoSansKR-Medium.ttf')
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
    plt.rcParams['axes.unicode_minus'] = False
else:
    # 폰트 파일이 없으면 시스템 기본 폰트 사용
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

# ==================== 초기화 및 세션 상태 ====================
# 세션 상태 기본값 설정
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.show_intro = True
    st.session_state.researcher = {'name': '', 'grade': '초3'}
    st.session_state.model = '원형 피자'
    st.session_state.a_denom = 3
    st.session_state.b_denom = 5
    st.session_state.prediction = None
    st.session_state.analysis = None
    st.session_state.show_overlay = False
    st.session_state.overlay_answer = None
    st.session_state.logs = []

# ==================== 유틸리티 함수 ====================

def frac_text(n):
    """단위분수 텍스트 표현을 반환합니다."""
    try:
        n = int(n)
        return f"1/{n}"
    except Exception:
        return "-"


def draw_pizza(ax, n, color='#FFD27F', alpha=1.0, clear=True, border_color='black', border_width=1):
    """원형 피자(원)를 n등분하여 단위분수 조각을 채웁니다."""
    radius = 1
    theta_start = 90
    if clear:
        ax.clear()
        ax.set_aspect('equal')
        ax.axis('off')
        for i in range(n):
            start = theta_start - (360.0 * i / n)
            end = 360.0 / n
            wedge = Wedge((0, 0), radius, start - end, start, facecolor='#F5F7FB', edgecolor='#BBBBBB', linewidth=1)
            ax.add_patch(wedge)
    wedge_fill = Wedge((0, 0), radius, theta_start - (360.0 / n), theta_start, facecolor=color, alpha=alpha, edgecolor=border_color, linewidth=border_width)
    ax.add_patch(wedge_fill)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)


def draw_chocolate(ax, n, color='#A27B5C', alpha=1.0, clear=True, border_color='black', border_width=1):
    """직사각형을 n등분하여 단위분수 조각을 채웁니다."""
    width, height = 2.4, 1.2
    if clear:
        ax.clear()
        ax.set_aspect('equal')
        ax.axis('off')
        rect = Rectangle((-width/2, -height/2), width, height, facecolor='#FDF7E5', edgecolor='#B88F59', linewidth=2)
        ax.add_patch(rect)
        for i in range(n):
            x0 = -width/2 + i * (width / n)
            rect_piece = Rectangle((x0, -height/2), width / n, height, facecolor='none', edgecolor='#CCCCCC', linewidth=1)
            ax.add_patch(rect_piece)
    piece = Rectangle((-width/2, -height/2), width / n, height, facecolor=color, alpha=alpha, edgecolor=border_color, linewidth=border_width)
    ax.add_patch(piece)
    ax.set_xlim(-width/2 - 0.15, width/2 + 0.15)
    ax.set_ylim(-height/2 - 0.15, height/2 + 0.15)


def render_fraction_plot(model, denom, ax, color, alpha=1.0):
    """모델과 분모에 따라 적절한 도형을 그립니다."""
    try:
        n = int(denom)
        if n <= 0:
            raise ValueError("분모는 양수여야 합니다")
    except Exception:
        ax.clear()
        ax.text(0.5, 0.5, '오류: 유효하지 않은 분모', ha='center', va='center')
        return

    if model == '원형 피자':
        draw_pizza(ax, n, color=color, alpha=alpha)
    elif model == '초콜릿 바(직사각형)':
        draw_chocolate(ax, n, color=color, alpha=alpha)
    else:
        ax.clear()
        ax.text(0.5, 0.5, '알 수 없는 모델', ha='center', va='center')


def draw_overlay_plot(model, a, b, ax, a_label, b_label):
    """왼쪽과 오른쪽 단위분수를 동일 좌표에 반투명으로 겹쳐서 그립니다."""
    ax.clear()
    ax.set_aspect('equal')
    ax.axis('off')

    if a == b:
        larger_denom, smaller_denom = a, b
        larger_color, smaller_color = '#7EC8E3', '#E16262'
        larger_label, smaller_label = a_label, b_label
    elif a < b:
        larger_denom, smaller_denom = a, b
        larger_color, smaller_color = '#7EC8E3', '#E16262'
        larger_label, smaller_label = a_label, b_label
    else:
        larger_denom, smaller_denom = b, a
        larger_color, smaller_color = '#7EC8E3', '#E16262'
        larger_label, smaller_label = b_label, a_label

    if model == '원형 피자':
        draw_pizza(ax, larger_denom, color=larger_color, alpha=0.6, clear=True, border_color='black', border_width=2)
        draw_pizza(ax, smaller_denom, color=smaller_color, alpha=0.7, clear=False, border_color='black', border_width=3)
        overlap_patch = Wedge((0, 0), 1, 90 - (360.0 / smaller_denom), 90, facecolor='#A17DD4', alpha=0.35, edgecolor='none')
        ax.add_patch(overlap_patch)
    elif model == '초콜릿 바(직사각형)':
        draw_chocolate(ax, larger_denom, color=larger_color, alpha=0.6, clear=True, border_color='black', border_width=2)
        draw_chocolate(ax, smaller_denom, color=smaller_color, alpha=0.7, clear=False, border_color='black', border_width=3)
        width, height = 2.4, 1.2
        overlap_patch = Rectangle((-width/2, -height/2), width / smaller_denom, height, facecolor='#A17DD4', alpha=0.35, edgecolor='none')
        ax.add_patch(overlap_patch)
    else:
        ax.text(0.5, 0.5, '알 수 없는 모델', ha='center', va='center')
        return

    ax.set_title(f"{frac_text(a)} 과 {frac_text(b)} 겹쳐보기", fontsize=18, pad=18)
    ax.text(0, -1.15, '파란색 = 더 큰 분수, 빨간색 = 작은 분수, 보라색 = 겹쳐진 부분', ha='center', va='top', fontsize=12, color='#444444')
    return larger_denom, smaller_denom, larger_label, smaller_label


def analyze_results(a, b):
    """실험 결과 자동 분석 (1/a vs 1/b) 및 규칙 도출"""
    try:
        a = int(a); b = int(b)
        if a == b:
            comparison = '같다'
            message = f"1/{a} = 1/{b}"
        elif a < b:
            comparison = '왼쪽'
            message = f"1/{a} > 1/{b} (분모가 작을수록 단위분수가 큽니다)"
        else:
            comparison = '오른쪽'
            message = f"1/{a} < 1/{b} (분모가 작을수록 단위분수가 큽니다)"
    except Exception:
        comparison = None
        message = '분석 불가: 분모 값을 확인하세요.'

    rules = [
        '분모가 커질수록 조각 수는 많아진다.',
        '분모가 커질수록 각 조각의 크기는 작아진다.',
        '전체 크기가 같을 때 단위분수는 분모가 작은 것이 더 크다.'
    ]
    return comparison, message, rules


def build_report_bytes(researcher, model, a, b, prediction, analysis_msg, discoveries, feeling, as_pdf=False):
    """간단한 보고서를 이미지(PNG) 또는 PDF 바이트로 반환합니다."""
    txt = []
    txt.append('🧪 분수 실험실 보고서')
    txt.append('')
    txt.append(f"연구원: {researcher.get('name','익명')} ({researcher.get('grade','')})")
    txt.append(f"날짜: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    txt.append(f"모델: {model}")
    txt.append(f"비교한 분수: 1/{a} vs 1/{b}")
    txt.append(f"예측: {prediction}")
    txt.append('')
    txt.append('분석 결과:')
    txt.append(analysis_msg)
    txt.append('')
    txt.append('발견한 규칙:')
    for r in discoveries:
        txt.append(f'- {r}')
    txt.append('')
    txt.append('느낀 점:')
    txt.append(feeling or '-')

    # matplotlib를 이용해 텍스트 형태의 간단한 리포트 생성
    fig, ax = plt.subplots(figsize=(8, 10), dpi=100)
    ax.axis('off')
    full_text = '\n'.join(txt)
    # 한글 폰트를 명시적으로 지정
    ax.text(0.1, 0.95, full_text, va='top', fontsize=11, 
            family='sans-serif', fontproperties=font_prop if 'font_prop' in globals() else None,
            wrap=True)
    buf = io.BytesIO()
    if as_pdf:
        fig.savefig(buf, format='pdf', bbox_inches='tight', dpi=100)
    else:
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf

# ==================== 레이아웃: 사이드바 ====================
st.set_page_config(page_title='🧪 분수 실험실', layout='wide')
st.sidebar.title('연구원 정보')
name = st.sidebar.text_input('연구원 이름', st.session_state.researcher.get('name', ''))
grade = st.sidebar.selectbox('학년 선택', options=['초3', '초4', '초5'], index=0 if st.session_state.researcher.get('grade','초3')=='초3' else 1)

model = st.sidebar.radio('실험 모델 선택', ['원형 피자', '초콜릿 바(직사각형)'], index=['원형 피자','초콜릿 바(직사각형)'].index(st.session_state.model))

# 세션 상태 업데이트
st.session_state.researcher['name'] = name
st.session_state.researcher['grade'] = grade
st.session_state.model = model

# 상단 제목
st.title('🧪 분수 실험실')
st.subheader('연구원이 되어 단위분수의 비밀을 밝혀보세요!')

# ==================== 1단계: 실험 준비 (팝업) ====================
if st.session_state.show_intro:
    try:
        with st.modal('분수 실험실 사용 방법'):
            st.header('분수 실험실 사용 방법')
            st.write('1. 분모를 조절해보세요.')
            st.write('2. 조각 크기가 어떻게 변하는지 관찰해보세요.')
            st.write('3. 어떤 분수가 더 큰지 예측해보세요.')
            st.write('4. 실험 결과를 탐구일지에 기록해보세요.')
            if st.button('확인'):
                st.session_state.show_intro = False
    except Exception:
        # st.modal이 없는 환경을 위한 폴백
        with st.expander('분수 실험실 사용 방법 (설명)'):
            st.write('1. 분모를 조절해보세요.')
            st.write('2. 조각 크기가 어떻게 변하는지 관찰해보세요.')
            st.write('3. 어떤 분수가 더 큰지 예측해보세요.')
            st.write('4. 실험 결과를 탐구일지에 기록해보세요.')
            if st.button('확인 (닫기)'):
                st.session_state.show_intro = False

# 탭 구성: 4단계
tabs = st.tabs(['1. 실험 준비', '2. 가설 세우기', '3. 실험 수행', '4. 탐구일지 작성'])

# -------------------- 1. 실험 준비 --------------------
with tabs[0]:
    st.markdown(f"**현재 실험 모델 : {st.session_state.model}**")
    st.info('분모를 변경하여 조각이 어떻게 변하는지 관찰해보세요!')

# -------------------- 2. 가설 세우기 --------------------
with tabs[1]:
    st.header('어느 조각이 더 클까요?')
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.subheader('분수 A')
        a = st.slider('분모 A', min_value=2, max_value=12, value=st.session_state.a_denom, key='a_slider')
        st.write(f'단위분수: {frac_text(a)}')
    with col2:
        st.subheader('분수 B')
        b = st.slider('분모 B', min_value=2, max_value=12, value=st.session_state.b_denom, key='b_slider')
        st.write(f'단위분수: {frac_text(b)}')
    with col3:
        st.subheader('예측')
        st.write('어떤 단위분수가 더 클 것 같나요?')
        pred = None
        c1, c2, c3 = st.columns(3)
        if c1.button('왼쪽 (A)'):
            pred = '왼쪽'
        if c2.button('오른쪽 (B)'):
            pred = '오른쪽'
        if c3.button('같다'):
            pred = '같다'
        if pred:
            st.session_state.prediction = pred
            st.success(f'예측이 저장되었습니다: {pred}')
    # 세션 업데이트
    st.session_state.a_denom = a
    st.session_state.b_denom = b

# -------------------- 3. 실험 수행 --------------------
with tabs[2]:
    st.header('실험 수행')
    st.write('슬라이더를 움직여 두 단위분수를 관찰하고, 겹쳐보기를 통해 크기를 비교해보세요.')
    colL, colR = st.columns(2)
    fig1, ax1 = plt.subplots(figsize=(3,3))
    fig2, ax2 = plt.subplots(figsize=(3,3))

    with colL:
        st.subheader(f'A: {frac_text(st.session_state.a_denom)}')
        render_fraction_plot(st.session_state.model, st.session_state.a_denom, ax1, color='#7EC8E3')
        st.pyplot(fig1)
    with colR:
        st.subheader(f'B: {frac_text(st.session_state.b_denom)}')
        render_fraction_plot(st.session_state.model, st.session_state.b_denom, ax2, color='#B3E283')
        st.pyplot(fig2)

    # 겹쳐보기 기능
    if st.button('조각 겹쳐보기'):
        st.session_state.show_overlay = True
        st.session_state.overlay_answer = None

    if st.session_state.show_overlay:
        st.subheader('겹쳐보기 (반투명)')
        figO, axO = plt.subplots(figsize=(6,6), dpi=120)
        overlay_result = draw_overlay_plot(
            st.session_state.model,
            st.session_state.a_denom,
            st.session_state.b_denom,
            axO,
            '왼쪽 분수',
            '오른쪽 분수'
        )
        st.pyplot(figO, use_container_width=True)

        if overlay_result is not None:
            larger_denom, smaller_denom, larger_label, smaller_label = overlay_result
            if st.session_state.a_denom == st.session_state.b_denom:
                st.info(f"파란색({frac_text(st.session_state.a_denom)})과 빨간색({frac_text(st.session_state.b_denom)})이 같은 크기예요. 두 분수는 같습니다.")
            else:
                larger_label_text = '왼쪽 분수' if larger_label == '왼쪽 분수' else '오른쪽 분수'
                smaller_label_text = '왼쪽 분수' if smaller_label == '왼쪽 분수' else '오른쪽 분수'
                st.info(f"{frac_text(larger_denom)}은(는) {frac_text(smaller_denom)}보다 큽니다.")
                st.info(f"빨간색 {smaller_label_text}({frac_text(smaller_denom)})가 보라색 겹친 부분으로 표시된 것을 볼 수 있어요.")
                st.info('분모가 작을수록 단위분수가 더 큽니다. 즉, 분모가 작은 쪽이 더 큰 조각이에요.')

                st.write('### 어떤 조각이 더 큰가요?')
                overlay_options = ['왼쪽 분수', '오른쪽 분수']
                overlay_answer = st.radio('선택해 보세요', overlay_options, index=0 if st.session_state.overlay_answer is None else overlay_options.index(st.session_state.overlay_answer), key='overlay_radio')
                st.session_state.overlay_answer = overlay_answer
                correct_answer = '왼쪽 분수' if st.session_state.a_denom < st.session_state.b_denom else '오른쪽 분수'
                if overlay_answer:
                    if st.session_state.a_denom == st.session_state.b_denom:
                        st.warning('두 분수가 같습니다. 왼쪽과 오른쪽 모두 같은 크기예요.')
                    elif overlay_answer == correct_answer:
                        st.success('정답이에요! 잘 비교했어요. 😊')
                    else:
                        st.error('조금 다르게 보셨네요. 다시 그림을 보면서 어느 색이 더 큰지 확인해볼까요?')

    # 실험 결과 확인
    if st.button('실험 결과 확인'):
        comp, msg, rules = analyze_results(st.session_state.a_denom, st.session_state.b_denom)
        st.session_state.analysis = {'comparison': comp, 'message': msg, 'rules': rules}
        # 예측과 비교
        if st.session_state.prediction is None:
            st.warning('먼저 2단계에서 예측을 저장해 보세요.')
        else:
            if comp == st.session_state.prediction:
                st.success('예측 성공! 🎉')
            else:
                st.error('다시 생각해보세요! 🤔')
        st.info(msg)
        # 로그 기록
        st.session_state.logs.append({'a': st.session_state.a_denom, 'b': st.session_state.b_denom, 'analysis': msg, 'prediction': st.session_state.prediction, 'time': datetime.now().isoformat()})

    # 규칙 발견 영역
    if st.session_state.analysis:
        st.subheader('규칙 발견')
        for r in st.session_state.analysis['rules']:
            st.write('- ' + r)

# -------------------- 4. 탐구일지 작성 --------------------
with tabs[3]:
    st.header('오늘의 연구 결과')
    st.write('완료된 체크리스트를 확인하고, 느낀 점과 발견한 규칙을 작성하세요.')
    checklist = st.checkbox('분모가 커질수록 단위분수는 작아진다。', value=True)
    c2 = st.checkbox('전체 크기가 같아야 분수를 비교할 수 있다。', value=True)
    c3 = st.checkbox('1/2는 1/4보다 크다。', value=True)
    c4 = st.checkbox('분모가 작은 단위분수가 더 크다。', value=True)

    feeling = st.text_area('오늘 새롭게 알게 된 점', height=80)
    discoveries = st.text_area('실험을 통해 발견한 규칙 (줄바꿈으로 구분)', height=120)

    if st.button('탐구일지 완성하기'):
        # 리포트 생성
        analysis_msg = st.session_state.analysis['message'] if st.session_state.analysis else '실험을 수행해 주세요.'
        discoveries_list = [d.strip() for d in discoveries.splitlines() if d.strip()] or (st.session_state.analysis['rules'] if st.session_state.analysis else [])
        buf_png = build_report_bytes(st.session_state.researcher, st.session_state.model, st.session_state.a_denom, st.session_state.b_denom, st.session_state.prediction, analysis_msg, discoveries_list, feeling, as_pdf=False)
        buf_pdf = build_report_bytes(st.session_state.researcher, st.session_state.model, st.session_state.a_denom, st.session_state.b_denom, st.session_state.prediction, analysis_msg, discoveries_list, feeling, as_pdf=True)
        st.success('탐구일지가 생성되었습니다!')
        st.image(buf_png)
        st.download_button('PNG로 저장', data=buf_png, file_name='fraction_lab_report.png', mime='image/png')
        st.download_button('PDF로 저장', data=buf_pdf, file_name='fraction_lab_report.pdf', mime='application/pdf')

# ==================== 예외 처리/마무리 ====================
try:
    pass
except Exception as e:
    st.error(f'앱 실행 중 오류가 발생했습니다: {e}')

# 개발자용 로그 보기 (선택사항)
with st.expander('실험 로그 보기'):
    if st.session_state.logs:
        df = pd.DataFrame(st.session_state.logs)
        st.dataframe(df)
    else:
        st.write('아직 실험 기록이 없습니다.')

# 코드 끝
