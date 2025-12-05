# PRD

Project Name: Simple Kanban Board with Dark Mode

1. Project Overview

    *Goal:* React와 Tailwind CSS를 사용하여 드래그 앤 드롭이 가능한 칸반 보드를 구축한다.
    *Target User:* 개인 할 일 관리가 필요한 개발자.
    *Key Value:* 직관적인 UX, 다크모드 지원, 로컬 스토리지 데이터 지속성.


2. Tech Stack

    *Framework:* React (Vite)
    *Styling:* Tailwind CSS
    *Icons:* Lucide React
    *State Management:* React Context API or Zustand (Simple local state is preferred for this demo)
    *Drag & Drop:* `@dnd-kit/core` (혹은 HTML5 Native API)


3. Core Features (MVP)
3.1 Board Layout

    화면 전체를 채우는 3개의 고정 컬럼: "To Do", "In Progress", "Done".
    모바일 반응형 지원 (모바일에서는 세로 스크롤).


3.2 Task Management

    *Add Task:* "To Do" 컬럼 하단에 `+ Add Task` 버튼. 클릭 시 모달 없이 인라인 입력.
    *Delete Task:* 카드 내 휴지통 아이콘 클릭 시 삭제.
    *Edit Task:* 텍스트 클릭 시 수정 모드 전환.


3.3 Drag and Drop

    카드를 같은 컬럼 내에서 순서 변경 가능.
    카드를 다른 컬럼으로 이동 가능.
    드래그 중인 카드는 약간 투명해지거나 그림자 효과(Visual Cue).


3.4 Dark Mode

    우측 상단 토글 스위치로 라이트/다크 모드 전환.
    시스템 설정값(prefers-color-scheme) 초기 감지.
    다크모드 시 배경: Slate-900, 카드: Slate-800, 텍스트: Slate-100.


3.5 Persistence

    모든 데이터(Tasks, Columns, Theme)는 `localStorage`에 저장되어 새로고침 후에도 유지되어야 함.


4. Constraints (Non-functional)

    *Performance:* 드래그 시 60fps 유지 (불필요한 리렌더링 방지).
    *Code Quality:* 컴포넌트는 단일 책임 원칙(SRP)을 준수하여 분리.
