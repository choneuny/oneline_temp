---
created: 2022-08-26 15:06
modificated: "<%+ tp.file.last_modified_date() %>"
tags: inbox
---

### 주제 : <%+ tp.file.title %>

작성 : 8월 26일 금요일 15:06
최종 수정 : <%+ tp.file.last_modified_date("MMMM Do dddd HH:mm") %>

### 메모

- 문제상황 :
  - Edgar의 API가 매우 불안정하기 때문에 edgar, edgar downloader등의 라이브러리를 통해 파일링다운로드 url을 제공하는 방법으로는 데이터의 무결성을 보장하기 어려움
  - 이를 해결하기 위해 클라우드 스토리지에 전처리된 파일링 텍스트를 저장하여 필요에 따라 쿼리해서 내려받을 수 있도록 만들고 싶음
- 2000~2022년 간 5000개 기업의 에드가 보고서를 전처리한다고 가정
- 전처리된 데이터는 클라우드에 년도별 폴더 / 분기별 폴더 / 파일 형식으로 저장됨
  - 파일 이름(키) 는 FilingDate_FormType_AccNum.txt
  - Redis에 ACC_NUM: {compressed_text} 형태로 저장?
-
- 지금 해야 되는 것 :
  - File 모듈에서 search의 return을( 혹은 acc_num의 리스트를 ) 받아서 밑의 형태의 df로 변환
  -

| date     | type | acc                  | string           |
| -------- | ---- | -------------------- | ---------------- |
| 20210101 | 10-K | 00512522-21-00412412 | "Lorem Ipsum..." |
| ...      | ...  | ...                  | ...              |

### 연결

-
