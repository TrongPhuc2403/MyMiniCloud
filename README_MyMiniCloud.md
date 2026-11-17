# MyMiniCloud

Đồ án mô phỏng hạ tầng đám mây với **9 loại server, 13 Docker Compose services**, triển khai trên Windows Local và AWS EC2. Công nghệ: Nginx, Flask, MariaDB, Keycloak, MinIO, BIND9, Prometheus, Node Exporter và Grafana.

Repository: [TrongPhuc2403/MyMiniCloud](https://github.com/TrongPhuc2403/MyMiniCloud) · Nhánh dashboard mới: `feature/cloud-dashboard-demo-20261117`.

Kịch bản trình diễn 9 server và 10 yêu cầu mở rộng: [DEMO_GUIDE.md](DEMO_GUIDE.md).

## 1. Khởi chạy Local — Windows

**Chuẩn bị:** Git, Docker Desktop đang chạy **Linux containers**. Dừng Apache trong XAMPP nếu đang chiếm cổng **80**. Không cần cài Flask, npm hoặc database riêng trên Windows.

Mở **PowerShell**:

```powershell
# Bỏ qua clone nếu đã có dự án.
git clone -b feature/cloud-dashboard-demo-20261117 https://github.com/TrongPhuc2403/MyMiniCloud.git
cd MyMiniCloud

# Chỉ tạo .env khi chưa có để giữ cấu hình hiện tại.
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
```

Kiểm tra `.env`, sau đó khởi chạy:

```powershell
docker info
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

Chờ các dịch vụ khởi động. Kỳ vọng **12 container Up**, riêng job `minio-init` hoàn tất sẽ **Exited (0)**.

Mở **[http://localhost/](http://localhost/)** để dùng dashboard qua Gateway. Cổng `8080` chỉ phục vụ Web Server chính, không có proxy API.

Kiểm tra nhanh:

```powershell
curl.exe -I http://localhost/
curl.exe -I http://localhost/blog/
curl.exe -i http://localhost/api/hello
curl.exe -i http://localhost/student/
curl.exe -i http://localhost/api/secure
```

Web/Blog/Hello/Student cần trả **200**; Secure API thiếu Bearer Token trả **401**.

## 2. Khởi chạy AWS EC2 — Ubuntu

**Chuẩn bị:** EC2 Ubuntu có Git, Docker Engine và Docker Compose plugin; SSH key `.pem`. Security Group cho phép **TCP 22 từ IP quản trị**, **TCP 80** để truy cập website. Mạng Docker dùng `172.19.0.0/16`, cần tránh trùng mạng hiện có.

Public IPv4 hiện tại: **54.169.9.254**. Cập nhật các địa chỉ bên dưới nếu IP thay đổi sau Stop/Start.

### Kết nối từ PowerShell Windows

Thay đường dẫn SSH key nếu tên/vị trí file của bạn khác:

```powershell
ssh -i "$env:USERPROFILE\Downloads\myminicloud-final-key.pem" ubuntu@54.169.9.254
```

### Chạy trong phiên SSH trên EC2

```bash
docker --version
docker compose version
docker info

# Bỏ qua clone nếu đã có dự án đúng phiên bản.
git clone -b feature/cloud-dashboard-demo-20261117 https://github.com/TrongPhuc2403/MyMiniCloud.git
cd MyMiniCloud
test -f .env || cp .env.example .env
chmod 600 .env
nano .env
```

Điền cấu hình môi trường và đổi mật khẩu demo trước khi cho truy cập công khai. Sau đó:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps -a

# Kiểm tra ngay trên EC2.
curl -I http://localhost/
curl -I http://localhost/blog/
curl -i http://localhost/api/hello
curl -i http://localhost/student/
```

Trên máy cá nhân, mở **[http://54.169.9.254/](http://54.169.9.254/)**. `localhost` trong phiên SSH là EC2; `localhost` trên Windows là máy Windows.

Để kiểm tra đường truy cập public từ **PowerShell Windows**:

```powershell
curl.exe --max-time 15 -I http://54.169.9.254/
curl.exe --max-time 15 -I http://54.169.9.254/blog/
curl.exe --max-time 15 -i http://54.169.9.254/api/hello
curl.exe --max-time 15 -i http://54.169.9.254/student/
```

## 3. Địa chỉ truy cập

Các console EC2 cần cổng tương ứng được cho phép từ IP quản trị hoặc truy cập qua SSH tunnel; không mặc định mở công khai tất cả cổng.

| Chức năng | Local | EC2 |
| --- | --- | --- |
| Dashboard / Gateway | [localhost](http://localhost/) | [54.169.9.254](http://54.169.9.254/) |
| Blog — ba bài viết | [/blog/](http://localhost/blog/) | [/blog/](http://54.169.9.254/blog/) |
| Hello API | [/api/hello](http://localhost/api/hello) | [/api/hello](http://54.169.9.254/api/hello) |
| Student JSON | [/student/](http://localhost/student/) | [/student/](http://54.169.9.254/student/) |
| Secure API | [/api/secure](http://localhost/api/secure) | [/api/secure](http://54.169.9.254/api/secure) |
| Keycloak Admin | [:8081/admin/](http://localhost:8081/admin/) | [:8081/admin/](http://54.169.9.254:8081/admin/) |
| MinIO Console | [:9001](http://localhost:9001/) | [:9001](http://54.169.9.254:9001/) |
| Prometheus Targets | [:9090/targets](http://localhost:9090/targets) | [:9090/targets](http://54.169.9.254:9090/targets) |
| Grafana Dashboard | [CPU / RAM / Network](http://localhost:3000/d/system-health-52400138) | [CPU / RAM / Network](http://54.169.9.254:3000/d/system-health-52400138) |
| Node Exporter | [:9100/metrics](http://localhost:9100/metrics) | [:9100/metrics](http://54.169.9.254:9100/metrics) |

Ví dụ dùng SSH tunnel để mở Grafana EC2 mà không mở cổng 3000 trong Security Group. Chạy trên Windows và giữ cửa sổ SSH mở:

```powershell
ssh -i "$env:USERPROFILE\Downloads\myminicloud-final-key.pem" -N -L 13000:127.0.0.1:3000 ubuntu@54.169.9.254
```

Mở [http://localhost:13000/](http://localhost:13000/) để vào Grafana **trên EC2**.

## 4. Chạy lại, cập nhật và xử lý lỗi

Chạy tại thư mục dự án trên Local hoặc EC2:

```bash
docker compose stop                       # Dừng, giữ dữ liệu
docker compose up -d                      # Chạy lại
docker compose up -d --build              # Build và chạy sau khi sửa source
docker compose logs --tail=80             # Xem log
```

**Không dùng `docker compose down -v` nếu cần giữ dữ liệu MariaDB, Keycloak và MinIO.** Không đưa `.env` hoặc SSH key lên Git.

| Lỗi | Cách kiểm tra |
| --- | --- |
| Docker không kết nối được | Mở Docker Desktop trên Windows; kiểm tra Docker Engine trên EC2 |
| `localhost` vào XAMPP, Gateway `Created` | Dừng Apache, chạy `docker compose up -d --no-deps api-gateway-proxy-server` |
| `Address already in use` | Kiểm tra cổng và `docker network inspect cloud-net`; sau khi giải quyết xung đột, chạy lại riêng service lỗi bằng `--no-deps` |
| EC2 truy cập timeout | Kiểm tra Public IP, Security Group, firewall và container Gateway |
| Dashboard mở được nhưng API 404 | Dùng Gateway cổng 80, không dùng Web Server trực tiếp `:8080` |
| HTTP 502 | Xem log Gateway/backend: `docker compose logs --tail=80 api-gateway-proxy-server application-backend-server` |
| Keycloak Admin 404 | Dùng `:8081/admin/`, không dùng `/admin/` trên Gateway |

**Lưu ý cấu hình:**

- Student API đọc `students.json`, chưa truy vấn MariaDB. Các thẻ tổng quan frontend là dữ liệu cấu hình; metrics thực xem tại Prometheus/Grafana.
- Keycloak realm `realm_52400114`, client `flask-app`; môi trường mới cần tạo user demo. Hướng dẫn JWT đầy đủ ở YC4 trong [DEMO_GUIDE.md](DEMO_GUIDE.md).
- Compose hiện ghi cứng issuer JWT `http://localhost:8081/realms/realm_52400114` và mật khẩu Grafana `admin/admin`; chỉnh riêng `.env` không ghi đè chúng. Token cấp qua Public IP có thể không khớp issuer. Các mật khẩu khác xem `.env`/Compose.
- Khi dùng hostname/HTTPS riêng, cập nhật URL console tại `web-frontend-server/html/assets/config.js`, đồng bộ rồi build lại cả ba frontend.

Nếu chỉnh giao diện, dùng Python 3 và Node.js trên host để đồng bộ/kiểm tra trước khi build:

```bash
python scripts/sync_frontends.py
python scripts/verify_frontend.py
node scripts/test_frontend.cjs
```

Nguồn chuẩn: `web-frontend-server/html/assets/`; nội dung dashboard sinh từ `scripts/build_dashboard.py`. Sau khi sửa bộ sinh, chạy `python scripts/build_dashboard.py` rồi đồng bộ. Các bản assets ở hai Web Node cần được giữ để Docker build độc lập.
