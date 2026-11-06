# MyMiniCloud – Authentication, Object Storage & Internal DNS

## 1. Giới thiệu

MyMiniCloud là dự án xây dựng hệ thống dịch vụ đám mây thu nhỏ, sử dụng Docker để triển khai và tích hợp nhiều dịch vụ trên cùng một mạng nội bộ.

| Dịch vụ | Công nghệ | Chức năng |
|---|---|---|
| Authentication & Identity Server | Keycloak 26.4 | Quản lý người dùng, xác thực và cấp JWT |
| Object Storage Server | MinIO | Lưu trữ và quản lý tệp tin |
| Internal DNS Server | BIND9 9.18 | Phân giải tên miền nội bộ |

Các dịch vụ sử dụng chung Docker Network `cloud-net` để giao tiếp với các thành phần khác của hệ thống.

## 2. Yêu cầu môi trường

Trước khi triển khai, cần chuẩn bị:

- Windows 10 hoặc Windows 11.
- Docker Desktop đã được cài đặt và khởi động.
- Docker Compose.
- PowerShell hoặc Terminal trong Visual Studio Code.
- Mã nguồn dự án MyMiniCloud.
- Các cổng 8081, 9000, 9001 và 1053 chưa bị chiếm dụng.

Kiểm tra Docker:

```powershell
docker --version
docker compose version
```

## 3. Cấu trúc thư mục

```text
MyMiniCloud/
├── docker-compose.hoan.yml
├── README.md
├── .env
├── authentication-identity-server/
│   └── realm-export.json
├── object-storage-server/
│   ├── init_buckets.py
│   └── requirements.txt
└── internal-dns-server/
    ├── named.conf
    ├── named.conf.options
    ├── named.conf.local
    └── db.cloud.local
```

Trong đó:

- `docker-compose.hoan.yml`: Khai báo các container và cấu hình triển khai.
- `realm-export.json`: Chứa cấu hình Realm của Keycloak.
- `init_buckets.py`: Tự động khởi tạo bucket MinIO.
- `named.conf`: Cấu hình chính của BIND9.
- `named.conf.local`: Khai báo DNS Zone.
- `db.cloud.local`: Chứa các bản ghi DNS nội bộ.


## 4. Cấu hình môi trường

Tạo file `.env` tại thư mục gốc của dự án.

Nội dung mẫu:

```dotenv
KC_ADMIN_PASSWORD=<your_keycloak_admin_password>
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<your_minio_root_password>
MARIADB_ROOT_PASSWORD=<your_mariadb_root_password>

OIDC_ISSUER=http://auth.cloud.local:8081/realms/realm_52400114
OIDC_AUDIENCE=flask-app
OIDC_JWKS_URL=http://authentication-identity-server:8080/realms/realm_52400114/protocol/openid-connect/certs
```

Thay các giá trị trong dấu ngoặc nhọn bằng mật khẩu thực tế trước khi chạy.

Các biến có ý nghĩa như sau:

| Biến | Mục đích |
|---|---|
| `KC_ADMIN_PASSWORD` | Mật khẩu quản trị Keycloak |
| `MINIO_ROOT_USER` | Tài khoản quản trị MinIO |
| `MINIO_ROOT_PASSWORD` | Mật khẩu quản trị MinIO |
| `MARIADB_ROOT_PASSWORD` | Mật khẩu root MariaDB, được sử dụng bởi dịch vụ cơ sở dữ liệu của nhóm |
| `OIDC_ISSUER` | Địa chỉ định danh của Realm Keycloak |
| `OIDC_AUDIENCE` | Audience JWT mà Flask kiểm tra |
| `OIDC_JWKS_URL` | Địa chỉ lấy khóa công khai để xác minh JWT |

Lưu ý: Các biến `MARIADB_ROOT_PASSWORD` và `OIDC_*` phục vụ tích hợp với dịch vụ của thành viên khác. Chúng không trực tiếp được sử dụng bởi ba container Keycloak, MinIO và BIND9 trong `docker-compose.hoan.yml`.

Không nên commit mật khẩu thực tế vào GitHub.

## 5. Chuẩn bị Docker Network

Các dịch vụ sử dụng mạng Docker chung:

- Network: `cloud-net`
- Driver: `bridge`
- Subnet: `172.19.0.0/16`
- Gateway: `172.19.0.1`

Kiểm tra mạng hiện tại:

```powershell
docker network inspect cloud-net
```

Nếu mạng chưa tồn tại, tạo mạng bằng lệnh:

```powershell
docker network create --driver bridge --subnet 172.19.0.0/16 cloud-net
```

Nếu mạng đã tồn tại thì bỏ qua bước tạo mới.

Cấu hình mạng trong `docker-compose.hoan.yml`:

```yaml
networks:
  cloud-net:
    external: true
    name: cloud-net
```

Cấu hình này cho phép các container của Hoàn tham gia mạng Docker chung mà không cần sửa file Compose của thành viên khác.

## 6. Khởi chạy dịch vụ

Mở PowerShell tại thư mục gốc MyMiniCloud.

### 6.1. Kiểm tra Docker Compose

```powershell
docker compose -f docker-compose.hoan.yml config --quiet
```

Nếu không xuất hiện lỗi, cấu hình YAML hợp lệ.

### 6.2. Khởi chạy các container

```powershell
docker compose -f docker-compose.hoan.yml up -d
```

Docker sẽ khởi chạy các dịch vụ:

1. `authentication-identity-server`
2. `object-storage-server`
3. `minio-init`
4. `internal-dns-server`

### 6.3. Kiểm tra trạng thái

```powershell
docker compose -f docker-compose.hoan.yml ps -a
```

Các dịch vụ chính cần ở trạng thái `Up`.

Riêng `minio-init` là tác vụ khởi tạo bucket chạy một lần, có thể kết thúc với mã `0` sau khi hoàn thành.

## 7. Authentication & Identity Server – Keycloak

### 7.1. Thông tin cấu hình

| Thuộc tính | Giá trị |
|---|---|
| Công nghệ | Keycloak 26.4 |
| Container | `authentication-identity-server` |
| Cổng truy cập | `8081` |
| IP nội bộ | `172.19.0.2` |
| Realm | `realm_52400114` |
| Client | `flask-app` |
| Giao thức | OpenID Connect, OAuth 2.0 |

Keycloak sử dụng volume `keycloak_data` để lưu dữ liệu.

### 7.2. Truy cập Keycloak

Mở trình duyệt:

http://localhost:8081/admin/

Đăng nhập bằng tài khoản quản trị:

- Username: `admin`
- Password: Giá trị `KC_ADMIN_PASSWORD` trong `.env` khi tài khoản quản trị được khởi tạo.

### 7.3. Kiểm tra Realm

Sau khi đăng nhập:

1. Mở danh sách Realm.
2. Chọn `realm_52400114`.
3. Truy cập mục Clients.
4. Kiểm tra Client `flask-app`.
5. Truy cập Users để kiểm tra các tài khoản đã tạo.

File `realm-export.json` được mount vào Keycloak để nhập cấu hình Realm khi khởi tạo. Với volume đã có dữ liệu, cần kiểm tra Realm hiện tại thay vì giả định cấu hình được nhập lại.

### 7.4. Kiểm tra OpenID Connect

Truy cập:

http://localhost:8081/realms/realm_52400114/.well-known/openid-configuration

Nếu trả về JSON chứa các endpoint OpenID Connect, Realm đã cung cấp metadata thành công.

### 7.5. Kiểm tra JWT

Keycloak cung cấp access token cho người dùng sau khi xác thực thành công.

Flask có thể sử dụng JWT để xác minh:

- Chữ ký của token.
- Issuer.
- Audience.
- Thời hạn hiệu lực.

Cấu hình tích hợp:

```dotenv
OIDC_ISSUER=http://auth.cloud.local:8081/realms/realm_52400114
OIDC_AUDIENCE=flask-app
OIDC_JWKS_URL=http://authentication-identity-server:8080/realms/realm_52400114/protocol/openid-connect/certs
```

Lưu ý: Issuer trong JWT phải khớp chính xác với giá trị mà Flask sử dụng để xác minh. Địa chỉ truy cập Keycloak qua `localhost` và `auth.cloud.local` có thể dẫn đến giá trị issuer khác nhau tùy cấu hình hostname.

## 8. Object Storage Server – MinIO

### 8.1. Thông tin cấu hình

| Thuộc tính | Giá trị |
|---|---|
| Công nghệ | MinIO |
| Container | `object-storage-server` |
| API Port | `9000` |
| Console Port | `9001` |
| IP nội bộ | `172.19.0.3` |
| Bucket demo | `demo` |
| Volume | `minio_data` |

### 8.2. Truy cập MinIO Console

Mở trình duyệt:

http://localhost:9001

Đăng nhập bằng:

- Username: `MINIO_ROOT_USER`
- Password: `MINIO_ROOT_PASSWORD`

### 8.3. Kiểm tra Bucket

Sau khi đăng nhập:

1. Mở Object Browser.
2. Chọn bucket `demo`.
3. Kiểm tra danh sách tệp.
4. Tải một tệp lên bucket.
5. Tải tệp xuống để kiểm tra.
6. Thử xóa một tệp kiểm thử nếu cần.

### 8.4. Tự động khởi tạo Bucket

Dịch vụ `minio-init` sử dụng Python và thư viện boto3 để tạo bucket `demo`.

Kiểm tra nhật ký:

```powershell
docker compose -f docker-compose.hoan.yml logs minio-init
```

Khi chạy thành công, nhật ký có thể xuất hiện:

```text
Bucket already exists: demo
Bucket initialization completed.
```

Nếu bucket chưa tồn tại, script sẽ tạo bucket mới. Nếu đã tồn tại, script giữ nguyên bucket hiện có.

### 8.5. Kiểm tra dữ liệu

MinIO sử dụng volume `minio_data`, giúp dữ liệu được duy trì khi container được khởi động lại.

Không xóa volume nếu muốn giữ các đối tượng đã tải lên.

## 9. Internal DNS Server – BIND9

### 9.1. Thông tin cấu hình

| Thuộc tính | Giá trị |
|---|---|
| Công nghệ | BIND9 9.18 |
| Container | `internal-dns-server` |
| IP nội bộ | `172.19.0.5` |
| DNS Zone | `cloud.local` |
| DNS Port trong container | `53` |
| DNS Port trên máy host | `1053` |

### 9.2. Các bản ghi DNS

| Tên miền | Địa chỉ IP | Dịch vụ |
|---|---|---|
| `auth.cloud.local` | `172.19.0.2` | Keycloak |
| `storage.cloud.local` | `172.19.0.3` | MinIO |
| `app.cloud.local` | `172.19.0.4` | Flask |
| `ns.cloud.local` | `172.19.0.5` | BIND9 |

Địa chỉ `app.cloud.local` phụ thuộc IP của container Flask do thành viên khác quản lý. Nếu IP Flask thay đổi, cần cập nhật bản ghi DNS.

### 9.3. Kiểm tra DNS Zone

Chạy:

```powershell
docker exec internal-dns-server named-checkzone cloud.local /etc/bind/db.cloud.local
```

Kết quả mong đợi:

```text
OK
```

### 9.4. Kiểm tra phân giải tên miền

```powershell
docker exec internal-dns-server dig @127.0.0.1 auth.cloud.local +short
```

Kết quả:

```text
172.19.0.2
```

Kiểm tra MinIO:

```powershell
docker exec internal-dns-server dig @127.0.0.1 storage.cloud.local +short
```

Kết quả:

```text
172.19.0.3
```

Kiểm tra Flask:

```powershell
docker exec internal-dns-server dig @127.0.0.1 app.cloud.local +short
```

Kết quả:

```text
172.19.0.4
```

### 9.5. Kiểm tra DNS qua TCP và UDP

BIND9 hỗ trợ truy vấn DNS qua cả UDP và TCP.

Kiểm tra UDP:

```powershell
docker exec internal-dns-server dig @127.0.0.1 auth.cloud.local
```

Kiểm tra TCP:

```powershell
docker exec internal-dns-server dig +tcp @127.0.0.1 auth.cloud.local
```

Kết quả mong đợi là `status: NOERROR` và bản ghi IP tương ứng.

### 9.6. Truy cập bằng tên miền trên Windows

Để truy cập từ trình duyệt Windows trong môi trường local, có thể cấu hình file:

```text
C:\Windows\System32\drivers\etc\hosts
```

Thêm các bản ghi:

```text
127.0.0.1 app.cloud.local
127.0.0.1 auth.cloud.local
127.0.0.1 storage.cloud.local
```

Sau đó truy cập:

- Flask: http://app.cloud.local:8085/hello
- Keycloak: http://auth.cloud.local:8081/admin/
- MinIO: http://storage.cloud.local:9001

Lưu ý: File `hosts` là cơ chế phân giải tên miền cục bộ của Windows, không phải kết quả truy vấn trực tiếp BIND9. Muốn chứng minh BIND9 hoạt động cần sử dụng các lệnh kiểm thử DNS ở trên.

Tên miền `.local` có thể xung đột với mDNS trong một số môi trường. Cấu hình này được sử dụng cho mục đích thực hành nội bộ.

## 10. Quản lý Docker Container

### 10.1. Xem trạng thái

```powershell
docker compose -f docker-compose.hoan.yml ps -a
```

### 10.2. Xem nhật ký

```powershell
docker compose -f docker-compose.hoan.yml logs --tail=50
```

### 10.3. Dừng dịch vụ

```powershell
docker compose -f docker-compose.hoan.yml stop
```

### 10.4. Khởi động lại

```powershell
docker compose -f docker-compose.hoan.yml start
```

### 10.5. Khởi chạy lại khi cần

```powershell
docker compose -f docker-compose.hoan.yml up -d
```

Không sử dụng `docker compose down -v` nếu muốn bảo toàn dữ liệu trong các volume.

## 11. Kiểm tra IP Container

Kiểm tra địa chỉ IP của các dịch vụ trong mạng chung:

```powershell
docker network inspect cloud-net --format '{{range .Containers}}{{println .Name .IPv4Address}}{{end}}'
```

Địa chỉ IP dự kiến:

```text
authentication-identity-server 172.19.0.2/16
object-storage-server 172.19.0.3/16
application-backend-server 172.19.0.4/16
internal-dns-server 172.19.0.5/16
```

Ba dịch vụ của Hoàn được khai báo IP tĩnh trong `docker-compose.hoan.yml`.

IP Flask cần được xác nhận riêng vì thuộc cấu hình triển khai của thành viên khác.

## 12. Bảo mật

- Sử dụng biến môi trường cho thông tin xác thực.
- Không đưa mật khẩu thực tế vào README.
- Không công khai access token hoặc refresh token.
- Kiểm tra file `realm-export.json` trước khi commit.
- Không commit dữ liệu Postman cá nhân.
- Bảo vệ các volume chứa dữ liệu Keycloak và MinIO.
- Chế độ `start-dev` của Keycloak chỉ phù hợp với môi trường phát triển và demo.

## 13. Kết quả triển khai

Các chức năng đã được kiểm thử trong môi trường local:

| STT | Chức năng | Kết quả |
|---|---|---|
| 1 | Khởi chạy Keycloak | Thành công |
| 2 | Tạo Realm và Client | Thành công |
| 3 | Cấp và kiểm thử JWT | Thành công |
| 4 | Truy cập Flask với JWT | Đã kiểm thử |
| 5 | Khởi chạy MinIO | Thành công |
| 6 | Upload, Download và Delete Object | Thành công |
| 7 | Tự động khởi tạo bucket `demo` | Thành công |
| 8 | Khởi chạy BIND9 | Thành công |
| 9 | Kiểm tra DNS Zone | Thành công |
| 10 | Phân giải DNS qua UDP/TCP | Thành công |
| 11 | Kiểm thử DNS giữa các container | Thành công |
| 12 | Truy cập dịch vụ bằng hostname trên Windows | Thành công |

## 14. Phân chia trách nhiệm

**Thành viên phụ trách: Hoàn**

Các nội dung thực hiện:

- Triển khai Authentication & Identity Server bằng Keycloak.
- Cấu hình Realm, Client và xác thực JWT.
- Triển khai Object Storage Server bằng MinIO.
- Xây dựng script khởi tạo bucket.
- Triển khai Internal DNS Server bằng BIND9.
- Cấu hình bản ghi DNS nội bộ.
- Kiểm thử khả năng truy cập và giao tiếp giữa các dịch vụ.
- Xây dựng Docker Compose và tài liệu hướng dẫn triển khai.

Các thành phần Flask, giao diện web và cơ sở dữ liệu được quản lý bởi thành viên phụ trách tương ứng.

---

**MyMiniCloud – Authentication, Object Storage & Internal DNS**
