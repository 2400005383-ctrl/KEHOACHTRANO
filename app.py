
import streamlit as st
import pandas as pd
from datetime import date
import calendar

st.set_page_config(page_title="Kế hoạch trả nợ", layout="wide")
st.title("PHẦN MỀM LẬP KẾ HOẠCH TRẢ NỢ")

st.write("Nhập thông tin khoản vay.")

# 1. Nhập dữ liệu
tien_vay = st.number_input(
    "Số tiền vay (đồng)", min_value=1_000_000,
    value=700_000_000, step=10_000_000
)

thoi_han = st.number_input(
    "Thời hạn vay (năm)", min_value=1,
    max_value=40, value=5, step=1
)

lai_suat_dau = st.number_input(
    "Lãi suất 3 tháng đầu (%/năm)",
    min_value=0.0, value=9.0
)

lai_suat_huy_dong = st.number_input(
    "Lãi suất huy động (%/năm)",
    min_value=0.0, value=10.0
)

bien_do = st.number_input(
    "Biên độ lãi suất (%/năm)",
    min_value=0.0, value=4.0
)

ngay_giai_ngan = st.date_input(
    "Ngày giải ngân", value=date(2023, 10, 22)
)

so_ky = st.number_input(
    "Số kỳ cần lập bảng", min_value=1,
    max_value=int(thoi_han * 12),
    value=min(5, int(thoi_han * 12)), step=1
)

co_so_ngay = st.selectbox(
    "Quy ước tính lãi",
    ["365 ngày/năm", "360 ngày/năm"]
)


def cong_thang(ngay, so_thang):
    tong_thang = ngay.month - 1 + so_thang
    nam = ngay.year + tong_thang // 12
    thang = tong_thang % 12 + 1
    ngay_moi = min(
        ngay.day,
        calendar.monthrange(nam, thang)[1]
    )
    return date(nam, thang, ngay_moi)


# 2. Tính toán khi nhấn nút
if st.button("TÍNH KẾ HOẠCH TRẢ NỢ", type="primary"):

    tong_ky = int(thoi_han * 12)
    goc_moi_ky = tien_vay / tong_ky
    lai_suat_sau = lai_suat_huy_dong + bien_do
    mau_so = 365 if co_so_ngay == "365 ngày/năm" else 360

    du_no = float(tien_vay)
    ngay_dau_ky = ngay_giai_ngan
    ngay_doi_lai = cong_thang(ngay_giai_ngan, 3)
    du_lieu = []

    for ky in range(1, int(so_ky) + 1):

        # Ngày chốt lãi là ngày 10 hàng tháng
        ngay_chot = cong_thang(ngay_giai_ngan, ky)
        ngay_chot = ngay_chot.replace(day=10)

        if ngay_chot <= ngay_dau_ky:
            ngay_chot = cong_thang(ngay_chot, 1)

        so_ngay = (ngay_chot - ngay_dau_ky).days
        tien_lai = 0.0
        moc = ngay_dau_ky

        # Chia kỳ tính lãi nếu đi qua ngày đổi lãi suất
        while moc < ngay_chot:
            if moc < ngay_doi_lai:
                moc_ket_thuc = min(ngay_chot, ngay_doi_lai)
                lai_suat = lai_suat_dau / 100
            else:
                moc_ket_thuc = ngay_chot
                lai_suat = lai_suat_sau / 100

            ngay_tinh = (moc_ket_thuc - moc).days
            tien_lai += du_no * lai_suat * ngay_tinh / mau_so
            moc = moc_ket_thuc

        tien_goc = min(goc_moi_ky, du_no)
        tong_tien = tien_goc + tien_lai
        du_no_cuoi = max(0.0, du_no - tien_goc)

        ngay_thu = ngay_chot.replace(day=15)

        du_lieu.append({
            "Kỳ": ky,
            "Ngày tính lãi": ngay_chot.strftime("%d/%m/%Y"),
            "Ngày thu nợ": ngay_thu.strftime("%d/%m/%Y"),
            "Dư nợ đầu kỳ (đồng)": round(du_no),
            "Số ngày tính lãi": so_ngay,
            "Tiền lãi (đồng)": round(tien_lai),
            "Tiền gốc (đồng)": round(tien_goc),
            "Tổng tiền trả (đồng)": round(tong_tien),
            "Dư nợ cuối kỳ (đồng)": round(du_no_cuoi)
        })

        du_no = du_no_cuoi
        ngay_dau_ky = ngay_chot

    # 3. Hiển thị bảng kết quả
    df = pd.DataFrame(du_lieu)

    st.subheader("BẢNG KẾ HOẠCH TRẢ NỢ")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("TỔNG HỢP")
    cot1, cot2, cot3 = st.columns(3)

    cot1.metric(
        "Tổng gốc trả",
        f"{df['Tiền gốc (đồng)'].sum():,.0f} đồng"
    )

    cot2.metric(
        "Tổng lãi phải trả",
        f"{df['Tiền lãi (đồng)'].sum():,.0f} đồng"
    )

    cot3.metric(
        "Dư nợ cuối kỳ",
        f"{df['Dư nợ cuối kỳ (đồng)'].iloc[-1]:,.0f} đồng"
    )

    # 4. Tải bảng kết quả
    csv_data = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="TẢI BẢNG TRẢ NỢ CSV",
        data=csv_data,
        file_name="ke_hoach_tra_no.csv",
        mime="text/csv"
    )
