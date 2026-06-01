# Coding Rules & Guidelines

1. General Principles

    *KISS (Keep It Simple, Stupid):* 과도한 추상화를 피하고 명확한 코드를 작성하라.
    *DRY (Don't Repeat Yourself):* 반복되는 로직은 커스텀 훅(`hooks/`)이나 유틸리티 함수(`utils/`)로 분리하라.
    *Functional Components:* 모든 컴포넌트는 React Functional Component로 작성하며 Hooks를 사용하라.


2. File Structure

    `/src/components`: UI 컴포넌트 (e.g., `Column.tsx`, `TaskCard.tsx`)
    `/src/hooks`: 로직 분리 (e.g., `useKanban.ts`, `useTheme.ts`)
    `/src/types`: TypeScript 인터페이스 정의 (e.g., `types.ts`)
    *Rule:* 하나의 파일에는 하나의 컴포넌트만 존재해야 한다. (100줄이 넘어가면 분리를 고려할 것)


3. Naming Conventions

    *Components:* PascalCase (e.g., `TaskCard`)
    *Functions/Variables:* camelCase (e.g., `handleDragEnd`, `isLoading`)
    *Types/Interfaces:* PascalCase with explicit naming (e.g., `Task`, `ColumnStatus`)


4. Styling (Tailwind CSS)

    인라인 스타일(`style={{}}`) 사용 금지. 동적 스타일링도 Tailwind 유틸리티 클래스 조합(`clsx` or `tailwind-merge`)을 사용할 것.
    색상은 하드코딩하지 말고 Tailwind의 시맨틱 컬러(bg-primary, text-muted 등)나 기본 팔레트를 활용할 것.


5. State Management & Logic

    `useEffect` 사용을 최소화하고 이벤트 핸들러 내에서 로직을 처리하라.
    비즈니스 로직(데이터 필터링, 드래그 계산 등)은 UI 컴포넌트 내부에 두지 말고 `hooks`로 분리하라.


6. Error Handling

    드래그 앤 드롭 실패 시 UI가 멈추지 않고 원상복구 되어야 한다.
    `localStorage` 접근 시 예외 처리를 포함하라 (try-catch).
