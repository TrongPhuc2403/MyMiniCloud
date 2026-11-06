# MyMiniCloud – Hệ thống Mô phỏng Hạ tầng Đám mây Thu nhỏ

## 1. Giới thiệu Dự án & Phân công Nhóm

**MyMiniCloud** là đồ án cuối kỳ môn **Điện toán đám mây (Cloud Computing)**, xây dựng hệ thống dịch vụ đám mây thu nhỏ sử dụng **Docker & Docker Compose** để triển khai và tích hợp **9 loại máy chủ (12 containers)** cùng **10 yêu cầu mở rộng** trên một mạng nội bộ chung `cloud-net` (`172.19.0.0/16`).

### Danh sách thành viên thực hiện

| Thành viên | Cụm máy chủ phụ trách | Yêu cầu mở rộng | File Compose riêng |
|---|---|---|---|
| **Nguyễn Trọng Phúc** (Nhóm trưởng) | Web Frontend (`Nginx`), Application Backend (`Flask`), Relational Database (`MariaDB`) | Mở rộng #1 (Blog 3 bài viết), #2 (`/student` JSON), #3 (`studentdb`) | `docker-compose.phuc.yml` |
| **Lê Khải Hoàn** | Authentication & Identity (`Keycloak`), Object Storage (`MinIO`), Internal DNS (`BIND9`) | Mở rộng #4 (`realm_52400114`, `sv01`, `sv02`), #5 (MinIO Buckets), #6 (DNS `cloud.local`) | `docker-compose.hoan.yml` |
| **Trần Hữu Long** (`52400138`) | Monitoring (`Prometheus` + `Node Exporter`), Visualization (`Grafana`), API Gateway & Load Balancer (`Nginx`) | Mở rộng #7 (Web Metrics), #8 (Grafana Dashboard 3 biểu đồ), #9 (Proxy `/student/`), #10 (Round-Robin Load Balancer 2 Web Servers) | `docker-compose.long.yml` |

File tích hợp toàn bộ hệ thống dùng chung cho cả nhóm: **`docker-compose.yml`**.

---

## 2. Cấu trúc Thư mục Dự án

```text
MyMiniCloud/
├── docker-compose.yml                 # File tích hợp toàn bộ 9 loại server (12 containers)
├── docker-compose.phuc.yml            # File chạy riêng phần của Nguyễn Trọng Phúc
├── docker-compose.hoan.yml            # File chạy riêng phần của Lê Khải Hoàn
├── docker-compose.long.yml            # File chạy riêng phần của Trần Hữu Long
├── .env.example                       # File mẫu biến môi trường dùng chung
├── README.md                          # Tài liệu hướng dẫn triển khai & kiểm thử toàn hệ thống
├── web-frontend-server/               # [Server 1] Nginx Web Server chính + Trang Blog (/blog/)
├── web-frontend-server1/              # [Server 1 - Node 1] Web Server 1 phục vụ Load Balancer
├── web-frontend-server2/              # [Server 1 - Node 2] Web Server 2 phục vụ Load Balancer
├── application-backend-server/        # [Server 2] Flask REST API (/hello, /student, /secure)
├── relational-database-server/        # [Server 3] MariaDB SQL (minicloud & studentdb)
├── authentication-identity-server/    # [Server 4] Keycloak OIDC Identity Server (realm_52400114)
├── object-storage-server/             # [Server 5] MinIO Object Storage + script khởi tạo bucket
├── internal-dns-server/               # [Server 6] BIND9 Internal DNS Server (zone cloud.local)
├── monitoring-prometheus-server/      # [Server 7] Prometheus & Node Exporter thu thập metrics
├── monitoring-grafana-dashboard-server/ # [Server 8] Grafana Dashboard (System Health of 52400138)
└── api-gateway-proxy-server/          # [Server 9] Nginx API Gateway, Reverse Proxy & Load Balancer
```

---

## 3. Cấu hình Biến môi trường (`.env`) và Mạng Docker (`cloud-net`)

### 3.1. Tạo file `.env`
Trước khi khởi chạy hệ thống, sao chép file `.env.example` thành `.env` tại thư mục gốc của dự án:

```powershell
cp .env.example .env
```

Nội dung chuẩn trong `.env`:

```dotenv
KC_ADMIN_PASSWORD=admin
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MARIADB_ROOT_PASSWORD=root

OIDC_ISSUER=http://auth.cloud.local:8081/realms/realm_52400114
OIDC_AUDIENCE=flask-app
OIDC_JWKS_URL=http://authentication-identity-server:8080/realms/realm_52400114/protocol/openid-connect/certs
```

| Biến | Mục đích |
|---|---|
| `KC_ADMIN_PASSWORD` | Mật khẩu quản trị Keycloak |
| `MINIO_ROOT_USER` | Tài khoản quản trị MinIO |
| `MINIO_ROOT_PASSWORD` | Mật khẩu quản trị MinIO |
| `MARIADB_ROOT_PASSWORD` | Mật khẩu root MariaDB |
| `OIDC_ISSUER` | Địa chỉ định danh của Realm Keycloak (`realm_52400114`) |
| `OIDC_AUDIENCE` | Audience JWT mà Flask kiểm tra (`flask-app`) |
| `OIDC_JWKS_URL` | Địa chỉ lấy khóa công khai để xác minh JWT nội bộ |

### 3.2. Quy hoạch Địa chỉ IP Tĩnh & Cổng Dịch vụ trên `cloud-net` (`172.19.0.0/16`)

| STT | Container Name | Công nghệ | IP nội bộ (`cloud-net`) | DNS (`cloud.local`) | Cổng Host | Phụ trách |
|---|---|---|---|---|---|---|
| 1 | `web-frontend-server` | Nginx 1.26 + Exporter | `172.19.0.6` | `web.cloud.local` | `8080:80` | Trọng Phúc |
| 2 | `web-frontend-server1` | Nginx 1.26 + Exporter | `172.19.0.11` | — | Nội bộ `:80` | Hữu Long |
| 3 | `web-frontend-server2` | Nginx 1.26 + Exporter | `172.19.0.12` | — | Nội bộ `:80` | Hữu Long |
| 4 | `application-backend-server` | Python 3.11 / Flask | `172.19.0.4` | `app.cloud.local` | `8085:8081` | Trọng Phúc |
| 5 | `relational-database-server` | MariaDB 11 | `172.19.0.7` | — | `127.0.0.1:3307:3306` | Trọng Phúc |
| 6 | `authentication-identity-server` | Keycloak 26.4 | `172.19.0.2` | `auth.cloud.local` | `8081:8080` | Khải Hoàn |
| 7 | `object-storage-server` | MinIO | `172.19.0.3` | `storage.cloud.local` | `9000:9000`, `9001:9001` | Khải Hoàn |
| 8 | `internal-dns-server` | BIND9 9.18 | `172.19.0.5` | `ns.cloud.local` | `1053:53/udp`, `1053:53/tcp` | Khải Hoàn |
| 9 | `monitoring-prometheus-server` | Prometheus v2.54.1 | `172.19.0.8` | — | `9090:9090` | Hữu Long |
| 10 | `monitoring-node-exporter-server` | Node Exporter v1.8.2 | `172.19.0.9` | — | `9100:9100` | Hữu Long |
| 11 | `monitoring-grafana-dashboard-server` | Grafana 11.2.0 | `172.19.0.10` | — | `3000:3000` | Hữu Long |
| 12 | `api-gateway-proxy-server` | Nginx 1.26.2 | `172.19.0.13` | — | `80:80` | Hữu Long |

---

## 4. Khởi chạy Toàn bộ Hệ thống (`docker-compose.yml`)

### 4.1. Kiểm tra cấu hình Compose
```powershell
docker compose config --quiet
```

### 4.2. Khởi chạy toàn bộ 12 containers
```powershell
docker compose up -d --build
```

### 4.3. Kiểm tra trạng thái các container
```powershell
docker compose ps -a
```
Tất cả các container dịch vụ chính đều ở trạng thái `Up` (riêng `minio-init` là container khởi tạo bucket chạy 1 lần và kết thúc với mã `Exited (0)`).

---

## 5. Phần 1: Web Frontend, Application Backend & Relational Database (Nguyễn Trọng Phúc)

### 5.1. Web Frontend Server & Mở rộng #1 (Blog cá nhân)
- **Trang chủ trực tiếp**: http://localhost:8080/
- **Trang Blog cá nhân (3 bài viết HTML kèm hình ảnh)**: http://localhost:8080/blog/ (hoặc qua Gateway tại http://localhost/blog/)
  - Bài viết 1: `blog1.html` – Giới thiệu Cloud Computing
  - Bài viết 2: `blog2.html` – Docker & Containerization
  - Bài viết 3: `blog3.html` – Hạ tầng AWS EC2 & S3

### 5.2. Application Backend Server (Flask) & Mở rộng #2 (`/student`)
- **Kiểm tra API `/hello`**:
  ```powershell
  curl.exe http://localhost:8085/hello
  ```
- **Kiểm tra API `/student` (đọc danh sách 5 sinh viên từ `students.json`)**:
  ```powershell
  curl.exe http://localhost:8085/student
  ```
- **Kiểm tra API bảo mật `/secure` (yêu cầu OIDC Bearer Token)**:
  ```powershell
  curl.exe -i http://localhost:8085/secure
  ```

### 5.3. Relational Database Server (MariaDB) & Mở rộng #3 (`studentdb`)
- Tự động khởi tạo khi container chạy lần đầu qua thư mục `relational-database-server/init/`:
  - `001_init.sql`: Tạo CSDL `minicloud`, bảng `notes` và dữ liệu mẫu.
  - `002_studentdb.sql`: Tạo CSDL `studentdb`, bảng `students` và dữ liệu sinh viên mẫu.
- **Lệnh kiểm thử truy vấn SQL**:
  ```powershell
  docker exec -it relational-database-server mariadb -uroot -proot -e "SELECT * FROM minicloud.notes; SELECT * FROM studentdb.students;"
  ```

---

## 6. Phần 2: Authentication, Object Storage & Internal DNS (Lê Khải Hoàn)

### 6.1. Authentication & Identity Server – Keycloak (Mở rộng #4)

| Thuộc tính | Giá trị |
|---|---|
| Công nghệ | Keycloak 26.4 |
| Container | `authentication-identity-server` |
| Cổng truy cập | `8081` (hoặc qua Gateway `/auth/`) |
| IP nội bộ | `172.19.0.2` (`auth.cloud.local`) |
| Realm | `realm_52400114` |
| Client | `flask-app` |
| Tài khoản sinh viên | `sv01`, `sv02` |

- **Truy cập trang quản trị Keycloak**: http://localhost:8081/admin/ (Username: `admin`, Password: giá trị `KC_ADMIN_PASSWORD` trong `.env`).
- **Kiểm tra OpenID Connect Metadata**:
  ```powershell
  curl.exe http://localhost:8081/realms/realm_52400114/.well-known/openid-configuration
  ```

### 6.2. Object Storage Server – MinIO (Mở rộng #5)

| Thuộc tính | Giá trị |
|---|---|
| Công nghệ | MinIO |
| Container | `object-storage-server` |
| API Port / Console Port | `9000` / `9001` |
| IP nội bộ | `172.19.0.3` (`storage.cloud.local`) |
| Bucket khởi tạo tự động | `demo` (qua container `minio-init` chạy `init_buckets.py`) |

- **Truy cập MinIO Console**: http://localhost:9001 (đăng nhập bằng `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`).
- **Kiểm tra log khởi tạo bucket tự động**:
  ```powershell
  docker compose logs minio-init
  ```

### 6.3. Internal DNS Server – BIND9 (Mở rộng #6)

| Tên miền | Địa chỉ IP | Dịch vụ |
|---|---|---|
| `auth.cloud.local` | `172.19.0.2` | Keycloak (`authentication-identity-server`) |
| `storage.cloud.local` | `172.19.0.3` | MinIO (`object-storage-server`) |
| `app.cloud.local` | `172.19.0.4` | Flask (`application-backend-server`) |
| `ns.cloud.local` | `172.19.0.5` | BIND9 (`internal-dns-server`) |
| `web.cloud.local` | `172.19.0.6` | Web Server (`web-frontend-server`) |

- **Kiểm tra cú pháp DNS Zone**:
  ```powershell
  docker exec internal-dns-server named-checkzone cloud.local /etc/bind/db.cloud.local
  ```
- **Kiểm tra phân giải tên miền bằng `dig`**:
  ```powershell
  docker exec internal-dns-server dig @127.0.0.1 auth.cloud.local +short
  docker exec internal-dns-server dig @127.0.0.1 storage.cloud.local +short
  docker exec internal-dns-server dig @127.0.0.1 app.cloud.local +short
  docker exec internal-dns-server dig @127.0.0.1 web.cloud.local +short
  ```

---

## 7. Phần 3: Monitoring, Visualization & API Gateway Load Balancer (Trần Hữu Long)

### 7.1. Monitoring Server – Prometheus & Node Exporter (Mở rộng #7)
- **Truy cập Prometheus Targets**: http://localhost:9090/targets
- Các जॉब (jobs) được cấu hình trong `monitoring-prometheus-server/prometheus.yml`:
  1. `prometheus` (`localhost:9090`) -> State: **UP**
  2. `node` (`monitoring-node-exporter-server:9100`) -> State: **UP**
  3. `web-frontend-server` (`web-frontend-server:80`, `web-frontend-server1:80`, `web-frontend-server2:80` qua endpoint `/metrics`) -> State: **UP (3/3)**

### 7.2. Visualization Server – Grafana Dashboard (Mở rộng #8)
- **Truy cập Grafana**: http://localhost:3000 (Tài khoản: `admin` / `admin`)
- **Dashboard tự động nạp (Provisioning)**: **System Health of 52400138** (`monitoring-grafana-dashboard-server/provisioning/dashboards/system_health_52400138.json`), bao gồm đầy đủ các panel trạng thái và 3 biểu đồ thời gian thực:
  1. **CPU Usage** (`node_cpu_seconds_total`)
  2. **Memory Usage** (`node_memory_MemAvailable_bytes`)
  3. **Network Traffic** (`node_network_receive_bytes_total` / `node_network_transmit_bytes_total`)

### 7.3. API Gateway / Reverse Proxy & Load Balancer – Nginx (Mở rộng #9 & #10)
- **Cấu hình tại**: `api-gateway-proxy-server/nginx.conf`
- **Các tuyến định tuyến qua cổng `80`**:
  - `http://localhost/` -> Cân bằng tải **Round-Robin** giữa `web-frontend-server1:80` và `web-frontend-server2:80` (Mở rộng #10).
  - `http://localhost/blog/` -> Chuyển tiếp tới `web-frontend-server:80/blog/`.
  - `http://localhost/api/hello` -> Chuyển tiếp tới `application-backend-server:8081/hello`.
  - `http://localhost/student/` -> Chuyển tiếp tới `application-backend-server:8081/student` (Mở rộng #9).
  - `http://localhost/auth/` -> Chuyển tiếp tới `authentication-identity-server:8080/`.

- **Lệnh kiểm thử Reverse Proxy & Load Balancer Round-Robin**:
  ```powershell
  curl.exe -s http://localhost/ | Select-String "Served by"
  curl.exe -s http://localhost/ | Select-String "Served by"
  curl.exe -s http://localhost/api/hello
  curl.exe -s http://localhost/student/
  curl.exe -I http://localhost/auth/
  ```

---

## 8. Quản lý & Dừng Hệ thống

- **Xem trạng thái toàn bộ dịch vụ**:
  ```powershell
  docker compose ps -a
  ```
- **Xem log hệ thống**:
  ```powershell
  docker compose logs --tail=50
  ```
- **Dừng hệ thống (giữ nguyên dữ liệu volume)**:
  ```powershell
  docker compose down
  ```
