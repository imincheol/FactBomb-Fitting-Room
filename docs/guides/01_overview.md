# 1. 프로젝트 개요 및 아키텍처

## 소개 (Introduction)
**Smh-Fassion** ("팩트폭행 피팅룸")은 사용자의 신체 비율을 "워너비(Wannabe)" 모델과 비교 분석하는 인터랙티브 웹 애플리케이션입니다. 컴퓨터 비전(CV)과 인공지능(AI)을 활용하여 유머러스한("팩트폭행") 피드백을 생성하고, 사용자가 모델의 비율을 가졌을 때의 모습을 시각화하여 보여줍니다.

## 기술 스택 (Tech Stack)
이 프로젝트는 다음과 같은 최신 분리형 아키텍처를 따릅니다:

*   **프론트엔드 (Frontend)**:
    *   **프레임워크**: React (v18+) - Vite 기반 빌드.
    *   **로직**: JavaScript (ES modules).
    *   **스타일링**: CSS Modules / Standard CSS.
*   **백엔드 (Backend)**:
    *   **프레임워크**: FastAPI (Python).
    *   **이미지 처리**: OpenCV, NumPy.
    *   **AI 통합**: Google Gemini API (Generative AI).
*   **통신**: RESTful API (JSON 페이로드 + Base64 이미지).

## 디렉토리 구조 (Directory Structure)
*   `backend/`: Python FastAPI 서버 애플리케이션을 포함합니다.
    *   `main.py`: 진입점(Entry point) 및 API 라우트 정의.
    *   `services/`: 핵심 로직 모듈 (이미지 처리, AI 서비스).
*   `frontend/`: React 클라이언트 애플리케이션을 포함합니다.
    *   `src/`: 컴포넌트 및 로직 소스 코드.
    *   `public/`: 정적 리소스(Assets).
*   `docs/`: 프로젝트 문서 및 가이드.
*   `scripts/`: 개발 및 테스트용 유틸리티 스크립트.
*   `samples/`: 테스트용 샘플 이미지 및 결과물 저장소.

## 고수준 데이터 흐름 (High-Level Data Flow)
1.  **입력**: 사용자가 프론트엔드에서 "사용자 이미지"와 "모델 이미지"를 선택합니다.
2.  **요청**: 프론트엔드가 이미지들과 선택된 "모드"(Standard, Mix, Full AI)를 백엔드(`/process-image`)로 전송합니다.
3.  **처리 (Backend)**:
    *   이미지 디코딩이 수행됩니다.
    *   **비주얼 코어**: `image_processor.py`가 랜드마크를 감지하고, 사용자 몸을 모델의 골격 비율에 맞춰 "워핑(Warping)" 변환을 수행합니다.
    *   **분석**: 모드에 따라 특정 알고리즘 또는 AI 모델이 데이터를 분석합니다.
4.  **응답**: 백엔드가 다음 데이터를 반환합니다:
    *   처리된 이미지 (Base64).
    *   분석 데이터 (등신 확인/N-Heads, 비율).
    *   텍스트 코멘터리 ("팩트폭행").
5.  **표시**: 프론트엔드가 결과 이미지와 텍스트 피드백을 렌더링합니다.
