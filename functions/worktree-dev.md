# Goal Prompt: Reusable Git Worktree Folder Migration (with Untracked File Protection)

> [!CAUTION]
> **CRITICAL SAFETY DIRECTIVE: UNTRACKED & IGNORED FILE PROTECTION**
> Git 추적을 받지 않는 파일/폴더(`git ignored` 및 `untracked` 파일, 예: `.agents/`, `.env`, `.vscode/`, `node_modules/`, HTML 리포트 생성물, 데이터 캐시 등)는 Git의 버전에 기록되지 않으므로, 부주의한 `rm -rf`, `git checkout`, `git clean` 등의 명령으로 삭제될 경우 **복구가 불가능**합니다.
> 이 프롬프트를 실행하는 모든 Agent는 **미추적 파일의 100% 보존**을 최우선 원칙으로 삼아야 합니다.

---

## 🎯 Goal

로컬 미추적(untracked) 또는 gitignore 처리된 개발/실험 전용 디렉터리를 Git 브랜치로 격리하고, `git worktree`로 연결한다. 작업 과정에서 기존 파일(HTML 리포트, 생성물, 미추적 파일) 및 메인 디렉터리의 미추적 폴더(`.agents/` 등)가 **절대로 삭제되거나 손실되지 않도록 격리 작업 및 전수 백업/복원 메커니즘을 통해 100% 철저히 보호**한다.

---

## ⚙️ Input Parameters

- `TARGET_DIR`: 이관할 폴더 경로 (기본값: `.dev`)
- `BRANCH_NAME`: 연결할 Git 브랜치 이름 (기본값: `dev`)
- `BRANCH_TYPE`: `orphan` (독립 이력, 기본값) 또는 `main-based` (main 승계)
- `EXCLUDE_FROM_COMMIT`: Git 커밋에서 제외할 패턴 목록 (예: `__pycache__/`, `*.pyc`, `*.html`, `output/*.html`)

---

## 🛡️ Mandatory Untracked File Protection Principles

1. **사전 전수 백업 (Complete Pre-Backup)**: 원본 디렉터리에 손을 대기 전, 미추적 파일/생성물/캐시를 포함한 전체 폴더를 백업 경로(`{TARGET_DIR}_backup`)로 100% 복사한다.
2. **격리 디렉터리 작업 (Main Workspace Isolation)**: 메인 작업영역의 미추적 파일/폴더(`.agents/`, `.env`, `.vscode/` 등)가 브랜치 전환이나 인덱스 변경에 노출되지 않도록, 브랜치 빌드는 반드시 `/tmp/` 임시 격리 공간에서 수행한다.
3. **미추적 생성물 파일 100% 복원 (Untracked Files Restoration)**: `git worktree` 연결 완료 후, 커밋에서 제외된 미추적 결과물(HTML, 데이터 파일 등)을 백업에서 원래 위치로 1:1 복원한다.
4. **최종 교차 검증 (Empirical Verification)**: 파일 존재 여부 및 `git worktree list`, `git status` 결과를 검증한 후에만 백업 폴더를 제거한다.

---

## 🚀 Execution Steps

### Step 1: Pre-Execution Inspection & Full Backup

1. 대상 디렉터리(`TARGET_DIR`) 내부 파일 목록 및 파일 개수 확인:
    ```bash
    find {TARGET_DIR} -type f | wc -l
    ```
2. 전체 백업 생성 (1단계 필수 안전장치):
    ```bash
    cp -r {TARGET_DIR} {TARGET_DIR}_backup
    ```

### Step 2: Isolated Branch Construction in `/tmp` (Main Protection)

> [!IMPORTANT]
> 메인 작업영역에서 `git checkout`이나 `git rm`을 직접 실행하면 메인 루트의 미추적 파일이나 인덱스가 오염될 수 있습니다. 반드시 `/tmp/` 임시 공간을 활용합니다.

1. 임시 작업용 워크트리 생성:
    ```bash
    rm -rf /tmp/worktree_builder
    git worktree add --detach /tmp/worktree_builder
    ```
2. `/tmp/worktree_builder`로 이동 후 Orphan 브랜치 초기화:
    ```bash
    cd /tmp/worktree_builder
    git checkout --orphan {BRANCH_NAME}
    git rm -rf .
    ```
3. 백업 디렉터리에서 소스/문서 파일 복사:
    ```bash
    cp -r {TARGET_DIR}_backup/* /tmp/worktree_builder/
    ```
4. 커밋 제외 대상(`EXCLUDE_FROM_COMMIT`) 정리 (`__pycache__`, `*.html` 등 소스 이외의 생성물은 임시 공간에서만 제거하여 백업에 보존시킴).
5. `{BRANCH_NAME}` 브랜치 전용 `.gitignore` 생성:
    ```gitignore
    # dev branch gitignore
    __pycache__/
    *.pyc
    ```
6. 파일 스테이징 및 초기 커밋:
    ```bash
    git add .
    git commit -m "feat: initialize {BRANCH_NAME} branch for development tools and experiments"
    ```
7. 임시 워크트리 해제:
    ```bash
    cd {PROJECT_ROOT}
    git worktree remove --force /tmp/worktree_builder
    ```

### Step 3: Worktree Linking & Directory Swap

1. 기존 원본 디렉터리 삭제 (백업 존재 확인 후 수행):
    ```bash
    rm -rf {TARGET_DIR}
    ```
2. Git worktree 연결:
    ```bash
    git worktree add {TARGET_DIR} {BRANCH_NAME}
    ```

### Step 4: Untracked / Ignored Files Restoration

> [!WARNING]
> Worktree 생성 직후에는 Git에 커밋된 소스코드만 존재합니다. 백업 폴더에 보존된 미추적 결과물(HTML, 데이터 파일 등)을 반드시 원래 위치로 복원해야 합니다.

1. 백업에서 제외 처리된 미추적 파일 및 폴더 구조 복원:
    ```bash
    # 예: HTML 결과물, 데이터 파일 복원
    cp -r {TARGET_DIR}_backup/.../*.html {TARGET_DIR}/.../ 2>/dev/null || true
    ```

### Step 5: Empirical Verification & Cleanup

1. **Worktree 연결 상태 확인**:
    ```bash
    git worktree list
    ```
2. **대상 디렉터리 내 Git Status 및 무시 파일 존재 확인**:
    ```bash
    cd {TARGET_DIR} && git status --ignored
    ```
3. **파일 수 비교 검증**:
    - 소스코드 + 복원된 미추적 파일 개수 확인:
    ```bash
    find {TARGET_DIR} -type f -not -path '*/.git/*' | wc -l
    ```
4. **검증 통과 후 백업 정리**:
    ```bash
    rm -rf {TARGET_DIR}_backup
    ```

---

## 📊 Safety Verification Checklist

- [ ] **메인 미추적 보호**: `/tmp/` 격리 작업으로 메인 루트의 `.agents/`, `.env` 등 미추적 파일 영향 0% 입증
- [ ] **결과물 파일 보존**: 커밋 제외된 HTML/데이터 결과물 파일이 `{TARGET_DIR}`로 100% 복원됨
- [ ] **Worktree 바인딩**: `git worktree list` 출력 결과 `{TARGET_DIR}`가 `{BRANCH_NAME}`으로 올바르게 매핑됨
- [ ] **Clean Status**: `{TARGET_DIR}` 및 메인 루트 모두 unexpected dirty status가 없음
