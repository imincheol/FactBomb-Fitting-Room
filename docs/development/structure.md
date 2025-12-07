# 문서화 구조 계획 (Documentation Structure Plan)

이 문서는 프로젝트 문서의 구조를 제안하며, 각 계층을 4-6개의 핵심 항목으로 제한하여 명확성과 탐색 용이성을 보장합니다.

## 1. 프로젝트 개요 및 아키텍처
*파일: `docs/guides/01_overview.md`*
*   **소재**: Smh-Fassion이란 무엇인가? (펙트폭행 피팅룸)
*   **기술 스택**: 프론트엔드 (React/Vite), 백엔드 (FastAPI/Python), AI (Gemini).
*   **고수준 흐름**: 사용자 업로드 -> 백엔드 처리 -> 시각적 & 텍스트 분석 -> 결과 표시.
*   **디렉토리 맵**: 핵심 폴더 및 용도 (`backend/`, `frontend/`, `docs/`).

## 2. 분석 모드 및 로직
*파일: `docs/guides/02_analysis_modes.md`*
*   **기본 모드 (Legacy)**: 컴퓨터 비전(CV) 로직, 신체 랜드마크 감지, 순수 알고리즘 방식.
*   **믹스 모드 (Mix Mode)**: 하이브리드 접근 방식. CV가 통계/비율을 계산하고, AI(Gemini Text)가 해당 통계를 바탕으로 "팩트폭행" 코멘트를 생성.
*   **풀 AI 모드 (Full AI Mode)**: End-to-end AI. 원본 이미지를 Gemini Vision으로 전송하여 전체적인 분석 및 코멘트 생성.
*   **공통 코어 (Common Core)**: 분석 모드와 관계없이 `image_processor.py`가 "워핑(Warping)" 시각적 결과를 제공하는 방식.

## 3. 설정 및 보안 (Configuration & Secrets)
*파일: `docs/guides/03_configuration.md`*
*   **환경 변수**: `.env` 파일 구조.
*   **API 키**: Google Gemini API 키 관리.
*   **로컬 설정**: 로컬에서 앱 실행하기 (`npm run dev`, `uvicorn`).
*   **의존성**: `requirements.txt` (백엔드) 및 `package.json` (프론트엔드).

## 4. 배포 가이드 (Deployment Guide)
*파일: `docs/guides/04_deployment.md`*
*   **프로덕션 아키텍처**: 프론트엔드(정적 파일)와 백엔드(API) 분리.
*   **빌드 단계**: 프론트엔드용 `npm run build`.
*   **서버 설정**: 호스팅 제안 (예: Nginx 정적 파일 서빙, Uvicorn 리버스 프록시).
*   **향후 고려사항**: 확장성 및 CI/CD 참고 사항.

---
*참고: 상세 개발 결정 사항과 계획은 `docs/development/` 폴더에 있습니다.*
