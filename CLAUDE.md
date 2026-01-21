# 개발 규칙

- 이모지 사용 금지
- 분석 결과 등 출력 콘텐츠는 한국어로 작성
- 커밋 메시지에 Claude 서명 포함하지 않음

# 플러그인 업데이트 절차

## 1. 버전 수정
```
plugins/vulture/.claude-plugin/plugin.json  # "version" 수정
.claude-plugin/marketplace.json              # "version" 동일하게 수정
```

## 2. Git push
```bash
git add -A
git commit -m "chore: vulture 플러그인 버전 X.X.X으로 업데이트"
git push origin main
```

## 3. 플러그인 재설치
```bash
claude plugin uninstall vulture@stock-claude
claude plugin install vulture@stock-claude --scope user
claude plugin list | grep -A 3 vulture  # 버전 확인
```
**참고: 재설치 후 Claude Code를 껐다가 다시 켜야 적용됩니다.**

## 4. 캐시 문제 시
GitHub에는 새 버전이 있지만 구버전이 설치되는 경우:
```bash
# GitHub 버전 확인
curl -s "https://raw.githubusercontent.com/megabytekim/stock-claude/main/plugins/vulture/.claude-plugin/plugin.json" | head -5

# 로컬 디렉토리로 직접 실행
claude --plugin-dir /Users/michael/Desktop/git_repo/stock-claude/plugins/vulture
```
