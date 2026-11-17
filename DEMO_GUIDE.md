# MyMiniCloud — Kịch bản demo 9 loại server và 10 yêu cầu mở rộng

Tài liệu dành cho buổi bảo vệ đồ án, đối chiếu với mã nguồn hiện tại. Các kết quả bên dưới là **kết quả mong đợi để kiểm chứng lúc demo**, không phải khẳng định trạng thái hiện tại của hệ thống.

Các lệnh dùng **PowerShell trên Windows**, chạy tại thư mục gốc dự án. Thời lượng gợi ý: **18–22 phút**, chưa tính hỏi đáp. Có thể chuẩn bị sẵn tab và đăng nhập console trước khi trình bày.

## 1. Mở đầu — 45 giây

> “MyMiniCloud là hệ thống mô phỏng hạ tầng điện toán đám mây bằng Docker Compose. Hệ thống gồm 9 loại máy chủ với 13 Compose services, trong đó có ba Web Frontend và một tác vụ khởi tạo MinIO. Các dịch vụ giao tiếp qua mạng cloud-net, subnet 172.19.0.0/16. Sau đây nhóm trình diễn 10 yêu cầu mở rộng bằng giao diện, phản hồi API, truy vấn cơ sở dữ liệu và kết quả giám sát thực tế.”

**Phân biệt:** 9 là số loại máy chủ theo chức năng; 13 là số service trong Compose. Không gọi cả 13 service là 13 loại server. `minio-init` hoàn tất rồi thoát, không cần chạy thường trực.

## 2. Bảng đối chiếu 9 server

| STT | Loại server | Công nghệ / Compose service | Phần demo chứng minh |
| --- | --- | --- | --- |
| 1 | Web Server | Nginx — `web-frontend-server`, `web-frontend-server1`, `web-frontend-server2` | YC1: dashboard, ba bài blog; YC10: hai node |
| 2 | Application Server | Flask — `application-backend-server` | YC2: Student JSON; YC4: kiểm tra JWT; YC9: request qua proxy |
| 3 | Database Server | MariaDB — `relational-database-server` | YC3: database `studentdb`, bảng `students`, truy vấn SQL |
| 4 | Authentication Server | Keycloak — `authentication-identity-server` | YC4: realm, client, cấp JWT và Flask xác minh |
| 5 | Object Storage Server | MinIO — `object-storage-server`, job `minio-init` | YC5: bucket, upload và tải object |
| 6 | Internal DNS Server | BIND9 — `internal-dns-server` | YC6: zone hợp lệ, phân giải bản ghi `cloud.local` |
| 7 | Monitoring Server | Prometheus + Node Exporter — `monitoring-prometheus-server`, `monitoring-node-exporter-server` | YC7: scrape targets, metrics thật |
| 8 | Visualization Server | Grafana — `monitoring-grafana-dashboard-server` | YC8: ba biểu đồ CPU, RAM, Network |
| 9 | API Gateway / Load Balancer | Nginx — `api-gateway-proxy-server` | YC9: proxy `/student/`; YC10: Round Robin |

## 3. Chuẩn bị trước buổi demo

### 3.1. Khởi động và kiểm tra cổng

1. Mở Docker Desktop, chờ Linux Engine sẵn sàng.
2. **Dừng Apache trong XAMPP** nếu đang chạy: máy này từng có xung đột cổng 80. Chỉ dừng Apache, không cần dừng MySQL của XAMPP.
3. Mở PowerShell:

```powershell
cd D:\52400028_52400114_52400138\MyMiniCloud
docker info
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

Nếu stack đã chạy và image đã cập nhật, không cần build lại trong buổi bảo vệ. Dùng `docker compose up -d` khi cần khởi động lại.

**Điều kiện sẵn sàng:** 12 service thường trực ở trạng thái `Up`; `minio-init` có thể là `Exited (0)`. Chờ Keycloak sẵn sàng và Prometheus thu thập dữ liệu trước buổi demo. Trạng thái `Up` của container chưa chứng minh mọi chức năng bên trong đã sẵn sàng.

```powershell
curl.exe -I http://localhost/
curl.exe -i http://localhost/api/hello
curl.exe -i http://localhost/student/
curl.exe -i http://localhost:9090/-/ready
curl.exe -i http://localhost:3000/api/health
```

`http://localhost/` phải trả header `Server: nginx`, không phải `Apache`. Nếu Gateway vẫn `Created` sau khi dừng Apache:

```powershell
docker compose up -d --no-deps api-gateway-proxy-server
docker compose logs --tail=50 api-gateway-proxy-server
```

### 3.2. Chuẩn bị các tab

| Tab | Địa chỉ | Mục đích |
| --- | --- | --- |
| 1 | http://localhost/ | Dashboard qua Gateway |
| 2 | http://localhost/blog/ | Blog và ba bài viết |
| 3 | http://localhost/#api-explorer | API Explorer |
| 4 | http://localhost:8081/admin/ | Keycloak Admin |
| 5 | http://localhost:9001/ | MinIO Console |
| 6 | http://localhost:9090/targets | Prometheus Targets |
| 7 | http://localhost:3000/d/system-health-52400138 | Grafana dashboard theo UID đã provisioning |

- Đăng nhập các console bằng tài khoản demo hiện có của nhóm; lấy cấu hình đăng nhập từ người quản trị và cấu hình triển khai, không chiếu mật khẩu lên màn hình.
- Tài khoản Keycloak dùng cho xin token phải thuộc realm `realm_52400114`, ví dụ `sv01`. Chuẩn bị trước theo YC4.
- Chuẩn bị hai file mẫu `object-storage-server/sample-files/avatar.jpg` và `object-storage-server/sample-files/report.pdf`; kiểm tra chúng mở được. Dùng dữ liệu demo, không dùng hồ sơ cá nhân.
- Đặt Grafana ở khoảng thời gian **Last 15 minutes**, refresh **5s hoặc 10s** nếu giao diện cho phép. Khởi động stack trước ít nhất vài phút để biểu đồ có dữ liệu.
- Dùng `localhost` trong các lệnh khi chạy ngay trên máy Docker. Thiết bị khác dùng IP/hostname của máy Docker, riêng issuer JWT cần chú ý ở YC4.

## 4. Lộ trình 10 yêu cầu mở rộng

| Yêu cầu | Nội dung | Thời lượng | Bằng chứng chính |
| --- | --- | --- | --- |
| YC1 | Website và Blog | 1,5 phút | Dashboard + listing + ba bài đầy đủ hình |
| YC2 | Backend API | 1 phút | `/student/` trả JSON, đối chiếu file |
| YC3 | Cơ sở dữ liệu | 1,5 phút | SQL: database, schema và các dòng students |
| YC4 | Xác thực | 3 phút | Realm/client, 401 khi thiếu token, 200 khi có JWT |
| YC5 | Lưu trữ đối tượng | 2 phút | Ba bucket, ảnh và PDF, thao tác upload/download |
| YC6 | DNS nội bộ | 1,5 phút | `named-checkzone`, `nslookup` ra IP đúng |
| YC7 | Giám sát Web | 1,5 phút | Ba Web targets thực tế UP trong Prometheus |
| YC8 | Dashboard | 2 phút | Ba biểu đồ CPU, RAM, Network có dữ liệu |
| YC9 | Reverse Proxy | 1 phút | Cùng dữ liệu qua Gateway và Flask trực tiếp |
| YC10 | Load Balancer | 1,5 phút | Headers từ nhiều request đi tới cả hai node |

### YC1 — Website và Blog

**Server:** Web Server (Nginx).

**Thao tác trình diễn:**

1. Mở `http://localhost/`, giới thiệu sidebar và bốn thẻ tổng quan.
2. Đổi Light/Dark Mode, mở Infrastructure để chỉ tuyến Client → Gateway → Web/API/Blog.
3. Mở `http://localhost/blog/` và lần lượt mở cả ba bài:
   - `/blog/blog1.html`: Tổng quan về Cloud Computing.
   - `/blog/blog2.html`: Docker và công nghệ Container.
   - `/blog/blog3.html`: Triển khai ứng dụng trên AWS EC2.
4. Cuộn từng bài để thấy nội dung, hình minh họa, mục lục và breadcrumb. Quay về listing bằng liên kết có sẵn.

**Đạt khi:** cả ba bài có nội dung và hình, liên kết không 404, tài nguyên CSS/JS tải được. Có thể thu nhỏ cửa sổ để trình diễn menu mobile.

**Lời trình bày:**

> “Nginx phục vụ website tĩnh. Dashboard dùng chung thiết kế trên ba frontend; Blog gồm ba bài và vẫn được Gateway định tuyến về Web Server chính. Các thẻ 9/13/3/2 là thông tin cấu hình, không phải số liệu runtime.”

**Minh chứng nên lưu:** một ảnh overview, một ảnh listing và ảnh thể hiện nội dung/hình của từng bài.

### YC2 — Backend API đọc JSON

**Server:** Application Server (Flask).

Trong API Explorer, chọn `/api/hello` → **Send Request**, sau đó chọn `/student/` → **Send Request**. Giới thiệu HTTP status, JSON Response và Copy.

Kiểm tra bằng PowerShell nếu cần:

```powershell
curl.exe -i http://localhost/api/hello
curl.exe -i http://localhost/student/
Get-Content application-backend-server/students.json -Encoding UTF8
```

**Đạt khi:** hello trả HTTP 200 với `Hello from App Server!`; Student API trả HTTP 200 và mảng JSON. File hiện có 5 sinh viên với `id`, `name`, `major`, `gpa`; đối chiếu dữ liệu thực tế lúc demo.

**Lời trình bày:**

> “Gateway chuyển request đến Flask. Endpoint student đọc dữ liệu từ students.json và trả JSON. API này hiện chưa truy vấn MariaDB; phần database sẽ được chứng minh riêng bằng SQL.”

**Minh chứng:** HTTP 200 và response, kèm đoạn route `student()` trong `application-backend-server/app.py`.

### YC3 — Database studentdb và bảng students

**Server:** Database Server (MariaDB).

Mở MariaDB CLI; nhập mật khẩu root của môi trường hiện tại khi được hỏi:

```powershell
docker compose exec relational-database-server mariadb -u root -p
```

Trong MariaDB CLI, chạy lần lượt:

```sql
SHOW DATABASES;
USE studentdb;
SHOW TABLES;
DESCRIBE students;
SELECT id, student_id, fullname, dob, major FROM students;
SELECT COUNT(*) AS total_students FROM students;
SHOW TABLES FROM minicloud;
SELECT * FROM minicloud.notes;
exit;
```

**Đạt khi:** có `studentdb.students` và `minicloud.notes`; truy vấn trả các dòng dữ liệu thực tế. Script `002_studentdb.sql` khởi tạo 3 dòng `SV001`, `SV002`, `SV003`, nhưng dữ liệu trên volume có thể đã thay đổi.

**Lời trình bày:**

> “MariaDB lưu dữ liệu quan hệ với database studentdb và bảng students. Nhóm chứng minh cấu trúc bảng và dữ liệu bằng truy vấn SQL trực tiếp. Đây là nguồn dữ liệu độc lập với file JSON của Student API hiện tại.”

**Lưu ý:** init SQL chỉ áp dụng khi database volume được khởi tạo lần đầu. Nếu bảng chưa có, xem log/cấu hình và chuẩn bị dữ liệu đúng quy trình trước buổi demo; không xóa volume để chạy lại cho nhanh.

**Minh chứng:** `DESCRIBE students` và `SELECT`, không chụp phần nhập mật khẩu.

### YC4 — Keycloak, Realm, Client và kiểm thử JWT

**Server:** Authentication Server (Keycloak) và Application Server (Flask).

**A. Chuẩn bị trước buổi demo:**

1. Đăng nhập `http://localhost:8081/admin/` bằng tài khoản quản trị demo.
2. Chọn realm **realm_52400114**.
3. Mở **Clients → flask-app**: client public (`publicClient: true`), Direct Access Grants được bật trong bản export hiện có. Audience mapper thêm `flask-app` vào access token.
4. Mở **Users**, kiểm tra user `sv01`. File realm export không có user, nên môi trường mới cần tạo user demo trước.
5. Nếu chưa có, tạo `sv01`, bật Enabled, điền first name/last name/email, dùng email demo; đặt mật khẩu demo với **Temporary = Off**. Xử lý các Required Actions còn chờ theo cấu hình realm. Không dùng tài khoản admin để xin token ứng dụng.

**B. Chứng minh thiếu token bị từ chối:**

```powershell
curl.exe -i http://localhost/api/secure
```

**Mong đợi:** HTTP 401, JSON `{"error":"Missing Bearer token"}`.

**C. Xin token và gọi API bảo vệ:**

Chạy block sau trong PowerShell trên chính máy Docker. Hộp nhập credential dùng tài khoản ứng dụng `sv01`; mật khẩu không nằm trong câu lệnh hay file. Không chạy `$demoTokenResponse` hoặc `$demoToken` riêng để tránh in token lên màn hình.

```powershell
$demoCredential = Get-Credential -UserName 'sv01' -Message 'Tai khoan demo trong realm_52400114'
try {
    if ($null -eq $demoCredential) { throw 'Da huy nhap tai khoan.' }
    $demoAuthBody = @{
        grant_type = 'password'
        client_id  = 'flask-app'
        username   = $demoCredential.UserName
        password   = $demoCredential.GetNetworkCredential().Password
    }
    $demoTokenResponse = Invoke-RestMethod -Method Post `
        -Uri 'http://localhost:8081/realms/realm_52400114/protocol/openid-connect/token' `
        -ContentType 'application/x-www-form-urlencoded' -Body $demoAuthBody
    $demoToken = $demoTokenResponse.access_token
    if (-not $demoToken) { throw 'Khong nhan duoc access token.' }
    Write-Host 'Keycloak da cap access token (khong hien thi token).'
    $demoSecureResponse = Invoke-WebRequest -UseBasicParsing `
        -Uri 'http://localhost/api/secure' `
        -Headers @{ Authorization = "Bearer $demoToken" }
    Write-Host ('HTTP ' + $demoSecureResponse.StatusCode)
    $demoSecureResponse.Content
}
finally {
    Remove-Variable demoCredential,demoAuthBody,demoTokenResponse,demoToken,demoSecureResponse `
        -ErrorAction SilentlyContinue
}
```

**Mong đợi:** HTTP 200, `{"message":"Secure resource OK","preferred_username":"sv01"}`. Thứ tự key JSON có thể khác. Có thể kiểm tra token sai bằng API Explorer: chọn `/api/secure`, nhập `invalid-demo-token`, Send Request → HTTP 401.

**Lời trình bày:**

> “Keycloak cấp access token cho user thuộc realm của nhóm. Flask lấy khóa công khai từ JWKS, kiểm tra chữ ký RS256, issuer, audience và hạn sử dụng. Không có token thì trả 401; JWT hợp lệ mới được truy cập tài nguyên bảo vệ.”

**Chú ý kỹ thuật:**

- Flask hiện yêu cầu issuer `http://localhost:8081/realms/realm_52400114`. Vì vậy block xin token dùng đúng hostname `localhost`, không đổi sang IP ở riêng bước này.
- Token qua `/auth/`, IP public hoặc hostname khác có thể có issuer khác và bị từ chối. Không tắt kiểm tra JWT để demo.
- Password Grant đang được cấu hình để phục vụ lab; không trình bày đây là luồng đăng nhập production được khuyến nghị.
- Không chụp token/mật khẩu, không dán token vào website bên ngoài. Chỉ cần chụp realm/client và hai kết quả HTTP 401/200.

### YC5 — Bucket, upload ảnh và tài liệu

**Server:** Object Storage Server (MinIO).

**Thao tác:**

1. Mở `http://localhost:9001/`, đăng nhập bằng tài khoản MinIO của môi trường hiện tại.
2. Mở danh sách bucket: **demo**, **profile-pics**, **documents**.
3. Mở `profile-pics`: kiểm tra `avatar.jpg`; mở `documents`: kiểm tra `report.pdf`.
4. Để chứng minh upload thật, dùng thao tác **Upload** trong Console, tải một ảnh và một PDF mẫu vào bucket tương ứng. Nếu object cùng tên đã tồn tại, dùng tên mới như `avatar-demo.jpg`, `report-demo.pdf` để giữ nguyên dữ liệu cũ.
5. Mở thông tin object: tên, dung lượng, content type. Dùng **Download** tải bản demo và mở file vừa tải để chứng minh nội dung còn nguyên.

Kiểm tra job khởi tạo bằng PowerShell:

```powershell
docker compose logs --tail=80 minio-init
```

**Đạt khi:** bucket và object xuất hiện thật trong Console, upload/download thành công. Log có thể ghi `Created bucket`, `already exists`, `Uploaded`, `Object already exists` hoặc bỏ qua file mẫu nếu không được mount. Chỉ dựa vào dòng `Exited (0)` chưa đủ chứng minh object tồn tại.

**Lời trình bày:**

> “MinIO cung cấp lưu trữ đối tượng tương thích S3. Bucket chứa các object, ví dụ ảnh đại diện và tài liệu PDF. Job minio-init tạo ba bucket và tải hai file mẫu khi có file được mount. Nhóm chứng minh lưu trữ bằng danh sách object và thao tác upload/download thực tế.”

**Minh chứng:** ba bucket, object ảnh/PDF và file tải về mở được. Dashboard frontend chỉ giới thiệu cấu hình và mở Console; thao tác file diễn ra trong MinIO.

### YC6 — Bản ghi DNS cloud.local

**Server:** Internal DNS Server (BIND9).

Kiểm tra zone ngay trong container:

```powershell
docker compose exec -T internal-dns-server named-checkzone cloud.local /etc/bind/db.cloud.local
```

**Mong đợi:** zone được load và kết thúc với `OK`.

Truy vấn từ Windows qua cổng DNS đã publish 1053:

```powershell
nslookup -port=1053 app.cloud.local 127.0.0.1
nslookup -port=1053 web.cloud.local 127.0.0.1
nslookup -port=1053 auth.cloud.local 127.0.0.1
nslookup -port=1053 storage.cloud.local 127.0.0.1
```

| Tên miền | Địa chỉ mong đợi |
| --- | --- |
| app.cloud.local | 172.19.0.4 |
| web.cloud.local | 172.19.0.6 |
| auth.cloud.local | 172.19.0.2 |
| storage.cloud.local | 172.19.0.3 |

Nếu Windows bị chặn truy vấn cổng 1053, kiểm tra từ mạng Docker bằng container kiểm tra dùng một lần. Lệnh này có thể tải image BusyBox nếu chưa có, nên chuẩn bị trước buổi demo:

```powershell
docker run --rm --network cloud-net busybox nslookup app.cloud.local 172.19.0.5
docker run --rm --network cloud-net busybox nslookup web.cloud.local 172.19.0.5
```

`--rm` chỉ xóa container kiểm tra sau khi chạy, không xóa dữ liệu stack. Nếu `nslookup` hiện `Server: Unknown` do thiếu PTR cho DNS server, kiểm tra phần trả lời bản ghi A; tên server Unknown tự nó không chứng minh truy vấn A thất bại.

**Lời trình bày:**

> “BIND9 quản lý zone cloud.local. Nhóm chỉ định DNS server và cổng truy vấn rõ ràng để chứng minh các tên nội bộ được phân giải về IP container. Đây là DNS trong mô hình lab, không phải tên miền Internet công khai.”

**Minh chứng:** `named-checkzone` OK và bốn kết quả DNS. Không dùng bảng cấu hình trong dashboard thay cho truy vấn trực tiếp.

### YC7 — Thêm Web Server vào Prometheus Targets

**Server:** Monitoring Server (Prometheus + Node Exporter).

1. Mở `http://localhost:9090/targets`.
2. Tìm job **web**, chỉ ra ba target:
   - `web-frontend-server:80/metrics`
   - `web-frontend-server1:80/metrics`
   - `web-frontend-server2:80/metrics`
3. Kiểm tra trạng thái từng target và thời gian scrape. Cấu hình mong đợi cả ba **UP** khi hoạt động bình thường.
4. Chỉ thêm job **node** và **prometheus**; tổng cộng 5 target theo cấu hình hiện tại. Chỉ nói “5/5 UP” nếu màn hình thực tế xác nhận.
5. Mở giao diện query `http://localhost:9090/` và chạy:

```promql
up{job="web"}
```

Sau đó:

```promql
web_frontend_up
```

Có thể xuất bảng trạng thái thực tế qua API:

```powershell
$demoTargets = Invoke-RestMethod 'http://localhost:9090/api/v1/targets'
$demoTargets.data.activeTargets |
    Select-Object @{Name='Job';Expression={$_.labels.job}},health,scrapeUrl,lastError |
    Format-Table -AutoSize
```

**Đạt khi:** job web có đủ ba target, scrape thành công. `up` trả 1 khi Prometheus scrape được; `web_frontend_up` là gauge cố định do Nginx trả ở `/metrics`, không phải phép đo CPU/RAM hay kiểm tra toàn bộ chức năng ứng dụng.

**Lời trình bày:**

> “Prometheus scrape theo chu kỳ 15 giây. Nhóm đã thêm cả ba Web Server vào job web. Chỉ số up phản ánh kết quả scrape; Node Exporter cung cấp metrics hệ thống cho các biểu đồ Grafana.”

**Minh chứng:** job web mở đủ ba target và bảng query có ba chuỗi dữ liệu.

### YC8 — Dashboard CPU, RAM và Network

**Server:** Visualization Server (Grafana), nguồn dữ liệu từ Prometheus/Node Exporter.

1. Mở `http://localhost:3000/`, tìm dashboard **System Health of 52400138** hoặc mở trực tiếp `http://localhost:3000/d/system-health-52400138`.
2. Chọn **Last 15 minutes**, bật refresh nếu cần.
3. Chỉ ba panel:
   - **1. CPU Usage (node_cpu_seconds_total)**.
   - **2. Memory Usage (node_memory_MemAvailable_bytes)**.
   - **3. Network Traffic (node_network_receive_bytes_total)**.
4. Di chuột lên đường biểu đồ để hiển thị timestamp và giá trị; chứng minh có mẫu thật, không chỉ có khung panel.
5. Nếu cần, mở query của panel để chỉ nguồn Prometheus datasource `prometheus_ds`.

Các query tiêu biểu đang có trong JSON dashboard:

```promql
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

```promql
node_memory_MemAvailable_bytes
node_memory_MemTotal_bytes
```

```promql
irate(node_network_receive_bytes_total[5m])
irate(node_network_transmit_bytes_total[5m])
```

**Đạt khi:** ba biểu đồ có dữ liệu theo thời gian. Giá trị mạng bằng 0 vẫn có thể hợp lệ khi ít lưu lượng; phân biệt với `No data`.

**Lời trình bày:**

> “Grafana trực quan hóa dữ liệu từ Prometheus. Biểu đồ CPU tính từ thời gian idle; panel RAM hiện hiển thị bộ nhớ available và total theo byte, chưa phải phần trăm RAM đã sử dụng. Biểu đồ Network dùng tốc độ nhận/gửi theo giây.”

**Giới hạn cần giải thích:** Node Exporter trong Compose hiện không mount `/proc`, `/sys`, root filesystem của Windows host. Trên Docker Desktop, không khẳng định các số này là tài nguyên Windows vật lý hay tài nguyên riêng từng container. Đây là metrics mà Node Exporter nhìn thấy trong môi trường chạy hiện tại; không mô tả là dashboard log tập trung.

Nếu panel `No data`: kiểm tra target node, datasource, khoảng thời gian và chờ đủ mẫu cho `irate`. Không tạo tải lớn hoặc dữ liệu giả chỉ để làm biểu đồ đẹp.

**Minh chứng:** ba panel có trục thời gian, đường dữ liệu và tooltip thực tế.

### YC9 — Reverse Proxy chuyển /student/ đến Flask

**Server:** API Gateway (Nginx) và Application Server (Flask).

So sánh truy cập trực tiếp backend với truy cập qua Gateway:

```powershell
curl.exe -i http://localhost:8085/student
curl.exe -i http://localhost/student/
```

Có thể so sánh JSON tự động:

```powershell
$demoDirect = Invoke-RestMethod 'http://localhost:8085/student'
$demoProxy = Invoke-RestMethod 'http://localhost/student/'
$demoDirectJson = ConvertTo-Json -InputObject $demoDirect -Depth 10 -Compress
$demoProxyJson = ConvertTo-Json -InputObject $demoProxy -Depth 10 -Compress
Write-Host ('Noi dung JSON giong nhau: ' + ($demoDirectJson -eq $demoProxyJson))
```

Mở `api-gateway-proxy-server/nginx.conf`, chỉ đoạn:

```nginx
location /student/ {
    proxy_pass http://application-backend-server:8081/student;
    # Các proxy headers được giữ trong cấu hình thật.
}
```

**Đạt khi:** cả hai URL trả HTTP 200, JSON tương đương; tuyến Gateway trả cùng dữ liệu Flask. Route có dấu `/` phía ngoài được chuyển đến `/student` của backend theo cấu hình.

**Lời trình bày:**

> “Người dùng chỉ cần gọi Gateway cổng 80. Nginx nhận /student/ rồi chuyển đến Flask cổng nội bộ 8081 với đường dẫn /student. Cổng 8085 là mapping truy cập trực tiếp để đối chiếu trong lab.”

**Minh chứng:** hai response và đoạn `location /student/`. Không gọi API `/student/` này là request cân bằng tải giữa hai Flask; hiện chỉ có một backend Flask.

### YC10 — Round Robin giữa hai Web Server

**Server:** Nginx Load Balancer và hai Web Node.

Mở `api-gateway-proxy-server/nginx.conf`, chỉ upstream:

```nginx
upstream web_backend {
    server web-frontend-server1:80;
    server web-frontend-server2:80;
}
```

Không có `ip_hash`, `least_conn` hoặc weight khác nhau; Nginx dùng Round Robin mặc định.

Gửi nhiều request và đọc header, không dựa riêng vào refresh trình duyệt:

```powershell
1..8 | ForEach-Object {
    Write-Host "Request $_"
    curl.exe -sS -I -H 'Cache-Control: no-cache' "http://localhost/?demo=$_" |
        Select-String 'HTTP/|X-Upstream-Addr|X-Load-Balancer'
}
```

**Mong đợi:** HTTP 200, `X-Load-Balancer: Nginx-Round-Robin`; `X-Upstream-Addr` xuất hiện cả:

- `172.19.0.8:80` → `web-frontend-server1`.
- `172.19.0.9:80` → `web-frontend-server2`.

Chạy khi ít request đồng thời để dễ quan sát luân phiên. Request từ tab khác, ảnh, CSS, JS hoặc trình duyệt cũng tham gia lịch phân phối; không bảo đảm mọi lần bấm refresh nhìn thấy nhãn đổi 1–2 tuyệt đối.

Sau đó mở Dashboard → **Load Balancer → Inspect request**. Chỉ ra kết quả header từ request mới và nhãn **Serving HTML: Node 1/Node 2** ở footer. Hai nhãn có thể khác vì thuộc hai request riêng.

**Đạt khi:** nhiều request thực tới Gateway đi qua cả hai upstream, giao diện hai Node đồng nhất, `/blog/` vẫn mở đúng máy chủ chính.

**Lời trình bày:**

> “Nginx phân phối các request web giữa hai Node theo Round Robin. Nhóm chứng minh bằng địa chỉ upstream trong response header. Blog và API có tuyến riêng nên không đi qua upstream web_backend.”

**Minh chứng:** bảng header nhiều request có cả `.8:80` và `.9:80`, kèm cấu hình upstream.

## 5. Kết luận — 30 giây

> “Nhóm đã trình diễn đủ 9 loại server qua 10 yêu cầu mở rộng: website và blog, JSON API, database quan hệ, JWT, object storage, DNS nội bộ, giám sát Web, dashboard tài nguyên, reverse proxy và cân bằng tải. Bằng chứng được lấy từ phản hồi HTTP, SQL, DNS và metrics thực tế. Dashboard frontend là nơi điều hướng và giới thiệu cấu hình; các chức năng quản trị và metrics được chứng minh tại dịch vụ tương ứng.”

Chỉ nói “đã đạt đủ 10 yêu cầu” sau khi các bước thực tế đều thành công. Nếu có mục lỗi, ghi rõ mục đó và bằng chứng hiện có.

## 6. Checklist bằng chứng trước khi kết thúc

| Mục | Bằng chứng cần có | Đã kiểm tra |
| --- | --- | --- |
| YC1 | Website, listing, ba bài đầy đủ nội dung và hình | ☐ |
| YC2 | Student API HTTP 200 và JSON đúng file nguồn | ☐ |
| YC3 | `studentdb`, `students`, schema và SELECT | ☐ |
| YC4 | Realm/client; 401 thiếu token; 200 JWT hợp lệ | ☐ |
| YC5 | Ba bucket; ảnh/PDF; upload và tải file mở được | ☐ |
| YC6 | Zone OK; bốn tên miền trả IP đúng | ☐ |
| YC7 | Ba Web targets và dữ liệu scrape thực tế | ☐ |
| YC8 | CPU/RAM/Network đều có dữ liệu | ☐ |
| YC9 | Response trực tiếp và qua Gateway tương đương | ☐ |
| YC10 | Nhiều request đi qua cả hai upstream | ☐ |

Lưu ảnh bằng tên `YC01-web-blog`, `YC02-api` … `YC10-round-robin` để đối chiếu nhanh với báo cáo. Không lưu token, mật khẩu, cookie phiên quản trị hoặc file người dùng thật trong ảnh minh chứng.

## 7. Xử lý lỗi nhanh trong buổi demo

| Hiện tượng | Kiểm tra và xử lý |
| --- | --- |
| `localhost` trả Apache/XAMPP | Dừng Apache để giải phóng cổng 80; khởi động lại riêng Gateway |
| Gateway `Created`, `Address already in use` | Kiểm tra xung đột cổng; chạy lại Gateway sau khi cổng trống. Nếu còn lỗi, kiểm tra log và network, không xóa volume |
| HTTP 502 | `docker compose ps -a` và log Gateway/backend; kiểm tra upstream đúng dịch vụ/cổng |
| Dashboard mở được nhưng API 404 | Đang vào `:8080` hoặc Python preview? Dùng Gateway `http://localhost/` |
| Student JSON có 5 dòng, SQL có 3 dòng | Bình thường với dữ liệu khởi tạo hiện tại: hai nguồn độc lập |
| MariaDB không có bảng mong đợi | Volume có thể được tạo trước script SQL mới; kiểm tra init/log, không xóa dữ liệu |
| `Account is not fully set up` | Kiểm tra profile user, Required Actions và Temporary password; chuẩn bị user trước demo |
| JWT vẫn 401 | Kiểm tra token mới, issuer, audience `flask-app`, JWKS và user đúng realm; không tắt xác minh JWT |
| Keycloak 404 tại `/admin/` cổng 80 | Dùng `http://localhost:8081/admin/` |
| MinIO thiếu object | Xem `minio-init` logs và file mount; upload file mẫu qua Console |
| DNS timeout | Dùng cổng 1053 từ Windows hoặc truy vấn từ container trong cloud-net |
| Prometheus target DOWN | Xem Last Error, container và endpoint `/metrics`; chờ chu kỳ scrape |
| Grafana `No data` | Kiểm tra Prometheus datasource, target node, thời gian truy vấn và đủ mẫu |
| Refresh không đổi nhãn Node | Kiểm tra nhiều response header khi ít request đồng thời; các request assets cũng được cân bằng |

Lệnh xem log tổng quát:

```powershell
docker compose ps -a
docker compose logs --tail=60 api-gateway-proxy-server
docker compose logs --tail=60 application-backend-server
docker compose logs --tail=60 authentication-identity-server
docker compose logs --tail=60 monitoring-prometheus-server
```

## 8. Những câu dễ bị hỏi

**Vì sao 9 server mà có 13 service?** Có ba Web Frontend, Monitoring gồm Prometheus và Node Exporter, và có thêm job `minio-init`; các loại server được nhóm theo vai trò.

**Student API đã kết nối MariaDB chưa?** Chưa. API đọc `students.json`; MariaDB được chứng minh riêng bằng database, schema và truy vấn SQL.

**Reverse Proxy khác Load Balancer thế nào trong dự án?** Tuyến `/student/` proxy đến một Flask backend. Tuyến `/` phân phối request giữa hai Web Node trong upstream `web_backend`.

**Tại sao Blog không đổi Node?** `/blog/` có location riêng chuyển tới Web Server chính để giữ đủ ba bài viết.

**Giá trị dashboard frontend có realtime không?** Bốn số tổng quan là cấu hình. Badge backend là kết quả kiểm tra `/api/hello`; header upstream là từ request Inspect. Metrics tài nguyên thật xem tại Prometheus/Grafana.

**Node Exporter đo Windows hay từng container?** Không khẳng định như vậy với cấu hình hiện tại. Nó xuất metrics của môi trường mà nó quan sát được; Compose chưa cấu hình đầy đủ host mounts để tuyên bố giám sát host Windows hoặc từng container.

**Có phải mô hình production hoàn chỉnh không?** Đây là môi trường lab mô phỏng. Cấu hình Keycloak start-dev/Password Grant và console publish phục vụ demo; vận hành công khai cần đánh giá thêm TLS, danh tính, quyền truy cập và bảo vệ dữ liệu.

## 9. Sau buổi demo

```powershell
docker compose stop
```

Lệnh này dừng container và giữ dữ liệu. Không dùng `docker compose down -v`, không xóa Docker volumes. Không cần push hoặc triển khai lại EC2 để hoàn thành demo local.

Các file nguồn đối chiếu: `docker-compose.yml`, `api-gateway-proxy-server/nginx.conf`, `application-backend-server/app.py`, `application-backend-server/students.json`, `relational-database-server/init/002_studentdb.sql`, `authentication-identity-server/realm-export.json`, `object-storage-server/init_buckets.py`, `internal-dns-server/db.cloud.local`, `monitoring-prometheus-server/prometheus.yml`, `monitoring-grafana-dashboard-server/provisioning/dashboards/system_health_52400138.json`.
