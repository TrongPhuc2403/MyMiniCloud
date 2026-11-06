# MyMiniCloud – Hệ Thống Dịch Vụ Đám Mây Thu Nhỏ

## 1. Giới thiệu

MyMiniCloud là dự án xây dựng mô phỏng hạ tầng đám mây thu nhỏ sử dụng Docker Compose để triển khai và tích hợp 9 loại máy chủ trên cùng một mạng nội bộ `cloud-net` (`172.19.0.0/16`).

| STT | Dịch vụ | Container | Cổng (Host -> Container) | IP nội bộ (`cloud-net`) | Phụ trách |
|---|---|---|---|---|---|
| 1 | Web Frontend Server (+ Blog) | `web-frontend-server` | `8080 -> 80` | `172.19.0.6` | Nguyễn Trọng Phúc |
| 1b | Web Upstream Node 1 & 2 (LB) | `web-frontend-server1`, `web-frontend-server2` | `80 (nội bộ)` | `172.19.0.8`, `172.19.0.9` | Trần Hữu Long |
| 2 | Application Backend Server | `application-backend-server` | `8085 -> 8081` | `172.19.0.4` | Nguyễn Trọng Phúc |
| 3 | Relational Database Server | `relational-database-server` | `3307 -> 3306` | `172.19.0.7` | Nguyễn Trọng Phúc |
| 4 | Authentication & Identity Server | `authentication-identity-server` | `8081 -> 8080` | `172.19.0.2` | Lê Khải Hoàn |
| 5 | Object Storage Server | `object-storage-server` | `9000, 9001 -> 9000, 9001` | `172.19.0.3` | Lê Khải Hoàn |
| 6 | Internal DNS Server | `internal-dns-server` | `1053 -> 53/udp, 53/tcp` | `172.19.0.5` | Lê Khải Hoàn |
| 7a | Monitoring Node Exporter | `monitoring-node-exporter-server` | `9100 -> 9100` | `172.19.0.10` | Trần Hữu Long |
| 7b | Monitoring Prometheus Server | `monitoring-prometheus-server` | `9090 -> 9090` | `172.19.0.11` | Trần Hữu Long |
| 8 | Visualization Grafana Server | `monitoring-grafana-dashboard-server` | `3000 -> 3000` | `172.19.0.12` | Trần Hữu Long |
| 9 | API Gateway / Reverse Proxy & LB | `api-gateway-proxy-server` | `80 -> 80` | `172.19.0.13` | Trần Hữu Long |

---

## 2. Cấu trúc thư mục

```text
MyMiniCloud/
├── docker-compose.yml              # File Compose tổng hợp toàn bộ hệ thống (9 loại server)
├── docker-compose.phuc.yml         # File Compose thành phần Web, App, Database
├── docker-compose.hoan.yml         # File Compose thành phần Auth, Storage, DNS
├── docker-compose.long.yml         # File Compose thành phần Monitoring, Grafana, Gateway & LB
├── .env.example                    # Mẫu biến môi trường dùng chung
├── README.md
├── web-frontend-server/            # Nginx phục vụ trang chủ, /blog/ và /metrics
├── web-frontend-server1/           # Node 1 phục vụ cân bằng tải Round-Robin
├── web-frontend-server2/           # Node 2 phục vụ cân bằng tải Round-Robin
├── application-backend-server/     # Flask REST API (/hello, /student, /secure)
├── relational-database-server/     # MariaDB khởi tạo CSDL minicloud và studentdb
├── authentication-identity-server/ # Keycloak Realm export (realm_52400114)
├── object-storage-server/          # Script khởi tạo bucket MinIO tự động
├── internal-dns-server/            # Cấu hình BIND9 DNS (zone cloud.local)
├── monitoring-prometheus-server/   # Cấu hình Prometheus scrape node & web
├── monitoring-grafana-dashboard-server/ # Provisioning Datasource & Dashboard System Health of 52400138
└── api-gateway-proxy-server/       # Cấu hình Nginx Reverse Proxy & Load Balancer
```

---

## 3. Khởi chạy toàn bộ hệ thống

### Bước 1: Chuẩn bị file `.env` (tùy chọn)

Sao chép từ file `.env.example` sang `.env` (nếu không tạo file `.env`, `docker-compose.yml` đã có sẵn các giá trị mặc định tương ứng):

```powershell
Copy-Item .env.example .env
```

Nội dung `.env`:

```dotenv
KC_ADMIN_PASSWORD=admin
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MARIADB_ROOT_PASSWORD=root

OIDC_ISSUER=http://auth.cloud.local:8081/realms/realm_52400114
OIDC_AUDIENCE=flask-app
OIDC_JWKS_URL=http://authentication-identity-server:8080/realms/realm_52400114/protocol/openid-connect/certs
```

### Bước 2: Khởi chạy tất cả các dịch vụ bằng `docker-compose.yml`

```powershell
docker compose up -d --build
```

Kiểm tra trạng thái các container:

```powershell
docker compose ps
```

---

## 4. Kiểm thử nhanh các thành phần

### 4.1. API Gateway / Reverse Proxy & Load Balancer (Cổng 80)

- Trang chủ cân bằng tải Round-Robin (`web-frontend-server1` và `web-frontend-server2`):
  ```powershell
  curl.exe http://localhost/
  ```
- Định tuyến `/api/hello` và `/student/` tới Flask Backend:
  ```powershell
  curl.exe http://localhost/api/hello
  curl.exe http://localhost/student/
  ```
- Định tuyến `/auth/` tới Keycloak:
  ```powershell
  curl.exe -I http://localhost/auth/
  ```

### 4.2. Web Frontend & Blog (Cổng 8080)

- Trang chủ Web Server: `http://localhost:8080/`
- Trang Blog cá nhân (3 bài viết): `http://localhost:8080/blog/`

### 4.3. Relational Database – MariaDB (Cổng 3307)

```powershell
docker exec -it relational-database-server mariadb -uroot -proot -e "SHOW DATABASES; SELECT * FROM minicloud.notes; SELECT * FROM studentdb.students;"
```

### 4.4. Authentication (Keycloak – Cổng 8081), Object Storage (MinIO – Cổng 9000/9001) & Internal DNS (BIND9 – Cổng 1053)

- **Keycloak Admin Console**: `http://localhost:8081/admin/` (`admin` / `admin`, Realm: `realm_52400114`, Client: `flask-app`)
- **MinIO Console**: `http://localhost:9001` (`minioadmin` / `minioadmin123`, Bucket khởi tạo tự động: `demo`)
- **Kiểm tra phân giải DNS nội bộ (`cloud.local`)**:
  ```powershell
  docker exec internal-dns-server dig @127.0.0.1 web.cloud.local +short
  docker exec internal-dns-server dig @127.0.0.1 app.cloud.local +short
  docker exec internal-dns-server dig @127.0.0.1 auth.cloud.local +short
  docker exec internal-dns-server dig @127.0.0.1 storage.cloud.local +short
  ```

### 4.5. Monitoring (Prometheus – Cổng 9090) & Visualization (Grafana – Cổng 3000)

- **Prometheus Targets**: `http://localhost:9090/targets` (giám sát `job="node"`, `job="prometheus"` và `job="web"`).
- **Grafana Dashboard**: `http://localhost:3000/d/system-health-52400138/system-health-of-52400138` (`admin` / `admin`) — hiển thị trực quan CPU Usage, Memory Usage và Network Traffic.
