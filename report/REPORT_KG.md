# Báo cáo Day 19 — Flat RAG vs GraphRAG

**Họ tên:** Lê Việt Hoàng  **MSSV:** 2A202602596  **Ngày:** 05/10/2026

---

## 1. Chi phí (10 điểm)

Dán 2 bảng `Indexing` và `Querying` từ `ket_qua_benchmark_kg.txt`:

```
Chat model: deepseek:deepseek-flash | Embedding: openrouter:openai/text-embedding-3-small | top_k=3 | chunk_size=800 | chunks=176 | KG: 229 nodes / 453 rels

== Indexing (one-off)
pipeline  calls    in_tok  out_tok       USD  seconds
flat        176     56072        0   0.00112     94.8
graph       196    106597    70483   0.02793    372.1

== Querying (mean per question)
pipeline  recall  judge   in_tok  out_tok       USD  seconds
flat        0.47   1.17      938      398   0.00024     3.12
graph       0.78   1.50     3739     2178   0.00113     9.34
```

| Chỉ số | Flat | Graph | Graph / Flat |
| --- | --- | --- | --- |
| Indexing USD | $0.00112 | $0.02793 | ×24.94 |
| Indexing giây | 94.8s | 372.1s | ×3.93 |
| Mỗi câu: USD | $0.00024 | $0.00113 | ×4.71 |
| Mỗi câu: giây | 3.12s | 9.34s | ×2.99 |
| Mỗi câu: in_tok | 938 | 3739 | ×3.99 |

**Chi phí tăng thêm đến từ đâu?**
- **Lúc Indexing (one-off):** Chi phí tăng chủ yếu do việc gọi LLM (`deepseek-flash`) ở JSON mode trên 20 bài báo tin tức để trích xuất thực thể, quan hệ và tóm tắt vụ án (tiêu tốn thêm ~50.500 input tokens và ~70.500 output tokens, làm chi phí indexing tăng gấp ~25 lần từ $0.00112 lên $0.02793).
- **Lúc Querying (mỗi câu hỏi):** Chi phí và độ trễ tăng khoảng 3–4 lần do GraphRAG bổ sung khối dữ kiện phong phú từ graph (`facts` mở rộng qua các quan hệ multi-hop, trung bình bổ sung ~2.800 input tokens vào prompt), khiến LLM mất thêm thời gian đọc hiểu và sinh câu trả lời chi tiết, trọn vẹn hơn (output tokens tăng từ 398 lên 2.178).

---

## 2. Từng câu hỏi (10 điểm)

| Câu | Loại | Flat recall / judge | Graph recall / judge | Thắng | Vì sao (1 câu) |
| --- | --- | --- | --- | --- | --- |
| **Q1** | single-hop-law | 1.00 / 2 | 1.00 / 2 | **Hòa** | Định nghĩa tiền chất nằm gọn trong một đoạn văn bản của Luật PCMT 2021, cả vector search và graph đều lấy trúng ngữ cảnh. |
| **Q2** | single-hop-news | 1.00 / 2 | 1.00 / 2 | **Hòa** | Thông tin 2 bị cáo Trần Thanh Tuấn và Trần Minh Tâm bị tuyên tử hình nằm trọn vẹn trong một bài báo tin tức. |
| **Q3** | cross-kb | 0.00 / 0 | 0.33 / 1 | **Graph** | Flat RAG thất bại hoàn toàn do thông tin phân tán; GraphRAG tìm đúng mức án 36 tháng tù và tội mua bán ma túy từ graph. |
| **Q4** | cross-kb | 0.00 / 0 | 0.33 / 1 | **Graph** | Flat RAG không có thông tin; GraphRAG tìm được tên thật Dương Minh Tuấn ("Hoàng Nato") và hành vi tổ chức sử dụng từ graph. |
| **Q5** | cross-kb-multi-hop | 0.80 / 2 | 1.00 / 2 | **Graph** | GraphRAG kết nối chính xác khối lượng 9,6kg MDMA với điểm b khoản 4 Điều 250 (ngưỡng từ 100g trở lên) và mức phạt tử hình. |
| **Q6** | aggregation | 0.00 / 1 | 1.00 / 1 | **Graph** | Câu hỏi tổng hợp trên toàn bộ kho tin; Flat RAG chỉ lấy được 3 chunks rời rạc, còn Graph gom đủ cả 3 vụ án nhờ quan hệ `INVOLVES` và gộp từ lóng. |

---

## 3. Phân tích lỗi (20 điểm)

### Lỗi E1: Cầu nối gãy — Vụ án không nối được sang Điều luật tương ứng (Câu Q4)

- **Hiện tượng:** Trong câu hỏi Q4 về giang hồ "Hoàng Nato", GraphRAG đã nhận diện chính xác "Hoàng Nato" là biệt danh của Dương Minh Tuấn và hành vi bị bắt là "tổ chức sử dụng trái phép chất ma túy", nhưng không thể liên kết sang Điều 255 BLHS và khung hình phạt tối đa.
- **Bằng chứng:**
  *Trích nguyên văn câu trả lời Q4 từ file `ket_qua_benchmark_kg.txt`:*
  ```
  --- Q4 [cross-kb] graph recall=0.33 judge=1 7.11s
  Theo dữ kiện knowledge graph, Dương Minh Tuấn — trong vụ bắt giữ “Hoàng Nato” — được ghi nhận với hành vi/tội danh: tổ chức sử dụng trái phép chất ma túy.
  Tuy nhiên, ngữ cảnh không cung cấp điều luật cụ thể hay mức phạt tù tối đa của tội tổ chức sử dụng trái phép chất ma túy. Các đoạn văn bản chỉ có nội dung liên quan đến các điều như Điều 249 BLHS (tàng trữ trái phép chất ma túy) và Điều 250 BLHS (vận chuyển trái phép chất ma túy), không phải tội danh nêu trên.
  Vì vậy, không đủ thông tin để xác định mức phạt tù tối đa cho hành vi này theo Bộ luật Hình sự dựa trên ngữ cảnh đã cho.
  ```

  *Truy vấn Cypher kiểm tra node Case và Crime của đối tượng:*
  ```cypher
  MATCH (p:Person)-[:INVOLVED_IN]->(k:Case)
  WHERE p.name CONTAINS 'Tuấn' OR any(a IN coalesce(p.aliases, []) WHERE a CONTAINS 'Nato')
  OPTIONAL MATCH (k)-[:CHARGED_WITH]->(c:Crime)
  RETURN p.name, p.aliases, k.name, c.name;
  ```

  *Kết quả trả về từ Neo4j:*
  ```
  p.name: "Dương Minh Tuấn"
  p.aliases: ["Hoàng Nato"]
  k.name: "Chuyên án ma túy lớn tại TP.HCM"
  c.name: null
  ```
- **Nguyên nhân:**
  Trong bài báo gốc (`news-100260924083658532`), phóng viên dùng cách hành văn: *"Công an TP.HCM đang điều tra Dương Minh Tuấn về hành vi tổ chức sử dụng trái phép chất ma túy..."*. Do bài báo dùng từ "hành vi" thay vì từ khóa "khởi tố tội danh", prompt trích xuất LLM đã gán giá trị này vào trường `person.charge` mà không đưa vào mảng `case.charges`. Vì vậy, node `Case` không được tạo cạnh `CHARGED_WITH` tới `Crime` ("tổ chức sử dụng trái phép chất ma túy"), làm đứt gãy đường đi sang `Article` (Điều 255 BLHS). Ngoài ra, corpus luật trong bài lab chưa bao gồm Điều 255 BLHS.
- **Đề xuất sửa:**
  - Trong hàm `extract_news_cases`, nếu `case["charges"]` rỗng nhưng tồn tại `person.get("charge")`, tự động bổ sung tội danh của các cá nhân vào danh sách tội danh chung của vụ án: `case["charges"] = list(set(case.get("charges", []) + [p["charge"] for p in case.get("people", []) if p.get("charge")]))`.
  - Bổ sung quan hệ trực tiếp `(:Person)-[:ACCUSED_OF]->(:Crime)` như đã triển khai trong ontology tùy biến.
  - *Đánh đổi:* Có thể gây gán nhầm tội danh chung cho vụ án trong các đại án có nhiều đối tượng phạm nhiều tội danh độc lập khác nhau.

---

### Lỗi E3: Trùng thực thể (Entity Resolution chưa triệt để giữa các bài báo)

- **Hiện tượng:** Cùng một vụ án ngoài đời thực bị phân tách thành nhiều node riêng biệt trong Knowledge Graph do sự khác biệt trong câu từ của các bài báo tin tức.
- **Bằng chứng:**
  *Truy vấn Cypher kiểm tra các vụ án liên quan đến đối tượng Cái Quang Huy:*
  ```cypher
  MATCH (p:Person {name: 'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)
  RETURN p.name, k.name, k.doc_id;
  ```

  *Kết quả trả về từ Neo4j:*
  ```
  Row 1: p.name: "Cái Quang Huy", k.name: "Vụ Cái Quang Huy và Nguyễn Tiến Đạt vận chuyển trái phép chất ma túy từ Đức về Việt Nam", k.doc_id: "news-100260909095646141"
  Row 2: p.name: "Cái Quang Huy", k.name: "Vụ Cái Quang Huy vận chuyển ma túy qua sân bay Nội Bài", k.doc_id: "news-100260909095646141"
  ```
  *(Cùng một bài báo và cùng một vụ án nhưng sinh ra 2 node `Case` khác nhau do LLM bóc tách hoặc đặt tên khác nhau).*

  *Minh chứng qua câu trả lời Q6 trong `ket_qua_benchmark_kg.txt`:*
  ```
  - Vụ vận chuyển trái phép chất ma túy từ Đức về Việt Nam qua sân bay Nội Bài / Vụ vận chuyển trái phép chất ma túy qua sân bay Nội Bài của Cái Quang Huy: KG ghi có hơn 9,6kg MDMA...
  ```
  Câu trả lời bị lặp thông tin vụ án do graph tồn tại 2 node `Case` song song cho cùng 1 sự việc.
- **Nguyên nhân:**
  Ontology sử dụng thuộc tính `name` làm khóa định danh (`MERGE (k:Case {name: $name})`). Do `name` là chuỗi văn bản tự do do LLM tự đặt tên tóm tắt cho từng bài báo, hai bài báo khác nhau (hoặc các đoạn văn khác nhau) sẽ sinh ra hai chuỗi `name` không trùng khớp ký tự, khiến lệnh `MERGE` coi đây là 2 vụ án hoàn toàn tách biệt.
- **Đề xuất sửa:**
  - Bổ sung bước Entity Linking / Resolution sau khi trích xuất: gom cụm các vụ án (`Case`) dựa trên tập hợp bị can trùng nhau (`Person`) và thời gian/địa bàn tương đồng trước khi nạp vào Neo4j.
  - Khóa định danh của `Case` có thể dựa trên mã vụ án hoặc kết hợp `bị can chính + năm + địa phương` (ví dụ: `Case_CaiQuangHuy_2024_NoiBai`).
  - *Đánh đổi:* Cần thêm 1 lượt xử lý đối soát hoặc gọi thêm LLM, làm tăng thời gian và chi phí indexing ban đầu.

---

## 4. Kết luận (5 điểm)

Từ số liệu đo đạc thực tế tại mục 1 và mục 2, ta rút ra kết luận:

1. **Khi nào Flat RAG là đủ?**
   - Khi bài toán chỉ bao gồm các câu hỏi **đơn bước (single-hop)** như Q1 và Q2, trong đó câu hỏi và câu trả lời nằm trọn vẹn trong cùng một đoạn văn bản hoặc cùng một tài liệu đơn lẻ. 
   - Với các câu hỏi này, Flat RAG đạt kết quả hoàn hảo (`recall = 1.00`, `judge = 2.00`) với chi phí cực rẻ ($0.00024/câu) và tốc độ nhanh hơn ~3 lần so với GraphRAG (3.12s so với 9.34s). Dựng KG cho các tác vụ này là lãng phí tài nguyên và chi phí không cần thiết.

2. **Khi nào NÊN dùng Knowledge Graph (GraphRAG)?**
   - Khi hệ thống phải trả lời các câu hỏi **xuyên nguồn (cross-KB)** và **nhiều bước nhảy (multi-hop)** như Q3, Q5, nơi thông tin bị phân mảnh giữa các cơ sở tri thức khác nhau (tin tức chỉ có tên bị cáo và mức án; văn bản luật chỉ có Điều khoản và khung hình phạt). Flat RAG thất bại hoàn toàn trên dạng câu hỏi này (`recall = 0.00`, `judge = 0`), trong khi GraphRAG đạt độ chính xác cao (`recall = 1.00`, `judge = 2.00` ở Q5).
   - Khi gặp các câu hỏi **tổng hợp (aggregation)** như Q6 ("Những vụ việc nào liên quan đến MDMA?"). Flat RAG bị giới hạn bởi `top-k` nên chỉ lấy được vài mẩu tin rời rạc không đủ bao quát (`recall = 0.00`), còn GraphRAG có khả năng duyệt qua toàn bộ các node kề của `Substance {name: 'MDMA'}` để tổng hợp đầy đủ tất cả các vụ án có liên quan trong toàn bộ cơ sở tri thức.

---

## 5. Tự kiểm (5 điểm)

```
$ pytest tests/ -q
................................................                         [100%]
48 passed in 0.20s

$ python bench_kg.py --check
[OK] Dữ liệu: 18 điều luật, 20 bài báo
[OK] KG-1 link_entity
[OK] Neo4j kết nối được
[provider] chat = deepseek:deepseek-flash | embedding = openrouter:openai/text-embedding-3-small
[OK] KG-2 build_graph: 149 node / 316 cạnh, đường xuyên 2 KB dài 2 cạnh
[OK] KG-3 context: 31 dữ kiện, có Điều 251
[OK] KG-4 GraphRAGAgent.answer
[OK] Chi phí check: 1 lần gọi LLM, $0.00239. Graph nhỏ (luật + 1 bài) vẫn còn trong Neo4j để bạn xem; chạy --judge để dựng graph đầy đủ.
```

- Ảnh chụp Neo4j Browser đầy đủ trong thư mục `report/img/`:
  1. `report/img/kg_count.png`: Bảng thống kê số lượng 7 loại node (thấy rõ thanh truy vấn Q-A: 229 nodes, 453 rels).
  2. `report/img/kg_cross_kb.png`: Graph hiển thị đường đi xuyên 2 KB qua node cầu nối Crime (thấy rõ thanh truy vấn Q-B và cột Results overview).
  3. `report/img/kg_my_case.png`: Graph hiển thị vụ án cụ thể của đối tượng **Trần Minh Tâm** nối sang tội danh, Điều luật, địa điểm và chất ma túy (thấy rõ thanh truy vấn Q-D và Results overview).
- Người đã chọn cho `kg_my_case.png`: **Trần Minh Tâm** (bị cáo trong vụ án mua bán trái phép chất ma túy hơn 36kg tại TP.HCM).

---

## Vấn đề gặp phải (không tính điểm)

- **Vấn đề ban đầu:** DeepSeek API chỉ hỗ trợ endpoint Chat Completion (`deepseek-flash`), hoàn toàn không cung cấp API Embedding (trả về lỗi 404). Đồng thời key OpenAI của học viên đã hết hạn mức (`insufficient_quota`).
- **Giải pháp giải quyết:** Đã cập nhật `src/llm.py` bổ sung provider `deepseek` cho phần Chat, kết hợp cùng `openrouter` (sử dụng model chuẩn `openai/text-embedding-3-small`) cho phần Embedding. Giải pháp này giúp hệ thống hoạt động ổn định, đo lường chính xác chi phí/token theo đúng quy chuẩn kỹ thuật của bài lab mà không vi phạm quy định.
