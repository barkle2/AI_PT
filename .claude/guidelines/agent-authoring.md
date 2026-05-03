# 에이전트 작성 가이드라인

## 메모리 섹션 형식

새 에이전트 프롬프트 파일(`.claude/agents/*.md`)을 작성할 때, `Persistent Agent Memory` 섹션은 **축약 형식**으로만 작성한다. 타입 설명, 예시, How to save 절차 등 보일러플레이트를 포함하지 않는다.

형식 기준 (`.claude/agents/데이터분석가.md` 또는 `예산계장.md` 참고):

```markdown
# Persistent Agent Memory

메모리 디렉토리: `D:\Workspace\AI_PT\.claude\agent-memory\{에이전트명}\`

## 저장 규칙

- **무엇을 저장**: {에이전트 도메인에 특화된 저장 대상 목록}
- **저장하지 않을 것**: 코드·파일 구조, 현재 대화의 임시 상태, CLAUDE.md에 이미 문서화된 내용
- **저장 방법**: 개별 `.md` 파일로 저장 후 `MEMORY.md`에 링크 추가 (frontmatter: `name`, `description`, `type` 필수)
- **타입**: `user` / `feedback` / `project` / `reference`
- **언제 조회**: 작업 시작 시 `MEMORY.md` 인덱스를 먼저 확인. 관련 항목이 있으면 해당 파일만 읽고, 없으면 건너뜀. 사용자가 명시적으로 기억을 요청할 때는 전체 메모리 파일 로드.
```

## YAML 작성 규칙

- 긴 텍스트 문단, `description`, `<example>` 블록은 **파이프(`|`)를 사용한 YAML 멀티라인 문자열** 형식으로 작성한다.
- `\n`, `\"` 같은 이스케이프 문자를 남발하지 않는다.
- `|` 기호 다음 줄부터는 적절한 들여쓰기(Indentation)를 적용한다.
