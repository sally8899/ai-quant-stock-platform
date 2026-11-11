# 云端部署检查清单

## 推荐首发：Streamlit Community Cloud
- 需要用户自己的 GitHub 账号和 Streamlit Community Cloud 登录授权。
- 将项目仓库推送到 GitHub 后，在 Streamlit Community Cloud 创建 App。
- Main file path 填写 `app.py`。
- Python 依赖读取 `requirements.txt`。
- 部署成功后平台会生成一个可分享的 HTTPS 地址，手机和电脑都可访问。

## 安全注意
- 不要在聊天中发送 GitHub 密码、验证码、访问令牌或券商凭据。
- 不要把密钥写入代码或提交到公开仓库。
- 当前项目不需要行情 API 密钥；AKShare 使用公开数据源，但稳定性和延迟不作保证。
- 若以后加入需要密钥的数据供应商，使用部署平台的 Secrets 功能注入环境变量。
- 正式公开给他人使用前，增加登录鉴权、访问限流、日志监控及 HTTPS 配置。

## 目前需要用户完成的动作
1. 登录 GitHub。
2. 创建仓库并上传项目 ZIP 解压后的全部文件。
3. 登录 Streamlit Community Cloud 并授权 GitHub。
4. 选择仓库，主文件填写 `app.py`，点击 Deploy。
5. 将生成的网页地址发回对话，可继续协助检查部署日志和修复问题。
