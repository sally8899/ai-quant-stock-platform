# 手机 / 电脑网页部署说明

本项目使用 Streamlit，界面会根据屏幕宽度自适应，可在手机和电脑浏览器打开同一个网址。

## 方案A：部署到 Streamlit Community Cloud（适合先试用）
1. 注册 GitHub 账号。
2. 新建一个私有或公开仓库，将本项目全部文件上传。
3. 登录 Streamlit Community Cloud，并授权 GitHub。
4. 选择仓库、分支和主文件 `app.py`。
5. 点击 Deploy。部署成功后会得到一个 `https://...streamlit.app` 网址。
6. 手机和电脑打开同一个网址即可。

注意：免费云服务可能休眠、限流或有资源限制；公开行情源也可能被限流。不要把券商密码、API密钥写进代码或公开仓库。

## 方案B：Docker部署到自己的云服务器
服务器安装 Docker 后，在项目根目录运行：
```bash
docker build -t ai-quant-web .
docker run -d --restart unless-stopped -p 8501:8501 --name ai-quant-web ai-quant-web
```
然后通过 `http://服务器公网IP:8501` 访问。正式使用建议配置域名、HTTPS、访问密码/身份认证、防火墙和日志监控，不建议直接裸露端口到公网。

## 局域网手机预览
电脑和手机连接同一个 Wi-Fi。电脑启动：
```bash
streamlit run app.py --server.address 0.0.0.0
```
在电脑上查看局域网 IP，手机浏览器访问：
`http://电脑局域网IP:8501`

## 当前版本边界
- 这是可部署的响应式网页项目，不代表已经获得公网网址。
- 需要用户或部署服务完成云端发布。
- 目前行情数据依赖公开数据源，可能延迟、限流或中断。
- 评分尚未接入完整财务、行业及资金数据，当前不是完整100分模型。
- 不提供自动实盘下单。
