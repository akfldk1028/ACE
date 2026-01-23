# Scripts

Auto-Claude 빌드, 배포, 유지보수를 위한 유틸리티 스크립트 모음입니다.

## 스크립트 목록

| 스크립트 | 언어 | 설명 |
|----------|------|------|
| `bump-version.js` | Node.js | 버전 범프 (patch/minor/major) |
| `install-backend.js` | Node.js | 백엔드 의존성 설치 |
| `test-backend.js` | Node.js | 백엔드 테스트 실행 |
| `validate-release.js` | Node.js | 릴리스 유효성 검증 |
| `update-readme.py` | Python | README 자동 업데이트 |
| `check_encoding.py` | Python | 파일 인코딩 검사 |
| `cleanup-version-branches.sh` | Bash | 버전 브랜치 정리 |
| `ai-pr-reviewer.md` | Markdown | AI PR 리뷰어 가이드 |

## 주요 스크립트

### bump-version.js

버전을 자동으로 증가시킵니다.

```bash
# 패치 버전 (2.8.0 -> 2.8.1)
node scripts/bump-version.js patch

# 마이너 버전 (2.8.0 -> 2.9.0)
node scripts/bump-version.js minor

# 메이저 버전 (2.8.0 -> 3.0.0)
node scripts/bump-version.js major
```

### install-backend.js

백엔드 Python 환경을 설정합니다.

```bash
node scripts/install-backend.js
```

수행 작업:
- Python 가상환경 생성 (.venv)
- requirements.txt 의존성 설치
- 테스트 의존성 설치 (선택적)

### test-backend.js

백엔드 테스트를 실행합니다.

```bash
node scripts/test-backend.js
```

### validate-release.js

릴리스 전 검증을 수행합니다.

```bash
node scripts/validate-release.js
```

검증 항목:
- 버전 일관성
- 빌드 성공 여부
- 테스트 통과 여부
- 보안 취약점 검사

### update-readme.py

README 파일을 자동 업데이트합니다.

```bash
python scripts/update-readme.py
```

### check_encoding.py

소스 파일의 인코딩을 검사합니다.

```bash
python scripts/check_encoding.py
```

Windows 환경에서 UTF-8 인코딩 문제를 감지합니다.

### cleanup-version-branches.sh

오래된 버전 브랜치를 정리합니다.

```bash
bash scripts/cleanup-version-branches.sh
```

## 릴리스 워크플로우

1. **버전 범프**
   ```bash
   node scripts/bump-version.js patch
   ```

2. **검증**
   ```bash
   node scripts/validate-release.js
   ```

3. **PR 생성**
   ```bash
   git push origin your-branch
   gh pr create --base main
   ```

4. **GitHub Actions가 자동으로:**
   - 태그 생성
   - 모든 플랫폼 빌드
   - 릴리스 생성

## npm 스크립트 연동

루트 `package.json`에서 호출 가능:

```bash
npm run install:all    # 전체 설치
npm run test:backend   # 백엔드 테스트
```

## 관련 문서

- [RELEASE.md](../RELEASE.md) - 릴리스 프로세스 문서
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 기여 가이드
