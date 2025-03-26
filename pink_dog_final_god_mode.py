
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress
from io import BytesIO
import base64

# 定义语言切换函数
def tr(zh, en):
    return zh if st.session_state.get("lang", "中文") == "中文" else en

st.set_page_config(page_title="Liu Method Fitting", layout="centered")

# 🌈 设置渐变背景
page_bg = """
<style>
body {
  background: linear-gradient(to bottom right, #ffe0f0, #e0f4ff);
  color: #333333;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

st.title("🔬 Liu 方法拟合工具 / Liu Method Fitting Tool")

st.session_state.lang = st.radio("选择语言 / Choose Language", ["中文", "English"], index=0)

st.markdown(tr(
    "利用烧蚀直径和激光能量数据，自动拟合出光斑半径、阈值能量和通量。",
    "Automatically fit Gaussian beam waist, energy threshold, and fluence threshold from laser ablation data."
))

# 数据输入
col1, col2 = st.columns(2)
def_energy = "10, 15, 22, 33, 50, 75, 110"
def_diameter = "4.1, 5.3, 6.0, 7.0, 8.1, 9.2, 10.1"

with col1:
    energy_input = st.text_area(tr("输入脉冲能量 E (μJ)", "Input pulse energy E (μJ)"), def_energy)
with col2:
    diameter_input = st.text_area(tr("输入烧蚀直径 D (μm)", "Input ablation diameter D (μm)"), def_diameter)

uploaded_file = st.file_uploader(tr("或上传 CSV 文件（两列: E, D）", "Or upload a CSV file (two columns: E, D)"))

if st.button(tr("开始拟合", "Fit Now")):
    try:
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            E_values = df.iloc[:, 0].values
            D_values = df.iloc[:, 1].values
        else:
            E_values = np.array([float(x) for x in energy_input.split(",")])
            D_values = np.array([float(x) for x in diameter_input.split(",")])

        if len(E_values) != len(D_values):
        else:
            D_squared = D_values**2
            ln_E = np.log(E_values)

            slope, intercept, r_value, _, _ = linregress(ln_E, D_squared)
            E_th_val = np.exp(-intercept / slope)
            w0_val = np.sqrt(2 * slope)
            F_th_val = (2 * E_th_val) / (np.pi * w0_val**2)

            st.success(tr("拟合成功 ✅", "Fit successful ✅"))
            st.markdown(f"**{tr('阈值能量 E_th', 'Threshold energy E_th')}** ≈ `{E_th:.2f}` μJ")
            st.markdown(f"**{tr('光斑半径 w₀', 'Beam waist w₀')}** ≈ `{w0:.2f}` μm")
            st.markdown(f"**{tr('阈值通量 F_th', 'Fluence threshold F_th')}** ≈ `{F_th:.5f}` J/cm²")
            st.markdown(f"**R² 值 / R-squared** ≈ `{r_value**2:.4f}`")

            fig, ax = plt.subplots()
            ln_E_fit = np.linspace(ln_E.min(), ln_E.max(), 100)
            D_fit = slope * ln_E_fit + intercept
            ax.scatter(ln_E, D_squared, color='blue', label=tr('实验数据', 'Experimental Data'))
            ax.plot(ln_E_fit, D_fit, color='red', label=tr('线性拟合', 'Linear Fit'))
            ax.set_xlabel('ln(E)')
            ax.set_ylabel('D² (μm²)')
            ax.set_title(tr('Liu 方法拟合图', 'Liu Method Fit'))
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

            df_out = pd.DataFrame({
                'Pulse Energy (μJ)': E_values,
                'ln(E)': ln_E,
                'Ablation Diameter (μm)': D_values,
                'D² (μm²)': D_squared
            })
            st.dataframe(df_out)

            # Excel 下载按钮
            towrite = BytesIO()
            with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
                df_out.to_excel(writer, index=False, sheet_name='Raw Data')
                pd.DataFrame({
                    'E_th (μJ)': [E_th_val],
                    'w0 (μm)': [w0_val],
                    'F_th (J/cm²)': [F_th_val],
                    'R²': [r_value**2]
                }).to_excel(writer, index=False, sheet_name='Fit Result')
                writer.save()
            towrite.seek(0)
            st.download_button(tr("📥 下载 Excel", "📥 Download Excel"), towrite, file_name="liu_fit_results.xlsx")

    except Exception as e: