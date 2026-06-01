# AGENTS

AI agent skills & prompts 모음집. Claude Code, Gemini CLI 등 AI agent CLI 도구에서 바로 쓸 수 있는 skill을 관리합니다.

---

## Quick Start

### 1. Skills 설치 (npx skills)

```bash
# 이 저장소의 모든 skill 설치
npx skills add pinedance/AGENTS

# 특정 skill만 설치
npx skills add pinedance/AGENTS --skill caveman
npx skills add pinedance/AGENTS --skill feature-planner --skill systematic-debugging

# 설치 가능한 skill 목록 확인
npx skills add pinedance/AGENTS --list
```

### 2. Skills 관리

```bash
# 설치된 skill 목록 확인
npx skills list

# skill 업데이트
npx skills update

# skill 제거
npx skills remove caveman
```

### 3. `~/.agents/skills`에 symlink 연결

이 저장소의 `skills/` 디렉토리를 `~/.agents/skills`에 symlink로 연결하면 모든 프로젝트에서 공통으로 사용할 수 있습니다.

```bash
# ~/.agents 디렉토리 생성 (없는 경우)
mkdir -p ~/.agents

# skills 디렉토리를 통째로 symlink
ln -s "$(pwd)/skills" ~/.agents/skills

# 연결 확인
ls -la ~/.agents/skills
```

> 이미 `~/.agents/skills`가 존재하면 먼저 제거하거나 다른 이름으로 백업하세요.

### 4. AI CLI에 프롬프트 연결

`prompts/agents.md`를 각 CLI 설정 파일에 symlink로 연결합니다.

```bash
# 현재 프로젝트에 연결
cd /your/project
ln -s "/path/to/AGENTS/prompts/agents.md" CLAUDE.md   # Claude Code
ln -s "/path/to/AGENTS/prompts/agents.md" GEMINI.md   # Gemini CLI
```



---

## 상세 설명

### 디렉토리 구조

```
AGENTS/
├── skills/              # AI agent skills (SKILL.md 기반)
│   ├── caveman/         # 토큰 절약 응답 압축 모드
│   ├── feature-planner/ # 기능 기획 및 계획 수립
│   ├── systematic-debugging/
│   └── ...
├── prompts/             # AI CLI 공통 지침
│   └── agents.md         # CLAUDE.md / GEMINI.md 공용 프롬프트
└── anythingllm-skills/  # AnythingLLM 전용 skills
```

### Skills 목록

| Skill | 설명 |
|-------|------|
| `brainstorming` | 아이디어 발산 및 브레인스토밍 진행 |
| `cavecrew` | 다중 역할 caveman 팀 시뮬레이션 |
| `caveman` | 토큰을 ~65–75% 절약하는 압축 응답 모드 |
| `caveman-commit` | caveman 스타일 git commit 메시지 생성 |
| `caveman-compress` | 기존 텍스트를 caveman 스타일로 압축 |
| `caveman-help` | caveman 모드 사용법 안내 |
| `caveman-review` | caveman 스타일 코드 리뷰 |
| `caveman-stats` | 토큰 절약량 통계 |
| `dispatching-parallel-agents` | 병렬 subagent 분기 및 조율 |
| `executing-plans` | 계획 문서를 단계별로 실행 |
| `feature-planner` | 기능 단위 개발 계획 수립 |
| `find-skills` | 적합한 skill 탐색 및 추천 |
| `finishing-a-development-branch` | 개발 브랜치 마무리 체크리스트 |
| `karpathy-guidelines` | Karpathy 스타일 코딩 원칙 적용 |
| `microsoft-foundry` | Microsoft Foundry 개발 가이드라인 |
| `receiving-code-review` | 코드 리뷰 피드백 수용 절차 |
| `requesting-code-review` | 코드 리뷰 요청 및 준비 |
| `skill-creator` | 새 SKILL.md 작성 가이드 |
| `subagent-driven-development` | Subagent 기반 개발 워크플로우 |
| `systematic-debugging` | 체계적 디버깅 절차 |
| `test-driven-development` | TDD 워크플로우 |
| `understand` | 코드베이스 전반 이해 |
| `understand-chat` | 대화 기록 분석 및 이해 |
| `understand-dashboard` | 대시보드 구조 파악 |
| `understand-diff` | diff/변경사항 분석 |
| `understand-domain` | 도메인 지식 정리 |
| `understand-explain` | 코드·개념 설명 생성 |
| `understand-knowledge` | 지식 베이스 구성 |
| `understand-onboard` | 신규 개발자 온보딩 가이드 생성 |
| `using-git-worktrees` | git worktree 활용 워크플로우 |
| `using-superpowers` | agent 고급 기능 활용 |
| `verification-before-completion` | 완료 전 검증 체크리스트 |
| `writing-plans` | 구현 계획서 작성 |
| `writing-skills` | SKILL.md 파일 작성법 |

### `npx skills` 주요 옵션

```bash
npx skills add pinedance/AGENTS [옵션]
```

| 옵션 | 설명 |
|------|------|
| `--list` | 설치 없이 사용 가능한 skill 목록만 출력 |
| `--skill <name>` | 특정 skill만 선택 설치 |
| `--all` | 모든 skill을 모든 agent에 설치 |
| `-g, --global` | 프로젝트 디렉토리 대신 사용자 홈에 설치 |
| `-a, --agent <name>` | 특정 agent에만 설치 (예: `claude-code`, `opencode`) |
| `-y, --yes` | 확인 프롬프트 없이 자동 설치 |

### `prompts/agents.md` — 공통 작업 원칙

Claude Code(`CLAUDE.md`) 및 Gemini CLI(`GEMINI.md`)에서 공유하는 작업 원칙을 정의합니다.

- **작업 순서**: 원인 파악 → 계획 수립(confirm) → 코드 수정(confirm)
- **코드 스타일**: Fail Fast, 재사용성 우선, package 활용
- **코드 수정 규칙**: 항상 코드를 새로 읽고 작업, 기존 주석 및 의도 보존
- **대화 규칙**: 불필요한 칭찬 금지, 더 나은 대안 적극 제안
- **테스트/문서**: `.dev/` 폴더에 저장

### Skill 구조

각 skill 디렉토리는 다음 파일을 포함합니다:

```
skills/<skill-name>/
├── SKILL.md     # LLM이 읽는 핵심 지침 (필수)
└── README.md    # 사람이 읽는 사용법 설명 (권장)
```

새 skill을 만들려면:

```bash
npx skills init my-skill-name
```

또는 `skills/writing-skills` skill을 참고하세요.

## REF

[vercel-labs/skills](https://github.com/vercel-labs/skills)