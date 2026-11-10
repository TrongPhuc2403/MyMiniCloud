# MyMiniCloud — Hệ thống mô phỏng hạ tầng đám mây thu nhỏ

> Đồ án cuối kỳ môn Điện toán đám mây (Cloud Computing). Triển khai bằng Docker Compose trên máy local và AWS EC2 Ubuntu.
>
> **Nhánh chứa bản tích hợp:** `feature/final-integration` · **Commit đã kiểm thử trên EC2:** `e747d90`.

## 1. Tổng quan

MyMiniCloud tích hợp **9 nhóm máy chủ**, triển khai qua **13 Compose services**: **12 container hoạt động thường trực** và **1 job khởi tạo MinIO (`minio-init`)**. Các dịch vụ giao tiếp qua mạng Docker `cloud-net` (`172.19.0.0/16`).

Các chức năng chính:

- Web Frontend, ba bài blog và hai Web Node được Nginx cân bằng tải Round Robin.
- Flask REST API: `/hello`, `/student`, `/secure` (JWT do Keycloak cấp).
- MariaDB với hai database `minicloud` và `studentdb`.
- Keycloak OIDC, realm `realm_52400114`, client `flask-app`.
- MinIO S3-compatible Object Storage, tự khởi tạo ba bucket cùng hai file mẫu.
- BIND9 phân giải các tên miền nội bộ `cloud.local`.
- Prometheus + Node Exporter và Grafana Dashboard (CPU, RAM, Network).

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
├── README.md
├── web-frontend-server/
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
Copy-Item .env.example .env
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

**Lưu ý cấu hình thật:** Trong commit `e747d90`, các biến `OIDC_ISSUER`, `OIDC_AUDIENCE` và `OIDC_JWKS_URL` của Flask được ghi trực tiếp trong `docker-compose.yml` (issuer là `http://localhost:8081/...`); chỉnh riêng `.env` **không** ghi đè các dòng này. Mặc định Grafana trong Compose cũng là `admin/admin`, trừ khi bạn đã thay Compose bằng tham chiếu `${GF_SECURITY_ADMIN_PASSWORD}` như ở phần EC2.

`.env` nằm trong `.gitignore`; **không commit file chứa mật khẩu lên GitHub**. Các thông tin đăng nhập trên chỉ dùng cho lab/demo; khi triển khai công khai cần thay bằng mật khẩu mạnh và HTTPS.

### 3.3. Khởi chạy

Mở Docker Desktop, bảo đảm Docker Engine đã hoạt động, sau đó chạy tại thư mục gốc dự án:

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

### 3.4. Địa chỉ LOCAL

| Chức năng                    | URL                           |
| ---------------------------- | ----------------------------- |
| Nginx Gateway / cân bằng tải | http://localhost/             |
| Blog                         | http://localhost/blog/        |
| Web chính trực tiếp          | http://localhost:8080/        |
| Flask Hello qua Gateway      | http://localhost/api/hello    |
| Danh sách sinh viên          | http://localhost/student/     |
| Flask trực tiếp              | http://localhost:8085/hello   |
| Keycloak Admin (trực tiếp)   | http://localhost:8081/admin/  |
| MinIO Console                | http://localhost:9001/        |
| Prometheus Targets           | http://localhost:9090/targets |
| Grafana                      | http://localhost:3000/        |
| Node Exporter                | http://localhost:9100/metrics |

**Lưu ý:** Trong cấu hình hiện tại, link `/auth/` qua Nginx có thể chuyển hướng đến `/admin/` ở Gateway và trả **404**. Khi quản trị Keycloak, hãy dùng trực tiếp cổng `8081/admin/`, không dùng `http://localhost/admin/`.

## 4. Chạy hệ thống trên AWS EC2 (Ubuntu 24.04)

### 4.1. Tạo EC2 và cấu hình mạng

1. AWS Console → **EC2 → Launch instances**.
2. Region `ap-southeast-1` (Singapore), Ubuntu Server 24.04 LTS (x86_64).
3. Ví dụ môi trường đã kiểm thử: `m7i-flex.large`, EBS 30 GiB gp3, **Auto-assign public IP: Enable**.
4. Tạo và tải SSH Key Pair, ví dụ `myminicloud-final-key.pem`.
5. Security Group: **TCP 22 từ IP quản trị `/32`**, **TCP 80 từ `0.0.0.0/0`** cho trang web. Chỉ mở các cổng khác khi thực sự cần và đã cấu hình bảo mật.
6. Ghi nhận Public IPv4 của EC2. Trong lần triển khai đã kiểm thử là `54.169.9.254`; IP có thể thay đổi khi Stop/Start nếu không gắn Elastic IP.

**Truy cập SSH trên Windows PowerShell:**

```powershell
ssh -i "$env:USERPROFILE\Downloads\myminicloud-final-key.pem" ubuntu@54.169.9.254
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

Thay `54.169.9.254` bằng **Public IPv4 hiện tại** nếu đã đổi:

| Dịch vụ            | URL trên EC2                     | Ghi chú                                             |
| ------------------ | -------------------------------- | --------------------------------------------------- |
| Website Nginx      | http://54.169.9.254/             | TCP 80                                              |
| Blog               | http://54.169.9.254/blog/        | Qua Nginx                                           |
| Flask API          | http://54.169.9.254/api/hello    | Qua Nginx TCP 80                                    |
| Student JSON       | http://54.169.9.254/student/     | Qua Nginx TCP 80                                    |
| Web chính          | http://54.169.9.254:8080/        | Cần TCP 8080 được phép                              |
| Keycloak Admin     | http://54.169.9.254:8081/admin/  | Cần TCP 8081; **không dùng `/admin/` trên port 80** |
| MinIO Console      | http://54.169.9.254:9001/        | Cần TCP 9001                                        |
| Prometheus Targets | http://54.169.9.254:9090/targets | Cần TCP 9090                                        |
| Grafana Dashboard  | http://54.169.9.254:3000/        | Cần TCP 3000                                        |
| Flask trực tiếp    | http://54.169.9.254:8085/hello   | Cần TCP 8085                                        |

**An toàn mạng:** Chỉ công khai cổng website `80` (và sau này `443` với HTTPS) là lựa chọn khuyến nghị. Với Keycloak, MinIO, Grafana, Prometheus hãy sử dụng SSH tunnel hoặc hạn chế Security Group theo IP quản trị; **không để `0.0.0.0/0` cùng mật khẩu mặc định**. MariaDB đang bind `127.0.0.1:3307` và không thể truy cập bên ngoài chỉ bằng cách mở Security Group. Prometheus Targets hiển thị tên container hoặc `localhost`; đó là các endpoint **nội bộ Docker**, không mở được trực tiếp từ trình duyệt Windows và không cần sửa.

**SSH Tunnel cho Grafana**, chạy từ **PowerShell Windows**:

```powershell
ssh -i "$env:USERPROFILE\Downloads\myminicloud-final-key.pem" -N -L 3000:127.0.0.1:3000 ubuntu@54.169.9.254
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

Kết quả đã kiểm thử: website và blog HTTP 200, `/api/hello` trả `{"message":"Hello from App Server!"}`, `/student/` trả JSON 5 sinh viên. Round Robin phân phối 3 lượt tới `172.19.0.8:80` và 3 lượt tới `172.19.0.9:80` trên 6 yêu cầu.

### 5.2. MariaDB

```bash
docker exec relational-database-server mariadb -uroot -proot -e "SHOW DATABASES;"
docker exec relational-database-server mariadb -uroot -proot -e "SHOW TABLES FROM minicloud; SHOW TABLES FROM studentdb;"
docker exec relational-database-server mariadb -uroot -proot -e "SELECT * FROM studentdb.students;"
```

Kết quả đã kiểm thử: `minicloud.notes`, `studentdb.students` và 3 sinh viên `SV001`, `SV002`, `SV003`. Thay `-proot` nếu mật khẩu MariaDB đã thay đổi.

### 5.3. MinIO

```bash
docker compose logs --tail=50 minio-init
```

Kết quả đã kiểm thử: các bucket `demo`, `profile-pics`, `documents`, file `profile-pics/avatar.jpg`, `documents/report.pdf`. Job `minio-init` kết thúc `Exited (0)` là bình thường; chạy lại giữ nguyên object đã có.

### 5.4. BIND9 DNS nội bộ

```bash
docker exec internal-dns-server named-checkzone cloud.local /etc/bind/db.cloud.local
docker run --rm --network cloud-net busybox nslookup app.cloud.local 172.19.0.5
docker run --rm --network cloud-net busybox nslookup web.cloud.local 172.19.0.5
```

Kết quả đã kiểm thử: `app.cloud.local → 172.19.0.4`, `web.cloud.local → 172.19.0.6`. Cảnh báo `file does not end with newline` không làm zone thất bại nếu `named-checkzone` in `OK`.

### 5.5. Prometheus và Grafana

```bash
curl -s -o /dev/null -w 'Prometheus: HTTP %{http_code}\n' http://localhost:9090/-/ready
curl -s -o /dev/null -w 'Grafana: HTTP %{http_code}\n' http://localhost:3000/api/health
curl -s http://localhost:9090/api/v1/targets | python3 -c 'import json,sys; d=json.load(sys.stdin); [print(t["labels"].get("job"),t["health"],t["scrapeUrl"]) for t in d["data"]["activeTargets"]]'
```

Kết quả đã kiểm thử: Prometheus và Grafana HTTP 200, **5/5 targets UP** (`node`, `prometheus`, 3 `web`). Grafana hiển thị ba biểu đồ CPU, RAM, Network; cần xác nhận các panel có dữ liệu, không chỉ xuất hiện khung biểu đồ.

### 5.6. Keycloak, JWT và Flask `/secure`

Kiểm tra endpoint OIDC:

```bash
curl -s -o /dev/null -w 'Keycloak: HTTP %{http_code}\n' http://localhost:8081/realms/realm_52400114/.well-known/openid-configuration
```

**Quan trọng:** File `realm-export.json` hiện **không chứa user** (`users: []`), nên khi triển khai máy mới phải tạo user test `sv01` riêng trong Keycloak. Trên EC2 đã tạo `sv01` và cập nhật email, họ tên, `emailVerified` để giải quyết lỗi `Account is not fully set up`.

Ví dụ tạo user với `kcadm.sh` (dùng cho lab, không dùng mật khẩu mặc định ở production):

```bash
# Chỉ chạy bước create khi sv01 chưa tồn tại.
docker exec authentication-identity-server /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password admin
docker exec authentication-identity-server /opt/keycloak/bin/kcadm.sh create users -r realm_52400114 -s username=sv01 -s enabled=true -s firstName=Demo -s lastName=Student -s email=sv01@example.com -s emailVerified=true
docker exec authentication-identity-server /opt/keycloak/bin/kcadm.sh set-password -r realm_52400114 --username sv01 --new-password 123456
```

Nếu đã tạo user nhưng chưa có thông tin hồ sơ, cập nhật user bằng ID lấy từ câu lệnh `get users` (không dùng ID cố định từ máy khác):

```bash
docker exec authentication-identity-server /opt/keycloak/bin/kcadm.sh get users -r realm_52400114 -q username=sv01 --fields id,username,enabled,firstName,lastName,email,requiredActions
```

Để xin token test **trên EC2** và tránh in token ra màn hình:

```bash
TOKEN_RESPONSE=$(curl -sS -X POST http://localhost:8081/realms/realm_52400114/protocol/openid-connect/token \
  -d grant_type=password -d client_id=flask-app -d username=sv01 --data-urlencode password=123456)
export TOKEN_RESPONSE
TOKEN=$(python3 -c 'import json,os; print(json.loads(os.environ["TOKEN_RESPONSE"]).get("access_token",""))')
if [ -n "$TOKEN" ]; then echo 'Access Token received'; else python3 -c 'import json,os; d=json.loads(os.environ["TOKEN_RESPONSE"]); print(d.get("error"),d.get("error_description"))'; fi
unset TOKEN_RESPONSE
[ -n "$TOKEN" ] && curl -i http://localhost:8085/secure -H "Authorization: Bearer $TOKEN"
```

**Kết quả đã kiểm thử trên EC2:** `Access Token received`, `HTTP/1.1 200 OK`, nội dung `{"message":"Secure resource OK","preferred_username":"sv01"}`.

> Password Grant (`directAccessGrantsEnabled=true`), mật khẩu `123456`, admin `admin` và Keycloak `start-dev` chỉ phục vụ demo. Không dùng cấu hình này cho production. Keycloak Admin qua cổng `8081/admin/`, không phải qua cổng 80 `/admin/` (sẽ trả 404 với Nginx hiện tại).

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
docker compose down
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

## 8. Kết quả triển khai đã xác nhận

Trên EC2 Ubuntu 24.04 tại Region Singapore, nhóm đã kiểm thử và ghi nhận:

- Docker **29.9.3**, Docker Compose **v5.7.0**.
- **12 container `Up`** và `minio-init Exited (0)`.
- Website và Blog **HTTP 200**, Flask `/api/hello`, `/student/` hoạt động.
- Nginx Round Robin cân bằng 6 request: 3 yêu cầu Web1, 3 yêu cầu Web2.
- MariaDB: **2 database**, bảng `notes`, `students`, 3 sinh viên mẫu.
- MinIO: tạo **3 bucket**, upload **2 file mẫu**, khởi tạo lặp không ghi đè file đã có.
- BIND9: zone `cloud.local` **OK**, phân giải tên miền nội bộ thành công.
- Prometheus: **5/5 targets UP**; Grafana: thấy ba panel CPU, RAM, Network.
- Keycloak cấp **JWT**, Flask `/secure` trả **HTTP 200** với `preferred_username=sv01`.

**Repository:** https://github.com/TrongPhuc2403/MyMiniCloud  
**Nhánh phát hành bài làm:** `feature/final-integration`
