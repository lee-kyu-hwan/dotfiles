# AWS CLI 설정

IAM Identity Center(SSO)를 사용하여 시크릿 키 없이 AWS CLI를 인증합니다.

## 프로필

| 프로필 | 역할 | 용도 |
|--------|------|------|
| `work` | AdministratorAccess | 업무용 기본 프로필 |

## 사용법

```bash
# SSO 로그인 (세션 만료 시)
aws sso login --profile work

# 명령 실행
aws s3 ls --profile work

# 매번 --profile 생략하려면
export AWS_PROFILE=work
```

## 세션 만료

SSO 세션은 일정 시간 후 만료됩니다. 만료되면 다시 `aws sso login --profile work`를 실행하세요.

## 파일 구조

| 파일 | chezmoi 관리 | 설명 |
|------|:---:|------|
| `~/.aws/config` | O | SSO 프로필 설정 |
| `~/.aws/credentials` | X | 사용하지 않음 (SSO로 대체) |
| `~/.aws/sso/cache/` | X | SSO 토큰 캐시 (자동 생성) |

## 초기 설정

새 머신에서 SSO를 처음 설정하는 경우:

```bash
aws configure sso
```

- SSO start URL: AWS access portal URL (IAM Identity Center → 설정에서 확인)
- SSO region: `ap-northeast-2`
