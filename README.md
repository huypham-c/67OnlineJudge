# 67 Online Judge System

Hệ thống chấm điểm lập trình trực tuyến (Online Judge) tích hợp quản lý lớp học, được thiết kế để hỗ trợ việc nộp bài, chấm điểm tự động và theo dõi tiến độ học tập của sinh viên.

## 🌟 Tính năng chính

- **Chấm điểm tự động:** Hỗ trợ ngôn ngữ Python và C++ với môi trường thực thi cô lập bằng Docker Sandbox để đảm bảo an toàn hệ thống.
- **Quản lý học thuật:** Cho phép Giáo viên/Admin tạo lớp học, bài tập và các kỳ thi (Problemsets) với thời gian bắt đầu và kết thúc cụ thể.
- **Bảng xếp hạng thời gian thực (Live Leaderboard):** Hiển thị thứ hạng sinh viên dựa trên tổng điểm cao nhất của các bài tập.
- **Hàng đợi ưu tiên (Priority Queue):** Sắp xếp thứ tự chấm bài dựa trên tính chất của bài nộp (ví dụ: bài thi được ưu tiên hơn bài tập về nhà).
- **Lịch sử bài nộp:** Sinh viên có thể xem lại toàn bộ quá trình nộp bài, điểm số chi tiết và mã nguồn đã nộp.
- **Quản lý người dùng:** Phân quyền chặt chẽ giữa Admin, Giáo viên và Sinh viên thông qua JWT Authentication.

## 🛠 Techstack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python), JWT Authentication, SQLite.
- **Frontend:** HTML5, [Tailwind CSS](https://tailwindcss.com/), Vanilla JavaScript, Quill.js (Rich Text Editor).
- **Core Engine:** Docker (Sandbox execution), [Pydantic](https://docs.pydantic.dev/) (Data validation).

## 📐 Kiến trúc và Giải thuật

Dự án chú trọng vào việc áp dụng các kiến thức về Cấu trúc dữ liệu và Giải thuật (DSA) để giải quyết các vấn đề hiệu năng:

1. **Hàng đợi chấm bài (Submission Queue):** Sử dụng `PriorityQueue` dựa trên `Heap` để quản lý các bài nộp. Độ phức tạp $O(\log N)$ cho cả thao tác thêm bài mới và lấy bài ra chấm.
2. **Bảng xếp hạng (Leaderboard):** Được lưu trữ trực tiếp trên RAM bằng `Red-Black Tree` (BST tự cân bằng). Điều này giúp thao tác cập nhật điểm số và tìm kiếm luôn duy trì ở $O(\log N)$, tránh tình trạng suy biến cây khi điểm số tăng dần.
3. **Bộ dọn rác (Garbage Collector):** Một worker chạy ngầm định kỳ quét và giải phóng các cây Leaderboard không còn hoạt động sau 15 phút để tối ưu hóa dung lượng RAM và tránh rò rỉ bộ nhớ (Memory Leak).

## 📂 Cấu trúc thư mục

- `API/api.py`: Điểm nhập chính của ứng dụng, chứa toàn bộ hệ thống API và các Background Workers.
- `core/`: Chứa các module cốt lõi như máy chấm (`judge.py`) và các thư viện cấu trúc dữ liệu tự cài đặt (`libs.py`).
- `db/`: Quản lý kết nối và các truy vấn cơ sở dữ liệu SQLite.
- `models/`: Định nghĩa các lớp đối tượng (User, Student, Problem, Submission,...) theo tư duy Hướng đối tượng (OOP
- `front_end/`: Giao diện người dùng và logic xử lý phía client.).
- `data/`: Lưu trữ vật lý các bộ test case, mô tả bài tập và các file liên quan.

## 🚀 Cài đặt

### 1. Chuẩn bị môi trường
- Đảm bảo máy tính đã cài đặt **Python 3.8+** và **Docker**.
- Clone repository về máy:
  ```bash
  git clone https://github.com/huypham-c/67OnlineJudge
  cd 67OnlineJudge
  ```
### 2. Xây dựng Sandbox Image
- Sử dụng Dockerfile có sẵn để build image cho máy chấm:
  ```bash
  docker build -t judge-sandbox:latest .
  ```
### 3. Cài đặt Dependencies
- 
  ```bash
  python -m venv venv
  source venv/bin/activate  # Trên Windows dùng: venv\\Scripts\\activate
  pip install fastapi uvicorn PyJWT pydantic
  ```
### 4. Chạy Server
- 
  ```bash
  python -m uvicorn api:app --reload
  ```
  Trang web sẽ có thể được truy cập tại `http://localhost:8000`
---
*Dự án được thực hiện như một đồ án môn học DSA.*
