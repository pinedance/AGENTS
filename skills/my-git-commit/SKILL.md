---
name: my-git-commit
description: >
  변경된 파일들을 내용별로 분석하여 논리적 그룹으로 나누고, 각 그룹마다 적절한 커밋 메시지를 붙여 순차적으로 커밋하는 스킬.
  "git commit 해줘", "커밋해줘", "변경사항 커밋해줘", "commit the changes", "commit 분리해서 해줘" 같은 요청에 반드시 사용한다.
  단순히 git commit을 하라는 요청이 오면 이 스킬을 사용해서 내용별로 나누어 커밋한다.
---

# Git Smart Commit

변경사항을 내용별로 분석해 논리적으로 나누어 커밋한다.
무조건 하나의 `git add -A && git commit`으로 묶지 말 것.

## 프로세스

### 1단계: 현황 파악

```bash
git status --short
git diff --stat
git diff          # 추적 중인 파일 변경사항
git diff --cached # 이미 staged된 파일 변경사항
```

untracked 파일은 `git diff`에 나오지 않으므로 내용을 직접 읽어 파악한다.

### 2단계: 변경사항 분석 및 그룹핑

각 파일의 변경 내용을 파악한 후, **변경의 목적과 영역**을 기준으로 그룹을 나눈다.

**그룹핑 기준**:
- 같은 기능/버그에 속하는 파일들 → 하나의 커밋
- 서로 다른 목적의 변경 → 별도 커밋

**전형적인 분리 패턴**:

| 변경 유형 | prefix | 예시 파일 |
|-----------|--------|-----------|
| 새 기능 추가 | `feat:` | 새 모듈, 새 컴포넌트 |
| 버그 수정 | `fix:` | 로직 오류 수정 |
| 문서 | `docs:` | README.md, 주석, 문서 파일 |
| CI/CD 파이프라인 | `ci:` | `.github/workflows/`, `Dockerfile` |
| 빌드/설정 | `chore:` | `pyproject.toml`, `package.json`, `.gitignore` |
| 리팩터링 | `refactor:` | 기능 변화 없는 코드 구조 변경 |
| 스타일 | `style:` | CSS, 포맷팅 |
| 테스트 | `test:` | 테스트 파일 |

하나의 파일이 여러 목적에 걸쳐있다면 가장 주된 목적으로 분류한다.

### 3단계: 커밋 계획 수립 → 사용자 승인 대기

> **커밋 실행 전 반드시 사용자 승인을 받는다. 승인 없이 절대 커밋하지 말 것.**

계획을 아래 형식으로 보여주고 명시적으로 승인을 요청한다:

```
아래 순서로 커밋하겠습니다. 진행할까요?

커밋 1: ci: schedule/push 트리거 활성화
  → .github/workflows/deploy.yml

커밋 2: feat: Amplify 빌드 설정 및 on_post_build hook 추가
  → amplify.yml, hooks/copy_amplify.py, mkdocs.yml

커밋 3: docs: README 개편
  → README.md
```

사용자가 수정을 요청하면 그룹/메시지를 조정한 뒤 다시 계획을 보여준다.
사용자가 승인하면 4단계로 진행한다.


### 4단계: 순차 커밋 실행

각 그룹별로:

```bash
git add <파일1> <파일2> ...
git commit -m "<prefix>: <제목>

<필요시 본문 — 무엇을, 왜 변경했는지>"
```

**커밋 메시지 규칙**:
- Conventional Commits 형식 사용
- 제목은 50자 이내 권장
- 언어는 프로젝트 언어 따름 (한국어 프로젝트면 한국어 OK)
- 여러 변경사항이 있으면 본문에 bullet로 나열

**실행 후 확인**:

```bash
git log --oneline -5
```

커밋 결과를 사용자에게 요약해서 보여준다.

## 예외 처리

- **변경사항이 없음**: `git status`가 clean이면 "커밋할 변경사항이 없습니다" 안내.
- **이미 staged된 파일이 있음**: staged 상태를 존중하되 사용자에게 알린다.
- **그룹이 1개뿐**: 나눌 필요 없으면 단일 커밋으로 진행 (단, 사용자에게 알림).
- **충돌/미해결 파일**: 커밋 전에 사용자에게 알리고 중단.

## 예시

**상황**: README 수정 + 새 기능 파일 + CI 설정 변경

```
커밋 1: docs: README에 설치 가이드 추가
  → README.md

커밋 2: feat: 사용자 인증 모듈 추가
  → src/auth.py, src/models/user.py

커밋 3: ci: GitHub Actions 배포 워크플로우 추가
  → .github/workflows/deploy.yml
```
