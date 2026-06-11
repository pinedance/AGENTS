# Development Task List

Phase 1: Setup & Structure

    [ ] Vite + React + TypeScript + Tailwind CSS 프로젝트 초기화
    [ ] `types.ts`에 핵심 데이터 모델 정의 (`Task`, `Column`, `Id`)
    [ ] 기본 레이아웃 잡기 (Header, Main Board Area)


Phase 2: Core Components (UI)

    [ ] `TaskCard` 컴포넌트 구현 (정적 디자인)
    [ ] `Column` 컴포넌트 구현 (TaskCard 리스트 렌더링)
    [ ] `KanbanBoard` 메인 컨테이너 구현


Phase 3: State & Logic

    [ ] `useKanban` 훅 생성 (Create, Read, Update, Delete 로직 구현)
    [ ] Task 추가/삭제/수정 기능 연동
    [ ] LocalStorage 저장/불러오기 기능 구현 (`useEffect`)


Phase 4: Drag and Drop (Complex)

    [ ] dnd-kit (또는 라이브러리) 설치 및 Context 설정
    [ ] `Draggable` 및 `Droppable` 영역 설정
    [ ] `onDragEnd` 핸들러 구현 (같은 컬럼 내 이동 + 다른 컬럼 이동 처리)


Phase 5: Polish & Refactor

    [ ] `useTheme` 훅 구현 및 다크모드 토글 기능 추가
    [ ] 다크모드 스타일링 적용 (Tailwind `dark:` 클래스)
    [ ] 코드 클린업 (RULES.md 위반 사항 점검)
