"""Generate the static dashboard. No framework or build dependency required."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web-frontend-server' / 'html'
PATHS = {
    'cloud': 'M5 17a4 4 0 0 1 0-8 7 7 0 0 1 13-2 5 5 0 0 1 0 10Z',
    'grid': 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    'layers': 'm12 3 10 5-10 5L2 8Z M2 12l10 5 10-5 M2 16l10 5 10-5',
    'server': 'M3 3h18v7H3z M3 14h18v7H3z M7 6.5h.01 M7 17.5h.01 M12 7h5 M12 18h5',
    'code': 'm8 6-6 6 6 6 M16 6l6 6-6 6 M14 3l-4 18',
    'database': 'M4 6c0-4 16-4 16 0s-16 4-16 0 M4 6v12c0 4 16 4 16 0V6 M4 12c0 4 16 4 16 0',
    'shield': 'm12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6Z m-4 10 3 3 5-6',
    'box': 'm12 2 10 5v10l-10 5L2 17V7Z M2 7l10 5 10-5 M12 12v10 M7 4.5l10 5v5',
    'network': 'M9 2h6v6H9z M2 16h6v6H2z M16 16h6v6h-6z M12 8v4 M5 16v-4h14v4',
    'chart': 'M3 3v18h18 M7 16v-4 M12 16V7 M17 16v-7',
    'balance': 'M12 3v7 M4 21v-7h16v7 M8 6l4-4 4 4 M1 18l3 4 3-4 M17 18l3 4 3-4',
    'book': 'M12 5C8 2 3 3 2 4v16c3-2 7-2 10 0 3-2 7-2 10 0V4c-3-2-7-2-10 1Z M12 5v15',
    'file': 'M14 2H4v20h16V8Z M14 2v6h6 M8 12h8 M8 16h8',
    'arrow': 'M4 12h16 M14 6l6 6-6 6',
    'external': 'M14 3h7v7 M21 3l-12 12 M10 3H3v18h18v-7',
    'sun': 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M12 1v3 M12 20v3 M1 12h3 M20 12h3 M4 4l2 2 M18 18l2 2 M4 20l2-2 M18 6l2-2',
    'menu': 'M3 6h18 M3 12h18 M3 18h18',
    'refresh': 'M20 7a9 9 0 1 0 1 8 M20 2v6h-6',
    'info': 'M12 8h.01 M12 11v6 M22 12a10 10 0 1 0-20 0 10 10 0 0 0 20 0',
    'copy': 'M8 8h13v13H8z M16 4V1H1v15h3',
    'github': 'M9 19c-5 2-5-3-7-3 M15 22v-4c0-1-.3-2-1-2 4-.5 7-2 7-6 0-2-.6-3-2-4 .3-1 .4-3-.2-4-2 0-4 2-4 2a13 13 0 0 0-6 0S7 2 5 2c-.6 1-.5 3-.2 4C3.5 7 3 8 3 10c0 4 3 5.5 7 6-.7.5-1 1-1 2v4',
    'chevron': 'm14 6-6 6 6 6',
}

def icon(name):
    return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="{PATHS[name]}"/></svg>'

def badge(text, cls=''):
    return f'<span class="badge {cls}">{text}</span>'

def button(text, href, glyph='arrow', primary=False, extra=''):
    return f'<a class="btn{" primary" if primary else ""}" href="{href}" {extra}>{icon(glyph)}{text}</a>'

def panel(title, subtitle, body, extra=''):
    return f'<div class="panel"><div class="panel-head"><div><h2>{title}</h2><p>{subtitle}</p></div>{extra}</div>{body}</div>'

def intro(label, title, description, actions=''):
    return f'<div class="page-intro"><div><div class="eyebrow">{label}</div><h1>{title}</h1><p>{description}</p></div><div class="intro-actions">{actions}</div></div>'

def details(rows):
    return '<dl class="details">' + ''.join(f'<div><dt>{a}</dt><dd>{b}</dd></div>' for a,b in rows) + '</dl>'

def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th scope="col">{h}</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join(f'<td>{v}</td>' for v in row)+'</tr>' for row in rows) + '</tbody></table></div>'

SERVICES = [
    ('Access Layer', 'Nginx Gateway', 'balance', 'Reverse Proxy · Round Robin đến hai Web Node.', 'Nginx', '80', '/', 'api-gateway-proxy-server'),
    ('Presentation Layer', 'Web Frontend', 'server', 'Website tĩnh trên ba máy chủ Nginx.', 'Nginx', '8080 / nội bộ 80', '/', 'web-frontend-server · server1 · server2'),
    ('Application Layer', 'Application API', 'code', 'REST API và xác minh JWT do Keycloak cấp.', 'Flask', '8085 → 8081', '#api-explorer', 'application-backend-server'),
    ('Data Layer', 'Relational Database', 'database', 'Hai database minicloud và studentdb.', 'MariaDB 11', 'nội bộ 3306', '#database', 'relational-database-server'),
    ('Data Layer', 'Object Storage', 'box', 'Lưu trữ S3-compatible và job khởi tạo bucket.', 'MinIO', '9000 / 9001', '#object-storage', 'object-storage-server · minio-init'),
    ('Identity Layer', 'Authentication', 'shield', 'Danh tính tập trung, OIDC và JWT.', 'Keycloak 26.4', '8081 → 8080', '#authentication', 'authentication-identity-server'),
    ('Network Layer', 'Internal DNS', 'network', 'Phân giải tên miền nội bộ cloud.local.', 'BIND9', '1053 → 53', '#dns', 'internal-dns-server'),
    ('Observability Layer', 'Metrics Collection', 'chart', 'Thu thập metrics theo chu kỳ 15 giây.', 'Prometheus', '9090', '#monitoring', 'monitoring-prometheus-server'),
    ('Observability Layer', 'Host Metrics', 'server', 'Xuất metrics hệ thống cho Prometheus.', 'Node Exporter', '9100', '#monitoring', 'monitoring-node-exporter-server'),
    ('Observability Layer', 'Visualization', 'grid', 'Dashboard CPU, bộ nhớ và lưu lượng mạng.', 'Grafana', '3000', '#monitoring', 'monitoring-grafana-dashboard-server'),
]

def service_card(item):
    layer, name, glyph, desc, tech, port, href, service = item
    return f'<article class="service-card"><div class="service-top"><span class="tile-icon">{icon(glyph)}</span>{badge("Not Monitored")}</div><h3>{name}</h3><p>{desc}</p><div class="service-meta"><span>{tech} · {port}</span><a href="{href}" aria-label="Mở {name}">Mở ↗</a></div><code class="service-id">{service}</code></article>'

def flow_box(title, sub, glyph, accent=False):
    return f'<div class="flow-box{" accent" if accent else ""}">{icon(glyph)}<div><b>{title}</b><small>{sub}</small></div></div>'

topology = f'''<div class="topology"><div class="flow-center">{flow_box('Client','Browser / HTTP :80','cloud')}<div class="flow-arrow">↓</div>{flow_box('Nginx Gateway','Reverse Proxy · 172.19.0.13','balance',True)}</div><div class="flow-arrow">↓</div><div class="flow-branches">{flow_box('Web Nodes 1 & 2','/ · Round Robin','server')}{flow_box('Flask API','/api/ · /student/','code')}{flow_box('Main Web Server','/blog/ · bài viết','book')}</div><p class="flow-caption">Luồng HTTP qua Gateway · cloud-net / 172.19.0.0/16</p></div>'''

navs = [('overview','Overview','grid'),('infrastructure','Infrastructure','layers'),('services','Services','server'),('api-explorer','API Explorer','code'),('database','Database','database'),('authentication','Authentication','shield'),('object-storage','Object Storage','box'),('dns','DNS','network'),('monitoring','Monitoring','chart'),('load-balancer','Load Balancer','balance')]
nav = ''.join(f'<a href="#{slug}" data-nav="{slug}" title="{label}">{icon(glyph)}<span class="nav-text">{label}</span></a>' for slug,label,glyph in navs)

quick = '<ul class="resource-list">'
for label, desc, glyph, href in [('API Explorer','Thử nghiệm REST endpoints','code','#api-explorer'),('Grafana Dashboard','CPU, Memory & Network','chart','#monitoring'),('Object Storage','Buckets & sample objects','box','#object-storage'),('Project Documentation','Hướng dẫn vận hành hệ thống','book','#documentation')]:
    quick += f'<li><span class="tile-icon">{icon(glyph)}</span><div><a href="{href}"><b>{label}</b><small>{desc}</small></a></div><a href="{href}" aria-label="Mở {label}">{icon("external")}</a></li>'
quick += '</ul><div class="panel-foot">' + icon('info') + 'Trạng thái dịch vụ chưa được giám sát tại đây.</div>'

stats = '<div class="config-note">'+icon('info')+'Static Configuration · Số liệu từ cấu hình dự án, không phải trạng thái runtime.</div><div class="stats">'
for number, name, sub, glyph, color in [('9','Server Types','Nhóm máy chủ hạ tầng','layers',''),('13','Compose Services','12 services + 1 initialization job','box','cyan'),('3','Web Frontends','Main server + 2 balanced nodes','server','violet'),('2','Deployment Environments','Local Docker & AWS EC2','cloud','amber')]:
    stats += f'<div class="stat"><div class="stat-top">{name}<span class="tile-icon {color}">{icon(glyph)}</span></div><strong>{number}</strong><small>{sub}</small></div>'
stats += '</div>'

blog = '<div class="blog-preview">'
for i, cat, title in [(1,'FOUNDATION','Tổng quan về Cloud Computing'),(2,'CONTAINERS','Docker và công nghệ Container'),(3,'INFRASTRUCTURE','Triển khai ứng dụng trên AWS EC2')]:
    blog += f'<a href="/blog/blog{i}.html"><img src="/assets/cover-{i}.svg" alt="" loading="lazy"><div class="copy"><small>{cat}</small><h3>{title}</h3><span class="text-link">Đọc bài viết →</span></div></a>'
blog += '</div>'

sections = {}
sections['overview'] = intro('Workspace / Overview','Infrastructure overview','Một góc nhìn rõ ràng về toàn bộ hạ tầng MyMiniCloud.',button('Documentation','#documentation','book')+button('Explore services','#services','arrow',True)) + stats + '<div class="overview-grid">'+panel('Infrastructure topology','Các tuyến truy cập trong hệ thống',topology,badge('Static Configuration','blue'))+panel('Quick access','Không gian làm việc của bạn',quick)+'</div>' + '<div class="section-heading"><div><h2>Core services</h2><p>Các thành phần tạo nên đám mây của bạn.</p></div><a class="text-link" href="#services">Tất cả dịch vụ '+icon('arrow')+'</a></div><div class="service-grid">'+''.join(service_card(SERVICES[i]) for i in [0,2,3,5,4,7])+'</div><div class="section-heading"><div><h2>From the cloud journal</h2><p>Kiến thức nền tảng, kết nối với thực hành.</p></div><a class="text-link" href="/blog/">Tất cả bài viết →</a></div>'+blog

sections['infrastructure'] = intro('Architecture','Built as one. Designed in layers.','9 nhóm máy chủ, 13 Compose services trên Docker bridge cloud-net.') + panel('Gateway routing','Các mũi tên biểu diễn tuyến HTTP đã cấu hình.',topology,badge('Static Configuration','blue'))+'<div class="notice">MariaDB, MinIO và DNS là các dịch vụ hạ tầng riêng. API student hiện đọc JSON; không có kết nối truy vấn MariaDB trong Flask.</div>'+panel('Network inventory','Địa chỉ cố định trong docker-compose.yml',table(['Service','Internal IP','Role'],[(escape(s),'172.19.0.'+str(ip),role) for s,ip,role in [('authentication-identity-server',2,'Identity'),('object-storage-server',3,'Data'),('application-backend-server',4,'Application'),('internal-dns-server',5,'Network'),('web-frontend-server',6,'Blog'),('relational-database-server',7,'Data'),('web-frontend-server1',8,'Presentation'),('web-frontend-server2',9,'Presentation'),('monitoring-node-exporter-server',10,'Observability'),('monitoring-prometheus-server',11,'Observability'),('monitoring-grafana-dashboard-server',12,'Observability'),('api-gateway-proxy-server',13,'Access')]]))

sections['services'] = intro('Service directory','Every service. One workspace.','Công nghệ, vai trò và đường dẫn truy cập theo từng lớp hạ tầng.')
for layer in dict.fromkeys(s[0] for s in SERVICES):
    sections['services'] += f'<h2 class="layer-title">{layer}</h2><div class="service-grid">'+''.join(service_card(s) for s in SERVICES if s[0]==layer)+'</div>'

sections['api-explorer'] = intro('Developer tools','API Explorer','Gửi request thật đến các endpoint hiện có qua Gateway.') + '<div class="two-col">'+panel('Request','Chỉ gửi Bearer Token khi bạn nhấn Send Request.','''<form id="api-form" class="panel-body"><label for="endpoint">Endpoint</label><div class="endpoint"><span class="badge blue">GET</span><select id="endpoint" name="endpoint"><option value="/api/hello">/api/hello</option><option value="/student/">/student/</option><option value="/api/secure">/api/secure</option></select></div><div class="token-row" id="token-row" hidden><label for="bearer-token">Bearer Token (tùy chọn để kiểm thử 401)</label><input id="bearer-token" name="bearer-token" type="password" autocomplete="off" spellcheck="false" placeholder="Dán token tại đây" aria-describedby="token-help"><p id="token-help" class="small">Token được che, chỉ giữ trong bộ nhớ trang và không lưu vào Local Storage.</p></div><button class="btn primary" id="send-request" type="submit">'''+icon('arrow')+'''Send Request</button><p class="small" style="margin-top:18px">/student/ trả dữ liệu từ students.json. /api/secure xác minh JWT bằng JWKS của Keycloak.</p></form>''')+panel('Response','HTTP status & response body','<div class="panel-body response-info" id="response-status" role="status" aria-live="polite">Chưa gửi request.</div><pre class="api-response" id="api-response" tabindex="0">Chọn endpoint và nhấn Send Request để bắt đầu.</pre>','<button class="btn" id="copy-response" type="button" disabled>'+icon('copy')+'Copy</button>')+'</div><div class="notice">Khi mở trực tiếp Web Server tại :8080, API chưa đi qua Gateway. Dùng địa chỉ Gateway (cổng 80) để thử các endpoint.</div>'

sections['database'] = intro('Data layer','Database overview','MariaDB 11 · Dữ liệu khởi tạo từ SQL, không truy vấn trực tiếp từ trình duyệt.')+'<div class="two-col">'+panel('minicloud','Application database','<div class="panel-body">'+details([('Table','<code>notes</code>'),('Columns','id · title · created_at'),('Initialization','001_init.sql'),('Status','Not Monitored')])+'</div>')+panel('studentdb','Student database','<div class="panel-body">'+details([('Table','<code>students</code>'),('Columns','id · student_id · fullname · dob · major'),('Initialization','002_studentdb.sql'),('Status','Not Monitored')])+'</div>')+'</div><div class="notice"><strong>Nguồn dữ liệu API:</strong> /student/ đọc từ <code>students.json</code>, chưa truy vấn MariaDB. Các bảng trên là cấu hình khởi tạo, không phải bản ghi được đọc trực tiếp.</div>'+button('Thử Student API','#api-explorer','code')

steps = '<ol class="step-list">'+''.join(f'<li><div><strong>{a}</strong>{b}</div></li>' for a,b in [('Client → Keycloak','Người dùng xác thực tại Keycloak để nhận access token.'),('Client → Flask','Gửi Bearer Token đến GET /api/secure qua Gateway.'),('Flask → Keycloak JWKS','Đọc khóa công khai, kiểm tra chữ ký RS256, issuer, audience và hạn sử dụng.'),('Flask → Client','Trả JSON nếu token hợp lệ; token thiếu hoặc không hợp lệ trả 401.')])+'</ol>'
sections['authentication'] = intro('Identity layer','Centralized authentication','Keycloak Authentication Server · OpenID Connect & JWT.')+'<div class="two-col">'+panel('Identity configuration','Static Configuration','<div class="panel-body">'+details([('Realm','<code>realm_52400114</code>'),('Client','<code>flask-app</code>'),('Algorithm','RS256'),('Public port','8081'),('Protected endpoint','<code>/api/secure</code>')])+'<p class="small">Console mở trực tiếp trên cổng đã publish. Tuyến /auth/ hiện chưa bảo đảm redirect Admin Console.</p>'+button('Keycloak Admin Console','#authentication','external',extra='data-console="keycloak" target="_blank" rel="noopener noreferrer"')+'</div>')+panel('Token verification flow','Luồng xác thực hiện có trong Flask','<div class="panel-body">'+steps+'</div>')+'</div><div class="notice">Issuer trong Compose hiện là http://localhost:8081/realms/realm_52400114. Token cấp qua hostname khác có thể không khớp issuer. Giao diện không thay đổi cấu hình JWT.</div>'

sections['object-storage'] = intro('Data layer','Object storage','MinIO · S3-compatible storage cho các đối tượng trong bucket.',button('Open MinIO Console','#object-storage','external',True,'data-console="minio" target="_blank" rel="noopener noreferrer"'))+panel('Buckets','Cấu hình khởi tạo · không phải danh sách được đọc trực tiếp từ MinIO',table(['Bucket','Purpose','Sample object','Status'],[('demo','Bucket mẫu','—','Not Monitored'),('profile-pics','Ảnh đại diện','avatar.jpg','Not Monitored'),('documents','Tài liệu','report.pdf','Not Monitored')]),badge('Static Configuration','blue'))+'<div class="notice">Bucket là vùng chứa các object. <code>minio-init</code> tạo ba bucket; chỉ tải avatar.jpg và report.pdf khi có file mẫu được mount. Không khẳng định object hiện đang tồn tại. Quản lý upload/download trong MinIO Console.</div>'

sections['dns'] = intro('Network layer','Internal DNS','BIND9 · Vùng tên miền cloud.local.')+panel('DNS records','Các bản ghi A trong db.cloud.local',table(['Hostname','Type','Internal address','Source'],[(name+'.cloud.local','A',ip,'Static Configuration') for name,ip in [('ns','172.19.0.5'),('app','172.19.0.4'),('web','172.19.0.6'),('auth','172.19.0.2'),('storage','172.19.0.3'),('app-backend','172.19.0.4'),('minio','172.19.0.3'),('keycloak','172.19.0.2')]]),badge('cloud.local','blue'))+'<div class="notice">DNS publish trên cổng 1053 TCP/UDP. Đây là bản ghi cấu hình, không phải kết quả nslookup trực tiếp. Địa chỉ 172.19.x.x thuộc mạng Docker nội bộ.</div>'

sections['monitoring'] = intro('Observability layer','See your infrastructure clearly.','Mở các công cụ hiện có để xem metrics thật. Dashboard này không tạo dữ liệu CPU/RAM.')+'<div class="service-grid">'
for name, key, glyph, port, desc in [('Prometheus','prometheus','chart','9090','Thu thập metrics, truy vấn PromQL và kiểm tra targets.'),('Grafana','grafana','grid','3000','Dashboard CPU, Memory và Network đã provisioning.'),('Node Exporter','exporter','server','9100','Endpoint /metrics cung cấp metrics cho Prometheus.')]:
    sections['monitoring'] += f'<article class="service-card"><div class="service-top"><span class="tile-icon">{icon(glyph)}</span>{badge("Not Monitored")}</div><h3>{name}</h3><p>{desc}</p><p class="small">Published port :{port}</p>'+button('Open '+name,'#monitoring','external',extra=f'data-console="{key}" target="_blank" rel="noopener noreferrer"')+'</article>'
sections['monitoring'] += '</div><div class="notice">Các liên kết console dùng hostname đang truy cập và cổng publish HTTP của Compose; chưa được kiểm tra khả dụng. Có thể cấu hình URL công khai khi dùng HTTPS hoặc reverse proxy.</div>'+panel('Scrape configuration','prometheus.yml · scrape_interval / evaluation_interval: 15s',table(['Job','Configured targets','Metrics path'],[('node','monitoring-node-exporter-server:9100','/metrics'),('prometheus','localhost:9090 (bên trong container)','/metrics'),('web','web-frontend-server:80 · server1:80 · server2:80','/metrics')] ))

sections['load-balancer'] = intro('Access layer','Traffic, evenly distributed.','Nginx Round Robin · phân phối request qua hai Web Node.')+panel('Request routing','Không mô phỏng số lượt truy cập.',f'<div class="topology"><div class="flow-center">{flow_box("Client","HTTP :80","cloud")}<div class="flow-arrow">↓</div>{flow_box("Nginx Gateway","upstream web_backend","balance",True)}</div><div class="flow-arrow">↓</div><div class="two-col">{flow_box("Web Server 1","web-frontend-server1 · .8","server")}{flow_box("Web Server 2","web-frontend-server2 · .9","server")}</div><p class="flow-caption">Request / và tài nguyên được cân bằng riêng · /blog/ luôn về máy chủ chính.</p></div>')+'<div class="panel panel-body" style="margin-top:20px"><h2>Inspect a real request</h2><p class="small">Đọc X-Upstream-Addr và X-Load-Balancer từ một GET / mới. Node này có thể khác node đã phục vụ trang hiện tại.</p><button class="btn primary" id="inspect-node" type="button">'+icon('refresh')+'Inspect request</button><div class="node-result" id="node-result" role="status" aria-live="polite">Chưa gửi request. Nhãn node trên footer thuộc HTML đang xem.</div></div>'

sections['documentation'] = intro('Project guide','Documentation','Hướng dẫn nhanh cho buổi trình diễn và vận hành hệ thống.',button('GitHub Repository','https://github.com/TrongPhuc2403/MyMiniCloud','github',extra='data-repository target="_blank" rel="noopener noreferrer"'))+'<div class="two-col">'+panel('Demo walkthrough','Khám phá hệ thống theo thứ tự.','<div class="panel-body"><ol class="step-list">'+''.join(f'<li><div><strong><a href="{link}">{title}</a></strong>{desc}</div></li>' for title,link,desc in [('Architecture','#infrastructure','Xem topology và địa chỉ các dịch vụ.'),('API Explorer','#api-explorer','Thử /api/hello, /student/ và /api/secure.'),('Load Balancer','#load-balancer','Kiểm tra header từ request thực tế.'),('Monitoring','#monitoring','Mở Prometheus, Grafana để xem metrics.'),('Cloud journal','/blog/','Ba bài viết Cloud Computing, Docker và EC2.')])+'</ol></div>')+panel('Deployment notes','Local Docker & AWS EC2','<div class="panel-body"><p class="small">Truy cập qua Gateway cổng 80. Console dùng các cổng publish riêng; khả dụng phụ thuộc firewall và Security Group.</p><p class="small">Với HTTPS hoặc tên miền riêng, cập nhật URL công khai trong assets/config.js và đồng bộ ba frontend. Không gửi token qua kết nối không tin cậy.</p><p class="small">9 loại máy chủ là nhóm chức năng; 13 Compose services bao gồm ba frontend và minio-init. Đây là số liệu cấu hình.</p>'+button('Đọc README trên GitHub','https://github.com/TrongPhuc2403/MyMiniCloud/blob/feature/final-integration/README_MyMiniCloud.md','book',extra='target="_blank" rel="noopener noreferrer"')+'</div>')+'</div>'

html = '''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="MyMiniCloud — Cloud Infrastructure Management. Docker, Nginx, Flask và các dịch vụ hạ tầng."><meta name="theme-color" content="#2563eb"><title>Overview · MyMiniCloud</title><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><script src="/assets/theme.js"></script><link rel="stylesheet" href="/assets/dashboard.css"><script src="/assets/config.js" defer></script><script src="/assets/dashboard.js" defer></script></head>
<body data-node="Main"><a class="skip" href="#main">Đến nội dung chính</a>
<aside class="sidebar" id="sidebar" aria-label="Điều hướng workspace"><a class="brand" href="/#overview"><span class="brand-mark">'''+icon('cloud')+'''</span><span class="brand-name">MyMini<span style="color:var(--blue)">Cloud</span></span></a>
<div class="workspace"><span class="workspace-icon">'''+icon('layers')+'''</span><div><b>Cloud workspace</b><small>Cloud Infrastructure Management</small></div></div><div class="nav-label">WORKSPACE</div><nav aria-label="Điều hướng chính">'''+nav+'''</nav><div class="nav-label">RESOURCES</div><nav aria-label="Tài nguyên"><a href="/blog/" title="Blog">'''+icon('book')+'''<span class="nav-text">Blog</span></a><a href="#documentation" data-nav="documentation" title="Documentation">'''+icon('file')+'''<span class="nav-text">Documentation</span></a></nav><div class="sidebar-bottom"><div class="project-note"><b>A small cloud. A big idea.</b><p>Đồ án Điện toán đám mây<br>Docker Compose × AWS EC2</p><a href="#infrastructure">Khám phá kiến trúc ↗</a></div><div class="team"><span class="avatar">MC</span><div><b>MyMiniCloud Team</b><small>Phúc · Hoàn · Long</small></div></div></div><button class="icon-button sidebar-toggle" id="collapse-sidebar" type="button" aria-label="Thu gọn sidebar" aria-expanded="true">'''+icon('chevron')+'''</button></aside><button class="scrim" id="menu-scrim" aria-label="Đóng menu" tabindex="-1"></button>
<div class="app"><header class="topbar"><button class="icon-button mobile-menu" id="mobile-menu" type="button" aria-label="Mở menu" aria-expanded="false" aria-controls="sidebar">'''+icon('menu')+'''</button><div class="topbar-title">Workspace <span style="padding:0 10px">/</span><strong id="current-page">Overview</strong><span class="subheading"> · Cloud Infrastructure Management</span></div><div class="top-actions"><span class="badge" id="backend-status" role="status" aria-live="polite"><span class="status-dot"></span>Backend · chưa kiểm tra</span><span class="divider"></span><button class="icon-button" data-theme-toggle type="button" aria-label="Chuyển giao diện">'''+icon('sun')+'''</button>'''+button('GitHub','https://github.com/TrongPhuc2403/MyMiniCloud','github',extra='data-repository target="_blank" rel="noopener noreferrer"')+'''</div></header><main class="content" id="main" tabindex="-1"><noscript><div class="notice">Bật JavaScript để dùng API Explorer, chuyển giao diện và kiểm tra backend. Các nội dung cấu hình bên dưới vẫn đọc được.</div></noscript>'''
for key, body in sections.items():
    html += f'<section id="{key}" data-page="{key}" aria-label="{key.replace("-", " ").title()}">{body}</section>\n'
html += '<footer class="footer"><span>© MyMiniCloud · Cloud Computing Project</span><span><span class="status-dot"></span>Serving HTML: <b id="serving-node">Main</b> · cloud-net</span></footer></main></div></body></html>\n'
WEB.joinpath('index.html').write_text(html, encoding='utf-8')
print('Generated canonical dashboard: web-frontend-server/html/index.html')
