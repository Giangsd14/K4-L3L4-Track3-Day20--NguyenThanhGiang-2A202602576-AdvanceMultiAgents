# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Thanh Giang | 2A202602576 | 100% |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `ChatOpenAI (gpt-6-luna)`, `LAB_TEMPERATURE=0`, `recursion_limit=60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: Deep Agents 0.7.21, Ubuntu 24.04 LTS (WSL2), chạy trực tiếp trong virtualenv `.venv`
- Số lần chạy tác vụ đã dùng / ngân sách: 0 / 40
- Commit của tag `freeze`: (sẽ cập nhật sau khi tạo tag freeze ở Phần 4)

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Điều kiện `subagents` sẽ tiêu thụ lượng token cao hơn gấp 2 đến 3 lần và thời gian chạy dài hơn so với `baseline`, nhưng điểm số trên tác vụ đánh giá sẽ không vượt trội đáng kể (dao động trong khoảng tương đương hoặc chỉ chênh lệch nhẹ). Căn cứ: Kết quả phân loại lỗi ở Mục 4 cho thấy 100% lỗi thất bại thuộc nhóm E (quy ước ngầm của tổ chức). Việc phân quyền đa tác tử (explorer, implementer, reviewer) chỉ tối ưu hóa việc phân tách ngữ cảnh và kiểm thử kỹ thuật (vốn dĩ baseline đã đạt 18/18 check kỹ thuật), không thể bù đắp được các tri thức thủ tục bị thiếu nếu không có cơ chế nạp kỹ năng; phù hợp với các công bố của Anthropic về chi phí và giới hạn của đa tác tử trong tác vụ phần mềm.
- H2 (skills-auto so với baseline): Điều kiện `skills-auto` sẽ đạt điểm số cao hơn rõ rệt so với `baseline` trên các check quy ước cũ được tái sử dụng, nhưng mức cải thiện sẽ bị suy giảm trên các quy ước mới của tác vụ đánh giá do hiện tượng quá khớp (overfitting). Căn cứ: Theo các nghiên cứu chuẩn đối sánh SkillsBench và SkillEvolBench, kỹ năng tự sinh từ phản hồi của tập học giúp củng cố checklist thủ tục rất tốt trên miền quen thuộc, nhưng tri thức tự sinh ít có khả năng tự suy luận ra các quy ước tổ chức hoàn toàn mới mà bot chấm điểm yêu cầu riêng ở tập đánh giá.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trung bình trên tác vụ đánh giá sẽ thấp hơn tác vụ học trên toàn bộ các điều kiện (sụt giảm khoảng 10-25%), đặc biệt ở nhóm check quy ước (`rule_`). Căn cứ: Thiết kế thực nghiệm của bài Lab quy định mỗi tác vụ đánh giá đều có dữ liệu mới và bổ sung thêm một quy ước tổ chức mới. Vì các quy ước mới này chưa từng xuất hiện trong phản hồi hay đề bài trước đó, tác tử sẽ gặp hiện tượng dịch chuyển phân phối kiểm tra (distribution shift) khiến tỷ lệ đạt check ở tập đánh giá sụt giảm tự nhiên.

## 3. Làm quen Deep Agents (Phần 0.3)

1. **Các công cụ mặc định và công cụ chạy lệnh:**
   - Tác tử mặc định nhìn thấy 9 công cụ:
     + Nhóm tệp: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`.
     + Nhóm shell: `execute`.
     + Nhóm tác tử con: `task`.
   - Công cụ duy nhất cho phép chạy lệnh shell là: `execute`.

2. **Mô tả của công cụ `task` về subagent `general-purpose` và ngữ cảnh nhìn thấy:**
   - Vai trò của `general-purpose`: Là tác tử tổng quát dùng để nghiên cứu các câu hỏi phức tạp, tìm kiếm tệp và nội dung, và thực hiện các tác vụ nhiều bước. Khi tìm kiếm từ khóa hoặc tệp mà tác tử chính không chắc chắn tìm đúng trong vài lần thử đầu, nó nên dùng subagent này để tìm kiếm. Subagent này có quyền truy cập toàn bộ công cụ như tác tử chính.
   - Ngữ cảnh nhìn thấy: Mỗi lần gọi là phi trạng thái theo mặc định (`stateless by default`). Subagent chỉ nhìn thấy duy nhất nội dung prompt mà tác tử chính gửi trong lời gọi và trả về một báo cáo cuối duy nhất (không nhìn thấy lịch sử ngữ cảnh trước đó của tác tử chính). Do đó, tác tử chính phải đưa đầy đủ chi tiết, quy tắc và đường dẫn vào prompt khi giao việc.

3. **Trích dẫn hướng dẫn hành vi từ mô tả của công cụ `task` và `execute`:**
   - Trích từ mô tả công cụ `task`: *"Put full detail in the prompt and state exactly what it should return — unless an agent type below says it inherits your conversation instead."*
   - Trích từ mô tả công cụ `execute`: *"You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `code-learn` | `rule_type_hints` | E | Detail: `RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value.` |
| `code-learn` | `rule_regression_tests` | E | Detail: `RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass.` |
| `code-learn` | `rule_changelog` | E | Detail: `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets).` |
| `data-learn` | `rule_money_in_cents` | E | Detail: `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667).` |
| `data-learn` | `rule_meta_block` | E | Detail: `RULE: answer.json has an object meta = {"source": <input file name>, "rows_in": <number of data rows...>, "rows_used": <number of distinct orders...>}.` |
| `data-learn` | `rule_clean_csv` | E | Detail: `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; one row per distinct order...` |
| `logs-learn` | `rule_service_names` | E | Detail: `RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service).` |
| `logs-learn` | `rule_sorted_errors` | E | Detail: `RULE: errors is sorted by service, then by timestamp_utc, ascending.` |
| `logs-learn` | `rule_schema_header` | E | Detail: `RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage".` |

**Nhận xét:**
- **Nhóm lỗi chiếm đa số:** 100% lỗi thất bại (9/9 checks) đều thuộc **Nhóm E (Vi phạm quy ước tổ chức / House rules)**. Các quy ước này (như ghi changelog, type hints cho mọi hàm public, chuyển tiền tệ sang cents, thêm khối meta, chuẩn hóa tên service với dấu gạch dưới) không được mô tả tường minh trong đề bài ban đầu (`instruction.md`) mà là các quy tắc ngầm định của tổ chức (Acme conventions) được bot đánh giá kiểm tra.
- **Bằng chứng phủ định cho các nhóm A đến D:** Theo kết quả từ `scripts/check_breakdown.py`, tác tử đạt **18/18 (100%) các check kỹ thuật** (technical checks) trên cả 3 tác vụ. Tác tử đã đọc kỹ hướng dẫn, sửa đúng lỗi logic gốc, xử lý dữ liệu bẩn và chạy test kiểm chứng đầy đủ. Do đó, tác tử hoàn toàn không mắc các lỗi nhóm A (bỏ qua đặc tả), nhóm B (không kiểm chứng), nhóm C (vá triệu chứng) hay nhóm D (bỏ sót dữ liệu bẩn).
- **Khả năng phòng ngừa của Skill:** Một skill thủ tục hoàn toàn CÓ THỂ phòng ngừa nhóm lỗi này nếu nó đúc kết các quy ước tổ chức thành danh sách kiểm tra (checklist) hành vi chuẩn mực: yêu cầu tác tử luôn kiểm tra type hints, tạo file regression test, ghi CHANGELOG, chuyển đổi đơn vị tiền tệ sang integer cents và kiểm tra metadata schema trước khi hoàn tất.

## 5. Điều kiện `subagents` (Phần 2.3)

- **Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):**
  1. `explorer`: Đọc và phân tích cấu trúc mã nguồn, tài liệu và dữ liệu mẫu; tóm tắt sự thật khách quan; không sửa đổi file. Thiết kế nhằm giảm context window cho tác tử chính ở giai đoạn tìm kiếm thông tin ban đầu.
  2. `implementer`: Trực tiếp áp dụng các thay đổi code/data, thực thi script và chạy test xác minh; báo cáo kết quả cụ thể. Thiết kế để tập trung vào thực thi một chuỗi thao tác độc lập.
  3. `reviewer`: Rà soát độc lập các thay đổi đối chiếu với docstring, các trường hợp biên (múi giờ, dòng trùng, định dạng); không sửa file. Thiết kế để tạo cơ chế phản biện độc lập (adversarial review).

- **`subagent_calls` ở từng tác vụ và nhận xét:**
  - `code-learn`: **2 calls** (`implementer` được gọi đầu tiên để phân tích và áp dụng fix, sau đó `reviewer` được gọi độc lập để rà soát code).
  - `data-learn`: **1 call** (`implementer` được gọi để thực hiện toàn bộ quy trình làm sạch và tính toán dữ liệu).
  - `logs-learn`: **1 call** (`implementer` được gọi để phân tích và tạo cấu trúc json).
  - **Nhận xét:** Tác tử chính tuân thủ tốt `SUBAGENTS_NOTE`, chủ động phân rã các bước không tầm thường (non-trivial) cho các subagent chuyên trách.

- **Thông tin thiếu hoặc thừa khi giao việc:**
  - Lời giao việc của tác tử chính rất chi tiết, nhắc lại các quy ước đường dẫn tương đối (`workspace/...`) và phạm vi công việc.
  - Tuy nhiên, do các quy ước tổ chức (nhóm E) là quy tắc ngầm không có trong đề bài, cả tác tử chính lẫn subagent đều không biết trước để truyền đạt hoặc tuân thủ, dẫn tới việc subagent dù hoàn thành xuất sắc các yêu cầu kỹ thuật vẫn không đạt các check quy ước ngầm.

- **Ảnh hưởng đến token và thời gian:**
  - **Token:** Tăng mạnh từ **1.7x đến 3.3x** so với `baseline`:
    + `code-learn`: từ 62,364 token (`baseline`) tăng lên 121,520 token (`subagents`, tăng 1.95x).
    + `data-learn`: từ 25,212 token tăng lên 82,826 token (tăng 3.28x).
    + `logs-learn`: từ 36,032 token tăng lên 63,452 token (tăng 1.76x).
    + Trung bình tăng từ 41,202 token lên 89,266 token/task.
  - **Thời gian:** Tăng tương ứng do phải khởi tạo và chạy các đồ thị tác tử con tuần tự (tổng thời gian thực thi tăng gấp đôi).
  - **Hiệu quả:** Điểm số không thay đổi (vẫn 7/10, 5/8, 6/9). Điều này minh chứng cho phát hiện của các nghiên cứu về hệ thống đa tác tử (như nghiên cứu của Anthropic): việc phân rã đa tác tử mang lại chi phí token và thời gian rất lớn nhưng không giải quyết được các thiếu sót về tri thức thủ tục/quy ước nếu các tác tử không được cung cấp kỹ năng phù hợp.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- **Số lần chạy curator, số skill bị xóa và lý do:** Chạy curator **1 lần duy nhất**. Số skill bị xóa: **0 skill**. Cả 3 skill do mô hình sinh ra đều vượt qua bộ kiểm duyệt `validate_skill` (đúng format frontmatter, không nhắc đến tài liệu đánh giá, thân dưới 40 dòng) và đạt tiêu chuẩn chất lượng cao về tính thủ tục tổng quát.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `repository-requirements` | **Hoàn toàn tổng quát:** Áp dụng cho mọi repository Python có yêu cầu về chất lượng mã (type hints, regression testing, changelog). Không chứa bất kỳ ID bài toán, tên tệp riêng (`inventory`), hay hàm cụ thể nào. | **Đúng hoàn toàn:** Hướng dẫn đầy đủ và chuẩn xác các bước thêm type annotations, tạo file test hồi quy cho từng bug, ghi changelog và kiểm tra lại toàn bộ quy tắc. | Dài **11 dòng** (thân 7 dòng checklist). `description`: *"Use when changing code in an existing repository with explicit quality, testing, or documentation requirements."* Đã được đọc ở `code-learn` (`skills_read = 1`) và giúp tác tử đạt check `rule_type_hints`. |
| `tabular-data-deliverables` | **Hoàn toàn tổng quát:** Áp dụng cho các bài toán xử lý dữ liệu bảng (CSV, tabular) chuyển thành tệp kết quả có cấu trúc. Không chứa tên file `sales.csv` hay `answer.json`. | **Đúng hoàn toàn:** Hướng dẫn phân tách số dòng vào vs số dòng sau deduplicate, xử lý múi giờ khi parse ngày tháng, chuẩn hóa danh mục, và tính toán tiền tệ theo số học thập phân / integer cents. | Dài **11 dòng** (thân 7 dòng checklist). `description`: *"Use when transforming tabular data into computed results and one or more structured output files."* Đã được đọc ở `data-learn` (`skills_read = 3`). |
| `structured-output-contracts` | **Hoàn toàn tổng quát:** Áp dụng cho trích xuất log và tạo đầu ra máy đọc được (JSON) có ràng buộc schema/versioning, thứ tự sắp xếp và chuẩn hóa định danh. Không chứa tên file `errors.json` hay service cụ thể. | **Đúng hoàn toàn:** Chỉ dẫn chuẩn hóa identifier, sắp xếp theo key/tie-breaker, bổ sung metadata version và re-parse kiểm chứng trước khi kết thúc. | Dài **9 dòng** (thân 5 dòng checklist). `description`: *"Use when producing machine-readable output from logs or other structured records with naming, ordering, or schema constraints."* Đã được đọc ở `logs-learn` (`skills_read = 2`). |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
