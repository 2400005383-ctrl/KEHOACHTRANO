import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar

st.set_page_config(page_title="Kế hoạch trả nợ", page_icon="🏦", layout="wide")
st.title("🏦 PHẦN MỀM LẬP KẾ HOẠCH TRẢ NỢ")
st.caption("Môn học: Thẩm định tín dụng | Trả gốc đều hằng tháng, lãi tính theo dư nợ thực tế")

def add_months(d, months):
    """Cộng tháng và giữ ngày hợp lệ trong tháng mới."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

with st.sidebar:
    st.header("Thông tin khoản vay")
    principal = st.number_input("Số tiền vay (đồng)", min_value=1_000_000, value=700_000_000, step=10_000_000)
    years = st.number_input("Thời hạn vay (năm)", min_value=1, max_value=40, value=5, step=1)
    first_rate = st.number_input("Lãi suất cố định ban đầu (%/năm)", min_value=0.0, max_value=100.0, value=9.0, step=0.25)
    fixed_months = st.number_input("Số tháng cố định lãi suất", min_value=1, max_value=120, value=3, step=1)
    deposit_rate = st.number_input("Lãi suất huy động sau thời gian cố định (%/năm)", min_value=0.0, max_value=100.0, value=10.0, step=0.25)
    margin = st.number_input("Biên độ cộng thêm (%/năm)", min_value=0.0, max_value=50.0, value=4.0, step=0.25)
    disbursement = st.date_input("Ngày giải ngân", value=date(2023, 10, 22))
    interest_day = st.number_input("Ngày chốt/tính lãi mỗi tháng", min_value=1, max_value=28, value=10, step=1)
    payment_day = st.number_input("Ngày thu tiền mỗi tháng", min_value=1, max_value=28, value=15, step=1)
    day_basis = st.selectbox("Quy ước ngày tính lãi", ["Actual/365", "Actual/360"])
    periods_to_show = st.number_input("Số kỳ muốn hiển thị", min_value=1, max_value=int(years * 12), value=min(5, int(years * 12)), step=1)

st.info(
    "Giả định của chương trình: ngân hàng chốt lãi vào ngày đã nhập; kỳ đầu tính từ ngày giải ngân đến ngày chốt lãi đầu tiên. "
    "Lãi suất được đổi sau đúng số tháng cố định kể từ ngày giải ngân. Ngày thu tiền được hiển thị riêng, "
    "không tự cộng thêm 5 ngày lãi sau ngày chốt lãi."
)

if st.button("TÍNH KẾ HOẠCH TRẢ NỢ", type="primary", use_container_width=True):
    total_months = int(years * 12)
    principal_per_period = principal / total_months
    denominator = 365 if day_basis == "Actual/365" else 360
    revised_rate = deposit_rate + margin
    rows = []
    balance = float(principal)
    previous_interest_date = disbursement

    for k in range(1, int(periods_to_show) + 1):
        # Ngày chốt lãi của kỳ k
        scheduled_interest_date = add_months(disbursement, k)
        scheduled_interest_date = scheduled_interest_date.replace(
day=min(int(interest_day), calendar.monthrange(
                scheduled_interest_date.year, scheduled_interest_date.month
            )[1])
        )
        # Với kỳ đầu, nếu ngày chốt lãi trước ngày giải ngân thì đẩy sang tháng kế tiếp
        if scheduled_interest_date <= previous_interest_date:
            scheduled_interest_date = add_months(scheduled_interest_date, 1)

        # Ngày thu nợ: tháng tương ứng với ngày chốt lãi
        payment_date = scheduled_interest_date.replace(
            day=min(int(payment_day), calendar.monthrange(
                scheduled_interest_date.year, scheduled_interest_date.month
            )[1])
        )

        # Tính lãi theo từng đoạn nếu ngày điều chỉnh lãi suất nằm giữa kỳ
        rate_change_date = add_months(disbursement, int(fixed_months))
        interest = 0.0
        cursor = previous_interest_date
        while cursor < scheduled_interest_date:
            if cursor < rate_change_date:
                segment_end = min(scheduled_interest_date, rate_change_date)
                annual_rate = first_rate / 100
            else:
                segment_end = scheduled_interest_date
                annual_rate = revised_rate / 100
            days = (segment_end - cursor).days
            interest += balance * annual_rate * days / denominator
            cursor = segment_end

        principal_payment = principal_per_period if k < total_months else balance
        principal_payment = min(principal_payment, balance)
        total_payment = principal_payment + interest
        ending_balance = max(0.0, balance - principal_payment)

        rows.append({
            "Kỳ": k,
            "Ngày chốt tính lãi": scheduled_interest_date.strftime("%d/%m/%Y"),
            "Ngày thu nợ": payment_date.strftime("%d/%m/%Y"),
            "Dư nợ gốc đầu kỳ (đồng)": round(balance),
            "Lãi suất áp dụng": f"{first_rate:.2f}%" if scheduled_interest_date <= rate_change_date else f"{revised_rate:.2f}%*",
            "Số ngày tính lãi": (scheduled_interest_date - previous_interest_date).days,
            "Tiền lãi (đồng)": round(interest),
            "Tiền gốc trả (đồng)": round(principal_payment),
            "Tổng tiền trả (đồng)": round(total_payment),
            "Dư nợ gốc cuối kỳ (đồng)": round(ending_balance),
        })
        balance = ending_balance
        previous_interest_date = scheduled_interest_date

    df = pd.DataFrame(rows)
    st.subheader("Kết quả kế hoạch trả nợ")
    c1, c2, c3 = st.columns(3)
    c1.metric("Gốc trả mỗi kỳ (xấp xỉ)", f"{principal_per_period:,.0f} đ")
    c2.metric("Tổng lãi trong các kỳ hiển thị", f"{df['Tiền lãi (đồng)'].sum():,.0f} đ")
c3.metric("Dư nợ cuối kỳ hiển thị", f"{df['Dư nợ gốc cuối kỳ (đồng)'].iloc[-1]:,.0f} đ")

    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Tải bảng kế hoạch trả nợ (CSV)", data=csv, file_name="ke_hoach_tra_no.csv", mime="text/csv")

    st.markdown(
        "**Chú thích:** Dấu * nghĩa là kỳ có thể áp dụng lãi suất mới sau ngày điều chỉnh. "
        "Nếu kỳ tính lãi đi qua ngày điều chỉnh lãi suất, tiền lãi được chia theo số ngày ở từng mức lãi suất."
    )
else:
    st.write("Nhập thông tin khoản vay ở thanh bên trái, sau đó bấm **TÍNH KẾ HOẠCH TRẢ NỢ**.")
