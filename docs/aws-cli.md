# AWS CLI 설정

IAM Identity Center(SSO)를 사용하여 시크릿 키 없이 AWS CLI를 인증합니다.

## 프로필

| 프로필 | 역할 | 용도 |
|--------|------|------|
| `default` | - | 기본 region/output 설정 (`ap-northeast-2`, `json`) |
| `work` | AdministratorAccess | 업무용 SSO 프로필 (`ALA` 세션 사용) |

`default`는 region/output 같은 공통 기본값만 갖고, 실제 SSO 인증은 `work` 프로필에서 수행한다.

## SSO 세션

`work` 프로필은 `ALA` SSO 세션을 참조한다. SSO 세션은 여러 프로필이 공유할 수 있는 로그인 설정 묶음이다.

| 세션 | 설정 | 값 |
|------|------|------|
| `ALA` | `sso_start_url` | AWS access portal URL (IAM Identity Center → 설정에서 확인) |
| `ALA` | `sso_region` | `ap-northeast-2` |
| `ALA` | `sso_registration_scopes` | `sso:account:access` |

`work` 프로필은 이 세션을 `sso_session = ALA`로 참조하며, `sso_account_id`(IAM Identity Center에서 확인)와 `sso_role_name = AdministratorAccess`를 지정한다.

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
