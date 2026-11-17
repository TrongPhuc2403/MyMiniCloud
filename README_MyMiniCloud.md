# MyMiniCloud — Hệ thống mô phỏng hạ tầng đám mây thu nhỏ

> Đồ án cuối kỳ môn Điện toán đám mây (Cloud Computing). Triển khai bằng Docker Compose trên máy local và AWS EC2 Ubuntu.
>
> **Nhánh tích hợp:** `feature/final-integration` · **Bản EC2 đã được ghi nhận trước đây:** `e747d90`. Kết quả lịch sử không thay thế kiểm thử phiên bản hiện tại.
>
> **Demo bảo vệ:** [Kịch bản 9 server và 10 yêu cầu mở rộng](DEMO_GUIDE.md).

## 1. Tổng quan

MyMiniCloud tích hợp **9 nhóm máy chủ**, triển khai qua **13 Compose services**: **12 container hoạt động thường trực** và **1 job khởi tạo MinIO (`minio-init`)**. Các dịch vụ giao tiếp qua mạng Docker `cloud-net` (`172.19.0.0/16`).

Các chức năng chính:

- Dashboard HTML/CSS/JavaScript thuần: sidebar, Light/Dark Mode, menu mobile, API Explorer và các khu vực quản lý hạ tầng.
- Ba bài blog đầy đủ nội dung/minh họa; hai Web Node dùng giao diện đồng bộ, phân biệt bằng nhãn Node 1/Node 2 và được Nginx cân bằng tải Round Robin.
- Flask REST API: `/hello`, `/student`, `/secure` (JWT do Keycloak cấp).
- MariaDB với hai database `minicloud` và `studentdb`.
- Keycloak OIDC, realm `realm_52400114`, client `flask-app`.
- MinIO S3-compatible Object Storage, tự khởi tạo ba bucket; tải hai file mẫu khi file được mount và object chưa có.
- BIND9 phân giải các tên miền nội bộ `cloud.local`.
- Prometheus + Node Exporter và Grafana Dashboard (CPU, RAM, Network).

**Phạm vi dữ liệu:** Student API đọc `application-backend-server/students.json`, **chưa truy vấn MariaDB**. Bốn thẻ 9/13/3/2 trên frontend là **Static Configuration**. Badge backend kiểm tra `/api/hello`; các dịch vụ chưa được kiểm tra ghi **Not Monitored**. Metrics thật xem tại Prometheus/Grafana.

### 9 loại server

| Loại server | Công nghệ | Vai trò |
| --- | --- | --- |
| Web Server | Nginx | Dashboard và Blog |
| Application Server | Flask | REST API, xác minh JWT |
| Database Server | MariaDB | Database `minicloud`, `studentdb` |
| Authentication Server | Keycloak | Realm, client và cấp token |
| Object Storage Server | MinIO | Bucket và object; job `minio-init` khởi tạo |
| Internal DNS Server | BIND9 | Phân giải zone `cloud.local` |
| Monitoring Server | Prometheus, Node Exporter | Thu thập metrics |
| Visualization Server | Grafana | Dashboard CPU, RAM, Network |
| API Gateway / Load Balancer | Nginx | Reverse proxy và Round Robin |

10 yêu cầu mở rộng gồm: Website/Blog, JSON API, database sinh viên, JWT, object storage, DNS, giám sát Web, dashboard tài nguyên, reverse proxy và load balancing. Các bước trình diễn, kết quả mong đợi và checklist minh chứng nằm trong [DEMO_GUIDE.md](DEMO_GUIDE.md).

### Thành viên

| Thành viên        | Nhiệm vụ                                                        |
| ----------------- | --------------------------------------------------------------- |
| Nguyễn Trọng Phúc | Web Frontend, Flask Backend, MariaDB, tích hợp và báo cáo       |
| Lê Khải Hoàn      | Keycloak, MinIO, BIND9 DNS                                      |
| Trần Hữu Long     | Prometheus, Node Exporter, Grafana, Nginx Gateway/Load Balancer |

### Cấu trúc mã nguồn

```text
MyMiniCloud/
├── docker-compose.yml                  # Toàn bộ hệ thống
├── docker-compose.phuc.yml             # Compose phần Phúc
├── docker-compose.hoan.yml             # Compose phần Hoàn
├── docker-compose.long.yml             # Compose phần Long
├── .env.example
├── README_MyMiniCloud.md               # Cài đặt, vận hành và cập nhật
├── DEMO_GUIDE.md                       # Kịch bản demo 9 server / 10 yêu cầu
├── scripts/                           # Sinh, đồng bộ và kiểm tra frontend
├── web-frontend-server/                # html/index.html, assets/, blog/
├── web-frontend-server1/
├── web-frontend-server2/
├── application-backend-server/
├── relational-database-server/init/
├── authentication-identity-server/realm-export.json
├── object-storage-server/
├── internal-dns-server/
├── monitoring-prometheus-server/
├── monitoring-grafana-dashboard-server/
└── api-gateway-proxy-server/nginx.conf
```

## 2. Yêu cầu trước khi cài đặt

**Local (Windows):** Docker Desktop (Linux containers, Docker Compose v2+), Git, PowerShell, RAM khả dụng nên từ 8 GiB, các cổng cần thiết chưa bị phần mềm khác chiếm.

Python 3 và Node.js chỉ cần khi chạy công cụ sinh/kiểm tra frontend trên host; **không cần npm install hoặc cài Flask trên Windows** để khởi chạy bằng Docker.

**AWS EC2:** Instance Ubuntu Server 24.04 LTS (x86_64), Docker Engine và Docker Compose Plugin, Git, SSH key `.pem`. Môi trường đã kiểm thử: **Singapore `ap-southeast-1`**, EC2 **`m7i-flex.large` (2 vCPU, 8 GiB RAM)**, EBS **30 GiB gp3**, Docker **29.9.3**, Compose **v5.7.0**. Tài nguyên và chi phí phụ thuộc cấu hình/credit AWS; không mặc định là miễn phí vĩnh viễn.

> **Chú ý:** `docker-compose.yml` sử dụng IP tĩnh của container trong `172.19.0.0/16`; không dùng nếu dải này trùng mạng LAN/VPN hoặc bridge Docker đang tồn tại.

## 3. Chạy toàn bộ hệ thống trên LOCAL (Windows)

### 3.1. Tải đúng nhánh tích hợp

Mở **PowerShell trên Windows**:

```powershell
git clone -b feature/final-integration https://github.com/TrongPhuc2403/MyMiniCloud.git
cd MyMiniCloud
git branch --show-current
```

Nếu đã clone từ trước:

```powershell
git fetch origin
git switch feature/final-integration
# Chỉ pull khi working tree sạch và muốn cập nhật phiên bản từ GitHub
git pull --ff-only
```

### 3.2. Cấu hình `.env`

```powershell
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
```

Dùng nội dung mẫu của nhóm cho **lab/demo cục bộ**:

```dotenv
KC_ADMIN_PASSWORD=admin
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MARIADB_ROOT_PASSWORD=root
GF_SECURITY_ADMIN_PASSWORD=admin
OIDC_ISSUER=http://localhost:8081/realms/realm_52400114
OIDC_AUDIENCE=flask-app
OIDC_JWKS_URL=http://authentication-identity-server:8080/realms/realm_52400114/protocol/openid-connect/certs
```

**Lưu ý cấu hình thật:** Trong `docker-compose.yml` hiện tại, các biến `OIDC_ISSUER`, `OIDC_AUDIENCE` và `OIDC_JWKS_URL` của Flask được ghi trực tiếp (issuer là `http://localhost:8081/...`); chỉnh riêng `.env` **không** ghi đè các dòng này. `.env.example` có issuer khác, nên cần đọc cấu hình Compose thực tế, không mặc định mọi biến trong `.env` được sử dụng. Grafana trong Compose cũng đang dùng `admin/admin`; biến `GF_SECURITY_ADMIN_PASSWORD` chỉ có tác dụng sau khi Compose được đổi sang tham chiếu biến đó.

`.env` nằm trong `.gitignore`; **không commit file chứa mật khẩu lên GitHub**. Các thông tin đăng nhập trên chỉ dùng cho lab/demo; khi triển khai công khai cần thay bằng mật khẩu mạnh và HTTPS.

### 3.3. Khởi chạy

Mở Docker Desktop, bảo đảm Docker Engine đã hoạt động, sau đó chạy tại thư mục gốc dự án:

**Nếu dùng XAMPP, dừng Apache trước:** Gateway cần cổng 80. Trên máy này từng xác nhận Apache chiếm cổng 80 khiến `localhost` vào XAMPP và Gateway ở trạng thái `Created`.

```powershell
docker --version
docker compose version
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

Nếu máy có lỗi Docker `Address already in use` khi khởi chạy nhiều container IP tĩnh cùng lúc, **không xóa volume**; khởi động riêng từng service bị lỗi rồi chạy lại `docker compose up -d`, ví dụ:

```powershell
docker compose up -d --no-deps authentication-identity-server
docker compose up -d --no-deps internal-dns-server
docker compose up -d --no-deps web-frontend-server2
docker compose up -d --no-deps monitoring-node-exporter-server
docker compose up -d --no-deps monitoring-prometheus-server
docker compose up -d --no-deps monitoring-grafana-dashboard-server
docker compose up -d --no-deps api-gateway-proxy-server
docker compose ps -a
```

**Kỳ vọng:** 12 container ở trạng thái `Up`; `minio-init` là job chạy xong sẽ `Exited (0)`.

Chờ Keycloak khởi động và Prometheus thu thập đủ mẫu. Container `Up` chưa bảo đảm mọi chức năng đã sẵn sàng. Khi gặp `Address already in use`, kiểm tra xung đột cổng trước; chỉ thử khởi động từng service sau khi đã xác định cổng không bị chiếm.

### 3.4. Địa chỉ LOCAL

| Chức năng                    | URL                           |
| ---------------------------- | ----------------------------- |
| Nginx Gateway / cân bằng tải | http://localhost/             |
| Blog                         | http://localhost/blog/        |
| Web chính trực tiếp          | http://localhost:8080/        |
| Flask Hello qua Gateway      | http://localhost/api/hello    |
| Danh sách sinh viên          | http://localhost/student/     |
| Secure API (thiếu token: 401) | http://localhost/api/secure   |
| Flask trực tiếp              | http://localhost:8085/hello   |
| Keycloak Admin (trực tiếp)   | http://localhost:8081/admin/  |
| MinIO Console                | http://localhost:9001/        |
| Prometheus Targets           | http://localhost:9090/targets |
| Grafana                      | http://localhost:3000/        |
| Dashboard đã provisioning    | http://localhost:3000/d/system-health-52400138 |
| Node Exporter                | http://localhost:9100/metrics |

**Lưu ý:** Trong cấu hình hiện tại, link `/auth/` qua Nginx có thể chuyển hướng đến `/admin/` ở Gateway và trả **404**. Khi quản trị Keycloak, hãy dùng trực tiếp cổng `8081/admin/`, không dùng `http://localhost/admin/`.

Dashboard phải được mở qua **Gateway cổng 80** để dùng API và kiểm tra Round Robin. Cổng `8080` là Web Server chính trực tiếp, không có các tuyến proxy API. Khi truy cập từ thiết bị khác, thay `localhost` bằng hostname/IP của máy Docker; lưu ý issuer JWT ở mục 5.6.

### 3.5. Luồng định tuyến

| Tuyến Gateway | Upstream |
| --- | --- |
| `/` và `/assets/*` | `web-frontend-server1:80`, `web-frontend-server2:80` — Round Robin |
| `/blog/` | `web-frontend-server:80/blog/` — máy chủ chính |
| `/api/*` | `application-backend-server:8081/` — bỏ prefix `/api/` |
| `/student`, `/student/` | Flask `/student` |
| `/auth/` | Keycloak cổng 8080; chưa bảo đảm Admin Console redirect đúng |

Các request HTML, CSS, JS và ảnh có thể đến những Web Node khác nhau. Vì vậy assets phải đồng bộ trên cả hai Node. Footer ghi node phục vụ HTML hiện tại; **Inspect request** đọc header từ một request mới, nên hai nhãn có thể khác nhau.

## 4. Chạy hệ thống trên AWS EC2 (Ubuntu 24.04)

### 4.1. Tạo EC2 và cấu hình mạng

1. AWS Console → **EC2 → Launch instances**.
2. Region `ap-southeast-1` (Singapore), Ubuntu Server 24.04 LTS (x86_64).
3. Ví dụ môi trường đã kiểm thử: `m7i-flex.large`, EBS 30 GiB gp3, **Auto-assign public IP: Enable**.
4. Tạo và tải SSH Key Pair, ví dụ `myminicloud-final-key.pem`.
5. Security Group: **TCP 22 từ IP quản trị `/32`**, **TCP 80 từ `0.0.0.0/0`** cho trang web. Chỉ mở các cổng khác khi thực sự cần và đã cấu hình bảo mật.
6. Ghi nhận Public IPv4 hiện tại của EC2. Trong các ví dụ bên dưới, thay `EC2_PUBLIC_IP` bằng địa chỉ đó; IP có thể thay đổi khi Stop/Start nếu không gắn Elastic IP.

**Truy cập SSH trên Windows PowerShell:**

```powershell
ssh -i "$env:USERPROFILE\Downloads\myminicloud-final-key.pem" ubuntu@EC2_PUBLIC_IP
```

Thay IP bằng **Public IPv4 hiện tại** của EC2. Nếu Windows báo `UNPROTECTED PRIVATE KEY FILE`, giới hạn quyền đọc file `.pem` cho tài khoản Windows đang dùng (ví dụ với `icacls`); không chia sẻ khóa riêng.

### 4.2. Cài Docker chính thức trên Ubuntu

**Chạy các lệnh dưới đây trong Terminal Ubuntu**, không phải trong PowerShell của Windows:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF_DOCKER
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF_DOCKER
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo usermod -aG docker ubuntu
newgrp docker
docker --version
docker compose version
docker ps
```

**Chú ý:** Tài khoản thuộc nhóm `docker` có đặc quyền cao gần tương đương root.

### 4.3. Clone nhánh bản hoàn chỉnh

```bash
cd ~
git clone -b feature/final-integration https://github.com/TrongPhuc2403/MyMiniCloud.git
cd ~/MyMiniCloud
git branch --show-current
git log -1 --oneline
```

Trong lần triển khai đã kiểm thử: nhánh `feature/final-integration`, commit `e747d90` (_Complete MyMiniCloud integration and automated service initialization_).

### 4.4. Tạo `.env` trên EC2

```bash
cd ~/MyMiniCloud
cp .env.example .env
chmod 600 .env
```

Có thể dùng các giá trị lab/demo trong **mục 3.2**, với `MINIO_ROOT_PASSWORD=minioadmin123`. Đối với hệ thống công khai, **hãy thay mật khẩu mặc định** và giới hạn quyền truy cập bằng Security Group/HTTPS. Không đưa mật khẩu thật vào README hoặc log gửi cho người khác.

Nếu cần Grafana lấy mật khẩu từ `.env` thay vì hardcode, có thể sửa Compose:

```yaml
GF_SECURITY_ADMIN_PASSWORD: ${GF_SECURITY_ADMIN_PASSWORD:?Set GF_SECURITY_ADMIN_PASSWORD in .env}
```

Thực hiện trong service `monitoring-grafana-dashboard-server` và đảm bảo `.env` có biến tương ứng. **Không cần sửa** nếu chỉ chạy đúng commit gốc với mật khẩu demo mặc định.

> **OIDC trên AWS:** `docker-compose.yml` hiện dùng issuer `http://localhost:8081/realms/realm_52400114` cho Flask. Đây là cấu hình đã được kiểm thử thành công với token xin **ngay trên EC2** qua `localhost:8081`. Nếu phát token từ trình duyệt/hostname công khai khác, phải đồng bộ Keycloak hostname, issuer, reverse proxy và HTTPS; không chỉ sửa `.env`.

### 4.5. Build và chạy container

```bash
cd ~/MyMiniCloud
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

Trên EC2 đã gặp lỗi `failed to set up container networking: Address already in use` khi tạo nhiều container IP tĩnh đồng thời. Giải pháp đã áp dụng thành công là chạy **từng service còn ở trạng thái Created**:

```bash
docker compose up -d --no-deps authentication-identity-server
docker compose up -d --no-deps internal-dns-server
docker compose up -d --no-deps web-frontend-server2
docker compose up -d --no-deps monitoring-node-exporter-server
docker compose up -d --no-deps monitoring-prometheus-server
docker compose up -d --no-deps monitoring-grafana-dashboard-server
docker compose up -d --no-deps api-gateway-proxy-server
docker compose up -d
docker compose ps -a
```

Chỉ chạy các service cần thiết nếu chúng chưa `Up`; **dừng để chẩn đoán nếu còn lỗi**. Không dùng `docker compose down -v` khi muốn giữ dữ liệu.

### 4.6. Địa chỉ truy cập EC2

Thay `EC2_PUBLIC_IP` bằng **Public IPv4 hiện tại** nếu đã đổi:

| Dịch vụ            | URL trên EC2                     | Ghi chú                                             |
| ------------------ | -------------------------------- | --------------------------------------------------- |
| Website Nginx      | http://EC2_PUBLIC_IP/             | TCP 80                                              |
| Blog               | http://EC2_PUBLIC_IP/blog/        | Qua Nginx                                           |
| Flask API          | http://EC2_PUBLIC_IP/api/hello    | Qua Nginx TCP 80                                    |
| Student JSON       | http://EC2_PUBLIC_IP/student/     | Qua Nginx TCP 80                                    |
| Web chính          | http://EC2_PUBLIC_IP:8080/        | Cần TCP 8080 được phép                              |
| Keycloak Admin     | http://EC2_PUBLIC_IP:8081/admin/  | Cần TCP 8081; **không dùng `/admin/` trên port 80** |
| MinIO Console      | http://EC2_PUBLIC_IP:9001/        | Cần TCP 9001                                        |
| Prometheus Targets | http://EC2_PUBLIC_IP:9090/targets | Cần TCP 9090                                        |
| Grafana Dashboard  | http://EC2_PUBLIC_IP:3000/        | Cần TCP 3000                                        |
| Flask trực tiếp    | http://EC2_PUBLIC_IP:8085/hello   | Cần TCP 8085                                        |

**An toàn mạng:** Chỉ công khai cổng website `80` (và sau này `443` với HTTPS) là lựa chọn khuyến nghị. Với Keycloak, MinIO, Grafana, Prometheus hãy sử dụng SSH tunnel hoặc hạn chế Security Group theo IP quản trị; **không để `0.0.0.0/0` cùng mật khẩu mặc định**. MariaDB đang bind `127.0.0.1:3307` và không thể truy cập bên ngoài chỉ bằng cách mở Security Group. Prometheus Targets hiển thị tên container hoặc `localhost`; đó là các endpoint **nội bộ Docker**, không mở được trực tiếp từ trình duyệt Windows và không cần sửa.

**SSH Tunnel cho Grafana**, chạy từ **PowerShell Windows**:

```powershell
ssh -i "$env:USERPROFILE\Downloads\myminicloud-final-key.pem" -N -L 3000:127.0.0.1:3000 ubuntu@EC2_PUBLIC_IP
```

Sau đó mở `http://localhost:3000/` trên Windows. Tương tự, đổi `3000` thành `8081` để truy cập Keycloak qua tunnel.

## 5. Kiểm thử hệ thống (Local và EC2)

Các lệnh `curl` dưới đây chạy trên **EC2 Ubuntu** (dùng `localhost` vì đang chạy trên chính host EC2); trên Windows dùng `curl.exe` thay cho `curl` nếu PowerShell alias gây nhầm lẫn.

### 5.1. Website, Backend và Round Robin

```bash
curl -I http://localhost/
curl -I http://localhost/blog/
curl -i http://localhost/api/hello
curl -i http://localhost/student/
for i in $(seq 1 6); do curl -sI http://localhost/ | grep -i X-Upstream-Addr; done
```

Kỳ vọng theo cấu hình / ghi nhận lịch sử: website và blog HTTP 200, `/api/hello` trả `{"message":"Hello from App Server!"}`, `/student/` trả JSON 5 sinh viên. Round Robin phân phối 3 lượt tới `172.19.0.8:80` và 3 lượt tới `172.19.0.9:80` trên 6 yêu cầu.

### 5.2. MariaDB

```bash
docker compose exec relational-database-server mariadb -u root -p
```

Nhập mật khẩu hiện tại khi được hỏi, rồi chạy trong MariaDB CLI:

```sql
SHOW DATABASES;
SHOW TABLES FROM minicloud;
SHOW TABLES FROM studentdb;
SELECT * FROM studentdb.students;
exit;
```

Kỳ vọng theo SQL khởi tạo: `minicloud.notes`, `studentdb.students` và 3 sinh viên `SV001`, `SV002`, `SV003`. Volume đã có dữ liệu có thể khác; không xóa volume để chạy lại init.

### 5.3. MinIO

```bash
docker compose logs --tail=50 minio-init
```

Kỳ vọng theo cấu hình / ghi nhận lịch sử: các bucket `demo`, `profile-pics`, `documents`, file `profile-pics/avatar.jpg`, `documents/report.pdf`. Job `minio-init` kết thúc `Exited (0)` là bình thường; chạy lại giữ nguyên object đã có.

### 5.4. BIND9 DNS nội bộ

```bash
docker exec internal-dns-server named-checkzone cloud.local /etc/bind/db.cloud.local
docker run --rm --network cloud-net busybox nslookup app.cloud.local 172.19.0.5
docker run --rm --network cloud-net busybox nslookup web.cloud.local 172.19.0.5
```

Kỳ vọng theo cấu hình / ghi nhận lịch sử: `app.cloud.local → 172.19.0.4`, `web.cloud.local → 172.19.0.6`. Cảnh báo `file does not end with newline` không làm zone thất bại nếu `named-checkzone` in `OK`.

### 5.5. Prometheus và Grafana

```bash
curl -s -o /dev/null -w 'Prometheus: HTTP %{http_code}\n' http://localhost:9090/-/ready
curl -s -o /dev/null -w 'Grafana: HTTP %{http_code}\n' http://localhost:3000/api/health
curl -s http://localhost:9090/api/v1/targets | python3 -c 'import json,sys; d=json.load(sys.stdin); [print(t["labels"].get("job"),t["health"],t["scrapeUrl"]) for t in d["data"]["activeTargets"]]'
```

Kỳ vọng theo cấu hình / ghi nhận lịch sử: Prometheus và Grafana HTTP 200, **5/5 targets UP** (`node`, `prometheus`, 3 `web`). Grafana hiển thị ba biểu đồ CPU, RAM, Network; cần xác nhận các panel có dữ liệu, không chỉ xuất hiện khung biểu đồ.

### 5.6. Keycloak, JWT và Flask `/secure`

Kiểm tra endpoint OIDC:

```bash
curl -s -o /dev/null -w 'Keycloak: HTTP %{http_code}\n' http://localhost:8081/realms/realm_52400114/.well-known/openid-configuration
```

**Quan trọng:** File `realm-export.json` hiện **không chứa user** (`users: []`), nên khi triển khai máy mới phải tạo user test `sv01` riêng trong Keycloak. Trên EC2 đã tạo `sv01` và cập nhật email, họ tên, `emailVerified` để giải quyết lỗi `Account is not fully set up`.

Tạo/kiểm tra user qua Keycloak Admin, điền profile và xử lý Required Actions. Chọn realm `realm_52400114`, client `flask-app`; không dùng tài khoản admin để xin token ứng dụng.

Kiểm thử không có token:

```bash
curl -i http://localhost/api/secure
```

Kỳ vọng HTTP 401 với `Missing Bearer token`. Các bước tạo user và block PowerShell xin JWT mà không in token/mật khẩu nằm tại **YC4 trong [DEMO_GUIDE.md](DEMO_GUIDE.md)**. JWT hợp lệ phải trả HTTP 200 với `Secure resource OK` và `preferred_username` tương ứng. Không dùng 401 đơn lẻ để kết luận luồng xác thực hoàn chỉnh đã đạt.

Trên EC2, xin token ngay tại host qua `localhost:8081` nếu giữ nguyên issuer. Khi dùng hostname công khai phải thống nhất issuer/Keycloak/proxy; không tắt xác minh JWT. Không lưu token trong log, Git hoặc ảnh minh chứng.

> Password Grant (`directAccessGrantsEnabled=true`) và Keycloak `start-dev` chỉ phục vụ demo. Keycloak Admin dùng cổng `8081/admin/`, không phải `/admin/` trên Gateway cổng 80.

## 6. Quản lý, cập nhật và xử lý sự cố

### 6.1. Lệnh quản trị

```bash
docker compose ps -a
docker compose logs --tail=80
docker compose logs --tail=80 authentication-identity-server
docker compose logs --tail=80 minio-init
docker network inspect cloud-net
docker stats --no-stream
df -h /
```

**Dừng, giữ dữ liệu:**

```bash
docker compose stop
```

**Chạy lại:**

```bash
docker compose up -d
```

**Cảnh báo:** `docker compose down -v` sẽ xóa Docker volumes (MariaDB, Keycloak, MinIO); **không sử dụng khi muốn giữ dữ liệu**.

### 6.2. Cập nhật source và deploy lại trên EC2

```bash
cd ~/MyMiniCloud
git status
git branch --show-current
# Chỉ thực hiện khi không có thay đổi local cần giữ:
git pull --ff-only origin feature/final-integration
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

Nếu đã sửa `docker-compose.yml` trên EC2 (ví dụ thay biến môi trường Grafana), `git pull` có thể bị chặn vì thay đổi local. **Sao lưu, đối chiếu và quyết định giữ/chuyển các sửa đổi trước khi pull**; không dùng `git reset --hard` tùy tiện.

### 6.3. Lỗi thường gặp

| Triệu chứng                                                     | Nguyên nhân thường gặp / cách xử lý                                                                                                                       |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `localhost` trả Apache/XAMPP; Gateway vẫn `Created` | Dừng Apache trong XAMPP để giải phóng cổng 80; chạy `docker compose up -d --no-deps api-gateway-proxy-server` |
| Dashboard mở được nhưng API 404 | Truy cập Gateway cổng 80; `:8080` hoặc Python preview không có proxy API |
| Ảnh bìa SVG lỗi dù HTTP 200 | Kiểm tra XML bằng `python scripts/verify_frontend.py`; ký tự `&` trong text SVG phải escape thành `&amp;`; sinh lại và đồng bộ trước khi build |
| Docker báo `Address already in use` khi tạo mạng                | Một số service IP tĩnh khởi chạy đồng thời; kiểm tra `docker network inspect cloud-net`, thử `docker compose up -d --no-deps <service>` theo từng service |
| `localhost/admin/` trả 404                                      | Nginx port 80 không có route `/admin/`; Keycloak trực tiếp dùng `:8081/admin/`                                                                            |
| Prometheus Targets `UP` nhưng nhấp endpoint không mở từ Windows | Endpoint `localhost`/tên container nằm trong Docker; trình duyệt Windows không thuộc `cloud-net`                                                          |
| `Account is not fully set up` khi xin Keycloak token            | Kiểm tra user profile (`email`, `firstName`, `lastName`), `requiredActions`, chính sách realm                                                             |
| `401` tại `/secure`                                             | Kiểm tra token chưa hết hạn, issuer, audience, JWKS URL và hostname Keycloak                                                                              |
| Truy cập Public IP timeout                                      | Kiểm tra Security Group, Public IPv4, subnet route `0.0.0.0/0 → Internet Gateway`, Network ACL, host firewall                                             |
| `UNPROTECTED PRIVATE KEY FILE` trên Windows                     | Giới hạn ACL của `.pem` để tài khoản Windows hiện tại có quyền đọc, loại quyền truy cập của nhóm khác                                                     |
| File `/etc/bind/db.cloud.local` báo thiếu newline               | Cảnh báo định dạng; nếu zone `OK` và phân giải đúng thì DNS vẫn chạy                                                                                      |

## 7. Bảo mật và phạm vi sử dụng

Đây là **môi trường bài tập/demo**, không phải cấu hình production: HTTP chưa có TLS, Keycloak chạy `start-dev`, các mật khẩu mẫu yếu, các dịch vụ quản trị publish cổng trên EC2. Trước khi cho mọi người truy cập Internet, cần ít nhất **thay mật khẩu mẫu, cấu hình HTTPS, hạn chế giao diện quản trị và không expose cơ sở dữ liệu hoặc metrics không được bảo vệ**. Việc Security Group mở cổng không tự sửa URL/redirect của ứng dụng.

Các cổng `3000` (Grafana), `9090` (Prometheus), `8081` (Keycloak), `9001` (MinIO Console) nên giới hạn theo IP hoặc SSH tunnel cho đến khi có xác thực/HTTPS phù hợp. Giữ SSH `22` cho IP quản trị và AWS Instance Connect prefix list khi cần.

## 8. Kết quả lịch sử trên EC2

README trước đây ghi nhận các kết quả sau trên EC2 Ubuntu 24.04 tại Singapore, bản `e747d90`. Đây là lịch sử của nhóm, **chưa được kiểm thử lại trên EC2 trong lần cập nhật frontend này**:

- Docker **29.9.3**, Docker Compose **v5.7.0**.
- **12 container `Up`** và `minio-init Exited (0)`.
- Website và Blog **HTTP 200**, Flask `/api/hello`, `/student/` hoạt động.
- Nginx Round Robin cân bằng 6 request: 3 yêu cầu Web1, 3 yêu cầu Web2.
- MariaDB: **2 database**, bảng `notes`, `students`, 3 sinh viên mẫu.
- MinIO: tạo **3 bucket**, upload **2 file mẫu**, khởi tạo lặp không ghi đè file đã có.
- BIND9: zone `cloud.local` **OK**, phân giải tên miền nội bộ thành công.
- Prometheus: **5/5 targets UP**; Grafana: thấy ba panel CPU, RAM, Network.
- Keycloak cấp **JWT**, Flask `/secure` trả **HTTP 200** với `preferred_username=sv01`.

## 9. Phát triển, đồng bộ và kiểm tra frontend

### 9.1. Nguồn chuẩn

Không có framework hoặc bước npm build. Nguồn chuẩn là `web-frontend-server/html/`; dashboard được sinh từ `scripts/build_dashboard.py`. Thay đổi nội dung dashboard trong script này; thay đổi CSS/JS/URL console trực tiếp trong `html/assets/`.

```powershell
python scripts/build_dashboard.py
python scripts/refresh_blog_style.py
python scripts/sync_frontends.py
python scripts/sync_frontends.py --check
```

| Công cụ | Mục đích |
| --- | --- |
| `build_dashboard.py` | Sinh HTML dashboard chuẩn |
| `refresh_blog_style.py` | Sinh ảnh bìa SVG và gắn theme blog, giữ nguyên article |
| `sync_frontends.py` | Chép HTML/assets sang hai build context; chỉ đổi nhãn node |
| `verify_frontend.py` | Kiểm tra HTML, links, assets, SVG XML, đồng bộ và article so với Git HEAD |
| `test_frontend.cjs` | Kiểm thử logic JS bằng DOM/fetch giả lập; không thay thế browser hoặc integration test |

Giữ các bản assets tại cả ba frontend: Dockerfile dùng build context riêng, không thể chỉ xóa bản sao ở hai Node. Tài nguyên CSS/JS, favicon và ba ảnh bìa SVG tự tạo không phụ thuộc CDN. Nội dung và minh họa của ba bài blog được giữ nguyên.

### 9.2. Cấu hình URL console và bảo vệ token

`web-frontend-server/html/assets/config.js` chỉ chứa URL công khai, không chứa mật khẩu/access key. Với trang HTTP, mặc định dùng hostname hiện tại và cổng publish của Compose. Khi dùng HTTPS hoặc reverse proxy, điền URL console thực tế rồi đồng bộ/build lại cả ba Node; giao diện không tự tạo liên kết downgrade HTTP từ trang HTTPS.

API Explorer dùng ô token dạng password, không ghi token vào console/storage, chỉ gửi đến `/api/secure` khi nhấn Send Request. Token được xóa khỏi ô nhập sau request, khi đổi endpoint hoặc rời trang; response che các trường token nhạy cảm. Backend badge là kết quả lần kiểm tra API, không phải hệ thống giám sát toàn bộ container.

Chưa có API frontend để đọc database, upload/download object, truy vấn DNS hoặc lấy metrics tổng hợp. Dùng MariaDB CLI, MinIO Console và Prometheus/Grafana tương ứng. Panel RAM hiện có biểu diễn available/total theo byte; Node Exporter chưa cấu hình host mounts để khẳng định đo Windows vật lý hoặc từng container.

### 9.3. Kiểm tra và cập nhật container frontend

```powershell
python scripts/verify_frontend.py
node --check web-frontend-server/html/assets/dashboard.js
node --check web-frontend-server/html/assets/theme.js
node --check web-frontend-server/html/assets/config.js
node scripts/test_frontend.cjs
docker compose config --quiet
docker compose build web-frontend-server web-frontend-server1 web-frontend-server2
docker compose up -d --no-deps web-frontend-server web-frontend-server1 web-frontend-server2
```

Nếu chỉ chỉnh source, container đang chạy vẫn phục vụ bản image cũ cho đến khi build và recreate. Không cần đổi network, Gateway hoặc xóa volume.

Xem thử tĩnh trên host:

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory web-frontend-server/html
```

Mở `http://127.0.0.1:8765/`; API không hoạt động qua server preview này. Khi demo đầy đủ, dùng Gateway.

**Kết quả đã xác nhận trong quá trình cập nhật local:**

- Kiểm tra 7 trang HTML, links/assets, 12 file SVG giữa ba frontend, đồng bộ và nội dung ba article so với Git HEAD: đạt.
- Kiểm thử logic JS: routing, loading/empty/error, 401/502/timeout, copy, xử lý token và theme: đạt trong môi trường giả lập.
- Build và cập nhật cả ba container frontend: thành công.
- Blog trả HTTP 200; ảnh bìa đã sửa tải qua máy chủ chính và cả hai upstream, XML hợp lệ. Headers thực tế xác nhận cả `172.19.0.8:80` và `172.19.0.9:80`.
- Responsive, dark mode và accessibility cần kiểm tra thêm trực tiếp trong trình duyệt. Kết quả trên không thay thế kiểm thử đầy đủ database/JWT/MinIO/DNS/monitoring và EC2; dùng checklist trong DEMO_GUIDE.md.

### 9.4. Dọn mã nguồn

Bản backup `init_buckets.py.bak`, ba JPG blog không còn được tham chiếu và báo cáo frontend tạm đã được loại bỏ. Thông tin vận hành frontend được gộp vào README này; `DEMO_GUIDE.md` giữ kịch bản trình diễn riêng.

Giữ các file Compose theo thành viên, Dockerfile, SQL/realm/provisioning, file mẫu MinIO và script kiểm tra/đồng bộ. Không commit `.env`, secrets hoặc dữ liệu volume; không dọn dữ liệu Docker bằng lệnh xóa volume.

**Repository:** https://github.com/TrongPhuc2403/MyMiniCloud  
**Nhánh phát hành bài làm:** `feature/final-integration`
