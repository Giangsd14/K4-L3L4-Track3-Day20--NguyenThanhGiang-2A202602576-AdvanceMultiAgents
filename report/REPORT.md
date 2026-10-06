# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Thanh Giang | 2A202602576 | 100% |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `ChatOpenAI (gpt-6-luna)`, `LAB_TEMPERATURE=0`, `recursion_limit=60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: Deep Agents 0.7.21, Ubuntu 24.04 LTS (WSL2), Python 3.12.3 chạy trực tiếp trong virtualenv `.venv`
- Số lần chạy tác vụ đã dùng / ngân sách: 27 / 40
- Commit của tag `freeze`: `7042a25` (đứng sau commit hypotheses `5b8040e`)

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
  - `code-eval`: **2 calls** (`implementer` và `reviewer`).
  - `data-eval`: **1 call** (`implementer`).
  - `logs-eval`: **1 call** (`implementer`).
  - **Nhận xét:** Tác tử chính tuân thủ tốt `SUBAGENTS_NOTE`, chủ động phân rã các bước không tầm thường (non-trivial) cho các subagent chuyên trách trên 100% các tác vụ.

- **Thông tin thiếu hoặc thừa khi giao việc:**
  - Lời giao việc của tác tử chính rất chi tiết, nhắc lại các quy ước đường dẫn tương đối (`workspace/...`) và phạm vi công việc.
  - Tuy nhiên, do các quy ước tổ chức (nhóm E) là quy tắc ngầm không có trong đề bài, cả tác tử chính lẫn subagent đều không biết trước để truyền đạt hoặc tuân thủ, dẫn tới việc subagent dù hoàn thành xuất sắc các yêu cầu kỹ thuật vẫn không đạt các check quy ước ngầm.

- **Ảnh hưởng đến token và thời gian:**
  - **Token:** Tăng mạnh từ **1.7x đến 3.3x** so với `baseline`:
    + `code-learn`: từ 62,364 token (`baseline`) tăng lên 121,520 token (`subagents`).
    + `data-learn`: từ 25,212 token tăng lên 82,826 token.
    + `logs-learn`: từ 36,032 token tăng lên 63,452 token.
    + `code-eval`: từ 67,976 token tăng lên 179,966 token (tăng 2.65x).
    + Trung bình trên cả 6 tác vụ: `baseline` tiêu thụ 40,001 token/task, trong khi `subagents` tiêu thụ 97,345 token/task (tăng 2.43x).
  - **Thời gian:** Thời gian chạy tăng trung bình gấp đôi (từ 32s lên 95s/task).
  - **Hiệu quả:** Điểm số trung bình trên tác vụ đánh giá thậm chí sụt giảm nhẹ (từ 0.60 xuống 0.56) do subagent trên `data-eval` gặp lỗi sót biên trong prompt cô lập. Điều này minh chứng cho phát hiện của các nghiên cứu về hệ thống đa tác tử (Anthropic): phân rã đa tác tử làm tăng chi phí và rủi ro mất mát thông tin qua ranh giới giao việc (delegation boundary) nếu không đi kèm kỹ năng rõ ràng.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- **Số lần chạy curator, số skill bị xóa và lý do:** Chạy curator **1 lần duy nhất**. Số skill bị xóa: **0 skill**. Cả 3 skill do mô hình sinh ra đều vượt qua bộ kiểm duyệt `validate_skill` (đúng format frontmatter, không nhắc đến tài liệu đánh giá, thân dưới 40 dòng) và đạt tiêu chuẩn chất lượng cao về tính thủ tục tổng quát.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `repository-requirements` | **Hoàn toàn tổng quát:** Áp dụng cho mọi repository Python có yêu cầu về chất lượng mã (type hints, regression testing, changelog). Không chứa bất kỳ ID bài toán, tên tệp riêng (`inventory`), hay hàm cụ thể nào. | **Đúng hoàn toàn:** Hướng dẫn đầy đủ và chuẩn xác các bước thêm type annotations, tạo file test hồi quy cho từng bug, ghi changelog và kiểm tra lại toàn bộ quy tắc. | Dài **11 dòng** (thân 7 dòng checklist). `description`: *"Use when changing code in an existing repository with explicit quality, testing, or documentation requirements."* Đã được đọc ở `code-learn` (`skills_read = 1`) và giúp tác tử đạt check `rule_type_hints`. |
| `tabular-data-deliverables` | **Hoàn toàn tổng quát:** Áp dụng cho các bài toán xử lý dữ liệu bảng (CSV, tabular) chuyển thành tệp kết quả có cấu trúc. Không chứa tên file `sales.csv` hay `answer.json`. | **Đúng hoàn toàn:** Hướng dẫn phân tách số dòng vào vs số dòng sau deduplicate, xử lý múi giờ khi parse ngày tháng, chuẩn hóa danh mục, và tính toán tiền tệ theo số học thập phân / integer cents. | Dài **11 dòng** (thân 7 dòng checklist). `description`: *"Use when transforming tabular data into computed results and one or more structured output files."* Đã được đọc ở `data-learn` (`skills_read = 3`). |
| `structured-output-contracts` | **Hoàn toàn tổng quát:** Áp dụng cho trích xuất log và tạo đầu ra máy đọc được (JSON) có ràng buộc schema/versioning, thứ tự sắp xếp và chuẩn hóa định danh. Không chứa tên file `errors.json` hay service cụ thể. | **Đúng hoàn toàn:** Chỉ dẫn chuẩn hóa identifier, sắp xếp theo key/tie-breaker, bổ sung metadata version và re-parse kiểm chứng trước khi kết thúc. | Dài **9 dòng** (thân 5 dòng checklist). `description`: *"Use when producing machine-readable output from logs or other structured records with naming, ordering, or schema constraints."* Đã được đọc ở `logs-learn` (`skills_read = 2`). |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

### Bảng so sánh tổng hợp (`report/table.md`)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 8/10 |
| data-learn | 5/8 | 5/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 6/9 |
| code-eval | 7/11 | 7/11 | 9/11 |
| data-eval | 5/9 | 4/9 | 5/9 |
| logs-eval | 6/10 | 6/10 | 6/10 |
| **Mean score - learning tasks** | 0.66 | 0.66 | 0.70 |
| **Mean score - evaluation tasks** | 0.60 | 0.56 | 0.66 |
| **Mean tokens per run** | 40,001 | 97,345 | 68,794 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |

### Bảng phân tích chi tiết kỹ thuật và quy ước (`scripts/check_breakdown.py`)

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     18/18         0/12          38,800      0/3     
baseline      learn    18/18         0/9           41,202      0/3     
subagents     eval     17/18         0/12         105,425      0/3     
subagents     learn    18/18         0/9           89,266      0/3     
skills-auto   eval     18/18         2/12          73,279      3/3     
skills-auto   learn    18/18         1/9           64,309      3/3     
```

- **Ghi chú về lỗi và tính toàn vẹn:**
  - Không có bất kỳ lần chạy nào gặp sự cố (`error = None` trên toàn bộ 18 runs chính thức).
  - Không có lần chạy nào vi phạm sửa đổi thư mục kỹ năng (`skills_modified = False` trên 100% các lần chạy).
  - Lệnh kiểm tra `python scripts/verify_freeze.py` trả về `OK` (mã thoát 0), xác nhận toàn bộ 6 lần chạy của `skills-auto` dùng đúng bộ skill đã đóng băng và bắt đầu sau thời điểm tag `freeze`.

## 8. Phân tích

### 1. So sánh cải thiện điểm số và dấu hiệu quá khớp
- **Tác vụ học:** `skills-auto` cải thiện điểm số trung bình từ **0.66** (`baseline`) lên **0.70** (tăng thêm 1 check đạt trên `code-learn`: 8/10 so với 7/10). Trong khi đó, `subagents` không đem lại cải thiện nào (vẫn 0.66).
- **Tác vụ đánh giá:** `skills-auto` đạt điểm trung bình **0.66**, cao hơn đáng kể so với `baseline` (**0.60**) và `subagents` (**0.56**). Mức tăng điểm này đến từ việc đạt thêm 2 checks quy ước tổ chức trên `code-eval` (9/11 so với 7/11).
- **Hiện tượng quá khớp (Overfitting):** Có dấu hiệu phân hóa hiệu quả. Trên họ bài toán `code`, kỹ năng `repository-requirements` tổng quát hóa rất tốt sang `code-eval`. Tuy nhiên, trên `data-eval` và `logs-eval`, điểm số của `skills-auto` bằng đúng `baseline` (5/9 và 6/10) và không đạt thêm check quy ước mới nào. Điều này phản ánh tính chất quá khớp nhẹ về ngữ cảnh quy ước: tác tử chỉ thực thi tốt các quy tắc đã được đúc kết từ tập học, không thể tự suy luận ra các quy ước mới của tập đánh giá.

### 2. Tách điểm kỹ thuật và quy ước (`rule_`)
- Dữ liệu từ `check_breakdown.py` cho thấy:
  + **Check kỹ thuật:** Đạt tuyệt đối **18/18 (100%)** ở cả 3 điều kiện trên cả 2 tập (riêng `subagents` đạt 17/18 trên eval do mất mát thông tin khi giao việc). Mô hình `gpt-6-luna` có năng lực lập trình và phân tích dữ liệu rất mạnh.
  + **Check quy ước (`rule_`):** `baseline` và `subagents` hoàn toàn thất bại: đạt **0/9** trên tập học và **0/12** trên tập đánh giá. Ngược lại, `skills-auto` là điều kiện duy nhất đạt được các check quy ước: đạt **1/9** trên tập học và **2/12** trên tập đánh giá.
- **Check quy ước mới của tác vụ đánh giá:** Tác vụ đánh giá đưa vào các quy ước mới: `rule_version_bump` (trong `code-eval`), `rule_clean_csv` format mới (trong `data-eval`), và `rule_schema_header` phiên bản 3 (trong `logs-eval`). Skill của curator **hoàn toàn không giúp được** các check quy ước mới này vì curator chỉ học từ phản hồi của tập học (nơi các quy ước này chưa từng tồn tại). Điều này chứng minh rằng tầng ngữ cảnh (context layer) bị giới hạn bởi phạm vi tri thức được cung cấp: tác tử không thể tự "đoán" được quy ước tổ chức mới nếu không có tài liệu hoặc phản hồi tương ứng.

### 3. Giải thích cơ chế qua vết (`trace.md`) và `skills_read`
- **Check mà skill giúp đạt (`rule_type_hints` và `rule_regression_tests` trong `code-eval`):**
  + Trong vết `trace.md` của `skills-auto/code-eval`, ngay ở bước đầu tiên sau khi nhận lệnh, tác tử gọi `read_file` đọc `skills/repository-requirements/SKILL.md`.
  + Tác tử trích xuất checklist và thực hiện tuần tự: sau khi sửa lỗi hàm tính toán trong `appointment.py`, nó dùng `read_file` quét toàn bộ các hàm public trong gói và dùng `edit_file` bổ sung đầy đủ type annotations cho tham số và kiểu trả về (đáp ứng `rule_type_hints`). Đồng thời, nó tạo file `tests/test_regressions.py` chứa 3 test function kiểm thử độc lập cho 3 bug vừa sửa (đáp ứng `rule_regression_tests`). Ở baseline, tác tử sửa code xong là kết thúc ngay, hoàn toàn không thực hiện hai bước này.
- **Check mà skill không giúp được (`rule_version_bump` trong `code-eval`):**
  + Check này yêu cầu nâng version trong `pyproject.toml` từ `0.1.0` lên `0.1.1`.
  + Trong vết của `skills-auto/code-eval`, tác tử đọc kỹ năng `repository-requirements`, nhưng kỹ năng này chỉ hướng dẫn về type hints, regression test và changelog (vì ở tập học chỉ có 3 quy ước này). Kỹ năng hoàn toàn không đề cập đến việc bump version. Do đó tác tử không sửa `pyproject.toml` và check `rule_version_bump` thất bại.

### 4. Phân tích chi phí và hiệu quả kinh tế (Token Efficiency)
- **So sánh số token trung bình:**
  + `baseline`: **40,001** tokens/run.
  + `skills-auto`: **68,794** tokens/run (tăng 1.72x so với baseline).
  + `subagents`: **97,345** tokens/run (tăng 2.43x so với baseline).
- **Hiệu quả điểm số trên mỗi token:**
  + `baseline`: 0.60 điểm / 38.8k token eval ≈ **1.55 × 10⁻⁵ điểm/token**.
  + `skills-auto`: 0.66 điểm / 73.3k token eval ≈ **0.90 × 10⁻⁵ điểm/token**.
  + `subagents`: 0.56 điểm / 105.4k token eval ≈ **0.53 × 10⁻⁵ điểm/token**.
- **Đa tác tử có đáng chi phí không?**
  + **Hoàn toàn KHÔNG đáng chi phí** trong thí nghiệm này. `subagents` tiêu tốn lượng token gấp 2.43 lần và thời gian chạy gấp 3 lần so với baseline, nhưng điểm số không tăng trên tập học (0.66 vs 0.66) và thậm chí sụt giảm trên tập đánh giá (0.56 vs 0.60). Việc phân quyền giao việc tạo thêm overhead hội thoại và rủi ro thất thoát thông tin ngữ cảnh mà không đem lại lợi ích bù đắp.

### 5. Dấu hiệu rò rỉ dữ liệu và quá khớp
- **Kiểm soát rò rỉ dữ liệu (Data Leakage):**
  + Hoàn toàn không có rò rỉ dữ liệu từ tập đánh giá sang kỹ năng. Hàm `curate_skills` lọc bỏ tuyệt đối các run có `role != "learn"` và hàm `validate_skill` quét kiểm tra toàn bộ danh sách `eval_markers()` (định danh độc quyền của tập eval).
  + Trong các file `SKILL.md` tự sinh, không hề xuất hiện các chuỗi đặc trưng của tập eval như `appointments`, `march_orders`, hay `audit_service`.
- **Dấu hiệu quá khớp (Overfitting):**
  + Kỹ năng tự sinh khái quát hóa rất tốt quy tắc viết type hints và regression tests sang `code-eval`, nhưng không thể khái quát hóa các quy ước về format dữ liệu sang `data-eval` (vốn đòi hỏi các trường meta và chuẩn hóa khác). Đây là đặc tính tự nhiên của quá trình tự tiến hóa: kỹ năng đúc kết từ phản hồi của tập học giải quyết triệt để các bài toán trong cùng phân phối nhưng cần thêm vòng lặp phản hồi khi gặp môi trường có quy ước mới.

### 6. Phân tích độ nhiễu thực nghiệm
- So sánh điểm số và token của cùng bộ skill trên tác vụ học giữa lần chạy thử nghiệm ở Phần 3.4 (`results/skills-auto-dev`) và lần chạy chính thức sau đóng băng (`results/skills-auto`):
  + `code-learn`: Dev = **8/10** (165,727 tokens) vs Freeze = **8/10** (108,006 tokens) => Chênh lệch điểm: **0.00**.
  + `data-learn`: Dev = **5/8** (59,822 tokens) vs Freeze = **5/8** (50,338 tokens) => Chênh lệch điểm: **0.00**.
  + `logs-learn`: Dev = **6/9** (47,254 tokens) vs Freeze = **6/9** (34,583 tokens) => Chênh lệch điểm: **0.00**.
- **Ý nghĩa khoa học:**
  + Độ biến động điểm số giữa hai lần chạy là **bằng 0 (0.00)**, chứng minh rằng điểm số partial credit trong môi trường nhiệt độ thấp (`LAB_TEMPERATURE=0`) có độ ổn định và độ tin cậy rất cao.
  + Chênh lệch điểm số quan sát được giữa các điều kiện (ví dụ `skills-auto` đạt 0.66 so với `baseline` 0.60 trên tập eval) là **sự khác biệt thực chất mang tính hệ thống**, không phải do nhiễu ngẫu nhiên của mô hình.
  + Tuy nhiên, số lượng token tiêu thụ có phương sai từ 15% đến 35% do độ dài đường suy luận (reasoning trajectory) và số bước công cụ có thể biến động nhẹ.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập tác vụ nhỏ:** Mỗi điều kiện chỉ được đánh giá trên 3 tác vụ học và 3 tác vụ đánh giá (tổng cộng 6 tác vụ). Cỡ mẫu nhỏ hạn chế khả năng kiểm định ý nghĩa thống kê (p-value) và có thể làm nổi bật các biến động cá biệt ở từng bài toán.
2. **Quy ước tổ chức mang tính nhân tạo:** Các quy ước tổ chức (như tiền tệ bằng cents, khối meta, định dạng changelog) được thiết kế có chủ đích bởi giảng viên để thử nghiệm cơ chế bắt lỗi của bot đánh giá, chưa đại diện đầy đủ cho sự phức tạp và mơ hồ của các quy ước dự án thực tế trong doanh nghiệp.
3. **Thử nghiệm trên một mô hình duy nhất:** Mọi thí nghiệm được thực hiện trên mô hình `gpt-6-luna`. Kết quả chưa phản ánh mức độ phụ thuộc vào năng lực mô hình nền (ví dụ: các mô hình nhỏ hơn có thể hưởng lợi nhiều hơn từ subagents, hoặc kỹ năng do mô hình này viết có chuyển giao hiệu quả sang mô hình khác hay không).
4. **Giới hạn số vòng lặp tiến hóa đơn lẻ:** Thí nghiệm mới chỉ đánh giá 1 chu kỳ tiến hóa (single-iteration evolution). Trong môi trường sản xuất, tác tử tự tiến hóa cần chạy liên tục qua nhiều chu kỳ (hot-path / multi-round evolution) với cơ chế tự prune và hợp nhất kỹ năng để tránh phình to (skill bloat).

## 10. Kết luận

Thực nghiệm đã chứng minh rằng tác tử tự tiến hóa ở tầng ngữ cảnh (`skills-auto`) đem lại hiệu quả vượt trội so với tác tử mặc định (`baseline`) và kiến trúc đa tác tử (`subagents`), nâng điểm số đánh giá từ 0.60 lên 0.66 nhờ khả năng khắc phục các vi phạm quy ước tổ chức mà không làm suy giảm năng lực kỹ thuật. Ngược lại, kiến trúc đa tác tử thông thường làm tăng chi phí token lên gấp 2.4 lần và kéo dài thời gian thực thi nhưng không đem lại giá trị gia tăng khi tác tử con thiếu tri thức thủ tục. Đề xuất cải tiến tiếp theo là tích hợp cơ chế nạp kỹ năng động trực tiếp cho subagents (`subagent with skills`) kết hợp vòng tuyển chọn curator đa chu kỳ để xử lý thích ứng với các quy ước mới xuất hiện trong runtime.

---

## Phụ lục

### Lệnh đã chạy (theo thứ tự thực hiện)

```bash
# 1. Cài đặt và kiểm tra harness
pytest tests/test_01_provided.py
pytest tests/test_02_agent.py
pytest tests/test_03_runner.py
pytest tests/test_04_curator.py
pytest

# 2. Khảo sát công cụ Deep Agents (Phần 0.3)
python scripts/tour.py

# 3. Chạy thực nghiệm tác vụ học (Phần 2)
python -m lab.runner --condition baseline --tasks learn
python -m lab.runner --condition subagents --tasks learn

# 4. Tự sinh skill và chạy thử nghiệm (Phần 3)
python -m lab.curator
python -m lab.runner --condition skills-auto --tasks learn
cp -r results/skills-auto results/skills-auto-dev

# 5. Giao thức đóng băng (Phần 4)
git add -A && git commit -m "hypotheses: dự đoán H1, H2, H3 trước khi đóng băng và đánh giá"
git commit --allow-empty -m "freeze skills" && git tag freeze

# 6. Chạy thực nghiệm chính thức (Phần 4.2)
python -m lab.runner --condition baseline --tasks eval
python -m lab.runner --condition subagents --tasks eval
python -m lab.runner --condition skills-auto --tasks all
python scripts/verify_freeze.py

# 7. Tổng hợp kết quả và phân tích (Phần 4.3, 4.4)
python -m lab.compare > report/table.md
python scripts/check_breakdown.py

# 8. Thử thách mở rộng: Hướng 6e (Lặp đo nhiễu trên tác vụ đánh giá)
python -m lab.runner --condition baseline --tasks eval --results results/bonus
python -m lab.runner --condition skills-auto --tasks eval --results results/bonus
```

### Thử thách mở rộng: Hướng 6e - Lặp để đo nhiễu (Repetition for Noise Measurement) - Tối đa +5 điểm

#### 1. Thiết kế thí nghiệm
- **Mục tiêu:** Đo lường phương sai ngẫu nhiên của mô hình trên tập đánh giá bằng cách lặp lại toàn bộ các tác vụ đánh giá cho hai điều kiện quan trọng nhất: `baseline` và `skills-auto` (với bộ kỹ năng đã đóng băng).
- **Thư mục kết quả độc lập:** Lưu trữ tách biệt hoàn toàn tại `results/bonus/` nhằm không ảnh hưởng đến bộ kết quả chính thức đã được `verify_freeze.py` xác thực.
- **Tham số:** Cùng mô hình `gpt-6-luna`, cùng `LAB_TEMPERATURE=0`, `recursion_limit=60`.

#### 2. Số liệu so sánh giữa Run 1 (Chính thức) và Run 2 (Bonus)

| Điều kiện | Tác vụ | Run 1 Score | Run 2 Score | Độ lệch điểm | Run 1 Tokens | Run 2 Tokens | Độ lệch Token | Run 1 Thời gian | Run 2 Thời gian |
|---|---|---|---|---|---|---|---|---|---|
| `baseline` | `code-eval` | 7/11 | 7/11 | **0** | 67,976 | 90,141 | +32.6% | 61.6s | 67.8s |
| `baseline` | `data-eval` | 5/9 | 5/9 | **0** | 24,512 | 27,772 | +13.3% | 16.4s | 20.8s |
| `baseline` | `logs-eval` | 6/10 | 6/10 | **0** | 23,914 | 38,648 | +61.6% | 19.8s | 27.7s |
| `skills-auto` | `code-eval` | 9/11 | 9/11 | **0** | 113,923 | 64,840 | -43.1% | 90.5s | 71.5s |
| `skills-auto` | `data-eval` | 5/9 | 5/9 | **0** | 65,638 | 72,953 | +11.1% | 41.0s | 32.8s |
| `skills-auto` | `logs-eval` | 6/10 | 6/10 | **0** | 40,276 | 37,923 | -5.8% | 30.9s | 32.6s |

**Điểm trung bình tác vụ đánh giá:**
- `baseline`: Run 1 = **0.60**, Run 2 = **0.60** (Độ lệch = 0.00).
- `skills-auto`: Run 1 = **0.66**, Run 2 = **0.66** (Độ lệch = 0.00).

#### 3. Phân tích cơ chế dựa trên vết
- **Tính ổn định của điểm số:** Điểm số partial credit đạt độ tái lập tuyệt đối 100% giữa 2 lần chạy độc lập. Trên `code-eval`, cả hai lần chạy của `skills-auto` đều đọc kỹ năng `repository-requirements` và kiên định hoàn thành hai check quy ước `rule_type_hints` và `rule_regression_tests`, giữ vững điểm 9/11 so với 7/11 của baseline.
- **Phương sai về chi phí token:** Mặc dù điểm số không đổi, token tiêu thụ dao động trong khoảng từ 5% đến 60%. Phân tích `trace.md` cho thấy mô hình đôi khi chọn đường dẫn khám phá khác nhau (ví dụ: chạy thêm lệnh `git status` hoặc `ls` kiểm tra lại trước khi kết thúc), làm thay đổi số lượt tool call nhưng dẫn đến cùng trạng thái workspace cuối cùng.

#### 4. Hạn chế và đề xuất bước tiếp theo
- **Hạn chế:** Thí nghiệm lặp lại với N=2 lần chạy; để tính độ lệch chuẩn và khoảng tin cậy 95% chuẩn mực cần tối thiểu N=5 đến N=10 lần chạy.
- **Đề xuất tiếp theo:** Tự động hóa cơ chế early-stopping khi tác tử đã thỏa mãn toàn bộ checklist trong skill để giảm thiểu phương sai token không cần thiết.
